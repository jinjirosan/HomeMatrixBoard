from flask import Flask, request
import paho.mqtt.client as mqtt
import json

# Import MQTT credentials from separate file
try:
    from mqtt_credentials import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD
except ImportError:
    # Default values if credentials file is not found (for development only)
    print("Warning: mqtt_credentials.py not found. Using default values.")
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_USER = "user"
    MQTT_PASSWORD = "password"

app = Flask(__name__)

# Valid preset IDs
VALID_PRESETS = ["on_air", "score", "breaking", "reset"]

def publish_to_mqtt(topic, message_data):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        message = json.dumps(message_data)
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
            mode = request.args.get('mode', 'timer')  # Optional: for preset mode
            preset_id = request.args.get('preset_id', '')  # Optional: for preset mode
        else:
            data = request.get_json(silent=True) or {}
            target = data.get('target', '')
            text = data.get('text', '')
            duration = data.get('duration', '')
            mode = data.get('mode', 'timer')
            preset_id = data.get('preset_id', '')

        # For backward compatibility, if no mode specified or timer mode
        if mode != 'preset':
            if not target or not duration or not text:
                return 'Missing target, text, or duration', 400
                
            message_data = {
                "name": text,
                "duration": int(duration)
            }
        else:
            # Handle preset mode
            if not target or not preset_id or preset_id not in VALID_PRESETS:
                return f'Invalid target or preset_id. Valid presets: {", ".join(VALID_PRESETS)}', 400
                
            message_data = {
                "mode": "preset",
                "preset_id": preset_id,
                "name": text if text else "",  # Optional text override
                "duration": int(duration) if duration else None  # Optional duration
            }

        # Map display targets to MQTT topics
        topic_mapping = {
            'wc': 'home/displays/wc',
            'bathroom': 'home/displays/bathroom',
            'eva': 'home/displays/eva'
        }

        topic = topic_mapping.get(target.lower())
        if not topic:
            return f'Invalid target display: {target}', 400

        if publish_to_mqtt(topic, message_data):
            return 'OK', 200
        else:
            return 'Failed to publish to MQTT', 500

    except Exception as e:
        print(f"Error processing request: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=52341) 