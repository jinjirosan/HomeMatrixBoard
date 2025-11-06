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
     - Preset displays (On Air, Score, Breaking, Music)
     - Custom text and durations
     - Two-line text display with automatic scrolling

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
   
   # Music Preset Mode
   {
       "mode": "preset",
       "preset_id": "music",
       "artist": "The Beatles",    # Required
       "song": "Hey Jude",         # Required
       "duration": 30              # Optional
   }
   ```
4. MQTT broker routes to appropriate display
5. Display shows either:
   - Animated countdown timer
   - Preset display with custom background and text
   - Music preset with two-line display (artist/song) and scrolling text

## Network Architecture
```ascii
+-------------+     +---------------+     +------------------+
| External    |---->| SigfoxWebhost |---->|  MQTT Broker     |
| Webhook     |     | 172.16.232.6  |     |  172.16.234.55   |
+-------------+     |               |     +------------------+
                    |  Spotify API  |              |
+-------------+     |  Integration  |              |
| Spotify API |---->|  (Optional)  |              |
+-------------+     +---------------+              |
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
- Spotify OAuth tokens stored securely (not in git)
- Credentials in separate files (mqtt_credentials.py, spotify_credentials.py)

## Testing
Test webhook endpoint:
```bash
curl "http://172.16.232.6/sigfox?name=wc&duration=60"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=breaking"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=score"
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=reset"       
```

Test Spotify integration (requires authentication):
```bash
# Authenticate with Spotify
curl "http://172.16.232.6:52341/spotify/auth"

# Display current track on WC display
curl "http://172.16.232.6:52341/spotify/wc"

# Display current track on all displays
curl "http://172.16.232.6:52341/spotify/all"
```

Test MQTT directly:
```bash
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name": "WC Tijd", "duration": 15}'

# Test music preset via MQTT
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"mode": "preset", "preset_id": "music", "artist": "The Beatles", "song": "Hey Jude", "duration": 30}'
```