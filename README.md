# Voice-Guided OS (Text-Guided Desktop Controller)

A Python application that uses text commands to control your desktop through an LLM-powered visual understanding system. The system analyzes screenshots, determines actions, and executes precise mouse clicks using a progressive grid-based refinement approach.

## 🎯 Overview

This project enables you to control your macOS desktop using natural language commands. Simply describe what you want to do (e.g., "Open Chrome", "Click the submit button", "Navigate to settings"), and the system will:

1. Capture a screenshot of your screen
2. Use GPT-4 Vision to analyze the screenshot and determine the next action
3. Use a three-stage grid system (3x3 → 3x3 → 3x3) to precisely locate click targets
4. Execute the action (click, type, button press) and repeat until the task is complete

## 🏗️ How It Works

### Architecture

The system follows a modular architecture with the following key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN CONTROL LOOP                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Capture Screenshot                                      │
│     ↓                                                        │
│  2. Send to LLM with command → Get Action Plan              │
│     ↓                                                        │
│  3. Execute action based on type:                           │
│     - Mouse actions (left/right/double-click):              │
│       a. Overlay 3x3 grid → LLM selects cell (Stage 1)     │
│       b. Crop cell, overlay 3x3 grid → LLM refines (Stage 2)│
│       c. Crop cell, overlay 3x3 grid → LLM refines (Stage 3)│
│       d. Calculate center point and execute click          │
│     - Keyboard actions:                                      │
│       a. Type text or press button directly                │
│     ↓                                                        │
│  4. Repeat until COMPLETE/ERROR                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Three-Stage Grid Refinement

The system uses a progressive three-stage refinement approach for precise click targeting:

1. **Stage 1 - 3x3 Grid Selection**: The full screen is divided into a 3x3 grid (columns 1-3, rows A-C). The LLM selects the cell containing the target element.

2. **Stage 2 - 3x3 Refinement**: The selected cell from Stage 1 is cropped and divided into another 3x3 grid. The LLM refines the selection to narrow down the target area.

3. **Stage 3 - 3x3 Final Refinement**: The selected cell from Stage 2 is cropped and divided into a final 3x3 grid. The LLM makes the final selection to pinpoint the exact click location.

4. **Click Execution**: The center of the final Stage 3 cell is calculated and the click is executed.

This three-stage approach provides high precision while maintaining efficiency, allowing the LLM to progressively narrow down from the full screen to a precise click target.

### Action Loop

The main control loop runs iteratively:

- Each iteration captures a new screenshot to see the current state
- The LLM analyzes the screenshot and determines the next action
- Actions can be:
  - `MOUSE_LEFT_CLICK`: Left click at a specific location (requires three-stage grid selection)
  - `MOUSE_RIGHT_CLICK`: Right click at a specific location (requires three-stage grid selection)
  - `MOUSE_DOUBLE_CLICK`: Double click at a specific location (requires three-stage grid selection)
  - `KEYBOARD_TYPE`: Type text into the focused field
  - `KEYBOARD_BUTTON_PRESS`: Press a special keyboard button (enter, tab, escape, etc.)
  - `COMPLETE`: Task is finished
  - `ERROR`: Task cannot be completed (with reason)
- The loop continues until COMPLETE or ERROR, or until max iterations (20) is reached

## 📋 Requirements

- **OS**: macOS (primary monitor only)
- **Python**: 3.8+ (uses local conda environment in `./env/`)
- **Permissions**: Screen recording and accessibility permissions must be granted
- **API Key**: OpenAI API key with access to GPT-4 Vision models

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd voice-guided-os
   ```

2. **Set up Python environment**:
   ```bash
   # Create conda environment (or use your preferred method)
   conda create -n voice-guided-os python=3.8
   conda activate voice-guided-os
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure API key**:
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Grant permissions**:
   - System Preferences → Security & Privacy → Privacy
   - Enable "Screen Recording" for Terminal/Python
   - Enable "Accessibility" for Terminal/Python

## 💻 Usage

Run the application:

```bash
python main.py
```

The application will start in terminal mode. Enter your commands at the prompt:

```
Enter command: Open Chrome
Enter command: Click the search bar
Enter command: Navigate to settings
```

### Command Examples

- `"Open Chrome"` - Opens the Chrome application
- `"Click the submit button"` - Clicks a submit button on the screen
- `"Right-click on the file"` - Opens context menu for a file
- `"Double-click the document"` - Opens a document
- `"Type 'Hello World' in the search bar"` - Types text into a search field
- `"Press Enter"` - Presses the Enter key
- `"Navigate to the settings menu"` - Finds and clicks settings
- `"Close the dialog"` - Closes an open dialog window
- `"Click on the first search result"` - Clicks the first result in a search

The system will:
1. Capture a screenshot
2. Analyze it with the LLM to determine the appropriate action
3. Execute the action (click, type, or button press) using the three-stage grid system for mouse actions
4. Repeat until the task is complete

Press `Ctrl+C` to exit.

## 📁 Project Structure

```
voice-guided-os/
├── main.py                     # Entry point and main control loop
├── config.py                   # Configuration and environment variables
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
│
├── modules/
│   ├── __init__.py
│   ├── screenshot.py          # Screenshot capture (mss-based)
│   ├── llm_client.py            # GPT-4 Vision API communication
│   ├── action_executor.py       # Mouse and keyboard action execution
│   ├── grid_processor.py       # Grid overlay and coordinate calculation
│   ├── execution_logger.py      # Execution logging and PDF generation
│   └── ui.py                    # Optional GUI interface (tkinter-based)
│
├── prompts/
│   ├── action_prompt.txt        # Prompt for action determination
│   └── grid_selection.txt       # Prompt for 3x3 grid selection (all stages)
│
├── utils/
│   └── __init__.py              # Utility modules
│
└── execution/                  # Auto-generated execution logs
    └── <timestamp>/             # One folder per command run
        ├── command.txt          # Original user command
        ├── step_01_complete.pdf # Complete documentation for step 1
        ├── step_02_complete.pdf # Complete documentation for step 2
        └── ...
```

