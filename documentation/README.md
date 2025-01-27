# Display System Documentation

## Overview
This system integrates Sigfox webhooks with MQTT messaging to control multiple MatrixPortal M4 displays. The architecture consists of two VMs (webserver and MQTT broker) and multiple display devices. The system features robust MQTT connection handling with automatic reconnection, memory optimization, and efficient error recovery.

## Components
- **Webserver VM**: Handles incoming webhooks and forwards messages to MQTT broker
- **MQTT Broker VM**: Manages message distribution to displays with optimized connection settings
- **MatrixPortal M4 Displays**: Show countdown timers and presets with reliable MQTT connectivity
  - Automatic reconnection with exponential backoff
  - Memory-efficient connection handling
  - Robust subscription recovery

## Documentation Structure
- **Technical Documentation**
  - Architecture details
  - MQTT broker setup and configuration
  - Webserver setup and configuration
  - Security considerations
  - Connection management and optimization

- **User Guides**
  - Display operation instructions
  - Webhook integration guide
  - Troubleshooting and maintenance

## Quick Start
1. Send webhook to: `http://172.16.234.39/sigfox?name=<display_name>&duration=<seconds>`
2. Supported display names: wc, bathroom, eva
3. Duration in seconds (e.g., 60 for one minute)
4. Monitor display's serial output for connection status 