# Always-on Linux host — Spotify MQTT bridge

Run **`spotify/bridge.py`** on a machine that is always on, has **internet** (Spotify API + LRCLIB), and can reach your **MQTT broker** — for example **`172.16.232.6`** (the same webserver that runs Flask/Gunicorn for `/spotify/...` and `/sigfox`).

The **matrix firmware does not use lyrics**; it only needs your existing display command topic. Lyrics go to `home/spotify/#` for **viewer** apps (Mac test, then Raspberry Pi + HDMI TV).

### Recommended: bridge on the webserver (`~/sigfox_mqtt_bridge`)

If Flask already lives at **`/home/rayf/sigfox_mqtt_bridge`** (see [Webserver setup](../webserver_setup.md)):

1. Copy the **`spotify/`** directory from the repo into that folder (same level as `app.py`).
2. Install bridge dependencies into the **existing** venv (the one Gunicorn uses):
   ```bash
   cd ~/sigfox_mqtt_bridge && source venv/bin/activate && pip install -r spotify/requirements.txt
   ```
3. Reuse **`spotify_credentials.py`** and **`.spotify_cache`** from OAuth via **`/spotify/auth`** — no second OAuth if the cache file stays in `WorkingDirectory`.
4. Ensure **`mqtt_credentials.py`** points at your broker (e.g. `172.16.234.55`) and the MQTT user is allowed to **publish** `home/spotify/#` (see [mqtt_broker.md](mqtt_broker.md)). If you use a dedicated `spotify_bridge` user, pass `--mqtt-user` / `--mqtt-password` on `ExecStart` or split credentials (same pattern as `--broker` override in the example unit).
5. Run manually: `cd ~/sigfox_mqtt_bridge && source venv/bin/activate && python3 -m spotify.bridge --broker 172.16.234.55`  
   Or install systemd from **`spotify/spotify-bridge.sigfox-webhost.service.example`** (edit `User`, paths, and `--broker` if needed).

Flask and the bridge are **separate processes**; only **Gunicorn** must be running for the website. The bridge needs a valid **`.spotify_cache`** and outbound HTTPS to Spotify and **lrclib.net**.

## What is already implemented in the repo

| Piece | Location | Role |
|--------|-----------|------|
| Bridge loop | `spotify/bridge.py` | Poll Spotify, fetch LRC from LRCLIB, publish MQTT |
| LRC parse | `spotify/lrc.py` | Parse synced lyrics, pick line by progress |
| LRCLIB HTTP | `spotify/lrclib_client.py` | Download synced lyrics |
| Topics | `spotify/topics.py` | `home/spotify/now_playing`, `lyrics/track`, `lyrics/current` |
| Viewer (Mac / Pi) | `spotify/viewer.py` | Tkinter UI subscribed to the same topics |
| Deps | `spotify/requirements.txt` | `spotipy`, `paho-mqtt`, `requests` |

You **do not** need new application code for this deployment — only **credentials**, **broker ACL**, **OAuth token cache**, and a **process supervisor** (manual run or systemd).

## 1. Broker ACL

The MQTT user used by the bridge must be allowed to **publish** under `home/spotify/#`. See [mqtt_broker.md](mqtt_broker.md) and `spotify/broker-acl-snippet.txt`.

## 2. On the bridge host (e.g. 172.16.232.6)

### Install

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
cd /opt   # or your preferred path
sudo git clone https://github.com/jinjirosan/HomeMatrixBoard.git
sudo chown -R "$USER:$USER" HomeMatrixBoard
cd HomeMatrixBoard
python3 -m venv .venv
source .venv/bin/activate
pip install -r spotify/requirements.txt
```

### Credentials (repo root)

| File | Source |
|------|--------|
| `mqtt_credentials.py` | Copy `mqtt_credentials.py.template` → set `MQTT_BROKER` to the hostname/IP **as this host reaches the broker** (not necessarily `172.16.232.6` unless the broker runs there). |
| `spotify_credentials.py` | Copy `spotify_credentials.py.template` → Spotify Dashboard **Client ID / Secret** and **Redirect URI** exactly as registered. |

Never commit these files; `*_credentials.py` is gitignored.

### Spotify OAuth token (`.spotify_cache`)

The bridge uses Spotipy’s OAuth cache file (default: repo root `.spotify_cache`, or set `SPOTIFY_CACHE_PATH`).

**Typical approaches:**

1. **Same host as Flask:** Complete OAuth once with **`/spotify/auth`** (see [Spotify integration](../spotify_integration.md)). The cache is written under the Flask **`WorkingDirectory`** (e.g. `~/sigfox_mqtt_bridge`). Run **`spotify.bridge`** from that same directory (or set **`SPOTIFY_CACHE_PATH`** to that file) — **no copy step**.
2. **Bridge on another machine:** Copy **`.spotify_cache`** next to **`spotify_credentials.py`** on that host (same Spotify app / redirect URI as used for auth), or complete a one-off Spotipy auth there.
3. Or run a **one-off** Spotipy auth on the bridge machine if you can open the redirect URL in a browser that reaches your Spotify app’s redirect URI.

Without a valid cache, the bridge cannot call Spotify.

### Smoke test (no MQTT)

```bash
cd /path/to/HomeMatrixBoard
source .venv/bin/activate
python3 -m spotify.bridge --dry-run
```

You should see JSON with `now_playing` and `lyrics_hint` while Spotify is playing.

### Run with MQTT

```bash
source .venv/bin/activate
python3 -m spotify.bridge
```

Optional overrides: `--broker`, `--port`, `--mqtt-user`, `--mqtt-password`, `--interval`, `--spotify-cache /path/to/cache`.

### Verify from any MQTT client

```bash
mosquitto_sub -h <BROKER> -u <USER> -P <PASS> -t 'home/spotify/#' -v
```

You should see `now_playing`, `lyrics/track` (on track change, retained), and `lyrics/current` about once per interval while playing.

## 3. systemd (optional)

- **Generic clone path:** `spotify/spotify-bridge.service.example`
- **Same VM as sigfox Flask (`~/sigfox_mqtt_bridge`):** `spotify/spotify-bridge.sigfox-webhost.service.example`

Copy the chosen file to `/etc/systemd/system/spotify-bridge.service`, edit `User`, `WorkingDirectory`, `ExecStart`, and `Environment`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now spotify-bridge.service
sudo journalctl -u spotify-bridge.service -f
```

## 4. Mac — test viewer only

On your Mac (same LAN as the broker, or VPN):

```bash
cd /path/to/HomeMatrixBoard
python3 -m venv .venv && source .venv/bin/activate
pip install -r spotify/requirements.txt
# mqtt_credentials.py with broker reachable from Mac, or:
python3 -m spotify.viewer --broker <BROKER_IP> --port 1883 --mqtt-user USER --mqtt-password PASS
```

Details: [mac_mini.md](mac_mini.md).

## 5. Raspberry Pi + TV

Same viewer command on the Pi with HDMI; see [raspberry_pi.md](raspberry_pi.md).

## Summary

| Where | What |
|--------|------|
| **172.16.232.6** (or similar) | `python3 -m spotify.bridge` + credentials + `.spotify_cache` |
| **MQTT broker** | ACL: bridge user may **write** `home/spotify/#` |
| **Mac / Pi** | `python3 -m spotify.viewer` + MQTT read access to `home/spotify/#` |
| **MatrixPortal** | Unchanged; no lyrics topics |
