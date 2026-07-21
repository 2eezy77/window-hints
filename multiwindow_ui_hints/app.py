"""Headless entry: hidden Tk root, full-screen overlay, global keyboard hooks."""

from __future__ import annotations

import ctypes
import signal
import sys
import threading
import time
import tkinter as tk
import traceback

import keyboard

from multiwindow_ui_hints.app_settings import load_hint_app_settings
from multiwindow_ui_hints.constants import HOTKEY_OPEN
from multiwindow_ui_hints.overlay import HintOverlay
from multiwindow_ui_hints.single_instance import exit_if_already_running
from multiwindow_ui_hints.tray_icon import start_tray


def _refresh_scan_cache() -> None:
    """One full UIA walk; updates shared cache (startup warm-up, tray, periodic refresh)."""
    try:
        from multiwindow_ui_hints import scan_cache
        from multiwindow_ui_hints.scan import scan_interactive_elements

        s = load_hint_app_settings()
        t = scan_interactive_elements(max_workers=s.effective_scan_workers())
        if t:
            scan_cache.update(t)
    except Exception:
        pass


def _background_scan_cache() -> None:
    """Warm and periodically refresh the UIA snapshot so the overlay can open instantly."""
    time.sleep(0.25)
    while True:
        _refresh_scan_cache()
        time.sleep(30.0)


def main() -> None:
    exit_if_already_running()
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-toolwindow", True)
    except tk.TclError:
        pass

    settings = load_hint_app_settings()
    hotkey = (settings.hotkey or HOTKEY_OPEN).strip().lower() or HOTKEY_OPEN

    overlay = HintOverlay(root)
    threading.Thread(target=_background_scan_cache, daemon=True, name="ui-hints-scan-cache").start()

    # Keyboard hook IDs — set only after Tk has pumped once (see `after(0, ...)` below).
    hooks: dict = {"hotkey_remove": None, "hook_remove": None}
    kb_reg = {"attempted": False, "ok": False}
    tray_icon: list = [None]  # mutable cell for nested defs / shutdown order

    def _open_overlay() -> None:
        root.after(0, overlay.show)

    def _scan_now_from_tray() -> None:
        threading.Thread(
            target=_refresh_scan_cache,
            daemon=True,
            name="ui-hints-scan-now",
        ).start()

    def _register_keyboard() -> None:
        """Run on the Tk thread after the first event-loop tick — tends to fix flaky `keyboard` init."""
        kb_reg["attempted"] = True
        try:
            hooks["hotkey_remove"] = keyboard.add_hotkey(hotkey, _open_overlay)
            hooks["hook_remove"] = keyboard.hook(overlay.on_global_key)
        except Exception as e:
            kb_reg["ok"] = False
            msg = (
                "Global keyboard hooks failed to register.\n"
                f"{e!s}\n"
                "Try: run this program as Administrator, or close apps using low-level keyboard hooks."
            )
            print(msg, file=sys.stderr)
            print(msg)
            try:
                ctypes.windll.user32.MessageBoxW(
                    None,
                    msg,
                    "Multi-window UI hints — keyboard",
                    0x00000010,
                )
            except Exception:
                pass
            root.after(0, root.quit)
            return
        kb_reg["ok"] = True

    def _shutdown() -> None:
        hr = hooks.get("hotkey_remove")
        hl = hooks.get("hook_remove")
        if hr is not None:
            try:
                keyboard.remove_hotkey(hr)
            except Exception:
                pass
        if hl is not None:
            try:
                keyboard.unhook(hl)
            except Exception:
                pass
        try:
            overlay.hide()
        except Exception:
            pass
        ti = tray_icon[0]
        if ti is not None:
            try:
                ti.stop()
            except Exception:
                pass
            tray_icon[0] = None
        root.destroy()

    # Prime Tk / display so low-level hooks attach reliably on some systems.
    try:
        root.update_idletasks()
        root.update()
    except Exception:
        pass

    root.after(0, _register_keyboard)

    try:
        tray_icon[0] = start_tray(
            on_scan_now=_scan_now_from_tray,
            on_quit=lambda: root.after(0, _shutdown),
        )
    except Exception as e:
        print(
            f"Tray icon could not start ({e!r}); hotkeys still work.",
            file=sys.stderr,
        )

    def _sigint(_signum: int, _frame: object) -> None:
        root.after(0, _shutdown)

    try:
        signal.signal(signal.SIGINT, _sigint)
    except (ValueError, OSError):
        pass

    root.protocol("WM_DELETE_WINDOW", _shutdown)

    try:
        root.mainloop()
    finally:
        hr = hooks.get("hotkey_remove")
        hl = hooks.get("hook_remove")
        if hr is not None:
            try:
                keyboard.remove_hotkey(hr)
            except Exception:
                pass
        if hl is not None:
            try:
                keyboard.unhook(hl)
            except Exception:
                pass
        if tray_icon[0] is not None:
            try:
                tray_icon[0].stop()
            except Exception:
                pass

    if kb_reg["attempted"] and not kb_reg["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "multiwindow_ui_hints crashed; see the console for the traceback.",
                "Multi-window UI hints",
                0x00000010,
            )
        except Exception:
            pass
        raise SystemExit(1) from None
