"""
Action executor module for text-guided desktop controller.
Executes mouse actions (left-click only) using logical pixel coordinates.
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
