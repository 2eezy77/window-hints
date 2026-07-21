"""Filesystem paths shared by the app."""

from __future__ import annotations

import os
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent.parent
USER_SETTINGS_JSON = _PKG_DIR / "user_settings.json"

_mousemaster_override = os.environ.get("UI_HINTS_MOUSEMASTER_PROPERTIES", "").strip()
MOUSEMASTER_PROPERTIES = (
    Path(_mousemaster_override).expanduser()
    if _mousemaster_override
    else _PKG_DIR / "mousemaster.properties"
)
