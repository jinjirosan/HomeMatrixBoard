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

2. Status Indicators
   - WiFi connection status
   - MQTT connection status
   - Error messages

## Message Format
Messages must be formatted as JSON:
```json
{
    "name": "WC Tijd",
    "duration": 15
}
```
- `name`: Display title (automatically centered)
- `duration`: Countdown time in seconds

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

## Testing

### 1. Direct MQTT Testing
```bash
# Test WC display
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" -m '{"name": "WC Tijd", "duration": 15}'

# Test bathroom display
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/bathroom" -m '{"name": "Bathroom Tijd", "duration": 30}'

# Test Eva display
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/eva" -m '{"name": "Eva Tijd", "duration": 45}'
```

### 2. Webhook Testing
```bash
# Test via webserver
curl "http://172.16.234.39/sigfox?name=wc&duration=60"
```

## Troubleshooting

### 1. Display Not Responding
1. Check power connection
2. Verify WiFi connection
3. Check MQTT subscription
4. Reset display if needed

### 2. Display Shows Error
1. Check error message in serial output
2. Verify MQTT credentials
3. Check message format
4. Verify network connectivity

### 3. Common Issues
1. WiFi Connection
   - Check WiFi credentials in secrets.py
   - Verify WiFi signal strength
   - Check network configuration

2. MQTT Connection
   - Verify broker IP address
   - Check MQTT credentials
   - Confirm topic subscription

3. Display Issues
   - Check power supply (needs 5V 4A)
   - Verify matrix connections
   - Check for loose cables

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