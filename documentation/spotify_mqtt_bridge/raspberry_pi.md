# Raspberry Pi — Spotify lyrics viewer (and optional bridge)

This guide covers running the **lyrics viewer** on Raspberry Pi OS connected to a TV (HDMI), and optionally running the **Spotify MQTT bridge** on the same Pi or another host.

## Requirements

- Raspberry Pi OS (Bookworm or later recommended) on a Pi 3B+ or newer (Pi 4/5 works well for fullscreen Tk).
- HDMI display and keyboard (or SSH for setup, then autostart the viewer locally).
- Network access to your **MQTT broker**.

## 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-tk git
```

`python3-tk` is required for `spotify/viewer.py`.

## 2. Get the code

```bash
cd ~
git clone https://github.com/rayflinkerbusch/HomeMatrixBoard.git
cd HomeMatrixBoard
```

## 3. Virtual environment and Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r spotify/requirements.txt
```

## 4. MQTT credentials (viewer = read-only)

Create `mqtt_credentials.py` in the **repo root** (same level as `app.py`):

```python
MQTT_BROKER = "172.16.234.55"   # your broker IP or hostname
MQTT_PORT = 1883
MQTT_USER = "spotify_viewer"    # user with read home/spotify/#
MQTT_PASSWORD = "your-password"
```

See [MQTT broker setup](mqtt_broker.md) to create `spotify_viewer` and ACLs.

**Security:** file permissions on the Pi:

```bash
chmod 600 ~/HomeMatrixBoard/mqtt_credentials.py
```

## 5. Run the viewer (manual test)

On the Pi desktop (local session, not only SSH if you want a window on HDMI):

```bash
cd ~/HomeMatrixBoard
source .venv/bin/activate
python3 -m spotify.viewer --broker 172.16.234.55 --fullscreen
```

- **Esc** — leave fullscreen  
- **q** — quit  

If fonts are too small on a TV:

```bash
python3 -m spotify.viewer --broker 172.16.234.55 --fullscreen --font-main 56 --font-meta 28
```

### SSH note

If you start the viewer over SSH without a display, Tk will fail. Either:

- Run the viewer from the Pi’s **local desktop** session, or  
- Use `export DISPLAY=:0` and X11 forwarding only if configured (not typical for TV setups).

For a TV wall display, use **autostart on the graphical session** (below).

## 6. Autostart on login (desktop session)

Create a launcher script:

```bash
mkdir -p ~/bin
nano ~/bin/spotify-lyrics-viewer.sh
```

Contents:

```bash
#!/bin/bash
cd /home/pi/HomeMatrixBoard
source .venv/bin/activate
exec python3 -m spotify.viewer --broker 172.16.234.55 --fullscreen --font-main 52 --font-meta 26
```

Adjust `pi`, paths, broker IP, and fonts.

```bash
chmod +x ~/bin/spotify-lyrics-viewer.sh
```

**Raspberry Pi OS — autostart:**

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/spotify-lyrics.desktop
```

Example:

```ini
[Desktop Entry]
Type=Application
Name=Spotify Lyrics Viewer
Exec=/home/pi/bin/spotify-lyrics-viewer.sh
X-GNOME-Autostart-enabled=true
```

Log out and log in (or reboot) to test.

## 7. Optional — run the bridge on the Pi

Usually the bridge runs on your always-on **webserver** next to Flask. Use the Pi as bridge only if you want a self-contained setup.

You need on the Pi:

- `spotify_credentials.py` in repo root  
- `.spotify_cache` (OAuth completed once — copy from server or run OAuth flow reachable from a browser)  
- `mqtt_credentials.py` with a user that can **write** `home/spotify/#`  

Then:

```bash
cd ~/HomeMatrixBoard
source .venv/bin/activate
python3 -m spotify.bridge --broker 172.16.234.55
```

### systemd service example (bridge only)

Replace `pi`, paths, and broker as needed.

```bash
sudo nano /etc/systemd/system/spotify-mqtt-bridge.service
```

```ini
[Unit]
Description=HomeMatrixBoard Spotify MQTT bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/HomeMatrixBoard
Environment=SPOTIFY_CACHE_PATH=/home/pi/HomeMatrixBoard/.spotify_cache
ExecStart=/home/pi/HomeMatrixBoard/.venv/bin/python3 -m spotify.bridge --broker 172.16.234.55
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now spotify-mqtt-bridge.service
sudo systemctl status spotify-mqtt-bridge.service
```

## 8. Verification

From the Pi or another host:

```bash
mosquitto_sub -h 172.16.234.55 -u spotify_viewer -P '<password>' -v -t 'home/spotify/#'
```

With the bridge running and Spotify playing, you should see traffic on all three topics.

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| Black screen / Tk error on boot | Delay autostart, or run script after desktop is up; check `journalctl --user -b` if using user services. |
| “Waiting for MQTT…” | Wrong broker IP, VPN down, ACL or password. |
| No lyrics | LRCLIB missing synced lyrics for that track. |
| Bridge fails Spotify auth | Renew `.spotify_cache`; check `SPOTIFY_REDIRECT_URI` matches Dashboard. |

## Related docs

- [MQTT broker setup](mqtt_broker.md)  
- [Mac Mini setup](mac_mini.md)  
- [Spotify integration (Flask + matrix)](../spotify_integration.md)  
