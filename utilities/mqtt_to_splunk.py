#!/usr/bin/env python3
"""
MQTT to Splunk Forwarder for Utilities Monitoring
==================================================

Subscribes to utilities/* MQTT topics and forwards to Splunk HEC with
manufacturer-specific sourcetype mapping:
  - utilities/heating    → kamstrup:heating
  - utilities/hotwater   → kamstrup:hotwater
  - utilities/coldwater  → elster:coldwater
  - utilities/energy     → emonpi:energy

Requirements:
  - Python 3.6+ (system Python, NOT Splunk's internal Python 2.7)
  - paho-mqtt
  - requests

Author: HomeMatrixBoard Project
License: See LICENSE file
"""

import sys
import os

# Ensure we're running Python 3.6+
if sys.version_info < (3, 6):
    print("ERROR: This script requires Python 3.6 or higher")
    print(f"Current Python version: {sys.version}")
    print("Please run with: /usr/bin/python3 mqtt_to_splunk.py")
    sys.exit(1)

import paho.mqtt.client as mqtt
import json
import requests
import time
from datetime import datetime
import logging
import urllib3

# Disable SSL warnings when SPLUNK_VERIFY_SSL = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION - Import from credentials file
# ============================================
try:
    from splunk_credentials import (
        MQTT_BROKER,
        MQTT_PORT,
        MQTT_USER,
        MQTT_PASSWORD,
        SPLUNK_HEC_URL,
        SPLUNK_HEC_TOKEN,
        SPLUNK_INDEX,
        SPLUNK_VERIFY_SSL
    )
except ImportError:
    logger.error("Could not import splunk_credentials.py")
    logger.error("Copy splunk_credentials.py.template to splunk_credentials.py and configure it")
    sys.exit(1)

# MQTT Topics to subscribe to
MQTT_TOPICS = [
    ("utilities/heating/#", 0),
    ("utilities/hotwater/#", 0),
    ("utilities/coldwater/#", 0),
    ("utilities/energy/#", 0),
]

# Topic to Sourcetype mapping (manufacturer/device-specific)
TOPIC_SOURCETYPE_MAP = {
    "utilities/heating": "kamstrup:heating",
    "utilities/hotwater": "kamstrup:hotwater",
    "utilities/coldwater": "elster:coldwater",
    "utilities/energy": "emonpi:energy",
}

# Topic to Source mapping (for device identification)
TOPIC_SOURCE_MAP = {
    "utilities/heating": "heating_main",
    "utilities/hotwater": "hotwater_main",
    "utilities/coldwater": "coldwater_main",
    "utilities/energy": "energy_main",
}

# ============================================
# Helper Functions
# ============================================

def determine_sourcetype(topic: str) -> str:
    """
    Map MQTT topic to Splunk sourcetype based on device manufacturer.
    
    Args:
        topic: MQTT topic (e.g., "utilities/heating/metrics")
    
    Returns:
        Sourcetype string or None (falls back to HEC default)
    """
    for prefix, sourcetype in TOPIC_SOURCETYPE_MAP.items():
        if topic.startswith(prefix):
            return sourcetype
    
    # Return None to let HEC use default sourcetype (mqtt:metrics)
    logger.warning(f"No sourcetype mapping found for topic: {topic}")
    return None


def determine_source(topic: str) -> str:
    """
    Map MQTT topic to Splunk source field.
    
    Args:
        topic: MQTT topic (e.g., "utilities/heating/metrics")
    
    Returns:
        Source string
    """
    for prefix, source in TOPIC_SOURCE_MAP.items():
        if topic.startswith(prefix):
            return source
    
    return "unknown"


