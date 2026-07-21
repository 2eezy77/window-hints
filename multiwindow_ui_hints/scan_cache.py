"""Thread-safe cache of the last successful UIA scan for instant overlay paint."""

from __future__ import annotations

import threading
import time
from typing import List, Optional

from multiwindow_ui_hints.models import HintTarget

_lock = threading.Lock()
_cached: Optional[List[HintTarget]] = None
_cache_mono: float = 0.0


def update(targets: List[HintTarget]) -> None:
    global _cached, _cache_mono
    with _lock:
        _cached = list(targets)
        _cache_mono = time.monotonic()


def peek_fresh(max_age_sec: float) -> Optional[List[HintTarget]]:
    """Return a shallow copy of cached targets if younger than max_age_sec."""
    with _lock:
        if not _cached:
            return None
        if time.monotonic() - _cache_mono > max_age_sec:
            return None
        return list(_cached)
