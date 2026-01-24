from flask import Flask, request, redirect
import paho.mqtt.client as mqtt
import json
import os

# Import MQTT credentials from separate file
try:
    from mqtt_credentials import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD
except ImportError:
    # Default values if credentials file is not found (for development only)
    print("Warning: mqtt_credentials.py not found. Using default values.")
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_USER = "user"
    MQTT_PASSWORD = "password"

# Import Spotify credentials
try:
    from spotify_credentials import (
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        SPOTIFY_REDIRECT_URI
    )
    SPOTIFY_ENABLED = True
except ImportError:
    print("Warning: spotify_credentials.py not found. Spotify integration disabled.")
    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    SPOTIFY_REDIRECT_URI = None
    SPOTIFY_ENABLED = False

# Initialize Spotify client if credentials are available
if SPOTIFY_ENABLED:
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-currently-playing user-read-playback-state",
            cache_path=".spotify_cache"
        ))
        print("Spotify client initialized successfully")
    except ImportError:
        print("Warning: spotipy library not installed. Install with: pip install spotipy")
        SPOTIFY_ENABLED = False
        sp = None
    except Exception as e:
        print(f"Warning: Failed to initialize Spotify client: {e}")
        SPOTIFY_ENABLED = False
        sp = None
else:
    sp = None

app = Flask(__name__)

# Valid preset IDs
VALID_PRESETS = ["on_air", "score", "breaking", "reset", "music"]

def publish_to_mqtt(topic, message_data):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        message = json.dumps(message_data)
        client.publish(topic, message)
        client.disconnect()
        return True
    except Exception as e:
        print(f"Error publishing to MQTT: {e}")
        return False

@app.route('/sigfox', methods=['POST', 'GET'])
def handle_webhook():
    try:
        # Handle both GET and POST methods for testing
        if request.method == 'GET':
            target = request.args.get('target', '')  # Which display to use
            text = request.args.get('text', '')      # What text to show
            duration = request.args.get('duration', '')
            mode = request.args.get('mode', 'timer')  # Optional: for preset mode
            preset_id = request.args.get('preset_id', '')  # Optional: for preset mode
            artist = request.args.get('artist', '')  # Optional: for music preset
            song = request.args.get('song', '')      # Optional: for music preset
        else:
            data = request.get_json(silent=True) or {}
            target = data.get('target', '')
            text = data.get('text', '')
            duration = data.get('duration', '')
            mode = data.get('mode', 'timer')
            preset_id = data.get('preset_id', '')
            artist = data.get('artist', '')  # Extract artist field for music preset
            song = data.get('song', '')      # Extract song field for music preset

        # For backward compatibility, if no mode specified or timer mode
        if mode != 'preset':
            if not target or not duration or not text:
                return 'Missing target, text, or duration', 400
                
            message_data = {
                "name": text,
                "duration": int(duration)
            }
        else:
            # Handle preset mode
            if not target or not preset_id or preset_id not in VALID_PRESETS:
                return f'Invalid target or preset_id. Valid presets: {", ".join(VALID_PRESETS)}', 400
                
            message_data = {
                "mode": "preset",
                "preset_id": preset_id,
                "name": text if text else "",  # Optional text override
                "duration": int(duration) if duration else None,  # Optional duration
            }
            # Add artist and song fields if provided (for music preset)
            if artist:
                message_data["artist"] = artist
            if song:
                message_data["song"] = song

        # Map display targets to MQTT topics
        topic_mapping = {
            'wc': 'home/displays/wc',
            'bathroom': 'home/displays/bathroom',
            'eva': 'home/displays/eva'
        }

        topic = topic_mapping.get(target.lower())
        if not topic:
            return f'Invalid target display: {target}', 400

        if publish_to_mqtt(topic, message_data):
            return 'OK', 200
        else:
            return 'Failed to publish to MQTT', 500

    except Exception as e:
        print(f"Error processing request: {e}")
        return str(e), 500

