"""Two-letter hint code assignment."""

from __future__ import annotations

from typing import Dict, List, Tuple

from multiwindow_ui_hints.constants import HINT_ALPHABET, MAX_TWO_LETTER_CODES


def generate_hint_codes(count: int, alphabet: str = HINT_ALPHABET) -> List[str]:
    """Only two-letter codes, ordered for fast typing (home row / low-repeat / interleaved prefixes)."""
    count = min(count, MAX_TWO_LETTER_CODES)
    rank = {ch: i for i, ch in enumerate(alphabet)}

    def _code_sort_key(code: str) -> Tuple[int, Tuple[int, ...]]:
        repeats = len(code) - len(set(code))
        return (repeats, tuple(rank[ch] for ch in code))

    all_pairs = [a + b for a in alphabet for b in alphabet]
    all_pairs.sort(key=_code_sort_key)

    buckets: Dict[str, List[str]] = {ch: [] for ch in alphabet}
    for candidate in all_pairs:
        buckets[candidate[0]].append(candidate)
    interleaved: List[str] = []
    bucket_index = {ch: 0 for ch in alphabet}
    while True:
        progressed = False
        for ch in alphabet:
            idx = bucket_index[ch]
            if idx < len(buckets[ch]):
                interleaved.append(buckets[ch][idx])
                bucket_index[ch] += 1
                progressed = True
        if not progressed:
            break

    return interleaved[:count]
