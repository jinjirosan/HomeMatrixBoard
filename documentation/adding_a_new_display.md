# Adding a New Display Guide

This guide provides step-by-step instructions for adding a new MatrixPortal M4 display to the HomeMatrixBoard system.

## Overview

When adding a new display, you need to configure:
1. **MQTT Broker**: Add new user and ACL permissions
2. **Webserver**: Add new target mapping in `app.py`
3. **Display Hardware**: Configure firmware and secrets.py
4. **Testing**: Verify the new display works correctly

## Prerequisites

- Access to MQTT broker server (172.16.234.55) via SSH
- Access to webserver (172.16.232.6) via SSH
- New MatrixPortal M4 hardware ready for setup
- USB-C cable for programming
- Basic knowledge of Linux command line

## Step 1: Choose Display Name and Target

First, decide on:
- **Display Name**: A friendly name (e.g., "kitchen", "bedroom", "office")
- **Target ID**: A short identifier used in URLs (e.g., "kitchen", "bedroom", "office")
- **MQTT Topic**: `home/displays/{target_id}`
- **MQTT Username**: `{target_id}_display`

**Example for a new "Kitchen" display:**
- Display Name: Kitchen
- Target ID: `kitchen`
- MQTT Topic: `home/displays/kitchen`
- MQTT Username: `kitchen_display`

## Step 2: Configure MQTT Broker

### 2.1 Add New User to MQTT Broker

SSH into the MQTT broker (172.16.234.55):

```bash
# SSH into broker
ssh user@172.16.234.55

# Add new display user (replace 'kitchen' with your target_id)
sudo mosquitto_passwd /etc/mosquitto/passwd kitchen_display
# Enter password when prompted (use a strong password)
```

**Important:** Do NOT use the `-c` flag as it will overwrite the existing password file. Use the command above without `-c`.

### 2.2 Update ACL File

Edit the ACL file to add permissions for the new display:

```bash
# Edit ACL file
sudo nano /etc/mosquitto/acl
```

Add the new display user and topic permissions:

```conf
# Publisher (Web server)
user sigfoxwebhookhost
topic write home/displays/#

# Individual display subscribers
user wc_display
topic read home/displays/wc

user bathroom_display
topic read home/displays/bathroom

user eva_display
topic read home/displays/eva

# Add your new display here
user kitchen_display
topic read home/displays/kitchen
```

Save and exit (Ctrl+X, then Y, then Enter).

### 2.3 Restart MQTT Broker

```bash
# Restart Mosquitto to apply changes
sudo systemctl restart mosquitto

# Verify service is running
sudo systemctl status mosquitto
```

### 2.4 Test MQTT Configuration

Test that the new user can subscribe to their topic:

```bash
# Subscribe to the new display topic (replace with your values)
mosquitto_sub -h localhost -u kitchen_display -P <password> -t "home/displays/kitchen"
```

In another terminal, test publishing:

```bash
# Publish a test message (use sigfoxwebhookhost credentials)
mosquitto_pub -h localhost -u sigfoxwebhookhost -P <password> \
    -t "home/displays/kitchen" -m '{"name": "Test", "duration": 5}'
```

You should see the message appear in the subscription terminal.

## Step 3: Update Webserver Configuration

### 3.1 Update app.py

SSH into the webserver (172.16.232.6):

```bash
# SSH into webserver
ssh user@172.16.232.6

# Navigate to project directory
cd ~/sigfox_mqtt_bridge

# Backup app.py
cp app.py app.py.backup

# Edit app.py
nano app.py
```

Find the `topic_mapping` dictionary (appears in multiple places). Update all occurrences:

**Location 1: In `handle_webhook()` function (around line 116):**
```python
# Map display targets to MQTT topics
topic_mapping = {
    'wc': 'home/displays/wc',
    'bathroom': 'home/displays/bathroom',
    'eva': 'home/displays/eva',
    'kitchen': 'home/displays/kitchen'  # Add your new display
}
```

**Location 2: In `spotify_current_track()` function (around line 169):**
```python
# Map display targets to MQTT topics
topic_mapping = {
    'wc': 'home/displays/wc',
    'bathroom': 'home/displays/bathroom',
    'eva': 'home/displays/eva',
    'kitchen': 'home/displays/kitchen'  # Add your new display
}
```

**Location 3: In `spotify_all_displays()` function (around line 255):**
```python
# Map display targets to MQTT topics
topic_mapping = {
    'wc': 'home/displays/wc',
    'bathroom': 'home/displays/bathroom',
    'eva': 'home/displays/eva',
    'kitchen': 'home/displays/kitchen'  # Add your new display
}
```

