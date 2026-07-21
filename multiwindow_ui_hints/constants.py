"""Shared constants for UI hint scanning and Neobrutalism chip rendering."""

from __future__ import annotations

import ctypes
import os

# Keep UIA bounds and overlay coordinates aligned on multi-monitor / mixed-DPI setups.
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# Speed-optimized letter order: home row → top row → bottom row (alternating hands, common rolls).
HINT_ALPHABET = "asdfghjklqwertyuiopzxcvbnm"
MAX_TWO_LETTER_CODES = len(HINT_ALPHABET) ** 2

CONTROL_TYPES = frozenset(
    {
        "Button",
        "Hyperlink",
        "Edit",
        "ComboBox",
        "CheckBox",
        "RadioButton",
        "ListItem",
        "MenuItem",
        "TabItem",
        "TreeItem",
        "DataItem",
    }
)

EXCLUDED_TOP_LEVEL_CLASSES = frozenset(
    {
        "Progman",
        "WorkerW",
        "Shell_TrayWnd",
        "Shell_SecondaryTrayWnd",
    }
)

# Parallel UIA window scans: 2× logical CPUs, capped (override via user_settings.json).
MAX_SCAN_WORKERS = min(128, max(8, (os.cpu_count() or 4) * 2))

# Instant overlay: show last scan if younger than this (seconds); async refresh still runs.
SCAN_CACHE_MAX_AGE_SEC = 4.0

# Neobrutalism hint chips — inspired by https://dribbble.com/shots/20764973-Neobrutalism-UI-How-to
NEO_FILL = "#B8A1F8"
NEO_FILL_ACTIVE = "#FFE566"
NEO_BORDER = "#000000"
NEO_SHADOW = "#000000"
NEO_TEXT = "#000000"
NEO_TEXT_DIM = "#2D2D2D"
NEO_BORDER_WIDTH = 3
NEO_SHADOW_DX = 3
NEO_SHADOW_DY = 3
NEO_CORNER_RADIUS = 7
NEO_FONT_FAMILY = "Segoe UI"
NEO_BOX_OPACITY = 1.0

HOTKEY_OPEN = "ctrl+shift+alt"
