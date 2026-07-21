"""Windows helpers: virtual screen, monitors, window visibility."""

from __future__ import annotations

import ctypes
from typing import List, Tuple


def virtual_screen_bounds() -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    x = user32.GetSystemMetrics(76)
    y = user32.GetSystemMetrics(77)
    w = user32.GetSystemMetrics(78)
    h = user32.GetSystemMetrics(79)
    return x, y, x + w, y + h


def monitor_rects() -> List[Tuple[int, int, int, int]]:
    rects: List[Tuple[int, int, int, int]] = []
    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.wintypes.HMONITOR,
        ctypes.wintypes.HDC,
        ctypes.POINTER(ctypes.wintypes.RECT),
        ctypes.wintypes.LPARAM,
    )
    user32 = ctypes.windll.user32

    def _enum_cb(hmonitor, hdc, lprc_monitor, lparam):
        rc = lprc_monitor.contents
        rects.append((rc.left, rc.top, rc.right, rc.bottom))
        return 1

    user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(_enum_cb), 0)
    return rects


def rects_intersect(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def is_window_really_visible_on_desktop(window) -> bool:
    try:
        hwnd = int(window.handle)
    except Exception:
        return False

    user32 = ctypes.windll.user32
    if not user32.IsWindowVisible(hwnd):
        return False
    if user32.IsIconic(hwnd):
        return False

    try:
        DWMWA_CLOAKED = 14
        cloaked = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            ctypes.wintypes.HWND(hwnd),
            DWMWA_CLOAKED,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked),
        )
        if cloaked.value != 0:
            return False
    except Exception:
        pass

    try:
        rect = window.rectangle()
    except Exception:
        return False
    if rect.width() <= 1 or rect.height() <= 1:
        return False

    wr = (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))
    return rects_intersect(wr, virtual_screen_bounds())
