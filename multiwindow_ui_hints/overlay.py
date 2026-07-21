"""Full-screen transparent overlay and hint typing."""

from __future__ import annotations

import ctypes
import threading
import tkinter as tk
from typing import List, Tuple

from PIL import ImageTk

from multiwindow_ui_hints.app_settings import HintAppSettings, load_hint_app_settings
from multiwindow_ui_hints.constants import HINT_ALPHABET, SCAN_CACHE_MAX_AGE_SEC
from multiwindow_ui_hints.models import HintTarget
from multiwindow_ui_hints.rendering import neo_chip_photo
from multiwindow_ui_hints import scan_cache
from multiwindow_ui_hints.scan import scan_interactive_elements
from multiwindow_ui_hints.win32_extra import monitor_rects, virtual_screen_bounds


class HintOverlay:
    """Transparent topmost layer; `master` is a hidden `tk.Tk` root (see `app.main`)."""

    def __init__(self, master: tk.Misc) -> None:
        self._hint_settings: HintAppSettings = load_hint_app_settings()
        self.style = self._hint_settings.to_ui_style()
        self.alphabet = self.style.alphabet or HINT_ALPHABET
        self.alphabet_set = set(self.alphabet)

        self.root = tk.Toplevel(master)
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self._transparent_color = "#010203"
        self.root.configure(bg=self._transparent_color)
        self.root.attributes("-transparentcolor", self._transparent_color)
        self.root.attributes("-alpha", 1.0)

        self.canvas = tk.Canvas(self.root, bg=self._transparent_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.targets: List[HintTarget] = []
        self._scan_generation = 0
        self._scan_busy = False
        self.typed = ""
        self._active = False
        self._monitor_rect_cache: List[Tuple[int, int, int, int]] = []
        self._chip_photos: List[ImageTk.PhotoImage] = []

        self.root.bind("<Escape>", lambda _: self.hide())

    def reload_settings_from_disk(self) -> None:
        """Reload `user_settings.json` + optional shared style defaults."""
        self._hint_settings = load_hint_app_settings()
        self.style = self._hint_settings.to_ui_style()

    def show(self) -> None:
        # Second hotkey while overlay is visible: close (same as Esc). Prevents
        # withdraw + rescan + multi-second "disappear then come back" flicker.
        if self._active:
            self.hide()
            return
        # Ignore spam while a scan is already in flight (same hotkey held / repeat).
        if self._scan_busy:
            return

        # Fresh settings + style for this invocation (shared defaults + user JSON).
        self._hint_settings = load_hint_app_settings()
        self.style = self._hint_settings.to_ui_style()
        self.alphabet = HINT_ALPHABET
        self.alphabet_set = set(self.alphabet)

        self._scan_generation += 1
        scan_gen = self._scan_generation
        self.targets = []
        self.typed = ""
        self._monitor_rect_cache = monitor_rects()

        self._active = False
        try:
            self.root.grab_release()
        except Exception:
            pass
        self.root.withdraw()
        self.canvas.delete("all")
        self._chip_photos.clear()

        self._scan_busy = True
        mw = self._hint_settings.effective_scan_workers()

        # Fresh snapshot → paint immediately; full scan still runs to refresh + refill cache.
        cached = scan_cache.peek_fresh(SCAN_CACHE_MAX_AGE_SEC)
        if cached:
            self._show_overlay_content(list(cached))

        self._start_async_scan(scan_gen, mw)

    def _show_overlay_content(self, targets: List[HintTarget]) -> None:
        """Map geometry, draw chips, then show window (caller must hold valid targets)."""
        if not targets:
            return
        self.targets = list(targets)
        x1, y1, x2, y2 = virtual_screen_bounds()
        self.root.geometry(f"{x2 - x1}x{y2 - y1}+{x1}+{y1}")
        self._active = True
        self._draw_once()
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.grab_set()
        self.root.focus_force()
        self.root.update_idletasks()

    def _on_scan_done(self, generation: int, fresh: List[HintTarget] | None) -> None:
        try:
            if generation != self._scan_generation:
                return
            if fresh is not None and fresh:
                scan_cache.update(fresh)
                self._show_overlay_content(fresh)
        finally:
            if generation == self._scan_generation:
                self._scan_busy = False

    def _start_async_scan(self, generation: int, max_workers: int) -> None:
        def _worker():
            try:
                fresh = scan_interactive_elements(max_workers=max_workers)
            except Exception:
                fresh = None

            def _apply():
                self._on_scan_done(generation, fresh)

            self.root.after(0, _apply)

        threading.Thread(target=_worker, daemon=True).start()

    def hide(self) -> None:
        self._scan_generation += 1
        self._scan_busy = False
        self._active = False
        self.typed = ""
        self.targets = []
        self._chip_photos.clear()
        self.canvas.delete("all")
        try:
            self.root.grab_release()
        except Exception:
            pass
        self.root.withdraw()

    def _filtered_targets(self) -> List[HintTarget]:
        if not self.typed:
            return self.targets
        return [t for t in self.targets if t.code.startswith(self.typed)]

    def _font_size_for_target(self, target: HintTarget) -> int:
        center_x = (target.left + target.right) // 2
        center_y = (target.top + target.bottom) // 2
        for left, top, right, bottom in self._monitor_rect_cache:
            if left <= center_x < right and top <= center_y < bottom:
                key = f"{right - left}x{bottom - top}"
                return self.style.font_size_overrides.get(key, self.style.font_size)
        return self.style.font_size

    def _draw_once(self) -> None:
        """Single full redraw (chips + labels)."""
        hs = self._hint_settings
        self.canvas.delete("all")
        self._chip_photos.clear()
        filtered = self._filtered_targets()
        vx1, vy1, _, _ = virtual_screen_bounds()

        for target in filtered:
            cx = (target.left + target.right) // 2
            cy = (target.top + target.bottom) // 2
            cx_canvas = cx - vx1
            cy_canvas = cy - vy1

            label = target.code
            font_size = self._font_size_for_target(target)
            chip_font = max(8, int(font_size * 0.96))
            pad_h = max(4, min(self.style.cell_horizontal_padding + 2, 10))
            pad_v = max(2, min(self.style.cell_vertical_padding + 2, 6))
            text_width = max(24, int((len(label) * chip_font * 0.58) + (pad_h * 2)))
            text_height = max(20, int(chip_font + (pad_v * 2) + 6))
            r = min(hs.neo_corner_radius, min(text_width, text_height) // 2)

            x = int(cx_canvas - (text_width // 2))
            y = int(cy_canvas - (text_height // 2))

            is_active = bool(self.typed and label.startswith(self.typed))
            fill = hs.neo_fill_active if is_active else hs.neo_fill
            text_color = hs.neo_text_dim if is_active else hs.neo_text

            photo, pad = neo_chip_photo(
                text_width,
                text_height,
                r,
                fill,
                float(hs.box_opacity),
                border_hex=hs.neo_border,
                shadow_hex=hs.neo_shadow,
                border_width=hs.neo_border_width,
                shadow_dx=hs.neo_shadow_dx,
                shadow_dy=hs.neo_shadow_dy,
                master=self.canvas,
            )
            self._chip_photos.append(photo)
            self.canvas.create_image(
                x - pad,
                y - pad,
                image=photo,
                anchor=tk.NW,
            )
            self.canvas.create_text(
                cx_canvas,
                cy_canvas,
                text=label,
                fill=text_color,
                font=(hs.font_family, chip_font, "bold"),
            )

    def _activate_target(self, target: HintTarget) -> None:
        cx = (target.left + target.right) // 2
        cy = (target.top + target.bottom) // 2
        try:
            user32 = ctypes.windll.user32
            user32.SetCursorPos(int(cx), int(cy))
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            user32.mouse_event(0x0004, 0, 0, 0, 0)
            return
        except Exception:
            pass

        try:
            target.wrapper.set_focus()
        except Exception:
            pass
        click = getattr(target.wrapper, "Click", None)
        if callable(click):
            try:
                click(simulateMove=False)
                return
            except Exception:
                pass
        try:
            target.wrapper.click_input()
        except Exception:
            try:
                target.wrapper.invoke()
            except Exception:
                pass

    def _handle_key_name(self, key: str) -> None:
        if not self._active:
            return

        if key in {"backspace", "back space"}:
            self.typed = self.typed[:-1]
            self._draw_once()
            return
        if key == "esc":
            self.hide()
            return
        if not key or key not in self.alphabet_set:
            return

        self.typed += key
        filtered = self._filtered_targets()
        if len(filtered) == 1 and filtered[0].code == self.typed:
            target = filtered[0]
            self.hide()
            self._activate_target(target)
            return

        if not filtered:
            self.typed = self.typed[:-1]
        self._draw_once()

    def on_global_key(self, event) -> None:
        if not self._active:
            return
        key = (event.name or "").lower()
        if not key:
            return
        self.root.after(0, lambda k=key: self._handle_key_name(k))
