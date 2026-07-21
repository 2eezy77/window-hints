"""Scan visible windows for interactive UIA elements."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from pywinauto import Desktop

# One full scan at a time (warm-up + hotkey share UIA/COM safely).
_scan_lock = threading.Lock()

from multiwindow_ui_hints.constants import (
    CONTROL_TYPES,
    EXCLUDED_TOP_LEVEL_CLASSES,
    HINT_ALPHABET,
    MAX_SCAN_WORKERS,
    MAX_TWO_LETTER_CODES,
)
from multiwindow_ui_hints.codes import generate_hint_codes
from multiwindow_ui_hints.models import HintTarget
from multiwindow_ui_hints.semantic_uia import scan_interactive_descendants_semantic
from multiwindow_ui_hints.win32_extra import is_window_really_visible_on_desktop, virtual_screen_bounds


def _elem_control_type_short(elem: object) -> str:
    try:
        return str(elem.element_info.control_type)
    except Exception:
        pass
    try:
        n = elem.ControlTypeName
        if isinstance(n, str) and n.endswith("Control"):
            return n[:-7]
        return str(n)
    except Exception:
        return ""


def scan_interactive_elements(max_workers: int | None = None) -> List[HintTarget]:
    with _scan_lock:
        return _scan_interactive_elements_impl(max_workers)


def _scan_interactive_elements_impl(max_workers: int | None = None) -> List[HintTarget]:
    com_inited = False
    try:
        try:
            import pythoncom

            pythoncom.CoInitialize()
            com_inited = True
        except Exception:
            pass

        workers = max_workers if max_workers and max_workers > 0 else MAX_SCAN_WORKERS
        vx1, vy1, vx2, vy2 = virtual_screen_bounds()
        desktop = Desktop(backend="uia")
        windows = desktop.windows(visible_only=True)
        candidates = []
        seen = set()

        eligible_windows = []
        for window in windows:
            try:
                class_name = (window.element_info.class_name or "").strip()
                if class_name in EXCLUDED_TOP_LEVEL_CLASSES:
                    continue
                if not window.is_visible() or window.element_info.control_type not in {"Window", "Pane"}:
                    continue
                if not is_window_really_visible_on_desktop(window):
                    continue
                eligible_windows.append(window)
            except Exception:
                continue

        def _scan_window(window) -> List[Tuple[int, int, str, object, object]]:
            com_worker = False
            try:
                import pythoncom

                pythoncom.CoInitialize()
                com_worker = True
            except Exception:
                pass
            try:
                hwnd = 0
                try:
                    hwnd = int(window.handle)
                except Exception:
                    pass
                if hwnd:
                    sem = scan_interactive_descendants_semantic(
                        hwnd, vx1, vy1, vx2, vy2, CONTROL_TYPES
                    )
                    if sem is not None:
                        return sem

                local = []
                try:
                    for elem in window.descendants():
                        try:
                            if not elem.is_visible() or not elem.is_enabled():
                                continue
                            ctype = elem.element_info.control_type
                            if ctype not in CONTROL_TYPES:
                                continue
                            rect = elem.rectangle()
                            if rect.width() < 8 or rect.height() < 8:
                                continue
                            if rect.right < vx1 or rect.left > vx2 or rect.bottom < vy1 or rect.top > vy2:
                                continue
                            name = elem.element_info.name or ""
                            local.append((rect.top, rect.left, name, elem, rect))
                        except Exception:
                            continue
                except Exception:
                    return []
                return local
            finally:
                if com_worker:
                    try:
                        import pythoncom

                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        try:
            with ThreadPoolExecutor(max_workers=min(workers, max(1, len(eligible_windows)))) as executor:
                futures = [executor.submit(_scan_window, w) for w in eligible_windows]
                for fut in as_completed(futures):
                    for item in fut.result():
                        _, _, name, elem, rect = item
                        ctype = _elem_control_type_short(elem)
                        key = (rect.left, rect.top, rect.right, rect.bottom, ctype, name)
                        if key in seen:
                            continue
                        seen.add(key)
                        candidates.append(item)
        except Exception:
            for w in eligible_windows:
                for item in _scan_window(w):
                    _, _, name, elem, rect = item
                    ctype = _elem_control_type_short(elem)
                    key = (rect.left, rect.top, rect.right, rect.bottom, ctype, name)
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(item)

        def _stable_key(item: Tuple[int, int, str, object, object]) -> Tuple:
            top, left, name, elem, rect = item
            try:
                w, h = rect.width(), rect.height()
                ctype = _elem_control_type_short(elem)
            except Exception:
                w, h, ctype = 0, 0, ""
            return (top, left, w, h, name or "", ctype)

        candidates.sort(key=_stable_key)

        max_targets = min(len(candidates), MAX_TWO_LETTER_CODES)
        candidates = candidates[:max_targets]
        codes = generate_hint_codes(len(candidates), alphabet=HINT_ALPHABET)
        targets: List[HintTarget] = []
        for i, (_, _, _, wrapper, rect) in enumerate(candidates):
            targets.append(
                HintTarget(
                    code=codes[i],
                    left=int(rect.left),
                    top=int(rect.top),
                    right=int(rect.right),
                    bottom=int(rect.bottom),
                    wrapper=wrapper,
                )
            )
        return targets
    finally:
        if com_inited:
            try:
                import pythoncom

                pythoncom.CoUninitialize()
            except Exception:
                pass
