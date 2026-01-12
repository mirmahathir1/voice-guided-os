# Implementation Plan: Text-Guided Desktop Controller

## 📋 Overview

A Python application that uses text commands (via a minimal UI) to control the desktop through an LLM-powered visual understanding system with progressive grid-based click refinement.

---

## 🖥️ Platform & Environment

| Setting | Value |
|---------|-------|
| **Target OS** | macOS only |
| **Permissions** | Assumes screen recording and accessibility permissions are already granted |
| **Monitor Support** | Primary monitor only |
| **Display Scaling** | Uses logical pixels (standard coordinate system) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TEXT-GUIDED DESKTOP CONTROLLER                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  MINIMAL UI                                                          │   │
│  │  ┌────────────────────────────┐ ┌──────┐ ┌──────┐  API Calls: 0      │   │
│  │  │  Text Input Field          │ │ Run  │ │ Stop │                    │   │
│  │  └────────────────────────────┘ └──────┘ └──────┘                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                 │                           │
│                                                 ▼                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        MAIN CONTROL LOOP                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │  1. Capture Screenshot                                          │ │   │
│  │  │  2. Send to LLM with command → Get Action                       │ │   │
│  │  │  3. If action requires click:                                   │ │   │
│  │  │     a. Overlay 10x10 grid → LLM selects cell                    │ │   │
│  │  │     b. Crop cell, overlay 2x2 grid → LLM refines selection      │ │   │
│  │  │     c. Click center of final cell                               │ │   │
│  │  │  4. Repeat until COMPLETE/ERROR                                 │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
text_desktop_controller/
├── main.py                     # Entry point and main loop
├── config.py                   # Configuration and API keys
├── requirements.txt            # Dependencies
│
├── modules/
│   ├── __init__.py
│   ├── ui.py                   # Minimal UI (text field + button)
│   ├── screenshot.py           # Screenshot capture and grid overlay
│   ├── llm_client.py           # GPT API communication
│   ├── action_executor.py      # Mouse/keyboard actions
│   ├── grid_processor.py       # Grid overlay and coordinate calculation
│   └── execution_logger.py     # Execution logging and artifact storage
│
├── prompts/
│   ├── action_prompt.txt       # Prompt for determining action
│   ├── grid_selection.txt      # Prompt for 10x10 grid selection
│   └── refinement_prompt.txt   # Prompt for 2x2 refinement
│
├── execution/                  # Auto-generated execution logs
│   └── <timestamp>/            # One folder per command run (e.g., 2026-01-11_14-32-05)
│       ├── command.txt         # Original user command
│       ├── step_01_screenshot.png
│       ├── step_01_prompt.txt
│       ├── step_01_response.json
│       ├── step_01_grid.png
│       ├── step_01_crop_2x2.png
│       ├── step_02_screenshot.png
│       ├── ...
│       └── final_screenshot.png  # Screenshot with red circled dot at click location
│
└── utils/
    ├── __init__.py
    ├── image_utils.py          # Image processing helpers
    └── logger.py               # Logging configuration
```

---

## 📦 Dependencies

```txt
# requirements.txt

# UI Framework
tkinter                         # Built-in with Python

# Screenshot & Image Processing
Pillow>=10.0.0
pyautogui>=0.9.54
mss>=9.0.1

# LLM API
openai>=1.0.0

# System Control
pynput>=1.7.6

