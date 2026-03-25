# Spotify MQTT bridge — installation guides

These guides describe how to run the **Spotify MQTT bridge** (`spotify/bridge.py`) and the **lyrics viewer** (`spotify/viewer.py`): Mosquitto topics under `home/spotify/#`, synced lyrics via [LRCLIB](https://lrclib.net/), and playback state from the Spotify Web API.

## Guides

| Guide | Purpose |
|--------|---------|
| [MQTT broker setup](mqtt_broker.md) | Mosquitto users, ACLs, topics, verification with `mosquitto_sub` / `mosquitto_pub` |
| [Mac Mini setup](mac_mini.md) | Python, credentials, running bridge and viewer on macOS |
| [Raspberry Pi setup](raspberry_pi.md) | OS packages, HDMI/TV viewer, optional systemd service for the bridge |

## Prerequisites (all environments)

- A **Spotify Developer** app (Client ID / Secret) and OAuth completed so `.spotify_cache` exists (see [Spotify integration](../spotify_integration.md) — use `/spotify/auth` on your Flask host, or the same cache path on the machine that runs the bridge).
- `spotify_credentials.py` in the **HomeMatrixBoard repo root** (copy from `spotify_credentials.py.template`).
- Network path from each machine to your **MQTT broker** (port `1883` unless you change it).

## Quick reference — topics

| Topic | Retained | Content |
|--------|----------|---------|
| `home/spotify/now_playing` | Yes | Artist, title, album, `track_uri`, `progress_ms`, `duration_ms`, `is_playing`, `timestamp_ms` |
| `home/spotify/lyrics/track` | Yes | Timed lines: `lines: [{ "t": ms, "text": "..." }]` |
| `home/spotify/lyrics/current` | No | Current / previous / next line hints plus progress snapshot |

## Repository paths

- Bridge: `python3 -m spotify.bridge` (from repo root)
- Viewer: `python3 -m spotify.viewer` (from repo root)
- Dependencies: `pip install -r spotify/requirements.txt`
