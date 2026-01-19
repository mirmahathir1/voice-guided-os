"""
Execution logging module for text-guided desktop controller.
Handles creation of timestamped execution folders and saving of all artifacts
including screenshots, prompts, responses, and click markers.
"""

import os
import json
from datetime import datetime
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import config


class ExecutionLogger:
    """
    Manages execution logging and artifact storage for each command run.
    """
    
    def __init__(self):
        """Initialize the execution logger."""
        self.execution_folder = None
        self.step_counter = 0
        self.base_dir = config.EXECUTION_LOG_DIR
        
        # Store step data in memory instead of saving files
        self.step_data = {}  # step_number -> {screenshot, prompt, response, grid, etc.}
        
        # Track temporary files for cleanup after PDF generation
        self.temp_files = []
        
        # Ensure execution directory exists
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_execution_folder(self):
        """
        Create a timestamped folder for the current execution run.
        
        Returns:
            str: Path to the created execution folder
        """
        # Generate timestamp in format: YYYY-MM-DD_HH-MM-SS
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.execution_folder = os.path.join(self.base_dir, timestamp)
        os.makedirs(self.execution_folder, exist_ok=True)
        
        # Reset step counter for new execution
        self.step_counter = 0
        self.step_data = {}  # Clear previous step data
        self.temp_files = []  # Clear temp files list
        
        return self.execution_folder
    
    def save_command(self, command):
        """
        Save the original user command to command.txt.
        
        Args:
            command (str): The user's text command
        """
        if not self.execution_folder:
            raise ValueError("Execution folder not created. Call create_execution_folder() first.")
        
        command_path = os.path.join(self.execution_folder, "command.txt")
        with open(command_path, "w", encoding="utf-8") as f:
            f.write(command)
    
    def _get_step_prefix(self):
        """
        Get the current step prefix (e.g., "step_01").
        
        Returns:
            str: Step prefix string
        """
        self.step_counter += 1
        return f"step_{self.step_counter:02d}"
    
    def save_screenshot(self, image, step=None, suffix=""):
        """
        Store a screenshot in memory (not saved to disk).
        
        Args:
            image (PIL.Image): Screenshot image to store
            step (int, optional): Step number. If None, auto-increments
            suffix (str, optional): Additional suffix (e.g., "grid_stage1", "grid_stage2", "grid_stage3")
        
        Returns:
            str: Virtual path (for compatibility)
        """
        if not self.execution_folder:
            raise ValueError("Execution folder not created. Call create_execution_folder() first.")
        
        # Use provided step or auto-increment
        if step is not None:
            step_num = step
        else:
            step_num = self.step_counter + 1
            self.step_counter = step_num
        
        # Initialize step data if needed
        if step_num not in self.step_data:
            self.step_data[step_num] = {}
        
        # Store image in memory
        if suffix:
            key = f"screenshot_{suffix}"
        else:
            key = "screenshot"
        
        self.step_data[step_num][key] = image.copy()  # Store a copy
        
        # Return virtual path for compatibility
        step_prefix = f"step_{step_num:02d}"
        if suffix:
            return f"{step_prefix}_{suffix}.png"
        else:
            return f"{step_prefix}_screenshot.png"
    
    def save_prompt(self, prompt_text, step=None):
        """
        Store LLM prompt in memory (not saved to disk).
        
        Args:
            prompt_text (str): The prompt text sent to LLM
            step (int, optional): Step number. If None, auto-increments
        
        Returns:
            str: Virtual path (for compatibility)
        """
        if not self.execution_folder:
            raise ValueError("Execution folder not created. Call create_execution_folder() first.")
        
        # Use provided step or auto-increment
        if step is not None:
            step_num = step
        else:
            step_num = self.step_counter + 1
            self.step_counter = step_num
        
        # Initialize step data if needed
        if step_num not in self.step_data:
            self.step_data[step_num] = {}
        
        # Store prompt in memory
        self.step_data[step_num]["prompt"] = prompt_text
        
        # Return virtual path for compatibility
        step_prefix = f"step_{step_num:02d}"
        return f"{step_prefix}_prompt.txt"
    
    def save_response(self, response_json, step=None):
        """
        Store LLM response in memory (not saved to disk).
        
        Args:
            response_json (dict or str): The LLM response (dict or JSON string)
            step (int, optional): Step number. If None, auto-increments
        
        Returns:
            str: Virtual path (for compatibility)
        """
        if not self.execution_folder:
            raise ValueError("Execution folder not created. Call create_execution_folder() first.")
        
        # Use provided step or auto-increment
        if step is not None:
            step_num = step
        else:
            step_num = self.step_counter + 1
            self.step_counter = step_num
        
        # Initialize step data if needed
        if step_num not in self.step_data:
            self.step_data[step_num] = {}
        
        # Convert to dict if string
        if isinstance(response_json, str):
            response_dict = json.loads(response_json)
        else:
            response_dict = response_json
        
        # Store response in memory
        self.step_data[step_num]["response"] = response_dict
        
        # Return virtual path for compatibility
        step_prefix = f"step_{step_num:02d}"
        return f"{step_prefix}_response.json"
    
    def draw_click_marker(self, image, x, y):
        """
        Draw a red circled dot at the click coordinates on the image.
        
        Args:
            image (PIL.Image): Image to draw on (will be copied, not modified)
            x (int): X coordinate of click
            y (int): Y coordinate of click
        
        Returns:
            PIL.Image: New image with red click marker drawn
        """
        # Create a copy to avoid modifying the original
        marked_image = image.copy()
        draw = ImageDraw.Draw(marked_image)
        
        # Get marker configuration
        radius = config.CLICK_MARKER_RADIUS
        color = config.CLICK_MARKER_COLOR
        
        # Draw red circle outline
        bbox = (x - radius, y - radius, x + radius, y + radius)
        draw.ellipse(bbox, outline=color, width=2)
        
        # Draw filled red dot at center
        dot_radius = 3
        dot_bbox = (x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius)
        draw.ellipse(dot_bbox, fill=color)
        
        return marked_image
    
    def save_final_screenshot(self, image, click_x=None, click_y=None, step=None):
        """
        Store final screenshot with optional red click marker in memory (not saved to disk).
        
        Args:
            image (PIL.Image): Final screenshot image
            click_x (int, optional): X coordinate where click was executed. If None, no marker is drawn.
            click_y (int, optional): Y coordinate where click was executed. If None, no marker is drawn.
            step (int, optional): Step number. If None, uses current step
        
        Returns:
            str: Virtual path (for compatibility)
        """
        if not self.execution_folder:
            raise ValueError("Execution folder not created. Call create_execution_folder() first.")
        
        # Draw click marker on image only if coordinates are provided
        if click_x is not None and click_y is not None:
            marked_image = self.draw_click_marker(image, click_x, click_y)
        else:
            marked_image = image.copy()
        
        # Determine step number
        if step is None:
            step = self.step_counter
        
        # Initialize step data if needed
        if step not in self.step_data:
            self.step_data[step] = {}
        
        # Store final screenshot in memory
        self.step_data[step]["final_screenshot"] = marked_image
        
        return "final_screenshot.png"
    
    def get_current_step(self):
        """
        Get the current step number without incrementing.
        
        Returns:
            int: Current step number
        """
        return self.step_counter
    
    def reset_step_counter(self):
        """Reset the step counter to 0."""
        self.step_counter = 0
    
    def save_grid_prompt(self, prompt_text, step):
        """Store grid selection prompt in memory."""
        if step not in self.step_data:
            self.step_data[step] = {}
        self.step_data[step]["grid_prompt"] = prompt_text
    
    def save_grid_response(self, response_json, step):
        """Store grid selection response in memory."""
        if step not in self.step_data:
            self.step_data[step] = {}
        if isinstance(response_json, str):
            response_dict = json.loads(response_json)
        else:
            response_dict = response_json
        self.step_data[step]["grid_response"] = response_dict
    
    def save_refinement_prompt(self, prompt_text, step, stage=2):
        """Store refinement prompt in memory for stage 2 or 3."""
        if step not in self.step_data:
            self.step_data[step] = {}
        key = f"refinement_prompt_stage{stage}"
        self.step_data[step][key] = prompt_text
    
    def save_refinement_response(self, response_json, step, stage=2):
        """Store refinement response in memory for stage 2 or 3."""
        if step not in self.step_data:
            self.step_data[step] = {}
        if isinstance(response_json, str):
            response_dict = json.loads(response_json)
        else:
            response_dict = response_json
        key = f"refinement_response_stage{stage}"
        self.step_data[step][key] = response_dict
    
    def _add_image_to_pdf(self, story, image, heading_text, heading_style):
        """Helper to add an image to PDF with proper sizing and high quality."""
        story.append(Paragraph(heading_text, heading_style))
        
        # Use higher DPI for better quality (150 DPI instead of 72)
        # This allows us to keep more detail even when scaling down
        target_dpi = 150
        
        # Max dimensions: 4.5 inches wide x 7 inches tall (conservative for margins)
        # Calculate max pixels at target DPI
        max_width_px = int(4.5 * target_dpi)  # 675 pixels at 150 DPI
        max_height_px = int(7.0 * target_dpi)  # 1050 pixels at 150 DPI
        
        img_width, img_height = image.size
        
        # Calculate scaling to fit within bounds
        width_scale = max_width_px / img_width if img_width > 0 else 1.0
        height_scale = max_height_px / img_height if img_height > 0 else 1.0
        scale = min(width_scale, height_scale, 1.0)  # Don't scale up
        
        # Resize image if needed, using high-quality resampling
        if scale < 1.0:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            # Use LANCZOS for high-quality downscaling (best quality, slower)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save image temporarily for reportlab - use absolute path
        # Save with high DPI to preserve quality
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png', dir=self.execution_folder)
        os.close(temp_fd)  # Close the file descriptor, we'll use the path
        
        # Save with high DPI setting - this helps reportlab render at better quality
        image.save(temp_path, dpi=(target_dpi, target_dpi), format='PNG', optimize=False)
        
        # Use absolute path for reportlab
        abs_temp_path = os.path.abspath(temp_path)
        
        # Track temp file for cleanup after PDF generation
        self.temp_files.append(abs_temp_path)
        
        # Calculate display size in points (1 inch = 72 points)
        # Use the actual image dimensions but convert from pixels at target_dpi to points
        display_width = (image.size[0] / target_dpi) * 72  # Convert pixels to points
        display_height = (image.size[1] / target_dpi) * 72
        
        # Constrain to max display size
        max_display_width = 4.5 * inch
        max_display_height = 7.0 * inch
        
        if display_width > max_display_width:
            scale_factor = max_display_width / display_width
            display_width = max_display_width
            display_height = display_height * scale_factor
        
        if display_height > max_display_height:
            scale_factor = max_display_height / display_height
            display_height = max_display_height
            display_width = display_width * scale_factor
        
        rl_img = RLImage(abs_temp_path, width=display_width, height=display_height)
        story.append(rl_img)
        story.append(Spacer(1, 0.1 * inch))
    
    def generate_step_pdf(self, step):
        """
        Generate a PDF document for a specific step containing all prompts, responses, and images.
        Uses in-memory data instead of reading files from disk.
        
        Args:
            step (int): Step number to generate PDF for
        
        Returns:
            str: Path to the generated PDF file, or None if no data found
        """
        if not self.execution_folder:
            raise ValueError("Execution folder not created. Call create_execution_folder() first.")
        
        # Get step data from memory
        if step not in self.step_data or not self.step_data[step]:
            return None
        
        step_data = self.step_data[step]
        
        step_prefix = f"step_{step:02d}"
        pdf_path = os.path.join(self.execution_folder, f"{step_prefix}_complete.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#000000',
            spaceAfter=12,
            alignment=TA_LEFT
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#333333',
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#000000',
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Courier'
        )
        
        # Add title
        title = Paragraph(f"Step {step} - Complete Documentation", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        # Add main prompt
        if 'prompt' in step_data:
            story.append(Paragraph("Main Prompt", heading_style))
            prompt_text = step_data['prompt']
            # Escape HTML special characters
            prompt_text = prompt_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Convert newlines to <br/> tags to preserve formatting
            prompt_text = prompt_text.replace('\n', '<br/>')
            prompt_para = Paragraph(prompt_text, body_style)
            story.append(prompt_para)
            story.append(Spacer(1, 0.1 * inch))
        
        # Add main screenshot (before response)
        if 'screenshot' in step_data:
            self._add_image_to_pdf(story, step_data['screenshot'], "Screenshot", heading_style)
        
        # Add main response (after screenshot)
        if 'response' in step_data:
            story.append(Paragraph("Main Response", heading_style))
            response_text = json.dumps(step_data['response'], indent=2, ensure_ascii=False)
            response_text = response_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            response_para = Paragraph(response_text, body_style)
            story.append(response_para)
            story.append(Spacer(1, 0.1 * inch))
        
        # Add stage 1 grid selection section if exists
        if 'screenshot_grid_stage1' in step_data or 'grid_prompt' in step_data or 'grid_response' in step_data:
            story.append(PageBreak())
            story.append(Paragraph("Stage 1: Grid Selection (3x3)", heading_style))
            
            if 'grid_prompt' in step_data:
                story.append(Paragraph("Grid Selection Prompt", heading_style))
                grid_prompt_text = step_data['grid_prompt']
                # Escape HTML special characters
                grid_prompt_text = grid_prompt_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Convert newlines to <br/> tags to preserve formatting
                grid_prompt_text = grid_prompt_text.replace('\n', '<br/>')
                grid_prompt_para = Paragraph(grid_prompt_text, body_style)
                story.append(grid_prompt_para)
                story.append(Spacer(1, 0.1 * inch))
            
            if 'grid_response' in step_data:
                story.append(Paragraph("Grid Selection Response", heading_style))
                grid_response_text = json.dumps(step_data['grid_response'], indent=2, ensure_ascii=False)
                grid_response_text = grid_response_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                grid_response_para = Paragraph(grid_response_text, body_style)
                story.append(grid_response_para)
                story.append(Spacer(1, 0.1 * inch))
            
            if 'screenshot_grid_stage1' in step_data:
                self._add_image_to_pdf(story, step_data['screenshot_grid_stage1'], "Stage 1: Grid Overlay Screenshot", heading_style)
        
        # Add stage 2 refinement section if exists
        if 'screenshot_grid_stage2' in step_data or 'refinement_prompt_stage2' in step_data or 'refinement_response_stage2' in step_data:
            story.append(PageBreak())
            story.append(Paragraph("Stage 2: Refinement Selection (3x3)", heading_style))
            
            if 'refinement_prompt_stage2' in step_data:
                story.append(Paragraph("Stage 2 Prompt", heading_style))
                refinement_prompt_text = step_data['refinement_prompt_stage2']
                # Escape HTML special characters
                refinement_prompt_text = refinement_prompt_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Convert newlines to <br/> tags to preserve formatting
                refinement_prompt_text = refinement_prompt_text.replace('\n', '<br/>')
                refinement_prompt_para = Paragraph(refinement_prompt_text, body_style)
                story.append(refinement_prompt_para)
                story.append(Spacer(1, 0.1 * inch))
            
            if 'refinement_response_stage2' in step_data:
                story.append(Paragraph("Stage 2 Response", heading_style))
                refinement_response_text = json.dumps(step_data['refinement_response_stage2'], indent=2, ensure_ascii=False)
                refinement_response_text = refinement_response_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                refinement_response_para = Paragraph(refinement_response_text, body_style)
                story.append(refinement_response_para)
                story.append(Spacer(1, 0.1 * inch))
            
            if 'screenshot_grid_stage2' in step_data:
                self._add_image_to_pdf(story, step_data['screenshot_grid_stage2'], "Stage 2: Cropped Cell with 3x3 Grid", heading_style)
        
        # Add stage 3 refinement section if exists
        if 'screenshot_grid_stage3' in step_data or 'refinement_prompt_stage3' in step_data or 'refinement_response_stage3' in step_data:
            story.append(PageBreak())
            story.append(Paragraph("Stage 3: Final Refinement Selection (3x3)", heading_style))
            
            if 'refinement_prompt_stage3' in step_data:
                story.append(Paragraph("Stage 3 Prompt", heading_style))
                refinement_prompt_text = step_data['refinement_prompt_stage3']
                # Escape HTML special characters
                refinement_prompt_text = refinement_prompt_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Convert newlines to <br/> tags to preserve formatting
                refinement_prompt_text = refinement_prompt_text.replace('\n', '<br/>')
                refinement_prompt_para = Paragraph(refinement_prompt_text, body_style)
                story.append(refinement_prompt_para)
                story.append(Spacer(1, 0.1 * inch))
            
            if 'refinement_response_stage3' in step_data:
                story.append(Paragraph("Stage 3 Response", heading_style))
                refinement_response_text = json.dumps(step_data['refinement_response_stage3'], indent=2, ensure_ascii=False)
                refinement_response_text = refinement_response_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                refinement_response_para = Paragraph(refinement_response_text, body_style)
                story.append(refinement_response_para)
                story.append(Spacer(1, 0.1 * inch))
            
            if 'screenshot_grid_stage3' in step_data:
                self._add_image_to_pdf(story, step_data['screenshot_grid_stage3'], "Stage 3: Cropped Cell with 3x3 Grid", heading_style)
        
        # Add final screenshot if exists (shows result after click)
        if 'final_screenshot' in step_data:
            story.append(PageBreak())
            self._add_image_to_pdf(story, step_data['final_screenshot'], "Final Screenshot (After Click)", heading_style)
        
        # Build PDF
        doc.build(story)
        
        # Clean up temporary files after PDF is generated
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                # Log but don't fail if cleanup fails
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
        
        # Clear temp files list for this step
        self.temp_files = []
        
        return pdf_path
