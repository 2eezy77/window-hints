"""Load hint styling from an optional shared properties file."""

from __future__ import annotations

import re
from typing import Dict, Tuple

from multiwindow_ui_hints.constants import HINT_ALPHABET, NEO_BOX_OPACITY
from multiwindow_ui_hints.models import UiStyle
from multiwindow_ui_hints.paths import MOUSEMASTER_PROPERTIES


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def load_mousemaster_style() -> UiStyle:
    defaults = UiStyle(
        alphabet=HINT_ALPHABET,
        box_color="#204E8A",
        border_color="#FFFFFF",
        font_color="#FFFFFF",
        selected_font_color="#CCCCCC",
        font_size=10,
        font_weight="bold",
        cell_horizontal_padding=10,
        cell_vertical_padding=1,
        box_border_radius=3,
        background_opacity=0.35,
        box_opacity=NEO_BOX_OPACITY,
        box_border_opacity=1.0,
        border_thickness=1,
        font_name="Segoe UI",
        font_size_overrides={},
    )
    if not MOUSEMASTER_PROPERTIES.exists():
        return defaults

    raw: Dict[str, str] = {}
    for line in MOUSEMASTER_PROPERTIES.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        raw[key.strip()] = value.strip()

    alias = raw.get("key-alias.hint1key.us-qwerty", "")
    if alias:
        defaults.alphabet = "".join(token for token in alias.split(" ") if len(token) == 1)

    defaults.box_color = raw.get("ui-hint-mode.hint.box-color", defaults.box_color)
    defaults.font_color = raw.get("ui-hint-mode.hint.font-color", defaults.font_color)
    defaults.selected_font_color = raw.get(
        "ui-hint-mode.hint.selected-font-color", defaults.selected_font_color
    )
    defaults.font_weight = raw.get("ui-hint-mode.hint.font-weight", defaults.font_weight).lower()
    defaults.font_size = int(raw.get("ui-hint-mode.hint.font-size", defaults.font_size))
    defaults.cell_horizontal_padding = int(
        raw.get("ui-hint-mode.hint.cell-horizontal-padding", defaults.cell_horizontal_padding)
    )
    defaults.cell_vertical_padding = int(
        raw.get("ui-hint-mode.hint.cell-vertical-padding", defaults.cell_vertical_padding)
    )
    defaults.box_border_radius = int(
        raw.get("ui-hint-mode.hint.box-border-radius", defaults.box_border_radius)
    )
    defaults.background_opacity = float(
        raw.get("ui-hint-mode.hint.background-opacity", defaults.background_opacity)
    )
    defaults.box_opacity = float(raw.get("ui-hint-mode.hint.box-opacity", defaults.box_opacity))
    defaults.box_border_opacity = float(
        raw.get("ui-hint-mode.hint.box-border-opacity", defaults.box_border_opacity)
    )
    defaults.border_color = raw.get("ui-hint-mode.hint.box-border-color", defaults.border_color)
    defaults.border_thickness = int(
        raw.get("ui-hint-mode.hint.box-border-thickness", defaults.border_thickness)
    )
    defaults.font_name = raw.get("ui-hint-mode.hint.font-name", defaults.font_name)

    for key, value in raw.items():
        match = re.match(r"ui-hint-mode\.hint\.font-size\.(\d+x\d+)$", key)
        if match:
            defaults.font_size_overrides[match.group(1)] = int(value)
    return defaults