def send_to_splunk(data: dict, source: str, sourcetype: str) -> bool:
    """
    Send event to Splunk via HTTP Event Collector.
    
    Args:
        data: Event data dictionary
        source: Splunk source field
        sourcetype: Splunk sourcetype field (or None for HEC default)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Prepare HEC event payload
        event = {
            "time": int(time.time()),
            "host": MQTT_BROKER,
            "source": source,
            "index": SPLUNK_INDEX,
            "event": data
        }
        
        # Only set sourcetype if we have a specific one
        # Otherwise HEC uses the default from inputs.conf (mqtt:metrics)
        if sourcetype:
            event["sourcetype"] = sourcetype
        
        headers = {
            "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            SPLUNK_HEC_URL,
            headers=headers,
            json=event,
            verify=SPLUNK_VERIFY_SSL,
            timeout=5
        )
        
        if response.status_code == 200:
            logger.debug(f"Event sent to Splunk successfully: {sourcetype or 'default'}/{source}")
            return True
        else:
            logger.error(
                f"Failed to send to Splunk. Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Timeout sending to Splunk HEC")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending to Splunk: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to Splunk: {e}", exc_info=True)
        return False


# ============================================
# MQTT Event Handlers
# ============================================

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        # Subscribe to all utility topics
        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos)
            logger.info(f"Subscribed to topic: {topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        logger.error(f"Error: {error_messages.get(rc, 'Unknown error')}")
        sys.exit(1)


def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    if rc != 0:
        logger.warning(f"Unexpected MQTT disconnection. Code: {rc}. Reconnecting...")
    else:
        logger.info("Disconnected from MQTT broker")


def on_message(client, userdata, msg):
    """Callback when message received from MQTT"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"Received message on topic '{topic}': {payload}")
        
        # Parse JSON payload or wrap raw values
        try:
            data = json.loads(payload)
            # If it's a simple value (not a dict), wrap it with field name from topic
            if not isinstance(data, dict):
                # Extract field name from topic (last part)
                field_name = topic.split('/')[-1]
                data = {field_name: data}
        except json.JSONDecodeError:
            # Not JSON at all - wrap as raw value with field name from topic
            logger.debug(f"Non-JSON payload on topic '{topic}', wrapping value")
            field_name = topic.split('/')[-1]
            data = {field_name: payload}
        
        # Determine sourcetype and source based on topic
        sourcetype = determine_sourcetype(topic)
        source = determine_source(topic)
        
        # Enrich data with metadata
        data['mqtt_topic'] = topic
        data['received_at'] = datetime.now(datetime.UTC).isoformat()
        
        # Send to Splunk
        success = send_to_splunk(data, source, sourcetype)
        if not success:
            logger.warning(f"Failed to send message from topic '{topic}' to Splunk")
        
    except Exception as e:
        logger.error(f"Error processing message from topic '{msg.topic}': {e}", exc_info=True)


def on_subscribe(client, userdata, mid, granted_qos):
    """Callback when subscription is confirmed"""
    logger.debug(f"Subscription confirmed. QoS: {granted_qos}")


def on_log(client, userdata, level, buf):
    """Callback for MQTT client logging"""
    logger.debug(f"MQTT: {buf}")


# ============================================
# Main Function
# ============================================

def main():
    """Main function to start MQTT to Splunk forwarder"""
    logger.info("=" * 60)
    logger.info("Starting MQTT to Splunk Forwarder for Utilities Monitoring")
    logger.info("=" * 60)
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Python Executable: {sys.executable}")
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"MQTT User: {MQTT_USER}")
    logger.info(f"Splunk HEC URL: {SPLUNK_HEC_URL}")
    logger.info(f"Splunk Index: {SPLUNK_INDEX}")
    logger.info(f"SSL Verification: {SPLUNK_VERIFY_SSL}")
    logger.info("=" * 60)
    
    # Create MQTT client (using callback API version 2)
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="splunk_forwarder",
        clean_session=True
    )
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    # Uncomment for verbose MQTT debugging:
    # client.on_log = on_log
    
    # Enable automatic reconnection
    client.reconnect_delay_set(min_delay=1, max_delay=120)
    
    # Connect to MQTT broker
    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start listening loop (blocking, with automatic reconnection)
        logger.info("Starting MQTT listening loop...")
        client.loop_forever()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        client.disconnect()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

