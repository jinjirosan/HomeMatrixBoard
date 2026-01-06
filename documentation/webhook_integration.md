# Webhook Integration Guide

This guide provides the API reference for the webhook endpoints used to control the HomeMatrixBoard displays.

## Base URL
- **Production**: `http://172.16.232.6:52341`
- **Endpoint**: `/sigfox`

## Endpoint
- **URL**: `http://172.16.232.6:52341/sigfox`
- **Methods**: GET, POST
- **Content-Type**: `application/json` (for POST requests)

## Required Parameters

### Timer Mode (Default)
- `target`: Display identifier (wc, bathroom, eva)
- `text`: Text to display on the screen
- `duration`: Time in seconds

### Preset Mode
- `target`: Display identifier (wc, bathroom, eva)
- `mode`: Set to "preset"
- `preset_id`: Preset identifier (on_air, score, breaking, music, reset)
- `duration`: Time in seconds (optional)
- `name`: Override text (optional, not used for music preset)

### Music Preset Mode
- `target`: Display identifier (wc, bathroom, eva)
- `mode`: Must be "preset"
- `preset_id`: Must be "music"
- `artist`: Artist name (required)
- `song`: Song name (required)
- `duration`: Time in seconds (optional)

## Examples

### Timer Mode (GET)
```bash
# Start a 60-second timer on WC display
curl "http://172.16.232.6:52341/sigfox?target=wc&text=Shower&duration=60"

# Start a 60-second timer with URL-encoded text
curl "http://172.16.232.6:52341/sigfox?target=wc&text=WC%20over&duration=60"
```

### Timer Mode (POST)
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","text":"WC over","duration":60}' \
     http://172.16.232.6:52341/sigfox
```

### Preset Mode (GET)
```bash
# Activate "On Air" preset on WC display
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air"

# Activate "Score" preset with 1-hour duration
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=score&duration=3600"

# Activate "Breaking" preset with custom text
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=breaking&name=News%20Flash"

# Reset display
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=reset"
```

### Preset Mode (POST)
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","mode":"preset","preset_id":"on_air","duration":3600}' \
     http://172.16.232.6:52341/sigfox
```

### Music Preset Mode (POST only)
```bash
# Music preset requires POST with JSON body
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","mode":"preset","preset_id":"music","artist":"The Beatles","song":"Hey Jude","duration":30}' \
     http://172.16.232.6:52341/sigfox
```

## Available Presets

1. **On Air** (`preset_id=on_air`)
   - Black background with red "ON AIR" text
   - Solid white border
   - Radio symbol displayed

2. **Score** (`preset_id=score`)
   - Green background with yellow "SCORE" text
   - Animated yellow border

3. **Breaking** (`preset_id=breaking`)
   - Blue background with white "BREAKING" text
   - Blinking red border

4. **Music** (`preset_id=music`)
   - Purple background (0x800080)
   - Two-line display:
     - Top line: Artist name (white text, scrolls if >10 chars)
     - Bottom line: Song name (white text, scrolls if >10 chars)
   - Animated magenta border (0xFF00FF)
   - Requires `artist` and `song` parameters (not `name`)
   - See [Spotify Integration](spotify_integration.md) for automated music display

5. **Reset** (`preset_id=reset`)
   - Black background with no text
   - No border
   - Resets display to initial state

## Response Codes
- **200**: Success
- **400**: Invalid parameters or missing required fields
- **500**: Server error

## Available Displays
- **WC**: use `target=wc`
- **Bathroom**: use `target=bathroom`
- **Eva**: use `target=eva`

## Music Preset Special Notes
- Music preset uses two separate fields: `artist` and `song` (not `name`)
- Both artist and song are displayed on separate lines
- Text automatically scrolls if longer than 10 characters per line
- If artist or song is missing, displays "Unknown Artist" or "Unknown Song"
- If both are missing, displays "NO TRACK DATA" error message

## Notes
- The text will be displayed exactly as provided
- For GET requests, use URL encoding for spaces in text:
  - Use `%20` or `+` for spaces (e.g., `WC%20over` or `WC+over`)
- POST requests don't need URL encoding
- Duration is in seconds
- Timer mode requires: `target`, `text`, `duration`
- Preset mode requires: `target`, `mode=preset`, `preset_id`
- Music preset requires: `target`, `mode=preset`, `preset_id=music`, `artist`, `song`

## Spotify Integration Endpoints

The webserver also provides Spotify integration endpoints for automated music display. These require Spotify credentials and authentication.

### Authentication
```bash
# Initiate Spotify OAuth flow
curl "http://172.16.232.6:52341/spotify/auth"
# Follow redirect to authenticate, then callback completes authentication
```

### Display Current Track
```bash
# Display current track on specific display
curl "http://172.16.232.6:52341/spotify/wc"
curl "http://172.16.232.6:52341/spotify/bathroom"
curl "http://172.16.232.6:52341/spotify/eva"

# Display current track on all displays
curl "http://172.16.232.6:52341/spotify/all"
```

**Note**: Spotify integration requires:
- `spotipy` Python library installed
- `spotify_credentials.py` file configured with Client ID, Secret, and Redirect URI
- Initial OAuth authentication via `/spotify/auth` endpoint

For detailed setup instructions, see [Spotify Integration Guide](spotify_integration.md).

## Service Management
After making changes to `app.py`, restart the service:
```bash
sudo systemctl restart sigfox-bridge
```

## Sigfox Backend Configuration

### Callback Type
- Type: URL
- Channel: UPLINK
- URL Pattern: 
  ```
  http://172.16.232.6:52341/sigfox
  ```

### Custom Parameters
- `target={customData#target}`
- `text={customData#text}`
- `duration={customData#duration}`
