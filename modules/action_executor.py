"""
Action executor module for text-guided desktop controller.
Executes mouse actions (left-click, right-click, double-click) and keyboard actions using logical pixel coordinates.
"""

import time
import pyautogui
import config


def click_at(x, y):
    """
    Perform a left mouse click at the given coordinates.
    Uses logical pixels (standard macOS coordinate system).
    After the click, waits ACTION_DELAY_SECONDS to allow UI updates
    (dialogs, popups, modals) to appear before the next screenshot.

    Args:
        x (int): X coordinate in screen pixels
        y (int): Y coordinate in screen pixels

    Raises:
        ValueError: If (x, y) is outside the primary screen bounds
    """
    try:
        width, height = pyautogui.size()
    except Exception:
        # If size() fails (e.g. headless), allow the click and let pyautogui handle it
        width, height = 2**31, 2**31

    if x < 0 or y < 0 or x >= width or y >= height:
        raise ValueError(
            f"Click coordinates ({x}, {y}) are outside screen bounds (0,0)-({width},{height})"
        )

    pyautogui.click(x, y)
    time.sleep(config.ACTION_DELAY_SECONDS)


def right_click_at(x, y):
    """
    Perform a right mouse click at the given coordinates.
    Uses logical pixels (standard macOS coordinate system).
    After the click, waits ACTION_DELAY_SECONDS to allow UI updates
    (dialogs, popups, modals) to appear before the next screenshot.

    Args:
        x (int): X coordinate in screen pixels
        y (int): Y coordinate in screen pixels

    Raises:
        ValueError: If (x, y) is outside the primary screen bounds
    """
    try:
        width, height = pyautogui.size()
    except Exception:
        # If size() fails (e.g. headless), allow the click and let pyautogui handle it
        width, height = 2**31, 2**31

    if x < 0 or y < 0 or x >= width or y >= height:
        raise ValueError(
            f"Click coordinates ({x}, {y}) are outside screen bounds (0,0)-({width},{height})"
        )

    pyautogui.rightClick(x, y)
    time.sleep(config.ACTION_DELAY_SECONDS)


def double_click_at(x, y):
    """
    Perform a double mouse click at the given coordinates.
    Uses logical pixels (standard macOS coordinate system).
    After the click, waits ACTION_DELAY_SECONDS to allow UI updates
    (dialogs, popups, modals) to appear before the next screenshot.

    Args:
        x (int): X coordinate in screen pixels
        y (int): Y coordinate in screen pixels

    Raises:
        ValueError: If (x, y) is outside the primary screen bounds
    """
    try:
        width, height = pyautogui.size()
    except Exception:
        # If size() fails (e.g. headless), allow the click and let pyautogui handle it
        width, height = 2**31, 2**31

    if x < 0 or y < 0 or x >= width or y >= height:
        raise ValueError(
            f"Click coordinates ({x}, {y}) are outside screen bounds (0,0)-({width},{height})"
        )

    pyautogui.doubleClick(x, y)
    time.sleep(config.ACTION_DELAY_SECONDS)


def type_text(text):
    """
    Type the given text using the keyboard.
    After typing, waits ACTION_DELAY_SECONDS to allow UI updates.

    Args:
        text (str): Text to type
    """
    if not text:
        return
    
    pyautogui.write(text, interval=0.05)  # Small delay between characters for reliability
    time.sleep(config.ACTION_DELAY_SECONDS)


def press_button(button):
    """
    Press a special keyboard button (non-alphanumeric).
    Supports keys like 'enter', 'tab', 'escape', 'return', 'backspace', etc.
    After pressing, waits ACTION_DELAY_SECONDS to allow UI updates.

    Args:
        button (str): Name of the button to press (e.g., 'enter', 'tab', 'escape')
    
    Raises:
        ValueError: If button name is invalid or not supported
    """
    if not button:
        raise ValueError("Button name cannot be empty")
    
    # Normalize button name to lowercase
    button = button.lower().strip()
    
    # List of valid button names supported by pyautogui
    valid_buttons = [
        'enter', 'return', 'tab', 'escape', 'esc', 'space', 'backspace',
        'delete', 'up', 'down', 'left', 'right', 'home', 'end', 'pageup',
        'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
        'f10', 'f11', 'f12', 'ctrl', 'alt', 'shift', 'cmd', 'command',
        'win', 'windows', 'capslock', 'numlock', 'scrolllock'
    ]
    
    # Check if button is valid
    if button not in valid_buttons:
        raise ValueError(
            f"Invalid button name: {button}. "
            f"Valid buttons include: {', '.join(valid_buttons[:10])}..."
        )
    
    # Map 'esc' to 'escape' for consistency
    if button == 'esc':
        button = 'escape'
    
    pyautogui.press(button)
    time.sleep(config.ACTION_DELAY_SECONDS)
