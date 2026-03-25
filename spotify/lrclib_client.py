"""Fetch synced lyrics from LRCLIB (https://lrclib.net/)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

LRCLIB_BASE = "https://lrclib.net/api"
USER_AGENT = "HomeMatrixBoard/1.0 (+https://github.com/rayflinkerbusch/HomeMatrixBoard)"


def _record_has_synced(rec: Dict[str, Any]) -> bool:
    sl = rec.get("syncedLyrics")
    return isinstance(sl, str) and bool(sl.strip())


def fetch_synced_lyrics(
    artist: str,
    track: str,
    album: str,
    duration_sec: int,
    session: Optional[requests.Session] = None,
    timeout: float = 25.0,
) -> Optional[str]:
    """
    Return LRC string or None if not found.
    Tries /api/get then /api/search + best duration match + /api/get/{id}.
    """
    sess = session or requests.Session()
    headers = {"User-Agent": USER_AGENT}
    album_use = album.strip() if album.strip() else "Unknown Album"
    params = {
        "artist_name": artist,
        "track_name": track,
        "album_name": album_use,
        "duration": max(1, int(duration_sec)),
    }

    r = sess.get(f"{LRCLIB_BASE}/get", params=params, headers=headers, timeout=timeout)
    if r.status_code == 200:
        data = r.json()
        sl = data.get("syncedLyrics")
        if isinstance(sl, str) and sl.strip():
            return sl

    # Search fallback (e.g. album mismatch)
    sparams = {"track_name": track, "artist_name": artist}
    r2 = sess.get(f"{LRCLIB_BASE}/search", params=sparams, headers=headers, timeout=min(timeout, 15.0))
    if r2.status_code != 200:
        return None

    results: List[Dict[str, Any]] = r2.json()
    if not isinstance(results, list):
        return None

    best: Optional[Dict[str, Any]] = None
    best_diff = 9999
    for rec in results:
        if not _record_has_synced(rec):
            continue
        d = rec.get("duration")
        if not isinstance(d, (int, float)):
            continue
        diff = abs(int(d) - int(duration_sec))
        if diff < best_diff and diff <= 5:
            best_diff = diff
            best = rec

    if not best:
        return None

    rid = best.get("id")
    if rid is None:
        return best.get("syncedLyrics") if isinstance(best.get("syncedLyrics"), str) else None

    r3 = sess.get(f"{LRCLIB_BASE}/get/{int(rid)}", headers=headers, timeout=timeout)
    if r3.status_code != 200:
        return best.get("syncedLyrics") if isinstance(best.get("syncedLyrics"), str) else None

    data3 = r3.json()
    sl = data3.get("syncedLyrics")
    if isinstance(sl, str) and sl.strip():
        return sl
    return None
