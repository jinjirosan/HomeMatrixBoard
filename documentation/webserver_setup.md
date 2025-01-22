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
MQTT_BROKER = "172.16.234.55"
MQTT_PORT = 1883
MQTT_USER = "sigfoxwebhookhost"
MQTT_PASSWORD = "system1234"

def publish_to_mqtt(topic, name, duration):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        message = json.dumps({
            "name": f"{name} Tijd",
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
        if request.method == 'GET':
            name = request.args.get('name', '')
            duration = request.args.get('duration', '')
        else:
            data = request.get_json(silent=True) or {}
            name = data.get('name', '')
            duration = data.get('duration', '')

        if not name or not duration:
            return 'Missing name or duration', 400

        topic_mapping = {
            'wc': ('home/displays/wc', 'WC'),
            'bathroom': ('home/displays/bathroom', 'Bathroom'),
            'eva': ('home/displays/eva', 'Eva')
        }

        topic_info = topic_mapping.get(name.lower())
        if not topic_info:
            return f'Invalid display name: {name}', 400

        topic, display_name = topic_info
        if publish_to_mqtt(topic, display_name, duration):
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
Create Nginx site configuration (/etc/nginx/sites-available/sigfox-bridge):

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
curl "http://172.16.234.39/sigfox?name=wc&duration=60"

# Test POST endpoint
curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"wc","duration":60}' \
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
       -t "home/displays/wc" -m '{"name":"WC Tijd","duration":15}'
   ```