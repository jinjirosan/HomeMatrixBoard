"""Parse LRCLIB / standard LRC synced lyrics into timed lines."""

from __future__ import annotations

import re
from typing import List, Tuple

# [mm:ss.xx] or [m:ss.xx] optional .xx or .x; optional word-level tags after ]
_LINE_RE = re.compile(
    r"^\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\](.*)$"
)


def _to_ms(minutes: str, seconds: str, frac: str | None) -> int:
    m = int(minutes)
    s = int(seconds)
    if frac:
        # Pad to milliseconds: "1" -> 100ms, "12" -> 120ms, "123" -> 123ms
        f = frac.ljust(3, "0")[:3]
        ms = int(f)
    else:
        ms = 0
    return (m * 60 + s) * 1000 + ms


def parse_synced_lrc(synced: str) -> List[Tuple[int, str]]:
    """
    Return list of (start_time_ms, text) sorted by time.
    Skips meta lines like [ar:...] and empty text.
    """
    if not synced or not synced.strip():
        return []

    lines: List[Tuple[int, str]] = []
    for raw in synced.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        text = m.group(4).strip()
        # Strip common trailing inline time tags like <00:05.00>
        text = re.sub(r"<[\d:.]+>\s*", "", text).strip()
        if not text:
            continue
        start_ms = _to_ms(m.group(1), m.group(2), m.group(3))
        lines.append((start_ms, text))

    lines.sort(key=lambda x: x[0])
    return lines


def line_at_progress(
    lines: List[Tuple[int, str]], progress_ms: int
) -> Tuple[int, str | None, str | None, str | None]:
    """
    Given sorted lines, return (index, previous_text, current_text, next_text).
    current_text is the line active at progress_ms.
    """
    if not lines:
        return -1, None, None, None

    idx = 0
    for i, (t, _) in enumerate(lines):
        if t <= progress_ms:
            idx = i
        else:
            break

    prev_t = lines[idx - 1][1] if idx > 0 else None
    cur_t = lines[idx][1]
    next_t = lines[idx + 1][1] if idx + 1 < len(lines) else None
    return idx, prev_t, cur_t, next_t