Also update the loop in `spotify_all_displays()` function (around line 262):
```python
results = {}
for target in ['wc', 'bathroom', 'eva', 'kitchen']:  # Add your new target
    topic = topic_mapping[target]
    success = publish_to_mqtt(topic, message_data)
    results[target] = "success" if success else "failed"
```

Save and exit (Ctrl+X, then Y, then Enter).

### 3.2 Restart Webserver Service

```bash
# Restart the Flask service
sudo systemctl restart sigfox-bridge

# Verify service is running
sudo systemctl status sigfox-bridge

# Check for errors
sudo journalctl -u sigfox-bridge -n 50
```

## Step 4: Configure Display Hardware

### 4.1 Connect Display to Computer

1. Connect the MatrixPortal M4 to your computer via USB-C
2. Wait for the `CIRCUITPY` drive to mount

### 4.2 Create Display Code File

You have two options:

**Option A: Use Existing Display Code as Template**
- Copy `displays/wc/code.py` or another display's code
- Rename it appropriately for your new display

**Option B: Use Spotify Template (Recommended)**
- Use `templates/display_code_py/spotify/code.py`
- This includes all features including Spotify support

Copy the chosen file to the CIRCUITPY drive as `code.py`.

### 4.3 Configure secrets.py

Create or edit `secrets.py` on the CIRCUITPY drive:

```python
# This file is where you keep secret settings, passwords, and tokens!
secrets = {
    'ssid': 'AirMAX-IoT',                  # WiFi network name
    'password': '********',                # WiFi password (replace with actual password)
    'mqtt_broker': '172.16.234.55',        # MQTT broker IP address
    'mqtt_port': 1883,                     # MQTT port
    'mqtt_topic': 'home/displays/kitchen', # MQTT topic - CHANGE THIS for your display
    'mqtt_user': 'kitchen_display',        # MQTT username - CHANGE THIS for your display
    'mqtt_password': '********',           # MQTT password (use the password you set in Step 2.1)
    'test_mode': False                     # Enable test mode for debugging
}
```

**Important:** Update these values:
- `mqtt_topic`: Must match the topic you configured in Step 2.2
- `mqtt_user`: Must match the username you created in Step 2.1
- `mqtt_password`: Must match the password you set in Step 2.1

### 4.4 Copy Required Libraries

Ensure the `lib/` folder on the CIRCUITPY drive contains all required libraries:
- adafruit_matrixportal
- adafruit_minimqtt
- adafruit_esp32spi
- adafruit_display_text (including scrolling_label.mpy)
- Other required libraries

Copy the `lib/` folder from the repository if needed.

### 4.5 Power Cycle Display

1. **Safely eject** the CIRCUITPY drive from your computer
2. **Power cycle** the MatrixPortal M4 (disconnect and reconnect power)
3. **Observe the display** - it should:
   - Connect to WiFi
   - Connect to the MQTT broker
   - Subscribe to its topic
   - Show its ready state (waiting for messages)

## Step 5: Test the New Display

### 5.1 Test Timer Mode

```bash
# Test timer mode via webhook
curl "http://172.16.232.6:52341/sigfox?target=kitchen&text=Test&duration=10"
```

The display should show a 10-second countdown timer.

### 5.2 Test Preset Mode

```bash
# Test "On Air" preset
curl "http://172.16.232.6:52341/sigfox?target=kitchen&mode=preset&preset_id=on_air"

# Test "Score" preset
curl "http://172.16.232.6:52341/sigfox?target=kitchen&mode=preset&preset_id=score"

# Test "Breaking" preset
curl "http://172.16.232.6:52341/sigfox?target=kitchen&mode=preset&preset_id=breaking"

# Test reset
curl "http://172.16.232.6:52341/sigfox?target=kitchen&mode=preset&preset_id=reset"
```

### 5.3 Test Direct MQTT (Optional)

```bash
# Test direct MQTT publishing
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/kitchen" -m '{"name": "Direct Test", "duration": 15}'
```

### 5.4 Test Spotify Integration (If Enabled)

```bash
# Test Spotify integration
curl "http://172.16.232.6:52341/spotify/kitchen"
```

## Step 6: Verify All Systems

### 6.1 Check MQTT Connection

Monitor the display's serial console to verify:
- WiFi connection successful
- MQTT connection successful
- Topic subscription successful
- No error messages

### 6.2 Check Webserver Logs

```bash
# On webserver, check logs
sudo journalctl -u sigfox-bridge -f
```

Send a test message and verify it appears in the logs.

