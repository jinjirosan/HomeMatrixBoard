# Webhook Integration Guide

## Endpoint Details
- URL: http://172.16.234.39/sigfox
- Methods: GET, POST

## Required Parameters
- `target`: Display identifier (wc, bathroom, eva)
- `text`: Text to display on the screen
- `duration`: Time in seconds

## Example Requests

### GET Request
```bash
# Basic example
curl "http://172.16.234.39/sigfox?target=wc&text=Shower&duration=60"

# Examples with spaces in text (use %20 or + for spaces)
curl "http://172.16.234.39/sigfox?target=wc&text=WC%20over&duration=60"
curl "http://172.16.234.39/sigfox?target=bathroom&text=Bath+Time&duration=300"
curl "http://172.16.234.39/sigfox?target=eva&text=Homework+Done&duration=1800"
```

### POST Request
```bash
# With POST requests, no URL encoding is needed for spaces
curl -X POST -H "Content-Type: application/json" \
     -d '{"target":"wc","text":"WC over","duration":"60"}' \
     http://172.16.234.39/sigfox
```

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