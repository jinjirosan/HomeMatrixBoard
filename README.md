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
- Custom preset displays with dynamic visual elements (borders, icons, animations)
- Configurable text colors and backgrounds
- Support for graphical symbols and indicators

## Documentation

Detailed documentation is available in the `documentation`