# Utilities
python-dotenv>=1.0.0
```

---

## 🔧 Module Implementation Details

### Module 1: `config.py`

**Purpose**: Centralized configuration management

**Key Configurations**:
- OpenAI API key loaded from environment
- Grid dimensions: 10x10 (rows A-J, columns 1-10)
- Refinement grid: 2x2 (rows A-B, columns 1-2)
- LLM model: gpt-5.2 (assumed available)
- Execution log directory path
- Click marker styling (color: red, radius: 15px)

**LLM API Parameters**:
- Temperature: 0.0 (deterministic responses for consistent actions)
- Max tokens: 256 (sufficient for JSON responses)
- Include previous actions as context for multi-step tasks

---

### Module 2: `modules/ui.py`

**Purpose**: Minimal UI for text command input with execution control

**UI Design**:
```
┌────────────────────────────────────────────────────────────────┐
│  Desktop Controller                                            │
├────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌───────┐  ┌───────┐         │
│  │ Enter command...            │  │  Run  │  │ Stop  │         │
│  └─────────────────────────────┘  └───────┘  └───────┘         │
│                                                                │
│  API Calls: 0                                                  │
└────────────────────────────────────────────────────────────────┘
```

**Key Functions**:
| Function | Description |
|----------|-------------|
| `create_window()` | Initialize tkinter window |
| `get_command()` | Return text from input field |
| `on_submit()` | Callback when button clicked or Enter pressed |
| `on_stop()` | Callback to forcefully stop the current execution |
| `increment_api_counter()` | Increment and update the API call count display |
| `reset_api_counter()` | Reset counter to 0 at start of new command |
| `set_running_state(is_running)` | Enable/disable Run button, enable/disable Stop button |

**Implementation Approach**:
- Create a tkinter window with "always on top" attribute
- Add a text entry field (width ~40 characters)
- Add a "Run" button to start execution
- Add a "Stop" button to forcefully terminate the current run
- Add a label displaying "API Calls: N" counter
- Bind Enter key to trigger submission
- On submit: reset counter, disable Run, enable Stop, invoke callback
- On stop: set a flag to abort the action loop, re-enable Run
- Increment counter each time an LLM API call is made
- Run the tkinter main loop to keep window responsive
- **Minimize window before each screenshot** to avoid capturing the controller UI
- No additional status messages or progress feedback beyond the API counter
- No confirmation dialogs for actions (all actions execute immediately)

---

### Module 3: `modules/screenshot.py`

**Purpose**: Capture and process screenshots

**Key Functions**:
| Function | Description |
|----------|-------------|
| `capture_full_screen()` | Take screenshot of entire display (primary monitor only) |
| `capture_region(x, y, w, h)` | Capture specific screen region |
| `encode_to_base64(image)` | Prepare image for API transmission |

**Screenshot Behavior**:
- The UI window is minimized before taking screenshots to avoid capturing itself
- Only the primary monitor is captured
- Uses logical pixel coordinates (standard macOS coordinate system)

---

### Module 4: `modules/grid_processor.py`

**Purpose**: Handle grid overlay and coordinate calculations

**Key Functions**:
| Function | Description |
|----------|-------------|
| `overlay_10x10_grid(image)` | Draw labeled 10x10 grid on screenshot |
| `overlay_2x2_grid(image)` | Draw 2x2 refinement grid on cropped image |
| `get_cell_bounds(grid_ref, image_size)` | Calculate pixel bounds for cell (e.g., "3", "B") |
| `get_cell_center(cell_bounds)` | Calculate center point for clicking |
| `crop_cell(image, cell_bounds)` | Extract cell region from image |

**Grid Labeling Schema**:
```
    1     2     3     4     5     6     7     8     9    10
  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
A │     │     │     │     │     │     │     │     │     │     │
  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
B │     │     │     │     │     │     │     │     │     │     │
  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  ...
  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
J │     │     │     │     │     │     │     │     │     │     │
  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

**2x2 Refinement Grid**:
```
      1     2
    ┌─────┬─────┐
  A │ A1  │ A2  │
    ├─────┼─────┤
  B │ B1  │ B2  │
    └─────┴─────┘
```

---

### Module 5: `modules/llm_client.py`

**Purpose**: Communicate with GPT-5.2 Vision API

**Key Functions**:
| Function | Description |
|----------|-------------|
| `get_action_plan(screenshot, user_command)` | Determine what action to perform |
| `select_grid_cell(gridded_screenshot, action)` | Get 10x10 cell selection |
| `refine_selection(original, cropped_2x2, action)` | Get 2x2 refinement |
| `parse_llm_response(response)` | Extract JSON from LLM output |

**API Request Approach**:
- Use OpenAI Chat Completions API with gpt-5.2 model
- Include system prompt defining the assistant's role
- Send user message containing both text instruction and base64-encoded screenshot image
- Request JSON response format for structured parsing
- **Include previous actions as context** for multi-step tasks (conversation history within a command execution)
- Parameters: temperature=0.0, max_tokens=256
- No API call budget or throttling limits

