# Spotify Integration Setup Checklist

Follow these steps in order to set up and test the Spotify integration.

## Prerequisites

- [ ] Spotify Developer Account created at https://developer.spotify.com/dashboard
- [ ] Spotify App created with Client ID and Client Secret
- [ ] Access to webserver (172.16.232.6) via SSH
- [ ] Access to all three MatrixPortal M4 displays (WC, Bathroom, Eva) via USB-C
- [ ] Spotify account with active music playback capability

## Step 1: Configure Spotify Developer App

1. [ ] Go to https://developer.spotify.com/dashboard
2. [ ] Create a new app (or use existing)
3. [ ] Copy the **Client ID** and **Client Secret**
4. [ ] Add redirect URI: `http://172.16.232.6:52341/spotify/callback`
   - Click "Edit Settings" in your Spotify app
   - Add the redirect URI exactly as shown above
   - Click "Add" and "Save"

## Step 2: Webserver Setup

### 2.1 Install Python Dependencies

```bash
# SSH into webserver
ssh user@172.16.232.6

# Navigate to project directory
cd ~/sigfox_mqtt_bridge  # or wherever your app.py is located

# Activate virtual environment (if using one)
source venv/bin/activate

# Install spotipy library
pip install spotipy

# If not using virtual environment, install globally:
# sudo pip3 install spotipy
```

- [ ] `spotipy` library installed successfully
- [ ] No installation errors

### 2.2 Create Spotify Credentials File

```bash
# Still on webserver, in project directory
# Create spotify_credentials.py file
nano spotify_credentials.py
```

Add the following content (replace with your actual credentials):

```python
# Spotify API Credentials
SPOTIFY_CLIENT_ID = "your_actual_client_id_here"
SPOTIFY_CLIENT_SECRET = "your_actual_client_secret_here"
SPOTIFY_REDIRECT_URI = "http://172.16.232.6:52341/spotify/callback"
```

- [ ] File `spotify_credentials.py` created
- [ ] Client ID added
- [ ] Client Secret added
- [ ] Redirect URI matches Spotify dashboard

### 2.3 Verify app.py is Updated

- [ ] Confirm `app.py` has Spotify integration endpoints
- [ ] Check that `VALID_PRESETS` includes "music"
- [ ] Verify file was updated from repository

### 2.4 Restart Flask Service

```bash
# Restart the Flask service to load new code and dependencies
sudo systemctl restart sigfox-bridge

# Check service status
sudo systemctl status sigfox-bridge
```

- [ ] Service restarted successfully
- [ ] Service is running (status shows "active")
- [ ] No errors in service logs

### 2.5 Authenticate with Spotify

```bash
# From your local machine or browser, visit:
# http://172.16.232.6:52341/spotify/auth

# Or use curl:
curl "http://172.16.232.6:52341/spotify/auth"
```

This will:
1. Redirect you to Spotify login page
2. Ask you to authorize the app
3. Redirect back to callback URL
4. Store authentication token in `.spotify_cache` file

- [ ] OAuth flow completed
- [ ] Redirected back to callback successfully
- [ ] Authentication message displayed
- [ ] `.spotify_cache` file created on webserver

## Step 3: Update Display Firmware

**Repeat these steps for EACH display (WC, Bathroom, Eva):**

### 3.1 Update WC Display

1. [ ] Connect WC MatrixPortal M4 to computer via USB-C
2. [ ] Wait for CIRCUITPY drive to mount
3. [ ] **Backup** existing `code.py` (optional but recommended)
4. [ ] Copy `displays/wc/code.py` from repository to CIRCUITPY drive
5. [ ] Verify `lib/adafruit_display_text/scrolling_label.mpy` exists in `lib/` folder
6. [ ] Safely eject CIRCUITPY drive
7. [ ] Power cycle the display (unplug and replug power)
8. [ ] Verify display connects to WiFi and MQTT (check serial console if needed)

### 3.2 Update Bathroom Display

1. [ ] Connect Bathroom MatrixPortal M4 to computer via USB-C
2. [ ] Wait for CIRCUITPY drive to mount
3. [ ] **Backup** existing `code.py` (optional but recommended)
4. [ ] Copy `displays/bathroom/code.py` from repository to CIRCUITPY drive
5. [ ] Verify `lib/adafruit_display_text/scrolling_label.mpy` exists in `lib/` folder
6. [ ] Safely eject CIRCUITPY drive
7. [ ] Power cycle the display (unplug and replug power)
8. [ ] Verify display connects to WiFi and MQTT (check serial console if needed)

### 3.3 Update Eva Display

