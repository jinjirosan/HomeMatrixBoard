# HomeMatrixBoard System Architecture

## Overview
The HomeMatrixBoard system is a distributed IoT display system that shows countdown timers on LED matrix displays. The system consists of three main components:

1. **Webserver (172.16.234.39)**
   - Debian 12 server running Flask application
   - Handles incoming Sigfox webhooks
   - Processes and forwards messages to MQTT broker
   - Protected by Nginx reverse proxy

2. **MQTT Broker (172.16.234.55)**
   - Debian 12 server running Mosquitto
   - Manages message distribution
   - Handles authentication and access control
   - Topic structure: home/displays/{location}

3. **MatrixPortal M4 Displays**
   - LED matrix displays showing countdown timers
   - WiFi-enabled with MQTT client
   - Locations: WC, Bathroom, Eva
   - Displays countdown timers with animations

## Message Flow
1. External trigger sends webhook to webserver (GET/POST)
2. Webserver validates and formats message
3. Message published to MQTT broker with format:
   ```json
   {
       "name": "WC Tijd",
       "duration": 60
   }
   ```
4. MQTT broker routes to appropriate display
5. Display shows animated countdown

## Network Architecture
```ascii
+-------------+     +---------------+     +------------------+
| External    |---->| Webserver    |---->| MQTT Broker     |
| Webhook     |     | 172.16.234.39|     | 172.16.234.55   |
+-------------+     +---------------+     +------------------+
                                                |
                                                |
                    +--------------------+      |
                    |      WiFi AP       |<-----+
                    |     AirMAX-IoT     |
                    +--------------------+
                            |
              +-------------+-------------+
              |             |             |
        +-----v-----+ +-----v-----+ +-----v-----+
        |    WC     | | Bathroom  | |   Eva     |
        | Display   | | Display   | | Display   |
        +-----------+ +-----------+ +-----------+
```

## Security
- MQTT authentication required for all connections
- Separate credentials for webserver and displays
- Topic-specific ACLs limit access
- Nginx reverse proxy protects webserver

## Testing
Test webhook endpoint:
```bash
curl "http://172.16.234.39/sigfox?name=wc&duration=60"
```

Test MQTT directly:
```bash
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name": "WC Tijd", "duration": 15}'
```