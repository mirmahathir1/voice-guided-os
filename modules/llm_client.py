"""
LLM client module for text-guided desktop controller.
Handles communication with OpenAI GPT Vision API for action determination,
grid selection, and refinement.
"""

import os
import json
import re
from openai import OpenAI
import config
from modules.screenshot import encode_to_base64


class LLMClient:
    """
    Client for communicating with OpenAI GPT Vision API.
    Manages conversation history and prompt templates.
    """
    
    def __init__(self):
        """Initialize the LLM client with API key validation."""
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in a .env file or export it as an environment variable."
            )
        
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL
        self.temperature = config.LLM_TEMPERATURE
        self.max_tokens = config.LLM_MAX_TOKENS
        
        # Load prompt templates
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        self.action_prompt_template = self._load_prompt("action_prompt.txt")
        self.grid_selection_template = self._load_prompt("grid_selection.txt")
        
        # Conversation history for multi-step tasks
        self.conversation_history = []
        
        # Track actions taken during execution
        self.action_history = []
    
    def _load_prompt(self, filename):
        """
        Load a prompt template from the prompts directory.
        
        Args:
            filename (str): Name of the prompt file
            
        Returns:
            str: Prompt template content
        """
        filepath = os.path.join(self.prompts_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    def _format_prompt(self, template, **kwargs):
        """
        Format a prompt template with provided variables.
        
        Args:
            template (str): Prompt template string
            **kwargs: Variables to substitute in the template
            
        Returns:
            str: Formatted prompt
        """
        return template.format(**kwargs)
    
    def _make_api_call(self, messages, max_retries=3):
        """
        Make an API call to OpenAI with retry logic.
        
        Args:
            messages (list): List of message dictionaries for the API
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: Response content from the API
            
        Raises:
            Exception: If API call fails after all retries
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"API call failed after {max_retries} attempts: {str(e)}")
                # Exponential backoff: wait 2^attempt seconds
                import time
                time.sleep(2 ** attempt)
        
        raise Exception("API call failed unexpectedly")
    
    def _parse_json_response(self, response_text):
        """
        Parse JSON from LLM response, handling cases where response may contain
        extra text or markdown code blocks.
        
        Args:
            response_text (str): Raw response text from LLM
            
        Returns:
            dict: Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from response: {response_text[:200]}... Error: {str(e)}")
    
    def reset_conversation(self):
        """Reset conversation history for a new command execution."""
        self.conversation_history = []
        self.action_history = []
    
    def add_action(self, action_type, target):
        """
        Add an action to the history.
        
        Args:
            action_type (str): Type of action (e.g., "MOUSE_LEFT_CLICK")
            target (str): Description of what was clicked/targeted
        """
        self.action_history.append({
            "action": action_type,
            "target": target
        })
    
    def _format_action_history(self):
        """Format action history for inclusion in prompt."""
        if not self.action_history:
            return "    None"
        
        formatted = []
        for i, action in enumerate(self.action_history, 1):
            formatted.append(f"    {i}. {{'action': '{action['action']}', 'target': '{action['target']}'}}")
        
        return "\n".join(formatted)
    
    def get_action_plan(self, screenshot, user_command, logger=None):
        """
        Determine what action to perform based on screenshot and user command.
        
        Args:
            screenshot (PIL.Image): Screenshot of the current screen
            user_command (str): User's text command
            logger (ExecutionLogger, optional): Logger for saving prompts/responses
            
        Returns:
            dict: Action plan with "action" key (and optional "reason" for ERROR)
        """
        # Format action history
        action_history_text = self._format_action_history()
        
        # Format the action prompt with action history
        prompt_text = self._format_prompt(
            self.action_prompt_template,
            user_command=user_command,
            action_history=action_history_text
        )
        
        # Encode screenshot to base64
        image_base64 = encode_to_base64(screenshot)
        
        # Build messages with conversation history
        messages = [
            {
                "role": "system",
                "content": "You are a desktop automation assistant. Analyze screenshots and determine actions."
            }
        ]
        
        # Add conversation history for context
        messages.extend(self.conversation_history)
        
        # Add current request
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_text
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        })
        
        # Make API call
        try:
            response_text = self._make_api_call(messages)
            
            # Parse JSON response
            response_json = self._parse_json_response(response_text)
            
            # Validate response structure
            if "action" not in response_json:
                raise ValueError("Response missing 'action' key")
            
            # Handle legacy format: if action is not MOUSE_LEFT_CLICK/COMPLETE/ERROR/KEYBOARD_TYPE/KEYBOARD_BUTTON_PRESS and no target,
            # extract target from action description
            if response_json["action"] not in ["COMPLETE", "ERROR", "MOUSE_LEFT_CLICK", "KEYBOARD_TYPE", "KEYBOARD_BUTTON_PRESS"]:
                # Legacy format: action contains description
                action_desc = response_json["action"]
                response_json["action"] = "MOUSE_LEFT_CLICK"
                response_json["target"] = action_desc
            elif response_json["action"] == "MOUSE_LEFT_CLICK" and "target" not in response_json:
                # New format but missing target - use action description if available
                if "description" in response_json:
                    response_json["target"] = response_json.pop("description")
                else:
                    response_json["target"] = "unknown target"
            elif response_json["action"] == "KEYBOARD_TYPE" and "text" not in response_json:
                # KEYBOARD_TYPE action but missing text - try to extract from description or target
                if "description" in response_json:
                    response_json["text"] = response_json.pop("description")
                elif "target" in response_json:
                    response_json["text"] = response_json.pop("target")
                else:
                    raise ValueError("KEYBOARD_TYPE action requires 'text' parameter")
            elif response_json["action"] == "KEYBOARD_BUTTON_PRESS" and "button" not in response_json:
                # KEYBOARD_BUTTON_PRESS action but missing button - try to extract from description or target
                if "description" in response_json:
                    response_json["button"] = response_json.pop("description")
                elif "target" in response_json:
                    response_json["button"] = response_json.pop("target")
                else:
                    raise ValueError("KEYBOARD_BUTTON_PRESS action requires 'button' parameter")
            
            # Save to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Log if logger provided
            if logger:
                logger.save_prompt(prompt_text)
                logger.save_response(response_json)
            
            return response_json
            
        except Exception as e:
            # If parsing fails, try to re-prompt with stricter instructions
            if "Failed to parse JSON" in str(e):
                return self._retry_with_strict_json(screenshot, user_command, logger)
            raise
    
    def _retry_with_strict_json(self, screenshot, user_command, logger=None):
        """
        Retry action plan request with stricter JSON format instructions.
        
        Args:
            screenshot (PIL.Image): Screenshot of the current screen
            user_command (str): User's text command
            logger (ExecutionLogger, optional): Logger for saving prompts/responses
            
        Returns:
            dict: Action plan
        """
        strict_prompt = f"""You are a desktop automation assistant. Analyze the screenshot and user command.

USER COMMAND: "{user_command}"

Based on the current screen state, determine the SINGLE next action needed.

You MUST respond with ONLY valid JSON, no other text:
- If an action is needed: {{"action": "<description of click action>"}}
- If task is complete: {{"action": "COMPLETE"}}
- If task cannot be done: {{"action": "ERROR", "reason": "<explanation>"}}

Respond with ONLY the JSON object, nothing else."""
        
        image_base64 = encode_to_base64(screenshot)
        
        messages = [
            {
                "role": "system",
                "content": "You are a desktop automation assistant. You must respond with valid JSON only."
            }
        ]
        messages.extend(self.conversation_history)
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": strict_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
            ]
        })
        
        response_text = self._make_api_call(messages)
        response_json = self._parse_json_response(response_text)
        
        if logger:
            logger.save_prompt(strict_prompt)
            logger.save_response(response_json)
        
        return response_json
    
    def select_grid_cell(self, gridded_screenshot, action_description, logger=None, stage=1):
        """
        Get 3x3 grid cell selection from LLM.
        
        Args:
            gridded_screenshot (PIL.Image): Screenshot with 3x3 grid overlay
            action_description (str): Description of the target action
            logger (ExecutionLogger, optional): Logger for saving prompts/responses
            stage (int): Stage number (1, 2, or 3) for logging purposes
            
        Returns:
            dict: Grid selection with "X" (1-3) and "Y" (A-C) keys
        """
        # Format the grid selection prompt
        prompt_text = self._format_prompt(
            self.grid_selection_template,
            action_description=action_description
        )
        
        # Encode screenshot to base64
        image_base64 = encode_to_base64(gridded_screenshot)
        
        messages = [
            {
                "role": "system",
                "content": "You are helping locate UI elements on screen using a 3x3 grid system."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        # Make API call
        response_text = self._make_api_call(messages)
        response_json = self._parse_json_response(response_text)
        
        # Validate response structure
        if "X" not in response_json or "Y" not in response_json:
            raise ValueError("Response missing 'X' or 'Y' key")
        
        # Validate X is 1-3
        x_val = str(response_json["X"]).strip()
        if not x_val.isdigit() or int(x_val) < 1 or int(x_val) > 3:
            raise ValueError(f"Invalid X value: {x_val}. Must be 1-3")
        
        # Validate Y is A-C
        y_val = str(response_json["Y"]).strip().upper()
        if y_val not in "ABC":
            raise ValueError(f"Invalid Y value: {y_val}. Must be A-C")
        
        # Normalize response
        response_json["X"] = x_val
        response_json["Y"] = y_val
        
        # Log if logger provided
        if logger:
            logger.save_prompt(prompt_text)
            logger.save_response(response_json)
        
        return response_json
    
