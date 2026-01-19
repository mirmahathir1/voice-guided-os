"""
Screenshot capture and processing module.
Handles full screen and region capture for macOS.
"""

import mss
from PIL import Image
import io
import base64


def capture_full_screen():
    """
    Capture a screenshot of the entire primary display.
    
    Returns:
        PIL.Image: Screenshot image of the full screen
    """
    with mss.mss() as sct:
        # Get primary monitor (monitor 1)
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img


def capture_region(x, y, width, height):
    """
    Capture a specific region of the screen.
    
    Args:
        x (int): Left coordinate of the region
        y (int): Top coordinate of the region
        width (int): Width of the region
        height (int): Height of the region
    
    Returns:
        PIL.Image: Screenshot image of the specified region
    """
    with mss.mss() as sct:
        monitor = {
            "top": y,
            "left": x,
            "width": width,
            "height": height
        }
        screenshot = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img


def encode_to_base64(image):
    """
    Encode a PIL Image to base64 string for API transmission.
    
    Args:
        image (PIL.Image): Image to encode
    
    Returns:
        str: Base64-encoded image string
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str
