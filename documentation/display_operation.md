# MatrixPortal M4 Display Operation Guide

## Overview
The system uses MatrixPortal M4 LED matrix displays to show countdown timers. Each display subscribes to a specific MQTT topic and shows countdown timers based on received messages.

## Hardware Requirements
- Adafruit MatrixPortal M4
- 64x32 RGB LED Matrix
- 5V 4A Power Supply
- USB-C cable for programming

## Display Features
1. Countdown Timer
   - Shows time remaining in MM:SS format
   - Border animation during countdown
   - Final countdown animation (last 10 seconds)
   - "DONE" message when complete

2. Preset Displays
   - "On Air" - Black background with red text
   - "Score" - Green background with yellow text
   - "Breaking" - Blue background with white text
   - "Music" - Purple background with white text (two-line display)
   - Configurable display duration
   - Custom border animations per preset
   - Automatic text scrolling for long text

3. Status Indicators
   - WiFi connection status
   - MQTT connection status
   - Error messages

## Message Format
Messages can be formatted in two ways:

1. Timer Mode (Original Format):
```json
{
    "name": "WC Tijd",
    "duration": 15
}
```
- `name`: Display title (automatically centered)
- `duration`: Countdown time in seconds

2. Preset Mode (New Format):
```json
{
    "mode": "preset",
    "preset_id": "on_air",
    "name": "Studio 1",    // Optional
    "duration": 3600      // Optional, auto-clear after duration
}
```
- `mode`: Set to "preset" for preset displays
- `preset_id`: One of: "on_air", "score", "breaking", "music", "reset"
- `name`: Optional custom text override (not used for music preset)
- `duration`: Optional display duration in seconds

3. Music Preset Mode (Special Format):
```json
{
    "mode": "preset",
    "preset_id": "music",
    "artist": "The Beatles",    // Required for music preset
    "song": "Hey Jude",         // Required for music preset
    "duration": 30              // Optional, auto-clear after duration
}
```
- `mode`: Must be "preset"
- `preset_id`: Must be "music"
- `artist`: Artist name (displayed on top line, scrolls if >10 chars)
- `song`: Song name (displayed on bottom line, scrolls if >10 chars)
- `duration`: Optional display duration in seconds

## Available Presets

### 1. On Air Preset
- Background: Black
- Text: "ON AIR" in red
- Border: Solid white
- Radio Symbol: Red transmission symbol below text
- Usage: `{"mode": "preset", "preset_id": "on_air"}`

### 2. Score Preset
- Background: Green
- Text: "SCORE" in yellow
- Border: Animated yellow
- Usage: `{"mode": "preset", "preset_id": "score"}`

### 3. Breaking Preset
- Background: Blue
- Text: "BREAKING" in white
- Border: Blinking red
- Usage: `{"mode": "preset", "preset_id": "breaking"}`

### 4. Music Preset
- Background: Purple (0x800080)
- Text: Two-line display
  - Top line: Artist name (white text)
  - Bottom line: Song name (white text)
- Border: Animated magenta (0xFF00FF)
- Text Scrolling: Automatically scrolls if text exceeds 10 characters per line
- Usage: `{"mode": "preset", "preset_id": "music", "artist": "Artist Name", "song": "Song Name"}`
- Error State: Shows "NO TRACK DATA" if artist/song not provided

### 5. Reset Preset
- Background: Black
- Text: None
- Border: None
- Resets display to initial state
- Usage: `{"mode": "preset", "preset_id": "reset"}`

## MQTT Topics
Each display subscribes to a specific topic:
- WC Display: `home/displays/wc`
- Bathroom Display: `home/displays/bathroom`
- Eva Display: `home/displays/eva`

## Display States

### 1. Ready State
- Shows display name
- Solid border
- Waiting for MQTT message

### 2. Countdown State
- Shows title and time remaining
- Animated border
- Updates every second

### 3. Final Countdown State (last 10 seconds)
- Blinking border
- Running ants animation
- Emphasized time display

### 4. Done State
- Shows "DONE" message
- Solid border
- Returns to ready state after 10 seconds

## MQTT Connection Management

### Connection Features
- Automatic reconnection with exponential backoff
- Memory-efficient connection handling
- Robust subscription recovery
- Optimized timeout configuration:
  - Socket timeout: 0.1s
  - Receive timeout: 0.2s
  - MQTT loop timeout: 0.1s

### Connection States
1. Initial Connection
   - Attempts connection to MQTT broker
   - Subscribes to display-specific topic
   - Reports connection status

2. Connection Monitoring
   - Regular connection checks
   - Automatic reconnection on failure
   - Resubscription after reconnection

3. Error Recovery
   - Exponential backoff for retry attempts
   - Base delay: 3 seconds
   - Maximum delay: 300 seconds (5 minutes)
   - Independent WiFi and MQTT retry tracking

## Testing

### 1. Direct MQTT Testing
```bash
# Test timer mode
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name": "WC Tijd", "duration": 15}'

# Test preset mode
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"mode": "preset", "preset_id": "on_air", "duration": 3600}'

# Test music preset mode
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"mode": "preset", "preset_id": "music", "artist": "The Beatles", "song": "Hey Jude", "duration": 30}'
```

### 2. Webhook Testing
```bash
# Test timer via webserver
curl "http://172.16.232.6/sigfox?name=wc&duration=60"

# Test preset via webserver
curl "http://172.16.232.6/sigfox?mode=preset&preset_id=on_air&name=wc"

# Test music preset via webserver (requires artist and song)
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","mode":"preset","preset_id":"music","artist":"The Beatles","song":"Hey Jude","duration":30}' \
     http://172.16.232.6:52341/sigfox
```


## Troubleshooting

### 1. Display Not Responding
1. Check power connection
2. Verify WiFi connection
3. Check MQTT subscription
4. Monitor serial output for connection status
5. Reset display if needed

### 2. Display Shows Error
1. Check error message in serial output
2. Verify MQTT credentials
3. Check message format
4. Verify network connectivity
5. Monitor connection retry attempts

### 3. Common Issues
1. WiFi Connection
   - Check WiFi credentials in secrets.py
   - Verify WiFi signal strength
   - Check network configuration
   - Monitor reconnection attempts

2. MQTT Connection
   - Verify broker IP address
   - Check MQTT credentials
   - Confirm topic subscription
   - Monitor connection retry intervals
   - Check serial output for connection status

3. Display Issues
   - Check power supply (needs 5V 4A)
   - Verify matrix connections
   - Check for loose cables
   - Monitor memory usage
   - Check for stack exhaustion errors

## Maintenance

### 1. Regular Checks
- Monitor power supply stability
- Check WiFi connection quality
- Verify MQTT connection status
- Clean display surface if needed

### 2. Software Updates
- Keep CircuitPython updated
- Update libraries when needed
- Backup configuration files
- Test after updates

### 3. Hardware Care
- Keep displays clean
- Check for loose connections
- Monitor power supply quality
- Ensure proper ventilation