---

### Module 6: `modules/action_executor.py`

**Purpose**: Execute mouse and keyboard actions

**Key Functions**:
| Function | Description |
|----------|-------------|
| `click_at(x, y)` | Perform mouse click at coordinates |
| `double_click_at(x, y)` | Double-click at coordinates |
| `type_text(text)` | Type text using keyboard |
| `press_key(key)` | Press special keys (Enter, Escape, etc.) |
| `scroll(direction, amount)` | Scroll up/down |

---

### Module 7: `modules/execution_logger.py`

**Purpose**: Log all execution artifacts for debugging and auditing

**Key Functions**:
| Function | Description |
|----------|-------------|
| `create_execution_folder()` | Create timestamped folder in `execution/` |
| `save_command(command)` | Save original user command to `command.txt` |
| `save_screenshot(image, step, suffix)` | Save screenshot with step number |
| `save_prompt(prompt_text, step)` | Save LLM prompt to text file |
| `save_response(response_json, step)` | Save LLM response to JSON file |
| `save_final_screenshot(image, click_x, click_y)` | Save final screenshot with red circled dot |
| `draw_click_marker(image, x, y)` | Draw red circled dot at click coordinates |

**Folder Naming Convention**:
```
execution/
├── 2026-01-11_14-32-05/    # Format: YYYY-MM-DD_HH-MM-SS
├── 2026-01-11_14-35-22/
└── 2026-01-11_15-01-47/
```

**Step File Naming Convention**:
```
step_01_screenshot.png      # Initial screenshot before action
step_01_prompt.txt          # Prompt sent to LLM
step_01_response.json       # LLM response
step_01_grid.png            # Screenshot with 10x10 grid overlay
step_01_crop_2x2.png        # Cropped cell with 2x2 refinement grid
step_02_screenshot.png      # Screenshot after first action
...
final_screenshot.png        # Final state with red click marker
```

**Red Click Marker Visualization**:
```
        ┌─────────────────┐
        │                 │
        │     ◉ ← Red     │
        │     circled     │
        │     dot at      │
        │     click       │
        │     location    │
        │                 │
        └─────────────────┘
```

**Implementation Approach**:
- On new command: generate timestamp (YYYY-MM-DD_HH-MM-SS format) and create folder
- Maintain a step counter that increments with each action in the loop
- Save screenshots as PNG files with step-prefixed filenames
- Save prompts as plain text files for readability
- Save LLM responses as formatted JSON files
- For final screenshot: draw a red circle outline with a filled red dot at the center marking the click coordinates
- Use Pillow's ImageDraw to render the click marker on a copy of the screenshot

---

## 🔄 Main Control Flow

### `main.py` - Execution Flow

