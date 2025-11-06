# Spotify Integration for HomeMatrixBoard

## Overview
This document outlines the implementation of Spotify integration to display currently playing tracks on the HomeMatrixBoard LED matrix displays. The integration allows real-time display of artist and song information from Spotify across any or all configured displays.

## Architecture

### System Flow
```
Spotify Web API → Flask Webhook → MQTT Broker → MatrixPortal Displays
```

### Components
1. **Spotify Web API**: Provides real-time track information
2. **Flask Webhook Server**: Extends existing `app.py` with Spotify endpoints
3. **MQTT Broker**: Existing infrastructure for message routing
4. **MatrixPortal Displays**: Existing display hardware (WC, Bathroom, Eva)

## Prerequisites

### 1. Spotify Developer Account
- Register at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Create a new app to get Client ID and Client Secret
- **Set redirect URI**: `http://172.16.232.6:52341/spotify/callback` (or your server URL)
  - This must match exactly in both Spotify dashboard and `spotify_credentials.py`

### 2. Required Permissions
- `user-read-currently-playing`: Read currently playing track
- `user-read-playback-state`: Read playback state (optional, for enhanced features)

### 3. Python Dependencies

**On Webserver (172.16.232.6):**
```bash
# SSH into webserver
ssh user@172.16.232.6

# Navigate to project directory
cd ~/sigfox_mqtt_bridge  # or your project directory

# Activate virtual environment (if using one)
source venv/bin/activate

# Install spotipy
pip install spotipy

# Restart Flask service
sudo systemctl restart sigfox-bridge
```

**Note:** If not using a virtual environment, install globally:
```bash
sudo pip3 install spotipy
```

### 4. Display Firmware Updates

**Required on all three displays (WC, Bathroom, Eva):**

1. **Update code.py files:**
   - Copy updated `displays/wc/code.py` to WC display
   - Copy updated `displays/bathroom/code.py` to Bathroom display
   - Copy updated `displays/eva/code.py` to Eva display

2. **Verify library availability:**
   - Ensure `adafruit_display_text/scrolling_label.mpy` is in the `lib/` folder
   - This library is required for automatic text scrolling

3. **Update process:**
   - Connect each MatrixPortal M4 via USB-C
   - Copy the updated `code.py` file to the CIRCUITPY drive
   - Safely eject and power cycle the display
   - See `display_setup.md` for detailed update instructions

## Implementation Choice

**Option 2: Music Preset Mode** has been implemented with enhanced features:
- Two-line display (artist on top, song on bottom)
- Automatic text scrolling for long text (>10 characters per line)
- Custom purple/magenta styling
- Separate `artist` and `song` fields (not combined `name` field)

**Message Format:**
```json
{
    "mode": "preset",
    "preset_id": "music",
    "artist": "The Beatles",
    "song": "Hey Jude",
    "duration": 30
}
```

**Features:**
- Two-line display: Artist on top line (y=8), Song on bottom line (y=20)
- Automatic scrolling: Text longer than 10 characters scrolls horizontally
- Custom styling: Purple background (0x800080), white text, animated magenta border
- Error handling: Shows "NO TRACK DATA" if artist/song not provided
- No truncation: Full text displayed with scrolling instead of cutting off

## Implementation Status

**✅ IMPLEMENTED: Music Preset Mode with Two-Line Display**

The integration has been fully implemented using Option 2 (Music Preset Mode) with enhanced features:

### Implemented Features

1. **Two-Line Display**
   - Artist name on top line (y=8)
   - Song name on bottom line (y=20)
   - Both lines support automatic scrolling

2. **Automatic Text Scrolling**
   - Text longer than 10 characters automatically scrolls horizontally
   - Uses `ScrollingLabel` from `adafruit_display_text` library
   - No text truncation - full artist and song names displayed

3. **Custom Styling**
   - Purple background (0x800080)
   - White text (0xFFFFFF)
   - Animated magenta border (0xFF00FF)
   - Error message: "NO TRACK DATA" (when no track info available)

4. **Message Format**
   ```json
   {
       "mode": "preset",
       "preset_id": "music",
       "artist": "The Beatles",
       "song": "Hey Jude",
       "duration": 30
   }
   ```

### Components Updated

1. **Webserver (`app.py`)**
   - ✅ Added Spotify integration endpoints
   - ✅ Sends `artist` and `song` separately (no truncation)
   - ✅ Added to `VALID_PRESETS` list
   - ✅ OAuth authentication flow implemented

2. **Display Firmware (all three displays)**
   - ✅ Added `PresetManager` class (bathroom and eva)
   - ✅ Added "music" preset configuration
   - ✅ Implemented two-line display handling
   - ✅ Added scrolling text support
   - ✅ Updated message processing for `artist`/`song` fields

3. **Configuration Files**
   - ✅ Created `spotify_credentials.py` template
   - ✅ Graceful handling when credentials missing

### Implementation Details

