"""RGBA chip images for the overlay canvas."""

from __future__ import annotations

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

from multiwindow_ui_hints.style import hex_to_rgb


def neo_chip_photo(
    w: int,
    h: int,
    corner_r: int,
    fill_hex: str,
    box_opacity: float,
    *,
    border_hex: str,
    shadow_hex: str,
    border_width: int,
    shadow_dx: int,
    shadow_dy: int,
    master: tk.Misc | None = None,
) -> tuple[ImageTk.PhotoImage, int]:
    """Rounded chip + hard shadow as RGBA; returns (PhotoImage, pad) for NW placement."""
    pad = max(border_width // 2 + 1, 2)
    dx, dy = shadow_dx, shadow_dy
    sr, sg, sb = hex_to_rgb(shadow_hex)
    fr, fg, fb = hex_to_rgb(fill_hex)
    br, bg, bb = hex_to_rgb(border_hex)
    a = max(0, min(255, int(round(255 * box_opacity))))
    img_w = pad * 2 + w + dx
    img_h = pad * 2 + h + dy
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = max(0, min(corner_r, min(w, h) // 2))
    draw.rounded_rectangle(
        [pad + dx, pad + dy, pad + dx + w, pad + dy + h],
        radius=r,
        fill=(sr, sg, sb, a),
    )
    draw.rounded_rectangle(
        [pad, pad, pad + w, pad + h],
        radius=r,
        fill=(fr, fg, fb, a),
        outline=(br, bg, bb, 255),
        width=max(1, border_width),
    )
    if master is not None:
        return ImageTk.PhotoImage(img, master=master), pad
    return ImageTk.PhotoImage(img), pad
