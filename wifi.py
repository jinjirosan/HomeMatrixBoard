import board
import time
from adafruit_matrixportal.matrixportal import MatrixPortal
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_esp32spi import adafruit_esp32spi_socketpool

# Get wifi details from secrets.py
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Initialize MatrixPortal with network
print("Initializing MatrixPortal...")
matrix = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

# Connect to WiFi
print("\nConnecting to WiFi...")
matrix.network.connect()

print("Connected to WiFi!")
print("IP Address:", matrix.network.ip_address)

# Create the socketpool using the ESP32's socket
pool = adafruit_esp32spi_socketpool.SocketPool(matrix.network._wifi.esp)

# MQTT Setup
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker!")
    print(f"Subscribing to {secrets['mqtt_topic']}...")
    try:
        client.subscribe(secrets['mqtt_topic'], qos=0)
        print("Successfully subscribed!")
    except Exception as e:
        print(f"Error subscribing: {e}")

def on_message(client, topic, message):
    """Handle incoming MQTT messages"""
    print("\n=== New Message Received ===")
    print(f"Topic: {topic}")
    print(f"Message: {message}")
    print(f"Message type: {type(message)}")
    try:
        # Try to decode if it's bytes
        if isinstance(message, bytes):
            message = message.decode('utf-8')
            print(f"Decoded message: {message}")
    except Exception as e:
        print(f"Error decoding message: {e}")
    print("=========================\n")

def on_subscribe(mqtt_client, userdata, topic, granted_qos):
    print(f"Subscribed to {topic} with QOS {granted_qos}")

# Set up MQTT client with authentication
print("Connecting to MQTT broker...")
mqtt_client = MQTT.MQTT(
    broker=secrets['mqtt_broker'],
    port=secrets['mqtt_port'],
    username=secrets['mqtt_user'],
    password=secrets['mqtt_password'],
    socket_pool=pool,
    is_ssl=False,
)

# Setup the callback methods
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_subscribe = on_subscribe

# Connect to MQTT broker
print(f"Attempting to connect to {secrets['mqtt_broker']} as {secrets['mqtt_user']}")
mqtt_client.connect()

print("MQTT setup complete!")

# Main loop
while True:
    try:
        mqtt_client.loop()
    except Exception as e:
        print("Failed to get/send data, retrying\n", e)
        try:
            print("Attempting to reconnect...")
            mqtt_client.reconnect()
            print("Reconnected!")
        except Exception as e:
            print("Failed to reconnect\n", e)
        continue
    time.sleep(0.1)  # Shorter sleep time for more responsive message handling 