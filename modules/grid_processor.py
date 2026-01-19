"""
Grid processor module for text-guided desktop controller.
Handles grid overlay drawing and coordinate calculations for 3x3 grids.
"""

from PIL import Image, ImageDraw, ImageFont
import config


# Try to load a readable font; fall back to default (no size for load_default)
def _get_font(size=14):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except OSError:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default()


def overlay_3x3_grid(image):
    """
    Draw a labeled 3x3 grid on a copy of the image.
    Columns 1-3 (left to right), Rows A-C (top to bottom).
    Adds white padding on left and bottom for labels, and draws grid in red.

    Args:
        image (PIL.Image): Screenshot or image to overlay

    Returns:
        PIL.Image: New image with 3x3 grid and labels drawn (original unchanged)
    """
    # Original image dimensions
    orig_w, orig_h = image.size
    cols, rows = config.GRID_COLS, config.GRID_ROWS
    cw, ch = orig_w / cols, orig_h / rows
    
    # Calculate padding size (proportional to cell size, minimum 50px)
    left_padding = max(50, int(cw * 0.25))
    bottom_padding = max(40, int(ch * 0.25))
    
    # Create new image with padding
    new_w = orig_w + left_padding
    new_h = orig_h + bottom_padding
    out = Image.new("RGB", (new_w, new_h), "white")
    
    # Paste original image at (left_padding, 0) so padding is on left and bottom
    out.paste(image, (left_padding, 0))
    
    draw = ImageDraw.Draw(out)
    
    # Grid lines (red) - only on the original image area
    for i in range(1, cols):
        x = left_padding + int(i * cw)
        draw.line([(x, 0), (x, orig_h)], fill="red", width=2)
    for i in range(1, rows):
        y = int(i * ch)
        draw.line([(left_padding, y), (left_padding + orig_w, y)], fill="red", width=2)
    
    # Draw border around the grid area
    draw.rectangle([(left_padding, 0), (left_padding + orig_w, orig_h)], outline="red", width=2)

    font = _get_font(min(24, max(16, int(cw * 0.6))))

    # Column labels 1-3 in bottom padding area
    for j in range(cols):
        x = left_padding + (j + 0.5) * cw
        try:
            bbox = draw.textbbox((0, 0), str(j + 1), font=font)
        except AttributeError:
            bbox = draw.textsize(str(j + 1), font=font)
        tw = bbox[2] - bbox[0] if hasattr(bbox, '__len__') and len(bbox) >= 3 else 10
        draw.text((int(x - tw / 2), orig_h + 2), str(j + 1), fill="black", font=font)

    # Row labels A-C in left padding area
    for i in range(rows):
        label = chr(ord("A") + i)
        y = (i + 0.5) * ch
        try:
            bbox = draw.textbbox((0, 0), label, font=font)
        except AttributeError:
            bbox = draw.textsize(label, font=font)
        th = (bbox[3] - bbox[1]) if hasattr(bbox, '__len__') and len(bbox) >= 4 else 12
        draw.text((left_padding // 2, int(y - th / 2)), label, fill="black", font=font)

    return out


def get_cell_bounds(grid_ref, image_size, grid_cols=None, grid_rows=None):
    """
    Compute pixel bounds (x1, y1, x2, y2) for a grid cell.

    Args:
        grid_ref (dict): {"X": "1"-"3", "Y": "A"-"C"}
        image_size (tuple): (width, height) of the image
        grid_cols (int, optional): Number of columns (default: config.GRID_COLS for 3x3)
        grid_rows (int, optional): Number of rows (default: config.GRID_ROWS for 3x3)

    Returns:
        tuple: (x1, y1, x2, y2) in pixel coordinates
    """
    if grid_cols is None:
        grid_cols = config.GRID_COLS
    if grid_rows is None:
        grid_rows = config.GRID_ROWS

    width, height = image_size
    cw, ch = width / grid_cols, height / grid_rows

    x_val = str(grid_ref.get("X", "1")).strip()
    y_val = str(grid_ref.get("Y", "A")).strip().upper()

    col = int(x_val) - 1
    row = ord(y_val) - ord("A")

    if col < 0 or col >= grid_cols or row < 0 or row >= grid_rows:
        raise ValueError(f"Grid ref out of range: X={x_val}, Y={y_val} for {grid_cols}x{grid_rows}")

    x1 = int(col * cw)
    y1 = int(row * ch)
    x2 = min(int((col + 1) * cw), width)
    y2 = min(int((row + 1) * ch), height)

    return (x1, y1, x2, y2)


def get_cell_center(cell_bounds):
    """
    Compute the center point of a cell for clicking.

    Args:
        cell_bounds (tuple): (x1, y1, x2, y2)

    Returns:
        tuple: (x, y) integers
    """
    x1, y1, x2, y2 = cell_bounds
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))


def crop_cell(image, cell_bounds):
    """
    Extract the region of the image for the given cell.

    Args:
        image (PIL.Image): Source image
        cell_bounds (tuple): (x1, y1, x2, y2)

    Returns:
        PIL.Image: Cropped image
    """
    return image.crop(cell_bounds)
