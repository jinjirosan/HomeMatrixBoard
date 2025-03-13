# MatrixPortal M4 Display Setup Guide

This guide explains how to set up a new MatrixPortal M4 display for the HomeMatrixBoard system.

## Hardware Requirements

- Adafruit MatrixPortal M4
- 64x32 RGB LED Matrix
- 5V 4A Power Supply
- USB-C cable for programming
- Computer with CircuitPython support

## Software Requirements

- CircuitPython 7.0 or later
- Required libraries (included in the lib/ folder)

## Initial Setup

1. **Connect the MatrixPortal M4 to your computer** using a USB-C cable
   - The device should appear as a drive named `CIRCUITPY`

2. **Install CircuitPython** (if not already installed)
   - Download the latest version from [circuitpython.org](https://circuitpython.org/board/matrixportal_m4/)
   - Follow the installation instructions on the website

## Configuration Steps

### 1. Prepare the Files

When you connect the MatrixPortal M4 to your computer, you should see:
- `CIRCUITPY` drive mounted
- `code.py` (main program)
- `secrets.py` (configuration file)
- `lib/` folder (libraries)

### 2. Configure the Display Identity

Edit the `secrets.py` file to configure the display's identity:

```python
# This file is where you keep secret settings, passwords, and tokens!
secrets = {
    'ssid': 'AirMAX-IoT',                  # WiFi network name
    'password': '********',                # WiFi password (replace with actual password)
    'mqtt_broker': '172.16.234.55',        # MQTT broker IP address
    'mqtt_port': 1883,                     # MQTT port
    'mqtt_topic': 'home/displays/wc',      # MQTT topic - CHANGE THIS for each display
    'mqtt_user': 'wc_display',             # MQTT username - CHANGE THIS for each display
    'mqtt_password': '********',           # MQTT password (replace with actual password)
    'test_mode': False                     # Enable test mode for debugging
}
```

**Important**: Change the `mqtt_topic` and `mqtt_user` values based on which display you're setting up:

| Display   | MQTT Topic                | MQTT Username       |
|-----------|---------------------------|---------------------|
| WC        | `home/displays/wc`        | `wc_display`        |
| Bathroom  | `home/displays/bathroom`  | `bathroom_display`  |
| Eva       | `home/displays/eva`       | `eva_display`       |

### 3. Install the Code

1. **Copy the code.py file** from the repository to the CIRCUITPY drive:
   - Use the appropriate code file from the repository:
     - `displays/wc/code.py` for WC display
     - `displays/bathroom/code.py` for Bathroom display
     - `displays/eva/code.py` for Eva display

2. **Copy the lib folder** from the repository to the CIRCUITPY drive:
   - Make sure all required libraries are included
   - The lib folder should contain:
     - adafruit_matrixportal
     - adafruit_minimqtt
     - adafruit_esp32spi
     - adafruit_display_text
     - Other required libraries

### 4. Test the Display

1. **Safely eject** the CIRCUITPY drive from your computer
2. **Power cycle** the MatrixPortal M4 (disconnect and reconnect power)
3. **Observe the display** - it should:
   - Connect to WiFi
   - Connect to the MQTT broker
   - Subscribe to its topic
   - Show its ready state (waiting for messages)

## Troubleshooting

### Serial Console

For debugging, connect to the serial console:
- Use a terminal program like `screen` or PuTTY
- Connect at 115200 baud
- Example: `screen /dev/tty.usbmodem* 115200`

### Common Issues

1. **Display not connecting to WiFi**
   - Check the SSID and password in secrets.py
   - Ensure the WiFi network is in range
   - Verify the WiFi network supports the device

2. **Display not connecting to MQTT**
   - Check the MQTT broker IP address
   - Verify the MQTT credentials
   - Ensure the MQTT broker is running and accessible

3. **Display not receiving messages**
   - Verify the MQTT topic matches the expected format
   - Check that the webserver is publishing to the correct topic
   - Test by publishing a message directly to the topic:
     ```bash
     mosquitto_pub -h 172.16.234.55 -u mqtt_username -P mqtt_password \
         -t "home/displays/wc" -m '{"name": "Test", "duration": 15}'
     ```

4. **Display showing errors or not updating**
   - Check the serial console for error messages
   - Ensure all required libraries are installed
   - Try resetting the device (press the reset button)

## Updating an Existing Display

To update an existing display:
1. Connect the display to your computer
2. Back up any custom configuration (secrets.py)
3. Copy the new code.py file to the CIRCUITPY drive
4. Update the lib folder if necessary
5. Restore your custom configuration
6. Safely eject and power cycle the display

## Testing Commands

Test the display with these commands:

```bash
# Test timer mode
curl "http://172.16.232.6:52341/sigfox?target=wc&text=Test&duration=10"

# Test preset mode
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air"

# Reset display
curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=reset"
```

Replace `wc` with the appropriate target for your display (wc, bathroom, eva). 