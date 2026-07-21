"""Filesystem paths shared by the app."""

from __future__ import annotations

from pathlib import Path

# Package lives in tools/multiwindow-ui-hints/multiwindow_ui_hints/
_TOOLS_ROOT = Path(__file__).resolve().parent.parent.parent
MOUSEMASTER_PROPERTIES = _TOOLS_ROOT / "mousemaster" / "mousemaster.properties"
# multiwindow-ui-hints/user_settings.json
_PKG_DIR = Path(__file__).resolve().parent.parent
USER_SETTINGS_JSON = _PKG_DIR / "user_settings.json"
