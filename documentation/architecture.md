# HomeMatrixBoard System Architecture

## Overview
The HomeMatrixBoard system is a distributed IoT display system that shows countdown timers and preset displays on LED matrix displays. The system consists of three main components:

1. **Webserver (172.16.232.6)**
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
   - LED matrix displays showing countdown timers and preset displays
   - WiFi-enabled with MQTT client
   - Locations: WC, Bathroom, Eva
   - Supports:
     - Countdown timers with animations
     - Preset displays (On Air, Score, Breaking)
     - Custom text and durations

## Message Flow
1. External trigger sends webhook to webserver (GET/POST)
2. Webserver validates and formats message
3. Message published to MQTT broker with format:
   ```json
   # Timer Mode
   {
       "name": "WC Tijd",
       "duration": 60
   }
   
   # Preset Mode
   {
       "mode": "preset",
       "preset_id": "on_air",
       "name": "Studio 1",    # Optional
       "duration": 3600      # Optional
   }
   ```
4. MQTT broker routes to appropriate display
5. Display shows either:
   - Animated countdown timer
   - Preset display with custom background and text

## Network Architecture
```ascii
+-------------+     +---------------+     +------------------+
| External    |---->| SigfoxWebhost |---->|  MQTT Broker     |
| Webhook     |     | 172.16.232.6  |     |  172.16.234.55   |
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
curl "http://172.16.232.6/sigfox?name=wc&duration=60"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=breaking"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=score"       
```

Test MQTT directly:
```bash
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name": "WC Tijd", "duration": 15}'
```