```
START
  │
  ▼
┌─────────────────────────────┐
│  Initialize Components      │
│  - UI window                │
│  - LLM client               │
│  - Screen capturer          │
│  - Execution logger         │
└─────────────────────────────┘
  │
  ▼
┌─────────────────────────────┐
│  Show UI Window             │
│  Wait for text input        │◀─────────────────────┐
└─────────────────────────────┘                      │
  │                                                  │
  ▼                                                  │
┌─────────────────────────────┐                      │
│  User submits command       │                      │
│  → Disable Run button       │                      │
│  → Enable Stop button       │                      │
│  → Reset API counter to 0   │                      │
└─────────────────────────────┘                      │
  │                                                  │
  ▼                                                  │
┌─────────────────────────────┐                      │
│  Create timestamped folder  │                      │
│  Save command.txt           │                      │
└─────────────────────────────┘                      │
  │                                                  │
  ▼                                                  │
┌─────────────────────────────┐                      │
│  ACTION LOOP                │                      │
│  ┌───────────────────────┐  │                      │
│  │ Check if Stop pressed │──┼── If yes → Exit ─────┤
│  └───────────────────────┘  │                      │
│            │                │                      │
│            ▼                │                      │
│  ┌───────────────────────┐  │                      │
│  │ Capture Screenshot    │  │                      │
│  │ → Save to folder      │  │                      │
│  └───────────────────────┘  │                      │
│            │                │                      │
│            ▼                │                      │
│  ┌───────────────────────┐  │                      │
│  │ Send to LLM           │  │                      │
│  │ → Increment counter   │  │                      │
│  │ → Save prompt         │  │                      │
│  │ → Save response       │  │                      │
│  └───────────────────────┘  │                      │
│            │                │                      │
│            ▼                │                      │
│     ┌──────┴──────┐         │                      │
│     │             │         │                      │
│   Click?    COMPLETE/ERROR? │                      │
│     │             │         │                      │
│     ▼             ▼         │                      │
│  ┌────────┐   Exit Loop ────┼──────────────────────┤
│  │ GRID   │                 │                      │
│  │ FLOW   │                 │                      │
│  │ → Save │                 │                      │
│  │  grids │                 │                      │
│  │ → Incr │                 │                      │
│  │  count │                 │                      │
│  └────────┘                 │                      │
│     │                       │                      │
│     ▼                       │                      │
│  ┌───────────────────────┐  │                      │
│  │ Execute Click         │  │                      │
│  │ → Save final with     │  │                      │
│  │   red click marker    │  │                      │
│  └───────────────────────┘  │                      │
│     │                       │                      │
│     ▼                       │                      │
│  Repeat Action Loop ────────┘                      │
│                                                    │
└────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────┐
│  Re-enable Run button       │
│  Disable Stop button        │
│  Ready for next command     │
└─────────────────────────────┘
  │
  ▼
 (Loop back to wait for input)
```

### Grid Selection Sub-Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     GRID SELECTION FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐                                    │
│  │ Capture Screenshot  │                                    │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐                                    │
│  │ Overlay 10x10 Grid  │                                    │
│  │ Labels: X(1-10)     │                                    │
│  │         Y(A-J)      │                                    │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │ Send to LLM         │───▶│ Response:           │         │
│  │ "Select cell for    │    │ {"X": "5", "Y": "C"}│         │
│  │  target action"     │    └─────────────────────┘         │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐                                    │
│  │ Crop Selected Cell  │                                    │
│  │ (Cell 5,C)          │                                    │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐                                    │
│  │ Overlay 2x2 Grid    │                                    │
│  │ on Cropped Cell     │                                    │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │ Send BOTH images:   │───▶│ Response:           │         │
│  │ - Original screen   │    │ {"X": "2", "Y": "A"}│         │
│  │ - Cropped 2x2       │    └─────────────────────┘         │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐                                    │
│  │ Calculate Center    │                                    │
│  │ of Final Cell       │                                    │
│  └─────────────────────┘                                    │
│            │                                                │
│            ▼                                                │
│  ┌─────────────────────┐                                    │
│  │ Execute Click       │                                    │
│  └─────────────────────┘                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 LLM Prompt Templates

### Prompt 1: Action Determination

```markdown
You are a desktop automation assistant. Analyze the screenshot and user command.

USER COMMAND: "{user_command}"

Based on the current screen state, determine the SINGLE next action needed.

Respond in JSON format:
- If an action is needed: {"action": "<description of click/type action>"}
- If task is complete: {"action": "COMPLETE"}
- If task cannot be done: {"action": "ERROR", "reason": "<explanation>"}

Examples:
- {"action": "Click on the Chrome icon in the dock"}
- {"action": "Click on the search bar"}
- {"action": "Type 'Wikipedia' in the search field"}
- {"action": "COMPLETE"}
```

### Prompt 2: 10x10 Grid Selection

```markdown
You are helping locate a UI element on screen.

TARGET ACTION: "{action_description}"

The screenshot has a 10x10 grid overlay:
- X-axis: labeled 1-10 (left to right)
- Y-axis: labeled A-J (top to bottom)

Identify which cell contains the element needed for the target action.

Respond ONLY with JSON: {"X": "<1-10>", "Y": "<A-J>"}
```

### Prompt 3: 2x2 Refinement Selection

