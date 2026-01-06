# HomeMatrixBoard System Architecture

## Overview
The HomeMatrixBoard system is a distributed IoT display system that shows countdown timers and preset displays on LED matrix displays. The system consists of three main components:

1. **Webserver (172.16.232.6)**
   - Debian 12 server running Flask application
   - Handles incoming Sigfox webhooks
   - Processes and forwards messages to MQTT broker
   - Optional Spotify integration
   - Protected by Nginx reverse proxy

2. **MQTT Broker (172.16.234.55)**
   - Debian 12 server running Mosquitto
   - Manages message distribution
   - Handles authentication and access control
   - Topic structure: `home/displays/{location}`

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
       "name": "Studio 1",    // Optional
       "duration": 3600      // Optional
   }
   
   # Music Preset Mode
   {
       "mode": "preset",
       "preset_id": "music",
       "artist": "The Beatles",    // Required
       "song": "Hey Jude",         // Required
       "duration": 30              // Optional
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

- **MQTT Authentication**: Required for all connections
- **Separate Credentials**: Different credentials for webserver and displays
- **Topic-specific ACLs**: Limit access to specific topics
- **Nginx Reverse Proxy**: Protects webserver
- **Spotify OAuth**: Tokens stored securely (not in git)
- **Credential Management**: Credentials in separate files (mqtt_credentials.py, spotify_credentials.py)

For detailed security information, see [Security Guide](security.md).

## Component Details

### Webserver
- **Technology**: Flask (Python)
- **WSGI Server**: Gunicorn
- **Reverse Proxy**: Nginx
- **Port**: 5000 (internal), 80/52341 (external)
- **Features**:
  - Webhook endpoint: `/sigfox`
  - Spotify endpoints: `/spotify/{target}`, `/spotify/all`, `/spotify/auth`
  - Message validation and formatting
  - MQTT publishing

### MQTT Broker
- **Technology**: Mosquitto
- **Port**: 1883
- **Authentication**: Username/password
- **Access Control**: ACL-based topic permissions
- **Users**:
  - `sigfoxwebhookhost`: Can publish to all display topics
  - `wc_display`, `bathroom_display`, `eva_display`: Can only subscribe to their own topics

### Displays
- **Hardware**: Adafruit MatrixPortal M4
- **Display**: 64x32 RGB LED Matrix
- **Firmware**: CircuitPython
- **Connection**: WiFi + MQTT
- **Features**:
  - Automatic reconnection with exponential backoff
  - Memory-optimized initialization
  - Text scrolling for long content
  - Multiple display modes

## Topic Structure

```
home/displays/
  ├── wc          # WC display topic
  ├── bathroom    # Bathroom display topic
  └── eva         # Eva display topic
```

Each display subscribes to its own topic and publishes status/health information to subtopics:
- `home/displays/{location}/status` - Connection status
- `home/displays/{location}/health` - Health events
- `home/displays/{location}/errors` - Error reports
- `home/displays/{location}/ack` - Message acknowledgments

## Data Flow Examples

### Timer Mode
1. Webhook: `GET /sigfox?target=wc&text=Shower&duration=60`
2. Webserver formats: `{"name": "Shower", "duration": 60}`
3. MQTT publish: `home/displays/wc` with message
4. Display receives and shows countdown timer

### Preset Mode
1. Webhook: `GET /sigfox?target=wc&mode=preset&preset_id=on_air`
2. Webserver formats: `{"mode": "preset", "preset_id": "on_air"}`
3. MQTT publish: `home/displays/wc` with message
4. Display receives and shows "On Air" preset

### Spotify Integration
1. Webhook: `GET /spotify/wc`
2. Webserver fetches current track from Spotify API
3. Webserver formats: `{"mode": "preset", "preset_id": "music", "artist": "...", "song": "..."}`
4. MQTT publish: `home/displays/wc` with message
5. Display receives and shows two-line music preset

## System Requirements

### Webserver
- Debian 12
- Python 3.11+
- Nginx
- Flask, paho-mqtt, gunicorn
- Optional: spotipy (for Spotify integration)

### MQTT Broker
- Debian 12
- Mosquitto
- Network access to webserver and displays

### Displays
- CircuitPython 7.0+
- Required libraries (see display_setup.md)
- WiFi network access
- MQTT broker access

## Related Documentation

- [Display Setup](display_setup.md) - How to set up displays
- [Display Operation](display_operation.md) - How to use displays
- [Webserver Setup](webserver_setup.md) - Webserver configuration
- [MQTT Broker Setup](mqtt_broker_setup.md) - MQTT broker configuration
- [Webhook Integration](webhook_integration.md) - API reference
- [Spotify Integration](spotify_integration.md) - Optional Spotify setup
