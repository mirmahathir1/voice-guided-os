# Voice-Guided OS (Text-Guided Desktop Controller)

A Python application that uses text commands to control your desktop through an LLM-powered visual understanding system. The system analyzes screenshots, determines actions, and executes precise mouse clicks using a progressive grid-based refinement approach.

## 🎯 Overview

This project enables you to control your macOS desktop using natural language commands. Simply describe what you want to do (e.g., "Open Chrome", "Click the submit button", "Navigate to settings"), and the system will:

1. Capture a screenshot of your screen
2. Use GPT-4 Vision to analyze the screenshot and determine the next action
3. Use a two-stage grid system (10x10 → 2x2) to precisely locate click targets
4. Execute the click and repeat until the task is complete

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
│  3. If action requires click:                               │
│     a. Overlay 10x10 grid → LLM selects cell               │
│     b. Crop cell, overlay 2x2 grid → LLM refines selection │
│     c. Calculate center point and click                    │
│     ↓                                                        │
│  4. Repeat until COMPLETE/ERROR                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Two-Stage Grid Refinement

The system uses a progressive refinement approach for precise click targeting:

1. **10x10 Grid Selection**: The full screen is divided into a 10x10 grid (columns 1-10, rows A-J). The LLM selects the cell containing the target element.

2. **2x2 Refinement**: The selected cell is cropped and divided into a 2x2 grid (columns 1-2, rows A-B). The LLM refines the selection to pinpoint the exact click location.

3. **Click Execution**: The center of the final 2x2 cell is calculated and the click is executed.

This approach balances precision with efficiency, allowing the LLM to make coarse selections first, then refine to pixel-accurate clicks.

### Action Loop

The main control loop runs iteratively:

- Each iteration captures a new screenshot to see the current state
- The LLM analyzes the screenshot and determines the next action
- Actions can be:
  - `MOUSE_LEFT_CLICK`: Click at a specific location (requires grid selection)
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
- `"Navigate to the settings menu"` - Finds and clicks settings
- `"Close the dialog"` - Closes an open dialog window
- `"Click on the first search result"` - Clicks the first result in a search

The system will:
1. Capture a screenshot
2. Analyze it with the LLM
3. Execute the necessary clicks
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
│   ├── action_executor.py       # Mouse click execution
│   ├── grid_processor.py       # Grid overlay and coordinate calculation
│   └── execution_logger.py      # Execution logging and PDF generation
│
├── prompts/
│   ├── action_prompt.txt        # Prompt for action determination
│   ├── grid_selection.txt       # Prompt for 10x10 grid selection
│   └── refinement_prompt.txt    # Prompt for 2x2 refinement
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
- **Grid Size**: 10x10 main grid, 2x2 refinement grid
- **Max Iterations**: 20 (prevents infinite loops)
- **Action Delay**: 1.0 second (wait time after each click)
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
- **Grid Selection**: 10x10 grid overlay and selection
- **Refinement Selection**: 2x2 refinement grid and selection
- **Final Screenshot**: Screen state after click (with red click marker)

This logging system enables:
- **Debugging**: See exactly what the LLM saw and decided
- **Auditing**: Track all actions taken during execution
- **Improvement**: Analyze failures and refine prompts

## 🧠 LLM Integration

The system uses OpenAI's GPT-4 Vision API with three types of prompts:

1. **Action Determination**: Analyzes the screenshot and user command to determine the next action
2. **Grid Selection**: Selects a cell from the 10x10 grid containing the target element
3. **Refinement**: Selects a cell from the 2x2 grid for precise click location

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
- **Precise Clicking**: Two-stage grid refinement for accurate targeting
- **Multi-Step Tasks**: Handles complex workflows automatically
- **Complete Logging**: PDF documentation for every step
- **Error Recovery**: Handles failures gracefully with retry logic
- **Context Awareness**: Maintains conversation history for context

## ⚠️ Limitations

- **Left-Click Only**: Currently supports only left mouse clicks
- **macOS Only**: Designed for macOS (primary monitor)
- **Single Monitor**: Only captures primary display
- **No Keyboard Input**: Cannot type text or use keyboard shortcuts
- **No Right-Click**: Context menus not supported
- **No Drag-and-Drop**: Cannot drag elements

## 🚀 Future Plans

The current implementation is limited to **left-click only** for simplicity and to establish a solid foundation. Future enhancements will include:

### Additional Mouse Actions
- **Double-click**: For opening files, selecting words, etc.
- **Right-click**: For context menus
- **Drag-and-drop**: For moving files, rearranging items, selecting text ranges
- **Hover**: For tooltips and hover-activated menus

### Keyboard Actions
- **Text Input**: Type text into input fields and text areas
- **Keyboard Shortcuts**: Support for system shortcuts (Cmd+C, Ctrl+V, Cmd+Tab, etc.)
- **Special Keys**: Enter, Escape, Tab, Arrow keys, etc.

### Advanced Interactions
- **Scrolling**: Vertical and horizontal scrolling to access off-screen elements. This will enable handling of elements that require scrolling to become visible.
- **Multi-step Sequences**: Complex workflows combining multiple action types
- **Action Chaining**: Automatic sequencing (e.g., click field → type text → press Enter)
- **Multi-Application Commands**: Support for commands that span multiple applications (e.g., "Copy text from Safari and paste it in Notes"). Application switching will be handled by clicking on application icons/windows. Currently limited to left-click only.

### Implementation Considerations for Future Features
- **Action Type Detection**: LLM will need to determine the appropriate action type based on context
- **Focus Management**: For typing, ensure the correct field is focused before input
- **Timing and Delays**: Handle variable response times for different action types
- **Error Recovery**: Retry mechanisms for failed actions with alternative approaches
- **Small Target Precision**: For very small UI elements (checkboxes, close buttons), consider whether a third refinement level beyond the 2x2 grid is needed for sufficient precision

## 🐛 Troubleshooting

### API Key Issues
- Ensure `.env` file exists with `OPENAI_API_KEY` set
- Verify the API key has access to GPT-4 Vision models

### Permission Issues
- Grant Screen Recording permission in System Preferences
- Grant Accessibility permission in System Preferences

### Click Accuracy Issues
- Check that the target element is visible in screenshots
- Review execution logs to see what the LLM selected
- Adjust grid sizes in `config.py` if needed

### Infinite Loops
- The system stops after 20 iterations automatically
- Check execution logs to see why the loop didn't complete
- Verify the task can be completed with left-clicks only

