# Webhook Integration Guide

## Endpoint
- URL: http://172.16.232.6/sigfox

## Required Parameters

### Timer Mode (Default)
- `target`: Display identifier (wc, bathroom, eva)
- `text`: Text to display on the screen
- `duration`: Time in seconds

### Preset Mode
- `target`: Display identifier (wc, bathroom, eva)
- `mode`: Set to "preset"
- `preset_id`: Preset identifier (on_air, score, breaking)
- `duration`: Time in seconds (optional)
- `text`: Override text (optional)

## Examples

### Timer Mode
```bash
# Start a 60-second timer on WC display
curl "http://172.16.232.6/sigfox?target=wc&text=Shower&duration=60"

# Start a 60-second timer with URL-encoded text
curl "http://172.16.232.6/sigfox?target=wc&text=WC%20over&duration=60"
```

### Preset Mode
```bash
# Activate "On Air" preset on WC display
curl "http://172.16.232.6/sigfox?target=wc&mode=preset&preset_id=on_air"

# Activate "Score" preset with 1-hour duration
curl "http://172.16.232.6/sigfox?target=wc&mode=preset&preset_id=score&duration=3600"

# Activate "Breaking" preset with custom text
curl "http://172.16.232.6/sigfox?target=wc&mode=preset&preset_id=breaking&text=News%20Flash"
```

### POST Request Examples
```bash
# Timer mode POST
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","text":"WC over","duration":"60"}' \
     http://172.16.232.6/sigfox

# Preset mode POST
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","mode":"preset","preset_id":"on_air","duration":3600}' \
     http://172.16.232.6/sigfox
```

## Available Presets
1. On Air (`preset_id=on_air`)
   - Red background with white "ON AIR" text
   - Solid white border

2. Score (`preset_id=score`)
   - Green background with yellow "SCORE" text
   - Animated yellow border

3. Breaking (`preset_id=breaking`)
   - Blue background with white "BREAKING" text
   - Blinking red border

## Response Codes
- 200: Success
- 400: Invalid parameters or missing required fields
- 500: Server error

## Available Displays
- WC: use `target=wc`
- Bathroom: use `target=bathroom`
- Eva: use `target=eva`

## Notes
- The text will be displayed exactly as provided
- For GET requests, use URL encoding for spaces in text:
  - Use `%20` or `+` for spaces (e.g., `WC%20over` or `WC+over`)
  - POST requests don't need URL encoding
- Duration is in seconds
- All parameters are required

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
  http://172.16.232.6/sigfox
  ```

### Custom Parameters
- target={customData#target}
- text={customData#text}
- duration={customData#duration}