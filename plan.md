# Python Voice-Controlled Screen Automation Script - Planning Document

## Overview

This script will create a voice-controlled automation assistant that:
1. Listens for voice commands
2. Captures the current screen state
3. Sends both to a vision-capable LLM
4. Returns structured actions (click coordinates, typing instructions)

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Voice Input    │────▶│  Speech-to-Text  │────▶│                 │
│  (Microphone)   │     │  (Whisper/etc)   │     │                 │
└─────────────────┘     └──────────────────┘     │                 │
                                                  │   LLM (Claude)  │
┌─────────────────┐     ┌──────────────────┐     │   with Vision   │
│  Screen Capture │────▶│  Screenshot      │────▶│                 │
│  (PIL/mss)      │     │  (Base64 encode) │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Execute Action │◀────│  Parse Response  │◀────│  JSON Output    │
│  (pyautogui)    │     │  (Structured)    │     │  (Actions)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Components & Libraries

### 1. Voice Recognition
| Library | Purpose | Notes |
|---------|---------|-------|
| `speech_recognition` | Capture microphone input | Easy API, multiple backends |
| `openai-whisper` | Local transcription | Accurate, runs offline |
| `pyaudio` | Audio stream handling | Required by speech_recognition |

### 2. Screenshot Capture
| Library | Purpose | Notes |
|---------|---------|-------|
| `mss` | Fast screenshot capture | Cross-platform, multi-monitor |
| `Pillow` | Image processing | Resize, encode to base64 |

### 3. LLM Integration
| Library | Purpose | Notes |
|---------|---------|-------|
| `anthropic` | Claude API client | Vision-capable, structured output |

### 4. Action Execution (Optional)
| Library | Purpose | Notes |
|---------|---------|-------|
| `pyautogui` | Mouse/keyboard control | Click, type, scroll |
| `pynput` | Alternative input control | More granular control |

---

## Output Schema

The LLM should return a structured JSON response:

```json
{
  "task_understanding": "User wants to open Chrome and search for weather",
  "actions": [
    {
      "step": 1,
      "action": "click",
      "target": "Chrome icon on taskbar",
      "coordinates": {"x": 450, "y": 1060},
      "confidence": 0.95
    },
    {
      "step": 2,
      "action": "wait",
      "duration_ms": 1000,
      "reason": "Wait for Chrome to open"
    },
    {
      "step": 3,
      "action": "click",
      "target": "URL/Search bar",
      "coordinates": {"x": 960, "y": 52},
      "confidence": 0.90
    },
    {
      "step": 4,
      "action": "type",
      "text": "weather today",
      "target": "Search bar"
    },
    {
      "step": 5,
      "action": "key",
      "key": "enter"
    }
  ],
  "warnings": ["Chrome may take longer to load on slow systems"]
}
```

---

## Module Structure

```
voice_screen_assistant/
├── main.py                 # Entry point, orchestration
├── config.py               # API keys, settings
├── modules/
│   ├── __init__.py
│   ├── voice_capture.py    # Microphone & transcription
│   ├── screen_capture.py   # Screenshot & encoding
│   ├── llm_client.py       # Claude API integration
│   ├── action_parser.py    # Parse LLM response
│   └── action_executor.py  # Execute mouse/keyboard actions
├── prompts/
│   └── system_prompt.txt   # LLM system prompt
└── requirements.txt
```

---

## Key Functions

### `voice_capture.py`
```python
def listen_for_command(timeout=5) -> str:
    """Listen to microphone and return transcribed text"""

def listen_continuous(callback) -> None:
    """Continuous listening with wake word detection"""
```

### `screen_capture.py`
```python
def capture_screen(monitor=0) -> PIL.Image:
    """Capture screenshot of specified monitor"""

def encode_for_llm(image, max_size=1920) -> str:
    """Resize and base64 encode image for API"""
```

### `llm_client.py`
```python
def analyze_screen(
    command: str, 
    screenshot_b64: str,
    screen_resolution: tuple
) -> dict:
    """Send command + screenshot to Claude, return parsed actions"""
```

### `action_executor.py`
```python
def execute_actions(actions: list, dry_run=False) -> None:
    """Execute the sequence of actions"""

def execute_single(action: dict) -> bool:
    """Execute one action (click, type, etc.)"""
```

---

## System Prompt Strategy

The LLM needs a carefully crafted prompt that:

1. **Explains the coordinate system** - Origin at top-left, specify resolution
2. **Defines action types** - click, double_click, right_click, type, key, scroll, wait
3. **Requests confidence scores** - So we can warn on uncertain actions
4. **Handles edge cases** - Element not visible, multiple matches, requires scrolling
5. **Safety constraints** - Avoid destructive actions without confirmation

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        MAIN LOOP                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Listen for voice  │◀─────────────────┐
                    │ command           │                  │
                    └─────────┬─────────┘                  │
                              │                            │
                              ▼                            │
                    ┌───────────────────┐                  │
                    │ Capture screenshot│                  │
                    └─────────┬─────────┘                  │
                              │                            │
                              ▼                            │
                    ┌───────────────────┐                  │
                    │ Send to Claude    │                  │
                    │ (command + image) │                  │
                    └─────────┬─────────┘                  │
                              │                            │
                              ▼                            │
                    ┌───────────────────┐                  │
                    │ Parse response    │                  │
                    └─────────┬─────────┘                  │
                              │                            │
                              ▼                            │
                    ┌───────────────────┐      ┌─────┐     │
                    │ Confirm with user?│─────▶│ No  │─────┘
                    └─────────┬─────────┘      └─────┘
                              │ Yes
                              ▼
                    ┌───────────────────┐
                    │ Execute actions   │
                    │ sequentially      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Report result     │──────────────────┘
                    └───────────────────┘
```

---

## Safety Considerations

| Concern | Mitigation |
|---------|------------|
| Destructive actions | Require confirmation for delete, close, shutdown |
| Credential exposure | Never type into password fields automatically |
| Runaway automation | Keyboard interrupt (Ctrl+C) always active |
| Privacy | Screenshot stays in memory, not saved by default |
| Misclicks | Dry-run mode to preview actions first |

---

## Configuration Options

```python
CONFIG = {
    "voice": {
        "wake_word": "hey assistant",  # Optional trigger phrase
        "timeout": 5,                   # Seconds to listen
        "energy_threshold": 300,        # Mic sensitivity
    },
    "screen": {
        "monitor": 0,                   # Which monitor to capture
        "max_dimension": 1920,          # Resize for API limits
    },
    "llm": {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
    },
    "execution": {
        "dry_run": False,               # Preview only
        "confirm_actions": True,        # Ask before executing
        "action_delay_ms": 100,         # Pause between actions
    }
}
```

---

## Next Steps

Would you like me to:

1. **Build the complete script** - Full implementation with all modules
2. **Start with a specific module** - e.g., just the voice capture or LLM integration
3. **Create a minimal prototype** - Single-file proof of concept
4. **Add specific features** - Wake word detection, multi-monitor support, etc.

Let me know which direction you'd like to take!