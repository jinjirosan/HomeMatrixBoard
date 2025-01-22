# HomeMatrixBoard

A distributed IoT system for managing and displaying countdown timers on LED matrix displays. The system consists of a webserver handling webhooks, an MQTT broker for message distribution, and MatrixPortal M4 displays showing countdown timers.

## System Overview

### Components
1. **Webserver (172.16.234.39)**
   - Handles incoming webhooks
   - Processes and forwards messages to MQTT broker
   - Built with Flask and Nginx

2. **MQTT Broker (172.16.234.55)**
   - Manages message distribution
   - Handles authentication and access control
   - Built with Mosquitto

3. **MatrixPortal M4 Displays**
   - Show countdown timers
   - Connect via WiFi
   - Subscribe to MQTT topics

### Features
- Beautiful LED matrix display with animations
- Real-time countdown updates
- Multiple display support (WC, Bathroom, Eva)
- Webhook integration
- Secure MQTT communication

## Documentation

Detailed documentation is available in the `documentation` folder:

1. [System Architecture](documentation/architecture.md)
   - System components and flow
   - Network architecture
   - Security overview

2. [Webserver Setup](documentation/webserver_setup.md)
   - Installation guide
   - Configuration
   - Testing

3. [MQTT Setup](documentation/mqtt_setup.md)
   - Broker installation
   - Access control
   - Topic configuration

4. [Display Operation](documentation/display_operation.md)
   - Hardware setup
   - Message format
   - Troubleshooting

## Quick Start

### 1. Test Webhook
```bash
curl "http://172.16.234.39/sigfox?name=wc&duration=60"
```

### 2. Test MQTT Directly
```bash
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name": "WC Tijd", "duration": 15}'
```

## Message Format
```json
{
    "name": "WC Tijd",
    "duration": 15
}
```

## Display Topics
- WC Display: `home/displays/wc`
- Bathroom Display: `home/displays/bathroom`
- Eva Display: `home/displays/eva`

## Requirements

### Webserver
- Debian 12
- Python 3.11+
- Nginx
- Flask
- paho-mqtt

### MQTT Broker
- Debian 12
- Mosquitto
- mosquitto-clients

### Displays
- Adafruit MatrixPortal M4
- 64x32 RGB LED Matrix
- 5V 4A Power Supply
- CircuitPython libraries

## Security
- MQTT authentication required
- Topic-specific access control
- Nginx reverse proxy
- Secure credential storage

## Troubleshooting
See the individual documentation files for component-specific troubleshooting guides:
- [Display Operation Guide](documentation/display_operation.md#troubleshooting)
- [MQTT Setup Guide](documentation/mqtt_setup.md#troubleshooting)
- [Webserver Setup Guide](documentation/webserver_setup.md#troubleshooting)

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details. 