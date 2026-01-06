# HomeMatrixBoard Documentation

## Overview
HomeMatrixBoard is a distributed IoT display system that shows countdown timers and preset displays on LED matrix displays. The system integrates Sigfox webhooks with MQTT messaging to control multiple MatrixPortal M4 displays.

## Quick Start

### Send a Timer
```bash
curl "http://172.16.232.6:52341/sigfox?target=wc&text=Shower&duration=60"
```

### Send a Preset
```bash
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air"
```

## Documentation Structure

### Setup Guides
- **[Display Setup](display_setup.md)** - How to set up and configure MatrixPortal M4 displays
- **[MQTT Broker Setup](mqtt_broker_setup.md)** - How to install and configure the MQTT broker
- **[Webserver Setup](webserver_setup.md)** - How to set up the Flask webhook server
- **[Spotify Integration](spotify_integration.md)** - Optional Spotify integration setup
- **[Spotify Setup Checklist](SPOTIFY_SETUP_CHECKLIST.md)** - Step-by-step Spotify setup checklist

### User Guides
- **[Display Operation](display_operation.md)** - How to use the displays, message formats, and testing
- **[Webhook Integration](webhook_integration.md)** - API reference for webhook endpoints
- **[Architecture](architecture.md)** - System architecture and message flow

### Reference
- **[CHANGELOG](CHANGELOG.md)** - Version history and changes
- **[Security](security.md)** - Security considerations and best practices

## System Components

1. **Webserver (172.16.232.6)**
   - Flask application handling webhooks
   - Optional Spotify integration
   - Nginx reverse proxy

2. **MQTT Broker (172.16.234.55)**
   - Mosquitto MQTT broker
   - Message routing and authentication

3. **MatrixPortal M4 Displays**
   - WC, Bathroom, and Eva displays
   - WiFi-enabled with MQTT clients
   - Support timer and preset modes

## Features

- **Timer Mode**: Countdown timers with animations
- **Preset Mode**: Pre-configured displays (On Air, Score, Breaking, Music, Reset)
- **Music Preset**: Two-line display showing artist and song with automatic scrolling
- **Spotify Integration**: Display currently playing tracks (optional)
- **Text Scrolling**: Long text automatically scrolls horizontally
- **Automatic Reconnection**: Robust MQTT connection handling

## Getting Help

- Check the troubleshooting sections in each guide
- Review the [Architecture](architecture.md) document for system overview
- See [Display Operation](display_operation.md) for testing and usage examples