```markdown
You are refining a click location.

TARGET ACTION: "{action_description}"

You have two images:
1. Original full screenshot (for context)
2. Cropped cell with 2x2 grid overlay

The 2x2 grid uses the same labeling as the main grid:
- X-axis: labeled 1-2 (left to right)
- Y-axis: labeled A-B (top to bottom)

Select the cell containing the exact click target.

Respond ONLY with JSON: {"X": "<1 or 2>", "Y": "<A or B>"}
```

---

## 🧮 Coordinate Calculation Logic

### 10x10 Grid Cell Bounds

**Approach**:
- Divide screen width by 10 to get cell width
- Divide screen height by 10 to get cell height
- Convert X label (1-10) to zero-based index (0-9)
- Convert Y label (A-J) to zero-based index using ASCII conversion (0-9)
- Calculate cell bounds: top-left corner at (index × cell_size), bottom-right at (top-left + cell_size)
- Return bounding box coordinates (x1, y1, x2, y2)

### 2x2 Refinement Center Calculation

**Approach**:
- Take the 10x10 cell bounds and divide into 4 cells (2×2 grid)
- Each cell is half the width and half the height of the selected 10x10 cell
- Convert X label (1 or 2) and Y label (A or B) to indices, same as main grid logic
- Based on X (1=left, 2=right) and Y (A=top, B=bottom), identify the target cell
- Calculate the center point of that cell
- Return the final (x, y) click coordinates as integers

---

## ⚠️ Error Handling Strategy

| Error Type | Handling Approach |
|------------|-------------------|
| Empty text input | Ignore; wait for valid input |
| API timeout | Retry with exponential backoff (max 3 attempts) |
| Invalid LLM JSON response | Re-prompt LLM with stricter format instructions |
| Click outside screen bounds | Log error; skip action; continue loop |
| Action loop > 20 iterations | Force ERROR state; prevent infinite loops |
| Screenshot capture failure | Retry once; then abort with error message |
| User clicked Stop | Immediately abort action loop; log partial execution; re-enable UI |

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Day 1)
- [ ] Set up project structure
- [ ] Implement `config.py` with environment loading
- [ ] Create `screenshot.py` with basic capture
- [ ] Test screenshot functionality

### Phase 2: Minimal UI (Day 2)
- [ ] Implement `ui.py` with tkinter
- [ ] Create text field and submit button
- [ ] Test command input callback
- [ ] Ensure window stays on top

### Phase 3: Execution Logging (Day 3)
- [ ] Implement `execution_logger.py`
- [ ] Create timestamped folder structure
- [ ] Implement screenshot/prompt/response saving
- [ ] Implement red click marker drawing
- [ ] Test folder creation and file saving

### Phase 4: LLM Integration (Days 4-6)
- [ ] Implement `llm_client.py`
- [ ] Create and test prompt templates
- [ ] Handle JSON parsing and validation
- [ ] Test with sample screenshots

### Phase 5: Grid System (Days 7-9)
- [ ] Implement `grid_processor.py`
- [ ] Create grid overlay drawing functions
- [ ] Implement coordinate calculation
- [ ] Test grid accuracy

### Phase 6: Action Execution (Days 10-11)
- [ ] Implement `action_executor.py`
- [ ] Test click accuracy
- [ ] Add keyboard input support

### Phase 7: Integration (Days 12-14)
- [ ] Implement `main.py` control loop
- [ ] Integrate all modules with execution logging
- [ ] End-to-end testing
- [ ] Verify execution logs are complete and accurate
- [ ] Bug fixes and refinement

---

## 🧪 Testing Checklist

- [ ] UI window displays correctly
- [ ] Text input captures user commands
- [ ] Run button triggers callback
- [ ] Enter key submits command
- [ ] Stop button terminates execution mid-run
- [ ] API call counter increments with each LLM call
- [ ] API call counter resets on new command
- [ ] Run button disabled during execution
- [ ] Stop button enabled during execution
- [ ] Screenshots capture full screen correctly
- [ ] 10x10 grid overlay is accurate and readable
- [ ] LLM returns valid JSON responses
- [ ] Grid coordinate calculations are accurate
- [ ] 2x2 refinement improves click precision
- [ ] Click actions execute at correct positions
- [ ] COMPLETE action terminates loop correctly
- [ ] ERROR action terminates with message
- [ ] No infinite loops occur
- [ ] Primary monitor screenshots captured correctly

