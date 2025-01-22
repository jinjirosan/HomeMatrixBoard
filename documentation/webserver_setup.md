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
pip install flask paho-mqtt gunicorn
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
MQTT_PASSWORD = "system1234"

def publish_to_mqtt(topic, display_text, duration):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Send the display text directly without modification
        message = json.dumps({
            "name": display_text,
            "duration": int(duration)
        })
        
        client.publish(topic, message)
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
            target = request.args.get('target', '')  # Which display to use
            text = request.args.get('text', '')      # What text to show
            duration = request.args.get('duration', '')
        else:
            data = request.get_json(silent=True) or {}
            target = data.get('target', '')
            text = data.get('text', '')
            duration = data.get('duration', '')

        if not target or not duration or not text:
            return 'Missing target, text, or duration', 400

        # Map display targets to MQTT topics
        topic_mapping = {
            'wc': 'home/displays/wc',
            'bathroom': 'home/displays/bathroom',
            'eva': 'home/displays/eva'
        }

        topic = topic_mapping.get(target.lower())
        if not topic:
            return f'Invalid target display: {target}', 400

        if publish_to_mqtt(topic, text, duration):
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

### 5. Nginx Configuration
Create and edit the Nginx site configuration:
```bash
# Create and edit the configuration file
sudo vim /etc/nginx/sites-available/sigfox-bridge
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name 172.16.234.39;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

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
Test the webhook endpoint:
```bash
# Test GET endpoint
curl "http://172.16.234.39/sigfox?target=wc&text=Shower&duration=60"

# Test POST endpoint
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","text":"Shower","duration":60}' \
     http://172.16.234.39/sigfox
```

## Troubleshooting
1. Check service status:
   ```bash
   sudo systemctl status sigfox-bridge
   sudo journalctl -u sigfox-bridge
   ```

2. Check Nginx logs:
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

3. Test MQTT connection:
   ```bash
   # Install mosquitto clients for testing
   sudo apt install -y mosquitto-clients
   
   # Test publishing
   mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P system1234 \
       -t "home/displays/wc" -m '{"name":"Shower","duration":15}'
   ```

4. After making changes to app.py:
   ```bash
   sudo systemctl restart sigfox-bridge
   ```