### 6.3 Check MQTT Broker Logs

```bash
# On MQTT broker, check logs
sudo tail -f /var/log/mosquitto/mosquitto.log
```

Verify messages are being published and subscribed correctly.

## Troubleshooting

### Display Not Connecting to MQTT

1. **Verify credentials match:**
   - Check `secrets.py` on display matches MQTT broker user/password
   - Verify username matches ACL entry

2. **Check MQTT broker:**
   - Verify user exists: `sudo cat /etc/mosquitto/passwd | grep kitchen_display`
   - Verify ACL entry exists: `sudo cat /etc/mosquitto/acl | grep kitchen`
   - Check broker is running: `sudo systemctl status mosquitto`

3. **Check network connectivity:**
   - Verify display can reach broker IP (172.16.234.55)
   - Check firewall rules if applicable

### Webserver Returns "Invalid target display"

1. **Verify app.py was updated:**
   - Check all three `topic_mapping` dictionaries include your new target
   - Verify service was restarted after changes

2. **Check service logs:**
   ```bash
   sudo journalctl -u sigfox-bridge -n 50
   ```

### Display Not Receiving Messages

1. **Verify topic subscription:**
   - Check serial console shows subscription successful
   - Verify topic name matches exactly (case-sensitive)

2. **Test MQTT directly:**
   - Use mosquitto_pub to send message directly
   - Use mosquitto_sub to verify display is subscribed

3. **Check ACL permissions:**
   - Verify display user has `read` permission for their topic
   - Verify webserver user has `write` permission for `home/displays/#`

## Summary Checklist

Use this checklist to ensure all steps are completed:

- [ ] **Step 1**: Chosen display name, target ID, MQTT topic, and username
- [ ] **Step 2.1**: Added new user to MQTT broker password file
- [ ] **Step 2.2**: Added ACL entry for new display
- [ ] **Step 2.3**: Restarted MQTT broker
- [ ] **Step 2.4**: Tested MQTT subscription and publishing
- [ ] **Step 3.1**: Updated all three `topic_mapping` dictionaries in app.py
- [ ] **Step 3.1**: Updated `spotify_all_displays()` loop if using Spotify
- [ ] **Step 3.2**: Restarted webserver service
- [ ] **Step 4.1**: Connected display hardware
- [ ] **Step 4.2**: Copied code.py to display
- [ ] **Step 4.3**: Configured secrets.py with correct values
- [ ] **Step 4.4**: Verified all libraries are present
- [ ] **Step 4.5**: Power cycled display and verified connection
- [ ] **Step 5.1**: Tested timer mode
- [ ] **Step 5.2**: Tested preset modes
- [ ] **Step 5.3**: Tested direct MQTT (optional)
- [ ] **Step 5.4**: Tested Spotify integration (if enabled)
- [ ] **Step 6**: Verified all systems working

## Example: Adding "Kitchen" Display

Here's a complete example for adding a "Kitchen" display:

### MQTT Broker Configuration
```bash
# Add user
sudo mosquitto_passwd /etc/mosquitto/passwd kitchen_display
# Enter password when prompted

# ACL entry
user kitchen_display
topic read home/displays/kitchen
```

### Webserver Configuration
```python
topic_mapping = {
    'wc': 'home/displays/wc',
    'bathroom': 'home/displays/bathroom',
    'eva': 'home/displays/eva',
    'kitchen': 'home/displays/kitchen'  # New
}
```

### Display secrets.py
```python
secrets = {
    'ssid': 'AirMAX-IoT',
    'password': 'your_wifi_password',
    'mqtt_broker': '172.16.234.55',
    'mqtt_port': 1883,
    'mqtt_topic': 'home/displays/kitchen',
    'mqtt_user': 'kitchen_display',
    'mqtt_password': 'your_mqtt_password',
    'test_mode': False
}
```

### Test Commands
```bash
# Timer mode
curl "http://172.16.232.6:52341/sigfox?target=kitchen&text=Cooking&duration=30"

# Preset mode
curl "http://172.16.232.6:52341/sigfox?target=kitchen&mode=preset&preset_id=on_air"

# Spotify (if enabled)
curl "http://172.16.232.6:52341/spotify/kitchen"
```

## Related Documentation

- [Display Setup](display_setup.md) - Initial display hardware setup
- [Display Operation](display_operation.md) - How to use displays
- [MQTT Broker Setup](mqtt_broker_setup.md) - MQTT broker configuration details
- [Webserver Setup](webserver_setup.md) - Webserver configuration details
- [Webhook Integration](webhook_integration.md) - API reference