### Execution Logging Tests
- [ ] Timestamped folder created for each command run
- [ ] `command.txt` contains original user command
- [ ] All screenshots saved with correct step numbering
- [ ] Prompts saved as readable text files
- [ ] Responses saved as valid JSON files
- [ ] Grid overlay screenshots saved correctly
- [ ] 2x2 crop screenshots saved correctly
- [ ] Final screenshot contains red circled dot
- [ ] Red marker accurately positioned at click coordinates
- [ ] Execution folder structure is browsable and debuggable

---

## 🔐 Security Considerations

1. **API Key Storage**: Use environment variables or `.env` file (never hardcode)
2. **Screenshot Privacy**: Screenshots are sent to OpenAI; warn users about sensitive content
3. **Rate Limiting**: Implement delays between API calls to avoid rate limits

---

This plan provides a complete roadmap for implementing the text-guided desktop controller with a minimal UI and progressive grid-based click refinement.

# Open Questions for Text-Guided Desktop Controller

## Action Handling

1. **Action Types Beyond Click**: The plan mentions typing, scrolling, and key presses, but:
    - How does the LLM decide between click vs. type?
    - What about right-click, double-click, drag-and-drop, hover?
    - How are keyboard shortcuts (Cmd+C, Ctrl+V) handled?

2. **Timing Between Actions**: How long should the system wait after an action before capturing the next screenshot? Some actions (opening apps, loading pages) take variable time.

3. **Typing Target**: When the LLM decides to type text, how does it know where to type? Does it assume the correct field is already focused, or should it click first?

4. **Scroll Parameters**: What constitutes "one scroll"? How many pixels or lines? How does the LLM specify scroll direction and amount?

---

## Grid & Targeting

5. **Elements Spanning Multiple Cells**: What if a button or element spans multiple grid cells? Should the LLM pick the center cell, or is there guidance for this?

6. **Small Targets**: For very small UI elements (checkboxes, close buttons), is the 2x2 refinement sufficient precision? Should there be a third refinement level?

7. **Off-Screen Elements**: What if the target element requires scrolling to become visible? How does the system detect and handle this?

8. **Multiple Matching Elements**: If the command is "click the submit button" and there are multiple submit buttons visible, how should the LLM decide which one?

---

## Error Recovery & Edge Cases

9. **Repeated Failures**: If the LLM keeps selecting wrong cells (click doesn't achieve expected result), is there a retry mechanism with feedback, or does it just continue the loop?

10. **Unexpected Dialogs**: What if a popup, alert, or modal appears during execution? Should the system detect and handle these specially?

11. **Application Crashes**: What if the target application crashes or becomes unresponsive during execution?

12. **Ambiguous Commands**: How should the system handle vague or ambiguous user commands like "do the thing" or "fix it"?

13. **Command Scope**: Can users issue multi-application commands ("Copy text from Safari and paste it in Notes")? If so, how is application switching handled?

---

## Logging & Debugging

14. **Log Retention**: How long should execution logs be kept? Should there be automatic cleanup of old logs?

15. **Log Size**: For long-running commands with many steps, logs could grow large. Is there a limit on steps logged or screenshot compression?

16. **Sensitive Data**: Screenshots may contain passwords, personal data, or confidential information. Should there be a warning, or options to exclude certain areas?

---

## Security & Safety

17. **Dangerous Actions**: Should certain actions be blocked or require confirmation (e.g., clicking "Delete All", "Format Disk", "Send Payment")?

18. **Rate Limiting**: Beyond API rate limits, should there be a limit on actions per minute to prevent runaway automation?

19. **Kill Switch**: Beyond the Stop button, should there be a global keyboard shortcut (e.g., Escape 3x) to abort execution even if the UI is obscured?

---

## Testing & Validation

20. **Validation Dataset**: How will click accuracy be measured? Is there a test suite of known UI elements and expected coordinates?

21. **Regression Testing**: How can prompt changes be tested to ensure they don't break existing functionality?

---

These questions should be resolved before implementation to avoid rework and ensure the system behaves predictably across different scenarios.