**Webserver (`app.py`):**
- Spotify client initialized at startup (if credentials available)
- Endpoints send `artist` and `song` fields separately in MQTT message
- No text truncation - full names sent to displays
- Graceful degradation: Returns 503 if credentials missing (doesn't crash)

**Display Firmware:**
- Music preset uses special two-line mode when `preset_id == "music"`
- Extracts `artist` and `song` from message (not `name` field)
- Automatically creates ScrollingLabel for text >10 characters
- Falls back to "Unknown Artist"/"Unknown Song" if fields missing
- Shows "NO TRACK DATA" if both artist and song are missing

## Installation Requirements by Component

### 1. Webserver (172.16.232.6)

**Python Dependencies:**
```bash
# SSH into webserver
ssh user@172.16.232.6

# Navigate to project directory
cd ~/sigfox_mqtt_bridge  # or your project directory

# Activate virtual environment (if using one)
source venv/bin/activate

# Install spotipy library
pip install spotipy

# Restart Flask service
sudo systemctl restart sigfox-bridge
```

**Configuration Files:**
- Create `spotify_credentials.py` in project root:
  ```python
  SPOTIFY_CLIENT_ID = "your_client_id_here"
  SPOTIFY_CLIENT_SECRET = "your_client_secret_here"
  SPOTIFY_REDIRECT_URI = "http://172.16.232.6:52341/spotify/callback"
  ```

**Files Updated:**
- ✅ `app.py` - Added Spotify endpoints and integration

### 2. Display Firmware (WC, Bathroom, Eva)

**Required Updates:**
1. **Update code.py files:**
   - Copy `displays/wc/code.py` → WC display CIRCUITPY drive
   - Copy `displays/bathroom/code.py` → Bathroom display CIRCUITPY drive
   - Copy `displays/eva/code.py` → Eva display CIRCUITPY drive

2. **Verify Library:**
   - Ensure `lib/adafruit_display_text/scrolling_label.mpy` exists
   - This is required for automatic text scrolling

3. **Update Process:**
   ```bash
   # For each display:
   # 1. Connect MatrixPortal M4 via USB-C
   # 2. Mount CIRCUITPY drive
   # 3. Copy updated code.py file
   # 4. Safely eject
   # 5. Power cycle display
   ```

**Files Updated:**
- ✅ `displays/wc/code.py` - Added PresetManager, music preset, scrolling
- ✅ `displays/bathroom/code.py` - Added PresetManager, music preset, scrolling
- ✅ `displays/eva/code.py` - Added PresetManager, music preset, scrolling

### 3. MQTT Broker

**No changes required** - Uses existing MQTT infrastructure

### 4. Configuration Files

**New Files:**
- ✅ `spotify_credentials.py` - Spotify API credentials (not in git)
- ✅ `.spotify_cache` - OAuth token cache (auto-generated, not in git)

## Usage Examples

### 1. Initial Authentication
```bash
# Start OAuth flow (redirects to Spotify login)
curl "http://172.16.232.6:52341/spotify/auth"

# After authentication, callback completes automatically
# Token is cached in .spotify_cache file
```

### 2. Display Current Track on Specific Display
```bash
# Display on WC
curl "http://172.16.232.6:52341/spotify/wc"

# Display on Bathroom
curl "http://172.16.232.6:52341/spotify/bathroom"

# Display on Eva
curl "http://172.16.232.6:52341/spotify/eva"
```

### 3. Display on All Displays
```bash
curl "http://172.16.232.6:52341/spotify/all"
```

**Response Format:**
```json
{
    "status": "success",
    "track": {
        "artist": "The Beatles",
        "song": "Hey Jude",
        "album": "The Beatles 1967-1970"
    },
    "displays": {
        "wc": "success",
        "bathroom": "success",
        "eva": "success"
    }
}
```

## Configuration

### Spotify Credentials File

Create `spotify_credentials.py` in the webserver project root:

```python
# Spotify API Credentials
# 
# To get these credentials:
# 1. Go to https://developer.spotify.com/dashboard
# 2. Create a new app
# 3. Copy the Client ID and Client Secret
# 4. Add redirect URI: http://your-server:52341/spotify/callback
#
# IMPORTANT: Add this file to .gitignore to keep credentials secure!

SPOTIFY_CLIENT_ID = "your_spotify_client_id_here"
SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret_here"
SPOTIFY_REDIRECT_URI = "http://172.16.232.6:52341/spotify/callback"  # Update with your server URL
```

### Display Settings (Firmware)

The music preset is configured in each display's `code.py`:

```python
"music": {
    "background": 0x800080,      # Purple background
    "text": "NO TRACK DATA",      # Error message when no track info
    "text_color": 0xFFFFFF,       # White text
    "border_mode": "animated",    # Animated border
    "border_color": 0xFF00FF,     # Magenta border
    "show_radio": False           # No radio symbol
}
```

**Display Behavior:**
- Artist displayed on top line (y=8)
- Song displayed on bottom line (y=20)
- Text scrolls automatically if >10 characters per line
- Default duration: 30 seconds (configurable via message)

## Testing

### 1. Authentication Test
```bash
# Start OAuth flow (redirects to Spotify login)
curl "http://172.16.232.6:52341/spotify/auth"

# After completing OAuth in browser, test display
curl "http://172.16.232.6:52341/spotify/wc"
```

### 2. Display Test
```bash
# Test Spotify integration (requires authentication first)
curl "http://172.16.232.6:52341/spotify/wc"

# Test music preset directly via MQTT
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/wc" \
    -m '{"mode": "preset", "preset_id": "music", "artist": "Test Artist", "song": "Test Song", "duration": 30}'
```

### 3. Verify Display Updates
```bash
# Check that displays show:
# - Top line: Artist name (scrolling if >10 chars)
# - Bottom line: Song name (scrolling if >10 chars)
# - Purple background with animated magenta border
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
- **Problem**: "Invalid client" or "Invalid redirect URI"
- **Solution**: Verify Client ID, Client Secret, and redirect URI in Spotify app settings

#### 2. No Track Playing
- **Problem**: API returns "No track currently playing"
- **Solution**: Ensure Spotify is actively playing music

#### 3. Display Not Updating
- **Problem**: MQTT message sent but display doesn't change
- **Solution**: Check MQTT broker connection and topic subscription

#### 4. Display Not Showing Music Preset
- **Problem**: Display shows "NO TRACK DATA" or doesn't update
- **Solution**: 
  - Verify display firmware has been updated with music preset support
  - Check that `scrolling_label.mpy` is in the display's `lib/` folder
  - Verify MQTT message includes both `artist` and `song` fields
  - Check serial console for error messages

#### 5. Text Not Scrolling
- **Problem**: Long text is cut off instead of scrolling
- **Solution**: 
  - Verify `adafruit_display_text/scrolling_label.mpy` is present
  - Check that text is longer than 10 characters (scrolling threshold)
  - Restart display after library update

### Debug Commands
```bash
# Check Spotify integration status
curl "http://172.16.232.6:52341/spotify/wc"
# Returns 503 if credentials missing, 404 if no track playing, 200 if successful

# Test MQTT connectivity
mosquitto_pub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "test/topic" -m "test message"

# Monitor MQTT messages
mosquitto_sub -h 172.16.234.55 -u sigfoxwebhookhost -P <password> \
    -t "home/displays/#"

# Check webserver logs
sudo journalctl -u sigfox-bridge -f
```

## Security Considerations

### 1. Token Management
- Store Spotify tokens securely
- Implement token refresh logic
- Use environment variables for credentials

### 2. API Rate Limiting
- Implement caching to avoid excessive API calls
- Use appropriate polling intervals
- Handle rate limit responses gracefully

### 3. Network Security
- Use HTTPS for OAuth redirects
- Secure MQTT broker with authentication
- Consider VPN for remote access

## Future Enhancements

### 1. Album Art Display
- Download and display album artwork
- Requires additional storage and processing

### 2. Playback Controls
- Display play/pause status
- Show progress bar
- Volume indicators

### 3. Queue Information
- Display next song in queue
- Show playlist information
- Queue management

### 4. Multiple User Support
- Support multiple Spotify accounts
- User-specific display preferences
- Account switching

### 5. Integration with Other Services
- Last.fm scrobbling
- Music recognition services
- Social sharing features

## Implementation Summary

### What Was Implemented

✅ **Music Preset Mode with Enhanced Features:**
- Two-line display (artist/song on separate lines)
- Automatic text scrolling for long text
- Custom purple/magenta styling
- Separate `artist` and `song` fields (no truncation)
- Error handling with "NO TRACK DATA" message

✅ **Webserver Integration:**
- `/spotify/<target>` - Display track on specific display
- `/spotify/all` - Display track on all displays
- `/spotify/auth` - OAuth authentication
- `/spotify/callback` - OAuth callback handler

✅ **Display Firmware Updates:**
- All three displays (WC, Bathroom, Eva) updated
- PresetManager class added to bathroom and eva
- Music preset configuration added
- Scrolling text support implemented

### Installation Checklist

**Webserver:**
- [ ] Install `spotipy`: `pip install spotipy`
- [ ] Create `spotify_credentials.py` with credentials
- [ ] Restart Flask service: `sudo systemctl restart sigfox-bridge`
- [ ] Authenticate via `/spotify/auth` endpoint

**Displays (WC, Bathroom, Eva):**
- [ ] Update `code.py` file on each display
- [ ] Verify `scrolling_label.mpy` in `lib/` folder
- [ ] Power cycle each display after update
- [ ] Test with MQTT message containing `artist` and `song` fields

**MQTT Broker:**
- [ ] No changes required (uses existing infrastructure)

## Conclusion

The Spotify integration has been fully implemented using Music Preset Mode with two-line display and automatic text scrolling. The integration leverages your existing MQTT infrastructure and display system, providing a seamless way to display real-time music information across all configured displays.

The implementation provides:
- Full artist and song names (no truncation)
- Automatic scrolling for long text
- Custom visual styling
- Error handling for missing data
- Support for all three displays (WC, Bathroom, Eva)


