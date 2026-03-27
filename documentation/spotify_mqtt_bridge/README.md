# Spotify MQTT bridge — installation guides

These guides describe how to run the **Spotify MQTT bridge** (`spotify/bridge.py`) and the **lyrics viewer** (`spotify/viewer.py`): Mosquitto topics under `home/spotify/#`, synced lyrics via [LRCLIB](https://lrclib.net/), and playback state from the Spotify Web API.

## Guides

| Guide | Purpose |
|--------|---------|
| [MQTT broker setup](mqtt_broker.md) | Mosquitto users, ACLs, topics, verification with `mosquitto_sub` / `mosquitto_pub` |
| [Always-on Linux bridge host](bridge_host.md) | Deploy `spotify.bridge` on a server (e.g. **webserver 172.16.232.6** or LAN appliance), credentials, systemd (`spotify-bridge.sigfox-webhost.service.example` for `~/sigfox_mqtt_bridge`) |
| [Mac Mini setup](mac_mini.md) | Python, credentials, running bridge and viewer on macOS |
| [Raspberry Pi setup](raspberry_pi.md) | OS packages, HDMI/TV viewer, optional systemd service for the bridge |

## Prerequisites (all environments)

- A **Spotify Developer** app (Client ID / Secret) and OAuth completed so `.spotify_cache` exists (see [Spotify integration](../spotify_integration.md) — open **`/spotify/auth`** in a **browser** using the **public HTTPS** URL, e.g. `https://172.16.232.6:52341/spotify/auth` when Nginx terminates TLS on 52341; the browser must **trust your TLS CA**. For `curl` against that host, use **`--cacert`** if the CA is not system-installed. Or reuse the same cache path on the machine that runs the bridge.
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
