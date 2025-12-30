#!/usr/bin/env python3
"""
Add a red grid overlay to an image, and add left/bottom white padding that contains
grid markers:
- Left padding: A, B, C, ... (rows)
- Bottom padding: 1, 2, 3, ... (columns)

Example:
  python3 grid_overlay.py \
    --input "Screenshot 2025-12-30 at 12.58.44 AM.png" \
    --output "Screenshot 2025-12-30 at 12.58.44 AM.grid.png" \
    --rows 10 --cols 10 --pad 100
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont


def excel_letters(n: int) -> str:
    """1 -> A, 2 -> B, ..., 26 -> Z, 27 -> AA, ..."""
    if n <= 0:
        raise ValueError("n must be >= 1")
    out = []
    while n:
        n, r = divmod(n - 1, 26)
        out.append(chr(ord("A") + r))
    return "".join(reversed(out))


def clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def load_font(font_size: int) -> ImageFont.ImageFont:
    """
    Prefer a common system font if available, else fall back to Pillow's default.
    """
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, font_size)
        except Exception:
            pass
    return ImageFont.load_default()


@dataclass(frozen=True)
class GridSpec:
    rows: int
    cols: int
    pad_left: int
    pad_bottom: int
    line_width: int
    line_color: Tuple[int, int, int, int]
    text_color: Tuple[int, int, int, int]
    bg_color: Tuple[int, int, int, int]
    font_size: int
    label_margin: int


def draw_grid_with_labels(img: Image.Image, spec: GridSpec) -> Image.Image:
    """
    Returns a new image with added padding, grid lines, and labels.
    Grid is drawn over the original image region (not on the padding).
    """
    if spec.rows <= 0 or spec.cols <= 0:
        raise ValueError("--rows and --cols must be >= 1")
    if spec.pad_left < 0 or spec.pad_bottom < 0:
        raise ValueError("--pad-left/--pad-bottom must be >= 0")

    base = img.convert("RGBA")
    w, h = base.size

    out_w = w + spec.pad_left
    out_h = h + spec.pad_bottom

    out = Image.new("RGBA", (out_w, out_h), spec.bg_color)
    out.paste(base, (spec.pad_left, 0))

    draw = ImageDraw.Draw(out)
    font = load_font(spec.font_size)

    # Grid geometry within original image region
    gx0, gy0 = spec.pad_left, 0
    gx1, gy1 = spec.pad_left + w, h

    cell_w = w / spec.cols
    cell_h = h / spec.rows

    # Draw vertical grid lines
    for c in range(spec.cols + 1):
        x = gx0 + int(round(c * cell_w))
        draw.line([(x, gy0), (x, gy1)], fill=spec.line_color, width=spec.line_width)

    # Draw horizontal grid lines
    for r in range(spec.rows + 1):
        y = gy0 + int(round(r * cell_h))
        draw.line([(gx0, y), (gx1, y)], fill=spec.line_color, width=spec.line_width)

    # Separator lines for padding (optional but helps visually)
    if spec.pad_left > 0:
        draw.line([(spec.pad_left, 0), (spec.pad_left, out_h)], fill=(200, 200, 200, 255), width=1)
    if spec.pad_bottom > 0:
        draw.line([(0, h), (out_w, h)], fill=(200, 200, 200, 255), width=1)

    # Row labels (A, B, C...) centered per row, in left padding
    if spec.pad_left > 0:
        for r in range(spec.rows):
            label = excel_letters(r + 1)
            cy = gy0 + (r + 0.5) * cell_h
            # Right-align near the separator
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = clamp_int(spec.pad_left - spec.label_margin - tw, 0, spec.pad_left - 1)
            y = int(round(cy - th / 2))
            y = clamp_int(y, 0, max(0, h - th))
            draw.text((x, y), label, fill=spec.text_color, font=font)

    # Column labels (1..N) centered per column, in bottom padding
    if spec.pad_bottom > 0:
        for c in range(spec.cols):
            label = str(c + 1)
            cx = gx0 + (c + 0.5) * cell_w
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = int(round(cx - tw / 2))
            x = clamp_int(x, gx0, max(gx0, gx1 - tw))
            y = clamp_int(h + spec.label_margin, h, max(h, out_h - th))
            draw.text((x, y), label, fill=spec.text_color, font=font)

    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Overlay a red grid and add row/column markers on padded white margins.")
    p.add_argument("--input", "-i", required=True, help="Input image path")
    p.add_argument("--output", "-o", required=True, help="Output PNG path")
    p.add_argument("--rows", type=int, default=10, help="Number of grid rows (default: 10)")
    p.add_argument("--cols", type=int, default=10, help="Number of grid columns (default: 10)")
    p.add_argument("--pad", type=int, default=100, help="Padding in pixels for both left and bottom (default: 100)")
    p.add_argument("--pad-left", type=int, default=None, help="Left padding in pixels (overrides --pad)")
    p.add_argument("--pad-bottom", type=int, default=None, help="Bottom padding in pixels (overrides --pad)")
    p.add_argument("--line-width", type=int, default=2, help="Grid line width (default: 2)")
    p.add_argument("--font-size", type=int, default=88, help="Marker font size (default: 88)")
    p.add_argument("--label-margin", type=int, default=12, help="Distance from separator to labels (default: 12)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    in_path = Path(args.input).expanduser()
    out_path = Path(args.output).expanduser()

    pad_left = args.pad_left if args.pad_left is not None else args.pad
    pad_bottom = args.pad_bottom if args.pad_bottom is not None else args.pad

    img = Image.open(in_path)

    spec = GridSpec(
        rows=args.rows,
        cols=args.cols,
        pad_left=pad_left,
        pad_bottom=pad_bottom,
        line_width=max(1, args.line_width),
        line_color=(255, 0, 0, 255),
        text_color=(0, 0, 0, 255),
        bg_color=(255, 255, 255, 255),
        font_size=max(8, args.font_size),
        label_margin=max(0, args.label_margin),
    )

    out = draw_grid_with_labels(img, spec)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure PNG output
    out.convert("RGBA").save(out_path, format="PNG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