1. [ ] Connect Eva MatrixPortal M4 to computer via USB-C
2. [ ] Wait for CIRCUITPY drive to mount
3. [ ] **Backup** existing `code.py` (optional but recommended)
4. [ ] Copy `displays/eva/code.py` from repository to CIRCUITPY drive
5. [ ] Verify `lib/adafruit_display_text/scrolling_label.mpy` exists in `lib/` folder
6. [ ] Safely eject CIRCUITPY drive
7. [ ] Power cycle the display (unplug and replug power)
8. [ ] Verify display connects to WiFi and MQTT (check serial console if needed)

## Step 4: Testing

### 4.1 Test Music Preset via MQTT (Direct Test)

This tests the display firmware without Spotify:

```bash
# Test WC display
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" \
    -m '{"mode": "preset", "preset_id": "music", "artist": "The Beatles", "song": "Hey Jude", "duration": 30}'

# Test Bathroom display
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/bathroom" \
    -m '{"mode": "preset", "preset_id": "music", "artist": "The Beatles", "song": "Hey Jude", "duration": 30}'

# Test Eva display
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/eva" \
    -m '{"mode": "preset", "preset_id": "music", "artist": "The Beatles", "song": "Hey Jude", "duration": 30}'
```

**Expected Result:**
- [ ] Display shows purple background
- [ ] Top line shows "The Beatles" (may scroll if long)
- [ ] Bottom line shows "Hey Jude" (may scroll if long)
- [ ] Animated magenta border
- [ ] Display clears after 30 seconds

### 4.2 Test Spotify Integration

**Prerequisites:**
- [ ] Spotify is playing music on your account
- [ ] You've completed OAuth authentication (Step 2.5)

```bash
# Test on WC display
curl "http://172.16.232.6:52341/spotify/wc"

# Test on Bathroom display
curl "http://172.16.232.6:52341/spotify/bathroom"

# Test on Eva display
curl "http://172.16.232.6:52341/spotify/eva"

# Test on all displays at once
curl "http://172.16.232.6:52341/spotify/all"
```

**Expected Result:**
- [ ] Returns JSON with track information
- [ ] Display shows current artist on top line
- [ ] Display shows current song on bottom line
- [ ] Text scrolls if artist/song names are long
- [ ] Purple background with animated magenta border

### 4.3 Test Error Handling

```bash
# Test when no track is playing (stop Spotify)
curl "http://172.16.232.6:52341/spotify/wc"
# Should return: "No track currently playing" (404)

# Test with missing credentials (temporarily rename spotify_credentials.py)
# Should return: "Spotify integration not enabled..." (503)
```

- [ ] Error handling works correctly
- [ ] Appropriate error messages displayed

## Step 5: Verification

### 5.1 Verify Display Features

- [ ] Two-line display works (artist on top, song on bottom)
- [ ] Text scrolling works for long names (>10 characters)
- [ ] Purple background displays correctly
- [ ] Animated magenta border works
- [ ] Display clears after duration expires

### 5.2 Verify All Displays

- [ ] WC display works correctly
- [ ] Bathroom display works correctly
- [ ] Eva display works correctly
- [ ] All displays show same track when using `/spotify/all`

### 5.3 Verify Existing Functionality Still Works

- [ ] Timer mode still works: `curl "http://172.16.232.6:52341/sigfox?target=wc&text=Test&duration=10"`
- [ ] Other presets still work: `curl "http://172.16.232.6:52341/sigfox?target=wc&mode=preset&preset_id=on_air"`
- [ ] No regressions in existing features

## Troubleshooting

### If Spotify Authentication Fails
- Check redirect URI matches exactly in Spotify dashboard and credentials file
- Verify Client ID and Client Secret are correct
- Check webserver logs: `sudo journalctl -u sigfox-bridge -f`

### If Display Doesn't Show Music Preset
- Verify `code.py` was updated on the display
- Check that `scrolling_label.mpy` is in `lib/` folder
- Check serial console for error messages
- Verify MQTT message format includes `artist` and `song` fields

### If Text Doesn't Scroll
- Verify `adafruit_display_text/scrolling_label.mpy` exists
- Check that text is actually longer than 10 characters
- Restart display after library update

### If Service Won't Start
- Check Python dependencies: `pip list | grep spotipy`
- Verify `spotify_credentials.py` syntax is correct
- Check service logs: `sudo journalctl -u sigfox-bridge -n 50`

## Quick Reference

**Webserver Commands:**
```bash
# Install spotipy
pip install spotipy

# Restart service
sudo systemctl restart sigfox-bridge

# Check service status
sudo systemctl status sigfox-bridge

# View logs
sudo journalctl -u sigfox-bridge -f
```

**Display Update Process:**
1. Connect USB-C
2. Copy `code.py` to CIRCUITPY drive
3. Verify `scrolling_label.mpy` in `lib/` folder
4. Eject and power cycle

**Test Commands:**
```bash
# Authenticate
curl "http://172.16.232.6:52341/spotify/auth"

# Display on WC
curl "http://172.16.232.6:52341/spotify/wc"

# Display on all
curl "http://172.16.232.6:52341/spotify/all"
```

