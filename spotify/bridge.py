#!/usr/bin/env python3
"""
Poll Spotify playback, publish now-playing and synced lyrics to MQTT.

Run from the repository root (so mqtt_credentials.py and spotify_credentials.py resolve):

  cd /path/to/HomeMatrixBoard
  python3 -m spotify.bridge

Requires: spotipy, paho-mqtt, requests
OAuth: complete once via the Flask app at /spotify/auth (same .spotify_cache), or run
  python3 -c "..." — token file must exist at repo root: .spotify_cache

Broker ACL: allow the MQTT user to publish to home/spotify/#
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import paho.mqtt.client as mqtt
import requests

from spotify.lrc import line_at_progress, parse_synced_lrc
from spotify.lrclib_client import fetch_synced_lyrics
from spotify import topics

try:
    from mqtt_credentials import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD
except ImportError:
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_USER = ""
    MQTT_PASSWORD = ""

try:
    from spotify_credentials import (
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        SPOTIFY_REDIRECT_URI,
    )
except ImportError:
    print("Missing spotify_credentials.py in repo root (copy from spotify_credentials.py.template).")
    sys.exit(1)


def _spotify_client(cache_path: Path) -> Any:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-currently-playing user-read-playback-state",
            cache_path=str(cache_path),
        )
    )


def _default_spotify_cache_path() -> Path:
    env = os.environ.get("SPOTIFY_CACHE_PATH", "").strip()
    if env:
        return Path(env).expanduser()
    return _ROOT / ".spotify_cache"


def _extract_track_state(
    current: Optional[Dict[str, Any]], server_ts_ms: int
) -> Dict[str, Any]:
    """Build now_playing JSON from spotipy current_user_playing_track() result."""
    if not current or not current.get("item"):
        return {
            "is_playing": False,
            "artist": None,
            "title": None,
            "album": None,
            "track_uri": None,
            "progress_ms": 0,
            "duration_ms": 0,
            "timestamp_ms": server_ts_ms,
        }

    item = current["item"]
    artists = item.get("artists") or []
    artist = ", ".join(a.get("name", "") for a in artists if a.get("name")) or None
    title = item.get("name")
    album = (item.get("album") or {}).get("name")
    uri = item.get("uri")
    duration_ms = int(item.get("duration_ms") or 0)
    progress_ms = int(current.get("progress_ms") or 0)
    is_playing = bool(current.get("is_playing"))

    return {
        "is_playing": is_playing,
        "artist": artist,
        "title": title,
        "album": album,
        "track_uri": uri,
        "progress_ms": progress_ms,
        "duration_ms": duration_ms,
        "timestamp_ms": server_ts_ms,
    }


def _make_mqtt_client() -> mqtt.Client:
    try:
        return mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id="spotify_mqtt_bridge",
        )
    except (AttributeError, TypeError):
        return mqtt.Client("spotify_mqtt_bridge")


def _mqtt_connect(
    client: mqtt.Client,
    broker: str,
    port: int,
    user: Optional[str],
    password: Optional[str],
) -> None:
    if user:
        client.username_pw_set(user, password or "")
    client.connect(broker, port, keepalive=60)
    client.loop_start()


def _publish(client: mqtt.Client, topic: str, payload: Dict[str, Any], retain: bool) -> None:
    client.publish(topic, json.dumps(payload), qos=0, retain=retain)


def _estimate_progress(now_playing: Dict[str, Any], now_ms: int) -> int:
    base = int(now_playing.get("progress_ms") or 0)
    ts = int(now_playing.get("timestamp_ms") or now_ms)
    if not now_playing.get("is_playing"):
        return max(0, base)
    return max(0, base + (now_ms - ts))


def run_loop(
    poll_interval: float,
    dry_run: bool,
    mqtt_broker: str,
    mqtt_port: int,
    mqtt_user: str,
    mqtt_password: str,
    spotify_cache: Path,
) -> None:
    sp = _spotify_client(spotify_cache)
    http = requests.Session()

    client = _make_mqtt_client()
    if not dry_run:
        _mqtt_connect(
            client,
            mqtt_broker,
            mqtt_port,
            mqtt_user or None,
            mqtt_password or None,
        )

    last_track_uri: Optional[str] = None
    lyric_lines: List[Tuple[int, str]] = []
    first_poll = True

    try:
        while True:
            ts_ms = int(time.time() * 1000)
            try:
                current = sp.current_user_playing_track()
            except Exception as e:
                print(f"Spotify API error: {e}")
                time.sleep(poll_interval)
                continue

            np = _extract_track_state(current, ts_ms)
            uri = np.get("track_uri")

            if not dry_run:
                _publish(client, topics.NOW_PLAYING, np, retain=True)

            if first_poll or uri != last_track_uri:
                first_poll = False
                last_track_uri = uri
                lyric_lines = []
                track_payload: Dict[str, Any] = {
                    "track_uri": uri,
                    "artist": np.get("artist"),
                    "title": np.get("title"),
                    "album": np.get("album"),
                    "duration_ms": np.get("duration_ms"),
                    "lines": [],
                    "has_lyrics": False,
                    "source": None,
                }
                if (
                    uri
                    and np.get("artist")
                    and np.get("title")
                    and int(np.get("duration_ms") or 0) > 0
                ):
                    dur_s = int(np["duration_ms"]) // 1000
                    lrc = fetch_synced_lyrics(
                        np["artist"],
                        np["title"],
                        np.get("album") or "",
                        dur_s,
                        session=http,
                    )
                    if lrc:
                        lyric_lines = parse_synced_lrc(lrc)
                        track_payload["lines"] = [{"t": t, "text": tx} for t, tx in lyric_lines]
                        track_payload["has_lyrics"] = True
                        track_payload["source"] = "lrclib"
                if not dry_run:
                    _publish(client, topics.LYRICS_TRACK, track_payload, retain=True)

            prog = _estimate_progress(np, int(time.time() * 1000))
            idx, prev_t, cur_t, next_t = line_at_progress(lyric_lines, prog)
            cur_payload = {
                "track_uri": uri,
                "is_playing": np.get("is_playing"),
                "progress_ms": np.get("progress_ms"),
                "duration_ms": np.get("duration_ms"),
                "timestamp_ms": np.get("timestamp_ms"),
                "has_lyrics": bool(lyric_lines),
                "line_index": idx,
                "previous": prev_t,
                "current": cur_t,
                "next": next_t,
            }
            if not lyric_lines and uri and np.get("is_playing"):
                cur_payload["message"] = "No synced lyrics (LRCLIB)"

            if not dry_run:
                _publish(client, topics.LYRICS_CURRENT, cur_payload, retain=False)

            if dry_run:
                print(json.dumps({"now": np, "lyrics_hint": cur_payload.get("current")}, indent=2))

            time.sleep(poll_interval)
    finally:
        if not dry_run:
            client.loop_stop()
            client.disconnect()


def main() -> None:
    p = argparse.ArgumentParser(description="Spotify → MQTT bridge (now playing + LRCLIB lyrics)")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Poll Spotify / publish interval in seconds (default: 1.0)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not use MQTT; print JSON to stdout",
    )
    p.add_argument("--broker", default=None, help="Override MQTT broker host")
    p.add_argument("--port", type=int, default=None, help="Override MQTT port")
    p.add_argument("--mqtt-user", default=None, help="Override MQTT username")
    p.add_argument("--mqtt-password", default=None, help="Override MQTT password")
    p.add_argument(
        "--spotify-cache",
        type=Path,
        default=None,
        help="OAuth token cache file (default: $SPOTIFY_CACHE_PATH or <repo>/.spotify_cache)",
    )
    args = p.parse_args()

    broker = args.broker or MQTT_BROKER
    port = args.port if args.port is not None else MQTT_PORT
    muser = args.mqtt_user if args.mqtt_user is not None else MQTT_USER
    mpass = args.mqtt_password if args.mqtt_password is not None else MQTT_PASSWORD

    scache = args.spotify_cache if args.spotify_cache else _default_spotify_cache_path()

    run_loop(
        poll_interval=max(0.3, args.interval),
        dry_run=args.dry_run,
        mqtt_broker=broker,
        mqtt_port=int(port),
        mqtt_user=str(muser or ""),
        mqtt_password=str(mpass or ""),
        spotify_cache=scache,
    )


if __name__ == "__main__":
    main()