# Spotify integration endpoints
@app.route('/spotify/<target>', methods=['GET'])
def spotify_current_track(target):
    """Display current Spotify track on specified display"""
    if not SPOTIFY_ENABLED or not sp:
        return 'Spotify integration not enabled. Check spotify_credentials.py and spotipy installation.', 503
    
    try:
        # Get current track from Spotify
        current_track = sp.current_user_playing_track()
        
        if not current_track or not current_track.get('is_playing', False):
            return 'No track currently playing', 404
            
        # Extract track information
        item = current_track.get('item', {})
        if not item:
            return 'No track information available', 404
            
        artist = item.get('artists', [{}])[0].get('name', 'Unknown Artist')
        song = item.get('name', 'Unknown Song')
        album = item.get('album', {}).get('name', 'Unknown Album')
        
        # Create message for preset mode with artist and song separately
        # Display will handle scrolling for long text
        message_data = {
            "mode": "preset",
            "preset_id": "music",
            "artist": artist,
            "song": song,
            "duration": 30  # Display for 30 seconds
        }
        
        # Map display targets to MQTT topics
        topic_mapping = {
            'wc': 'home/displays/wc',
            'bathroom': 'home/displays/bathroom',
            'eva': 'home/displays/eva'
        }
        
        topic = topic_mapping.get(target.lower())
        if not topic:
            return f'Invalid target display: {target}', 400
            
        if publish_to_mqtt(topic, message_data):
            return json.dumps({
                "status": "success",
                "track": {
                    "artist": artist,
                    "song": song,
                    "album": album
                }
            }), 200
        else:
            return 'Failed to publish to MQTT', 500
            
    except Exception as e:
        print(f"Spotify error: {e}")
        return f'Error: {str(e)}', 500

@app.route('/spotify/auth', methods=['GET'])
def spotify_auth():
    """Initiate Spotify OAuth flow"""
    if not SPOTIFY_ENABLED or not sp:
        return 'Spotify integration not enabled. Check spotify_credentials.py and spotipy installation.', 503
    
    try:
        auth_url = sp.auth_manager.get_authorize_url()
        return redirect(auth_url)
    except Exception as e:
        return f'Authentication error: {str(e)}', 500

@app.route('/spotify/callback', methods=['GET'])
def spotify_callback():
    """Handle Spotify OAuth callback"""
    if not SPOTIFY_ENABLED or not sp:
        return 'Spotify integration not enabled. Check spotify_credentials.py and spotipy installation.', 503
    
    try:
        code = request.args.get('code')
        if not code:
            return 'No authorization code provided', 400
            
        token_info = sp.auth_manager.get_access_token(code)
        return 'Spotify authentication successful! You can now use /spotify/<target> endpoints.', 200
    except Exception as e:
        return f'Authentication failed: {str(e)}', 500

@app.route('/spotify/all', methods=['GET'])
def spotify_all_displays():
    """Display current track on all displays"""
    if not SPOTIFY_ENABLED or not sp:
        return 'Spotify integration not enabled. Check spotify_credentials.py and spotipy installation.', 503
    
    try:
        # Get current track from Spotify
        current_track = sp.current_user_playing_track()
        
        if not current_track or not current_track.get('is_playing', False):
            return 'No track currently playing', 404
            
        # Extract track information
        item = current_track.get('item', {})
        if not item:
            return 'No track information available', 404
            
        artist = item.get('artists', [{}])[0].get('name', 'Unknown Artist')
        song = item.get('name', 'Unknown Song')
        
        # Create message for preset mode with artist and song separately
        # Display will handle scrolling for long text
        message_data = {
            "mode": "preset",
            "preset_id": "music",
            "artist": artist,
            "song": song,
            "duration": 30
        }
        
        # Map display targets to MQTT topics
        topic_mapping = {
            'wc': 'home/displays/wc',
            'bathroom': 'home/displays/bathroom',
            'eva': 'home/displays/eva'
        }
        
        results = {}
        for target in ['wc', 'bathroom', 'eva']:
            topic = topic_mapping[target]
            success = publish_to_mqtt(topic, message_data)
            results[target] = "success" if success else "failed"
        
        return json.dumps({
            "status": "success",
            "track": {
                "artist": artist,
                "song": song
            },
            "displays": results
        }), 200
        
    except Exception as e:
        print(f"Spotify error: {e}")
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=52341) 