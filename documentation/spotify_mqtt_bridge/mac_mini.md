# Mac Mini — Spotify MQTT bridge and lyrics viewer

This guide covers installing and running the HomeMatrixBoard **Spotify MQTT bridge** and **tkinter lyrics viewer** on macOS (Apple Silicon or Intel).

## Requirements

- macOS with **Python 3.11+** (recommended: [python.org](https://www.python.org/downloads/) or a managed install you control).
- **Tk** for the viewer: the python.org installer usually includes Tk. If `python3 -m spotify.viewer` fails with `_tkinter` errors, install/fix Tk for your Python (Homebrew Python often needs `brew install python-tk` or use python.org builds).
- **Git** (optional) to clone the repo, or copy the project folder from another machine.
- Network access to your **MQTT broker** (e.g. VPN to home if the broker is not on the LAN).

## 1. Get the code

```bash
cd ~/github   # or your preferred path
git clone https://github.com/rayflinkerbusch/HomeMatrixBoard.git
cd HomeMatrixBoard
```

## 2. Python virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r spotify/requirements.txt
```

For every new terminal session:

```bash
cd ~/github/HomeMatrixBoard
source .venv/bin/activate
```

## 3. Credentials in the repo root

Create these files next to `app.py` (they are gitignored):

### `mqtt_credentials.py`

Copy from `mqtt_credentials.py.template` and set broker IP, port, user, and password.

- If the Mac **only runs the viewer**, use a user with **read** access to `home/spotify/#` (see [MQTT broker setup](mqtt_broker.md)).
- If the Mac **runs the bridge**, use a user with **write** access to `home/spotify/#`.

### `spotify_credentials.py`

Copy from `spotify_credentials.py.template` and set `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REDIRECT_URI` (must match your Spotify Dashboard app).

### Spotify OAuth token (`.spotify_cache`)

The bridge needs a valid OAuth token file.

**Typical approach:** Complete OAuth once on your **Flask server** (same repo) using **`https://…/spotify/auth`** (production uses **HTTPS** on Nginx — see [Webserver setup](../webserver_setup.md)), then copy `.spotify_cache` to the Mac into the **same repo root** as `spotify_credentials.py`.

Alternatively run the bridge only on the server and run **only the viewer** on the Mac (no Spotify cache needed on the Mac).

**Custom cache path:**

```bash
export SPOTIFY_CACHE_PATH="$HOME/secrets/.spotify_cache"
python3 -m spotify.bridge --broker 172.16.234.55
```

## 4. Run the lyrics viewer (most common on Mac)

From the repo root, with venv activated:

```bash
python3 -m spotify.viewer --broker 172.16.234.55
```

Use your real broker address. User/password are read from `mqtt_credentials.py` unless overridden:

```bash
python3 -m spotify.viewer --broker 172.16.234.55 --mqtt-user spotify_viewer --mqtt-password 'your-password'
```

Environment overrides (optional):

```bash
export MQTT_BROKER=172.16.234.55
export MQTT_PORT=1883
export MQTT_USER=spotify_viewer
export MQTT_PASSWORD='your-password'
python3 -m spotify.viewer
```

**Fullscreen (e.g. external display):**

```bash
python3 -m spotify.viewer --broker 172.16.234.55 --fullscreen
```

- **Esc** — exit fullscreen  
- **q** — quit the app  

**Larger text:**

```bash
python3 -m spotify.viewer --broker 172.16.234.55 --font-main 52 --font-meta 26
```

## 5. Run the bridge on the Mac (optional)

Only needed if this Mac should **publish** Spotify state to MQTT (usually the home server does this instead).

```bash
cd ~/github/HomeMatrixBoard
source .venv/bin/activate
python3 -m spotify.bridge --broker 172.16.234.55
```

CLI overrides match `app.py` patterns:

```bash
python3 -m spotify.bridge --broker 172.16.234.55 --interval 1.0 --mqtt-user sigfoxwebhookhost --mqtt-password '...'
```

**Dry run (no MQTT, debug Spotify + LRCLIB):**

```bash
python3 -m spotify.bridge --dry-run
```

## 6. Quick tests

**LRC parser self-test:**

```bash
python3 spotify/test_lrc.py
```

**Watch MQTT from Terminal:**

```bash
mosquitto_sub -h 172.16.234.55 -u spotify_viewer -P '<password>' -v -t 'home/spotify/#'
```

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| `No module named 'spotify'` | Run from repo root; use `python3 -m spotify.viewer`, not a script path under `spotify/` alone. |
| `_tkinter` / Tk errors | Use python.org Python with Tk, or install Tk for Homebrew Python. |
| Viewer stuck on “Waiting for MQTT…” | Broker IP/firewall, wrong MQTT user/password, ACL missing `read home/spotify/#`. |
| “Not playing” forever | Bridge not running or Spotify paused; start bridge and play a track. |
| No lyrics | LRCLIB may not have synced lyrics for that track; try a popular song. |
| Spotify errors on bridge | Refresh token: redo `/spotify/auth` on server, copy new `.spotify_cache`. |

## Related docs

- [MQTT broker setup](mqtt_broker.md)  
- [Raspberry Pi setup](raspberry_pi.md)  
- [Spotify integration (Flask + matrix)](../spotify_integration.md)  
