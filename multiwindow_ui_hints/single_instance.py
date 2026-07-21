"""Single running instance via localhost socket bind (no Win32 mutex quirks)."""

from __future__ import annotations

import os
import socket
import sys

# If another process already bound this port, another copy is running (or something else used the port).
_LOCK_HOST = "127.0.0.1"
_LOCK_PORT = 58471

_lock_socket: socket.socket | None = None


def _console_or_messagebox(msg: str) -> None:
    print(msg, file=sys.stderr)
    print(msg)
    if not (sys.stdout and sys.stdout.isatty()) and not (sys.stderr and sys.stderr.isatty()):
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                None, msg, "Multi-window UI hints", 0x00000040
            )
        except Exception:
            pass


def exit_if_already_running() -> None:
    """Bind a localhost TCP port; if busy, another instance is already using it."""
    global _lock_socket
    e = os.environ.get("UI_HINTS_ALLOW_MULTI", "").strip().lower()
    if e in ("1", "true", "yes", "on"):
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((_LOCK_HOST, _LOCK_PORT))
        s.listen(8)
    except OSError:
        s.close()
        msg = (
            "multiwindow_ui_hints is already running (or port %d is in use).\n\n"
            "Quit from the tray (right-click → Quit), end the python.exe running this app, "
            "or set UI_HINTS_ALLOW_MULTI=1 to skip this check.\n\n"
            "Port: %s:%d"
            % (_LOCK_PORT, _LOCK_HOST, _LOCK_PORT)
        )
        _console_or_messagebox(msg)
        raise SystemExit(2)

    _lock_socket = s
