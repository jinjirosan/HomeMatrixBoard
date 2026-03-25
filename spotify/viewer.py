#!/usr/bin/env python3
"""
Subscribe to HomeMatrixBoard Spotify MQTT topics and show synced lyrics (tkinter).

Works on macOS and Raspberry Pi OS when Python has Tk installed.

From repo root (with mqtt_credentials.py):

  python3 -m spotify.viewer

Or override broker (e.g. from Mac Mini to LAN broker):

  python3 -m spotify.viewer --broker 172.16.234.55

Environment (optional): MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import time
import tkinter as tk
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import paho.mqtt.client as mqtt

from spotify import topics

try:
    from mqtt_credentials import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD
except ImportError:
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_USER = ""
    MQTT_PASSWORD = ""

from spotify.lrc import line_at_progress


def _make_mqtt_client() -> mqtt.Client:
    try:
        return mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=f"spotify_lyrics_viewer_{os.getpid()}",
        )
    except (AttributeError, TypeError):
        return mqtt.Client(f"spotify_lyrics_viewer_{os.getpid()}")


def _estimate_progress(now_playing: Dict[str, Any], now_ms: int) -> int:
    base = int(now_playing.get("progress_ms") or 0)
    ts = int(now_playing.get("timestamp_ms") or now_ms)
    if not now_playing.get("is_playing"):
        return max(0, base)
    return max(0, base + (now_ms - ts))


class ViewerState:
    def __init__(self) -> None:
        self.lock_msg_queue: queue.Queue = queue.Queue()
        self.now_playing: Dict[str, Any] = {}
        self.lyric_lines: List[Tuple[int, str]] = []
        self.last_current: Dict[str, Any] = {}


def _on_message_factory(state: ViewerState):
    def on_message(_client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        state.lock_msg_queue.put((msg.topic, payload))

    return on_message


def _apply_message(state: ViewerState, topic: str, payload: Dict[str, Any]) -> None:
    if topic == topics.NOW_PLAYING:
        state.now_playing = payload
    elif topic == topics.LYRICS_TRACK:
        raw_lines = payload.get("lines") or []
        tuples: List[Tuple[int, str]] = []
        if isinstance(raw_lines, list):
            for row in raw_lines:
                if not isinstance(row, dict):
                    continue
                t = row.get("t")
                text = row.get("text")
                if isinstance(t, (int, float)) and isinstance(text, str):
                    tuples.append((int(t), text))
        tuples.sort(key=lambda x: x[0])
        state.lyric_lines = tuples
    elif topic == topics.LYRICS_CURRENT:
        state.last_current = payload


def run_ui(
    mqtt_broker: str,
    mqtt_port: int,
    mqtt_user: str,
    mqtt_password: str,
    fullscreen: bool,
    font_main: int,
    font_meta: int,
) -> None:
    state = ViewerState()
    client = _make_mqtt_client()
    client.on_message = _on_message_factory(state)
    if mqtt_user:
        client.username_pw_set(mqtt_user, mqtt_password or "")
    client.connect(mqtt_broker, mqtt_port, keepalive=60)

    client.subscribe([(topics.NOW_PLAYING, 0), (topics.LYRICS_TRACK, 0), (topics.LYRICS_CURRENT, 0)])
    client.loop_start()

    root = tk.Tk()
    root.title("Spotify lyrics (MQTT)")
    root.configure(bg="black")
    if fullscreen:
        root.attributes("-fullscreen", True)
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
    root.bind("<q>", lambda e: root.destroy())
    root.bind("<Q>", lambda e: root.destroy())

    meta = tk.Label(
        root,
        text="Waiting for MQTT…",
        fg="#aaaaaa",
        bg="black",
        font=("Helvetica", font_meta),
        wraplength=900,
        justify="center",
    )
    meta.pack(pady=(24, 8), padx=24, fill="x")

    current = tk.Label(
        root,
        text="",
        fg="white",
        bg="black",
        font=("Helvetica", font_main, "bold"),
        wraplength=1100,
        justify="center",
    )
    current.pack(pady=16, padx=24, fill="both", expand=True)

    nxt = tk.Label(
        root,
        text="",
        fg="#666666",
        bg="black",
        font=("Helvetica", max(font_main - 8, 14)),
        wraplength=1000,
        justify="center",
    )
    nxt.pack(pady=(8, 32), padx=24, fill="x")

    hint = tk.Label(
        root,
        text="q: quit   Esc: exit fullscreen",
        fg="#444444",
        bg="black",
        font=("Helvetica", 12),
    )
    hint.pack(side="bottom", pady=8)

    def drain_queue() -> None:
        try:
            while True:
                topic, payload = state.lock_msg_queue.get_nowait()
                _apply_message(state, topic, payload)
        except queue.Empty:
            pass

    def tick() -> None:
        drain_queue()
        now_ms = int(time.time() * 1000)
        np = state.now_playing

        artist = np.get("artist") or "—"
        title = np.get("title") or "—"
        meta.config(text=f"{artist}\n{title}")

        if not np.get("is_playing") and not np.get("title"):
            current.config(text="Not playing")
            nxt.config(text="")
        elif state.lyric_lines:
            prog = _estimate_progress(np, now_ms)
            _, _p, cur, nex = line_at_progress(state.lyric_lines, prog)
            current.config(text=cur or "…")
            nxt.config(text=nex or "")
        else:
            cur = state.last_current.get("current")
            nex = state.last_current.get("next")
            msg = state.last_current.get("message")
            if cur:
                current.config(text=cur)
                nxt.config(text=nex or "")
            elif msg:
                current.config(text=msg)
                nxt.config(text="")
            else:
                current.config(text="No lyric data yet")
                nxt.config(text="")

        root.after(100, tick)

    root.after(100, tick)
    root.mainloop()
    client.loop_stop()
    client.disconnect()


def main() -> None:
    p = argparse.ArgumentParser(description="MQTT synced lyrics viewer (tkinter)")
    p.add_argument("--broker", default=os.environ.get("MQTT_BROKER", MQTT_BROKER))
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MQTT_PORT", str(MQTT_PORT))),
    )
    p.add_argument("--mqtt-user", default=os.environ.get("MQTT_USER", MQTT_USER))
    p.add_argument(
        "--mqtt-password",
        default=os.environ.get("MQTT_PASSWORD", MQTT_PASSWORD),
    )
    p.add_argument("--fullscreen", action="store_true", help="Fullscreen (Esc toggles off)")
    p.add_argument("--font-main", type=int, default=42, help="Main lyric font size")
    p.add_argument("--font-meta", type=int, default=22, help="Artist/title font size")
    args = p.parse_args()

    run_ui(
        mqtt_broker=args.broker,
        mqtt_port=args.port,
        mqtt_user=str(args.mqtt_user or ""),
        mqtt_password=str(args.mqtt_password or ""),
        fullscreen=args.fullscreen,
        font_main=args.font_main,
        font_meta=args.font_meta,
    )


if __name__ == "__main__":
    main()
