# Webserver Setup Guide

## System Requirements
- Debian 12
- Python 3.11+
- Nginx
- Git (for deployment)

## Installation Steps

### 1. System Setup
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx git
```

### 2. Application Setup
```bash
# Create project directory
mkdir -p ~/sigfox_mqtt_bridge
cd ~/sigfox_mqtt_bridge

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install flask paho-mqtt gunicorn spotipy
```

### 3. Application Configuration
Create the Flask application (~/sigfox_mqtt_bridge/app.py):

```python
from flask import Flask, request
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# MQTT Configuration
MQTT_BROKER = "172.16.234.55"  # Your MQTT broker IP
MQTT_PORT = 1883
MQTT_USER = "sigfoxwebhookhost"
MQTT_PASSWORD = "YOUR_PASSWORD_HERE"

def publish_to_mqtt(topic, message):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(topic, json.dumps(message))
        client.disconnect()
        return True
    except Exception as e:
        print(f"Error publishing to MQTT: {e}")
        return False

@app.route('/sigfox', methods=['POST', 'GET'])
def handle_webhook():
    try:
        # Handle both GET and POST methods for testing
        if request.method == 'GET':
            target = request.args.get('target', '')    # Which display to use
            mode = request.args.get('mode', 'timer')   # Display mode (timer or preset)
            
            if mode == 'timer':
                text = request.args.get('text', '')    # What text to show
                duration = request.args.get('duration', '')
                message = {
                    "mode": "timer",
                    "name": text,
                    "duration": int(duration)
                }
            else:  # preset mode
                preset_id = request.args.get('preset_id', '')
                name = request.args.get('name', '')     # Optional custom name
                duration = request.args.get('duration', '')  # Optional duration
                message = {
                    "mode": "preset",
                    "preset_id": preset_id
                }
                if name:
                    message["name"] = name
                if duration:
                    message["duration"] = int(duration)
        else:
            data = request.get_json(silent=True) or {}
            target = data.get('target', '')
            mode = data.get('mode', 'timer')
            
            if mode == 'timer':
                message = {
                    "mode": "timer",
                    "name": data.get('text', ''),
                    "duration": int(data.get('duration', 0))
                }
            else:  # preset mode
                message = {
                    "mode": "preset",
                    "preset_id": data.get('preset_id', '')
                }
                if 'name' in data:
                    message["name"] = data['name']
                if 'duration' in data:
                    message["duration"] = int(data['duration'])

        if not target:
            return 'Missing target display', 400
            
        if mode == 'timer' and (not message.get('name') or not message.get('duration')):
            return 'Missing text or duration for timer mode', 400
        elif mode == 'preset' and not message.get('preset_id'):
            return 'Missing preset_id for preset mode', 400

        # Map display targets to MQTT topics
        topic_mapping = {
            'wc': 'home/displays/wc',
            'bathroom': 'home/displays/bathroom',
            'eva': 'home/displays/eva'
        }

        topic = topic_mapping.get(target.lower())
        if not topic:
            return f'Invalid target display: {target}', 400

        if publish_to_mqtt(topic, message):
            return 'OK', 200
        else:
            return 'Failed to publish to MQTT', 500

    except Exception as e:
        print(f"Error processing request: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

### 4. Service Configuration
Create systemd service file (/etc/systemd/system/sigfox-bridge.service):

```ini
[Unit]
Description=Sigfox to MQTT Bridge
After=network.target

[Service]
User=rayf
WorkingDirectory=/home/rayf/sigfox_mqtt_bridge
Environment="PATH=/home/rayf/sigfox_mqtt_bridge/venv/bin"
ExecStart=/home/rayf/sigfox_mqtt_bridge/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

### 5. Nginx Configuration (HTTPS on 52341 — production)

Spotify’s authorization server **rejects non-loopback `http://` redirect URIs** as insecure. For `/spotify/auth` and `/spotify/callback` you need **HTTPS** on the port the browser uses (here **52341**), with a certificate trusted by clients (or your internal CA installed on admin machines).

Create and edit the Nginx site configuration:
```bash
sudo vim /etc/nginx/sites-available/sigfox-bridge
```

Example **TLS** configuration (adjust paths to your certificate files):

```nginx
server {
    listen 52341 ssl;
    server_name 172.16.232.6;

    ssl_certificate     /etc/nginx/ssl/172.16.232.6-cert-chain.pem;   # full chain (leaf + intermediates)
    ssl_certificate_key /etc/nginx/ssl/172.16.232.6.key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**TLS certificate tips (avoid common verify failures):**

- If users open **`https://172.16.232.6:52341/...`**, the server certificate must include the IP in **Subject Alternative Name** as an **IP address** (`IP:172.16.232.6` in OpenSSL config), **not** as `DNS:172.16.232.6`. The latter makes browsers/`curl` fail with *no alternative certificate subject name matches target ipv4 address*.
- You may add a **DNS** SAN as well (e.g. `sigfoxwebhookhost.flinkerbusch.intranet`) if you use that hostname in URLs; the redirect URI in Spotify and `SPOTIFY_REDIRECT_URI` must match **exactly** (scheme, host, port, path).
- Use **`ssl_certificate`** = **full chain** file (server cert + intermediate CAs) so clients can build a path to your root/enterprise CA.

**HTTP-only (no Spotify OAuth on this URL):** For a purely internal lab you can use `listen 52341;` without `ssl` for `/sigfox` only. Spotify will still require **`https://`** for redirect URIs that are not `http://localhost` / `http://127.0.0.1`.

**Production ports (important):**

| Port | Process | Role |
|------|---------|------|
| **52341** | Nginx | Public **HTTPS** (TLS): `/sigfox`, `/spotify/...` (after TLS termination). |
| **5000** | Gunicorn (`app:app`) | Internal Flask app; Nginx **`proxy_pass http://127.0.0.1:5000`** (IPv4; avoid `localhost` here — see troubleshooting). |

- **Spotify OAuth:** Register redirect URI and set **`SPOTIFY_REDIRECT_URI`** to the **browser-visible HTTPS** URL, e.g. `https://172.16.232.6:52341/spotify/callback`, not port **5000** and not plain `http://` for this host.
- **Token file:** `.spotify_cache` is written under the systemd **`WorkingDirectory`** after a successful `/spotify/callback`. The [Spotify MQTT bridge](spotify_mqtt_bridge/README.md) on the same host should run from that directory (or set `SPOTIFY_CACHE_PATH`) so it shares the same cache.
- **Conflict:** Do not bind another process (including `python app.py` if it uses port **52341**) on the same host where Nginx already listens on **52341**. The repository’s `app.py` uses port 52341 only for **standalone** dev without Nginx; production uses Gunicorn on **5000** only.

**Note:** If you prefer port **443** (or **80** for HTTP-only), change `listen` and update all public URLs and the Spotify redirect URI accordingly.

**Testing with `curl` and an internal CA:**

```bash
curl --cacert /path/to/ca.cert.pem 'https://172.16.232.6:52341/sigfox?target=wc&text=Shower&duration=60'
```

Without `--cacert`, `curl` may fail verification unless the CA is in the system trust store.

### 6. Enable and Start Services
```bash
# Enable and start systemd service
sudo systemctl enable sigfox-bridge
sudo systemctl start sigfox-bridge

# Configure Nginx
sudo ln -s /etc/nginx/sites-available/sigfox-bridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Testing
Test the webhook endpoint (use **`https://`** when Nginx serves TLS; add **`--cacert`** if you use a private CA):

```bash
# Test timer mode (GET)
curl --cacert /path/to/ca.cert.pem 'https://172.16.232.6:52341/sigfox?target=wc&text=Shower&duration=60'

# Test preset mode (GET)
curl --cacert /path/to/ca.cert.pem 'https://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air'

# Test preset with custom name and duration (GET)
curl --cacert /path/to/ca.cert.pem 'https://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air&name=Studio%201&duration=3600'

# Test timer mode (POST)
curl --cacert /path/to/ca.cert.pem -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","text":"Shower","duration":60}' \
     https://172.16.232.6:52341/sigfox

# Test preset mode (POST)
curl --cacert /path/to/ca.cert.pem -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","mode":"preset","preset_id":"on_air"}' \
     https://172.16.232.6:52341/sigfox

# Test preset with custom name and duration (POST)
curl --cacert /path/to/ca.cert.pem -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","mode":"preset","preset_id":"on_air","name":"Studio 1","duration":3600}' \
     https://172.16.232.6:52341/sigfox
```

For more detailed API documentation and examples, see [Webhook Integration Guide](webhook_integration.md).

## Troubleshooting

1. **502 Bad Gateway** from Nginx (e.g. `curl` to `https://172.16.232.6:52341/sigfox?...` returns 502):

   **Isolate Flask vs Nginx first** (502 is usually **not** caused by `app.py` if Gunicorn is healthy):

   - Test Gunicorn **directly** with a **quoted** URL (shell treats `&` specially otherwise):
     ```bash
     curl -sS -o /dev/null -w "%{http_code}\n" 'http://127.0.0.1:5000/sigfox?target=wc&text=Test&duration=1'
     ```
     Expect **200** if MQTT publish succeeds, or **400** if parameters are wrong — **not** connection refused.
   - If **5000** works but **52341** still returns **502**, the problem is **Nginx → upstream**, not your Python code. Swapping to an older `app.py` will not help.

   **Common upstream causes:**

   - **Nothing on port 5000:** `sudo systemctl status sigfox-bridge` and `sudo ss -tlnp | grep 5000`. Start or fix `sigfox-bridge` so `ExecStart` matches `proxy_pass` (this guide uses `http://127.0.0.1:5000`).
   - **`proxy_pass http://localhost:5000` and IPv6:** On many Linux systems `localhost` resolves to **`[::1]`** first. Gunicorn with `--bind 0.0.0.0:5000` listens on **IPv4 only**, so Nginx may try **`[::1]:5000`**, get **connection refused**, and return 502. Check:
     ```bash
     sudo tail -20 /var/log/nginx/error.log
     ```
     If you see `upstream: "http://[::1]:5000/..."` and `connect() failed (111: Connection refused)`, change **`proxy_pass`** to **`http://127.0.0.1:5000`** (as in the Nginx example above), then `sudo nginx -t && sudo systemctl reload nginx`.
   - **Stale Nginx workers or config not applied:** If Gunicorn is up and `127.0.0.1:5000` responds but **52341** still returns 502, run **`sudo systemctl reload nginx`** or **`sudo systemctl restart nginx`**. Operators have seen 502 persist until reload/restart even when `app.py` was unchanged.

   **Spotify redirect check (optional):** `curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/spotify/auth` — expect **302** when Spotify is configured (or **503** if disabled), not connection refused.

2. **TLS / certificate errors** (`curl: SSL certificate problem`, *no alternative certificate subject name matches target ipv4 address*):
   - Ensure the cert presented on **52341** has a **SAN** that matches how you connect: **IP** SAN for `https://172.16.232.6/...`, or **DNS** SAN for `https://your.hostname/...` — do not put the IP only under `DNS:`.
   - Install your **CA** in the trust store on clients, or use `curl --cacert /path/to/ca.pem`.
   - After replacing certs, `sudo nginx -t && sudo systemctl reload nginx`.

3. Check service status:
   ```bash
   sudo systemctl status sigfox-bridge
   sudo journalctl -u sigfox-bridge
   ```

4. Check Nginx logs:
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

5. Test MQTT connection:
   ```bash
   # Install mosquitto clients for testing
   sudo apt install -y mosquitto-clients
   
   # Test publishing
   mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P YOUR_PASSWORD \
       -t "home/displays/wc" -m '{"name":"Shower","duration":15}'
   ```
   For MQTT broker configuration details, see [MQTT Broker Setup](mqtt_broker_setup.md).

6. After making changes to app.py:
   ```bash
   sudo systemctl restart sigfox-bridge
   ```

### 7. Spotify MQTT bridge (lyrics) on this same host

To publish **`home/spotify/#`** (now playing + LRCLIB synced lyrics) from **`172.16.232.6`**:

1. Place the **`spotify/`** package under **`~/sigfox_mqtt_bridge`** next to `app.py`.
2. In the **same** venv: `pip install -r spotify/requirements.txt`.
3. Reuse **`spotify_credentials.py`** and **`.spotify_cache`** after **`/spotify/auth`** (same `WorkingDirectory` as Gunicorn).
4. MQTT user in **`mqtt_credentials.py`** must be allowed to **publish** `home/spotify/#` on the broker (often extend the webhook user; see [Spotify MQTT broker ACLs](spotify_mqtt_bridge/mqtt_broker.md)).
5. Optional systemd: **`spotify/spotify-bridge.sigfox-webhost.service.example`** → `/etc/systemd/system/spotify-bridge.service`.

Full steps: [Always-on Linux bridge host](spotify_mqtt_bridge/bridge_host.md).

## Related Documentation

- [Webhook Integration](webhook_integration.md) - API reference for webhook endpoints
- [MQTT Broker Setup](mqtt_broker_setup.md) - MQTT broker configuration
- [Spotify Integration](spotify_integration.md) - Optional Spotify integration setup
- [Spotify MQTT bridge](spotify_mqtt_bridge/README.md) - Lyrics topics, viewer, bridge on webserver or appliance
- [Architecture](architecture.md) - System architecture overview