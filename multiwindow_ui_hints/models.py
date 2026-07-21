"""Data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class HintTarget:
    code: str
    left: int
    top: int
    right: int
    bottom: int
    wrapper: object


@dataclass
class UiStyle:
    alphabet: str
    box_color: str
    border_color: str
    font_color: str
    selected_font_color: str
    font_size: int
    font_weight: str
    cell_horizontal_padding: int
    cell_vertical_padding: int
    box_border_radius: int
    background_opacity: float
    box_opacity: float
    box_border_opacity: float
    border_thickness: int
    font_name: str
    font_size_overrides: Dict[str, int]
