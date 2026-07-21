"""User-editable settings: JSON persistence merged with optional shared defaults."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from typing import Any, Dict

from multiwindow_ui_hints.constants import (
    HOTKEY_OPEN,
    MAX_SCAN_WORKERS,
    NEO_BORDER_WIDTH,
    NEO_BOX_OPACITY,
    NEO_CORNER_RADIUS,
    NEO_FILL,
    NEO_FILL_ACTIVE,
    NEO_FONT_FAMILY,
    NEO_SHADOW_DX,
    NEO_SHADOW_DY,
    NEO_SHADOW,
    NEO_BORDER,
    NEO_TEXT,
    NEO_TEXT_DIM,
)
from multiwindow_ui_hints.models import UiStyle
from multiwindow_ui_hints.paths import USER_SETTINGS_JSON
from multiwindow_ui_hints.style import load_mousemaster_style


@dataclass
class HintAppSettings:
    """User-tunable fields; overlay reloads from disk each time hints open."""

    hotkey: str = HOTKEY_OPEN
    max_scan_workers: int = 0  # 0 → use MAX_SCAN_WORKERS from constants

    neo_fill: str = NEO_FILL
    neo_fill_active: str = NEO_FILL_ACTIVE
    neo_border: str = NEO_BORDER
    neo_shadow: str = NEO_SHADOW
    neo_text: str = NEO_TEXT
    neo_text_dim: str = NEO_TEXT_DIM
    neo_border_width: int = NEO_BORDER_WIDTH
    neo_shadow_dx: int = NEO_SHADOW_DX
    neo_shadow_dy: int = NEO_SHADOW_DY
    neo_corner_radius: int = NEO_CORNER_RADIUS
    font_family: str = NEO_FONT_FAMILY

    font_size: int = 10
    cell_horizontal_padding: int = 10
    cell_vertical_padding: int = 1
    box_opacity: float = NEO_BOX_OPACITY
    box_border_opacity: float = 1.0

    def effective_scan_workers(self) -> int:
        if self.max_scan_workers and self.max_scan_workers > 0:
            return max(1, min(128, self.max_scan_workers))
        return MAX_SCAN_WORKERS

    def to_ui_style(self) -> UiStyle:
        """UiStyle fields used by overlay sizing / font overrides."""
        mm = load_mousemaster_style()
        return UiStyle(
            alphabet=mm.alphabet,
            box_color=self.neo_fill,
            border_color=self.neo_border,
            font_color=self.neo_text,
            selected_font_color=self.neo_text_dim,
            font_size=self.font_size,
            font_weight=mm.font_weight,
            cell_horizontal_padding=self.cell_horizontal_padding,
            cell_vertical_padding=self.cell_vertical_padding,
            box_border_radius=self.neo_corner_radius,
            background_opacity=mm.background_opacity,
            box_opacity=self.box_opacity,
            box_border_opacity=self.box_border_opacity,
            border_thickness=self.neo_border_width,
            font_name=self.font_family,
            font_size_overrides=mm.font_size_overrides,
        )


def default_hint_settings() -> HintAppSettings:
    """Baseline from optional shared style + built-in Neo defaults."""
    return _defaults_from_mousemaster()


def _defaults_from_mousemaster() -> HintAppSettings:
    mm = load_mousemaster_style()
    return HintAppSettings(
        hotkey=HOTKEY_OPEN,
        max_scan_workers=0,
        neo_fill=NEO_FILL,
        neo_fill_active=NEO_FILL_ACTIVE,
        neo_border=NEO_BORDER,
        neo_shadow=NEO_SHADOW,
        neo_text=NEO_TEXT,
        neo_text_dim=NEO_TEXT_DIM,
        neo_border_width=NEO_BORDER_WIDTH,
        neo_shadow_dx=NEO_SHADOW_DX,
        neo_shadow_dy=NEO_SHADOW_DY,
        neo_corner_radius=NEO_CORNER_RADIUS,
        font_family=mm.font_name or NEO_FONT_FAMILY,
        font_size=mm.font_size,
        cell_horizontal_padding=mm.cell_horizontal_padding,
        cell_vertical_padding=mm.cell_vertical_padding,
        box_opacity=float(mm.box_opacity),
        box_border_opacity=float(mm.box_border_opacity),
    )


def _coerce_field(name: str, value: Any) -> Any:
    if value is None:
        return None
    for f in fields(HintAppSettings):
        if f.name != name:
            continue
        t = f.type
        if t is int:
            return int(value)
        if t is float:
            return float(value)
        if t is str:
            return str(value).strip()
        break
    return value


def load_hint_app_settings() -> HintAppSettings:
    base = _defaults_from_mousemaster()
    if not USER_SETTINGS_JSON.exists():
        return base
    try:
        raw: Dict[str, Any] = json.loads(USER_SETTINGS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return base
    data = asdict(base)
    for k, v in raw.items():
        if k not in data:
            continue
        coerced = _coerce_field(k, v)
        if coerced is not None:
            data[k] = coerced
    return HintAppSettings(**data)


def save_hint_app_settings(settings: HintAppSettings) -> None:
    USER_SETTINGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(settings)
    USER_SETTINGS_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