## 🔧 Configuration

Key settings in `config.py`:

- **LLM Model**: `gpt-4o` (GPT-4 Vision)
- **Grid Size**: 3x3 for all three stages (Stage 1, Stage 2, Stage 3)
- **Max Iterations**: 20 (prevents infinite loops)
- **Action Delay**: 1.0 second (wait time after each action)
- **Click Marker**: Red circle with 15px radius

## 📊 Execution Logging

Every command execution is logged with complete documentation:

### Execution Folders

Each command run creates a timestamped folder in `execution/`:
```
execution/
├── 2026-01-11_14-32-05/
│   ├── command.txt
│   ├── step_01_complete.pdf
│   ├── step_02_complete.pdf
│   └── ...
```

### PDF Documentation

Each step generates a comprehensive PDF containing:
- **Main Prompt**: The prompt sent to the LLM for action determination
- **Screenshot**: The screen state before the action
- **Main Response**: The LLM's action plan
- **Stage 1 Grid Selection**: 3x3 grid overlay on full screen and selection
- **Stage 2 Refinement**: 3x3 grid overlay on Stage 1 cell and selection
- **Stage 3 Final Refinement**: 3x3 grid overlay on Stage 2 cell and selection
- **Final Screenshot**: Screen state after action (with red click marker if applicable)

This logging system enables:
- **Debugging**: See exactly what the LLM saw and decided
- **Auditing**: Track all actions taken during execution
- **Improvement**: Analyze failures and refine prompts

## 🧠 LLM Integration

The system uses OpenAI's GPT-4 Vision API with two types of prompts:

1. **Action Determination**: Analyzes the screenshot and user command to determine the next action (click, type, button press, complete, or error)
2. **Grid Selection**: Selects a cell from a 3x3 grid (used in all three stages of refinement for mouse actions)

### Conversation History

The LLM maintains conversation history within a single command execution, allowing it to:
- Remember previous actions taken
- Understand multi-step workflows
- Handle context-dependent commands

### Error Handling

- **Invalid JSON**: Retries with stricter format instructions
- **API Timeouts**: Exponential backoff retry (up to 3 attempts)
- **Invalid Coordinates**: Validates grid selections and raises errors
- **Max Iterations**: Stops after 20 iterations to prevent infinite loops

## 🎯 Key Features

- **Visual Understanding**: Uses GPT-4 Vision to understand screen content
- **Precise Clicking**: Three-stage grid refinement (3x3 → 3x3 → 3x3) for accurate targeting
- **Multiple Action Types**: Supports left-click, right-click, double-click, keyboard typing, and button presses
- **Multi-Step Tasks**: Handles complex workflows automatically
- **Complete Logging**: PDF documentation for every step with all three grid stages
- **Error Recovery**: Handles failures gracefully with retry logic
- **Context Awareness**: Maintains conversation history and action history for context

## ⚠️ Limitations

- **macOS Only**: Designed for macOS (primary monitor)
- **Single Monitor**: Only captures primary display
- **No Drag-and-Drop**: Cannot drag elements or select text ranges
- **No Scrolling**: Cannot scroll to access off-screen elements
- **No Keyboard Shortcuts**: Cannot execute keyboard shortcuts (Cmd+C, Cmd+V, etc.) - only individual button presses
- **No Multi-Key Combinations**: Cannot press modifier key combinations (e.g., Cmd+Tab)

## 🚀 Future Plans

The current implementation supports multiple mouse actions (left-click, right-click, double-click) and basic keyboard input (typing and button presses). Future enhancements will include:

### Advanced Mouse Actions
- **Drag-and-drop**: For moving files, rearranging items, selecting text ranges
- **Hover**: For tooltips and hover-activated menus

### Enhanced Keyboard Actions
- **Keyboard Shortcuts**: Support for system shortcuts (Cmd+C, Ctrl+V, Cmd+Tab, etc.)
- **Multi-Key Combinations**: Support for modifier key combinations (Cmd+Shift+T, etc.)

### Advanced Interactions
- **Scrolling**: Vertical and horizontal scrolling to access off-screen elements. This will enable handling of elements that require scrolling to become visible.
- **Action Chaining**: Automatic sequencing optimizations (e.g., click field → type text → press Enter)
- **Multi-Application Commands**: Enhanced support for commands that span multiple applications (e.g., "Copy text from Safari and paste it in Notes")

### Implementation Considerations for Future Features
- **Focus Management**: Enhanced focus detection and management for typing
- **Timing and Delays**: Adaptive delays based on action type and UI responsiveness
- **Error Recovery**: Advanced retry mechanisms with alternative approaches
- **Grid Optimization**: Consider dynamic grid sizing based on screen resolution and target element size

## 🐛 Troubleshooting

### API Key Issues
- Ensure `.env` file exists with `OPENAI_API_KEY` set
- Verify the API key has access to GPT-4 Vision models

### Permission Issues
- Grant Screen Recording permission in System Preferences
- Grant Accessibility permission in System Preferences

### Click Accuracy Issues
- Check that the target element is visible in screenshots
- Review execution logs to see what the LLM selected at each stage
- The three-stage grid system should provide sufficient precision for most UI elements

### Infinite Loops
- The system stops after 20 iterations automatically
- Check execution logs to see why the loop didn't complete
- Verify the task can be completed with the available action types (clicks, typing, button presses)

