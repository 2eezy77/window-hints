"""System tray: quit cleanly and trigger a one-shot UIA cache refresh."""

from __future__ import annotations

import sys
import threading
import traceback
from typing import Callable

import pystray
from PIL import Image, ImageDraw

_TRAY_TOOLTIP = "Multi-window UI hints"


def _tray_image() -> Image.Image:
    """Small Neo-style chip; RGB for reliable Windows / pystray backends."""
    size = 64
    img = Image.new("RGB", (size, size), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (4, 4, 59, 59),
        radius=12,
        fill=(184, 161, 248),
        outline=(0, 0, 0),
        width=2,
    )
    return img


def start_tray(
    *,
    on_scan_now: Callable[[], None],
    on_quit: Callable[[], None],
) -> pystray.Icon:
    """
    Run the tray icon on a daemon thread. Callers should invoke ``on_quit`` on the Tk
    thread (e.g. ``root.after(0, ...)``) from the Quit menu item.
    """

    def _scan(_icon: pystray.Icon, _item: object) -> None:
        on_scan_now()

    def _quit(_icon: pystray.Icon, _item: object) -> None:
        on_quit()

    menu = pystray.Menu(
        pystray.MenuItem("Scan now", _scan),
        pystray.MenuItem("Quit", _quit),
    )
    icon = pystray.Icon(
        "multiwindow_ui_hints",
        _tray_image(),
        _TRAY_TOOLTIP,
        menu,
    )

    def _run() -> None:
        try:
            icon.run()
        except Exception:
            traceback.print_exc()
            print(
                "Tray icon thread crashed; the app may lack a tray. Hotkeys still work.",
                file=sys.stderr,
            )

    threading.Thread(target=_run, daemon=True, name="ui-hints-tray").start()
    return icon
