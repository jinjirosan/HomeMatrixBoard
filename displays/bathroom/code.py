# pyright: ignore[reportShadowedImports]
import board
import time
import json
import terminalio
import displayio
import os
import supervisor
import microcontroller
import watchdog
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_display_text.scrolling_label import ScrollingLabel
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_esp32spi import adafruit_esp32spi_socketpool

print("\n" * 2)
print("=" * 40)
print("MatrixPortal M4 Startup")
print("=" * 40)

# Configuration variables
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
TEST_FILE = "test_trigger.json"
DONE_DISPLAY_TIME = 10  # How long to show "DONE" message
FINAL_COUNTDOWN = 10    # When to start running ants animation
STOPWATCH_TEXT = "STOPWATCH"  # Text to display during stopwatch mode
RECONNECT_DELAY = 5     # Seconds to wait between reconnection attempts
MAX_FAILED_PINGS = 3    # Maximum failed ping attempts before reconnecting

# Colors
RED = 0xFF0000
WHITE = 0xFFFFFF
BLACK = 0x000000

# Enable serial output for debugging
try:
    supervisor.runtime.serial_connected = True
except:
    pass

# Setup watchdog
watchdog.timeout = 30  # 30 second timeout
watchdog.mode = watchdog.WatchDogMode.RESET
watchdog.feed()

# Get wifi details from secrets.py
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

class DisplayText:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.title_label = None
        self.timer_label = None
        self.text_group = displayio.Group()
        self.last_lengths = {}  # Cache for text lengths
        self.last_positions = {}  # Cache for calculated positions
        # Manual scrolling state
        self.scrolling_labels = {}  # Track which labels are scrolling
        self.scroll_speed = 0.05  # Seconds per pixel movement
        self.scroll_pause = 1.0  # Pause at start/end before scrolling
        self.setup_text()
        self.matrixportal.display.root_group.append(self.text_group)
        
    def setup_text(self):
        """Initialize and create text labels"""
        # Create title label with empty text
        self.title_label = Label(
            terminalio.FONT,
            text="",  # Empty text instead of "READY"
            color=WHITE,
            x=0,  # Start at x=0 since there's no text to center
            y=8
        )
        
        # Create timer label
        self.timer_label = Label(
            terminalio.FONT,
            text="",  # Empty text instead of "--:--"
            color=WHITE,
            x=0,  # Start at x=0 since there's no text to center
            y=20
        )
        
        # Add labels to group
        self.text_group.append(self.title_label)
        self.text_group.append(self.timer_label)
    
    def center_text_position(self, text):
        """Calculate x position to center text"""
        # Use cached position if text length hasn't changed
        text_len = len(text)
        if text_len in self.last_positions:
            return self.last_positions[text_len]
            
        # Calculate new position
        text_width = text_len * 6
        center_pos = (DISPLAY_WIDTH - text_width) // 2
        print(f"Calculating new position for text: '{text}' width={text_width} pos={center_pos}")
        
        # Cache the result
        self.last_positions[text_len] = center_pos
        return center_pos
    
    def update_text(self, text, label, y_position):
        """Update text content and position"""
        # Only update position if text length changed
        if len(text) != len(label.text):
            label.x = self.center_text_position(text)
            print(f"Text length changed, new position: x={label.x} y={label.y}")
        label.text = text
    
    def update_text_with_scrolling(self, text, label, y_position, max_chars=10):
        """Update text with manual scrolling if it's too long"""
        text_width = len(text) * 6
        max_width = max_chars * 6
        
        # Remove old scrolling label if it exists
        if hasattr(label, '_scrolling_label'):
            self.text_group.remove(label._scrolling_label)
            delattr(label, '_scrolling_label')
        
        # Stop scrolling for this label if it was scrolling
        if label in self.scrolling_labels:
            del self.scrolling_labels[label]
        
        if text_width > max_width:
            # Use manual scrolling for long text
            # Start text so right edge is at right edge of display (text will be partially visible)
            # This ensures text is visible immediately, then scrolls left
            label.text = text
            # Calculate start position: right edge of text at right edge of display
            # label.x is the left edge, so: x = DISPLAY_WIDTH - text_width
            start_x = DISPLAY_WIDTH - text_width
            label.x = start_x
            label.y = y_position
            
            # Track scrolling state
            self.scrolling_labels[label] = {
                "text": text,
                "width": text_width,
                "start_x": start_x,  # Start position (right edge of text at right edge of display)
                "end_x": -text_width,  # End position (off-screen to the left)
                "last_update": time.monotonic(),
                "paused": True,  # Pause briefly at start so user can see the end of the text
                "pause_start": time.monotonic()
            }
        else:
            # Use regular label for short text (centered)
            self.update_text(text, label, y_position)
    
    def update_scrolling(self, current_time):
        """Update manual scrolling animation"""
        for label, scroll_info in list(self.scrolling_labels.items()):
            # Handle pause at start
            if scroll_info["paused"]:
                if (current_time - scroll_info["pause_start"]) < self.scroll_pause:
                    continue  # Still pausing
                else:
                    scroll_info["paused"] = False
                    scroll_info["last_update"] = current_time
            
            # Check if we need to update position
            time_since_update = current_time - scroll_info["last_update"]
            if time_since_update >= self.scroll_speed:
                # Move label left by 1 pixel
                label.x -= 1
                scroll_info["last_update"] = current_time
                
                # Check if we've scrolled off the left edge
                if label.x <= scroll_info["end_x"]:
                    # Reset to start position and pause
                    label.x = scroll_info["start_x"]
                    scroll_info["paused"] = True
                    scroll_info["pause_start"] = current_time

class BorderManager:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.animation_step = 0
        self.current_mode = "none"  # none, solid, animated, blinking
        self.last_animation_update = time.monotonic()
        self.setup_border()
        
    def setup_border(self):
        """Initialize border display elements"""
        self.border_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 2)
        self.border_palette = displayio.Palette(2)
        self.border_palette[0] = BLACK
        self.border_palette[1] = RED
        
        self.border_grid = displayio.TileGrid(
            self.border_bitmap,
            pixel_shader=self.border_palette
        )
        
        self.border_group = displayio.Group()
        self.border_group.append(self.border_grid)
        
    def draw_pixel(self, x, y, on=True):
        """Draw a single border pixel"""
        if 0 <= x < DISPLAY_WIDTH and 0 <= y < DISPLAY_HEIGHT:
            self.border_bitmap[x, y] = 1 if on else 0
            
    def clear_pixels(self):
        """Clear all border pixels without changing mode"""
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                self.border_bitmap[i, j] = 0
                
    def clear_border(self):
        """Clear border and reset mode"""
        self.current_mode = "none"
        self.clear_pixels()
                
    def set_dashed(self):
        """Set dashed border"""
        self.clear_pixels()
        for x in range(DISPLAY_WIDTH):
            if x % 2 == 0:  # Only draw every other pixel for dashed effect
                self.draw_pixel(x, 0)
                self.draw_pixel(x, DISPLAY_HEIGHT-1)
        for y in range(DISPLAY_HEIGHT):
            if y % 2 == 0:  # Only draw every other pixel for dashed effect
                self.draw_pixel(0, y)
                self.draw_pixel(DISPLAY_WIDTH-1, y)

    def set_solid_border(self):
        """Set solid continuous border"""
        self.current_mode = "solid"
        self.clear_pixels()
        # Draw continuous lines for all border pixels
        for x in range(DISPLAY_WIDTH):
            self.draw_pixel(x, 0)  # Top border
            self.draw_pixel(x, DISPLAY_HEIGHT-1)  # Bottom border
        for y in range(DISPLAY_HEIGHT):
            self.draw_pixel(0, y)  # Left border
            self.draw_pixel(DISPLAY_WIDTH-1, y)  # Right border
            
    def set_animated(self):
        """Switch to animated border mode"""
        self.current_mode = "animated"
        self.animation_step = 0
            
    def set_blinking(self):
        """Switch to blinking border mode"""
        self.current_mode = "blinking"
        self.animation_step = 0

    def update_animation(self, current_time):
        """Update border animation based on current mode"""
        if self.current_mode == "none" or self.current_mode == "solid":
            return
            
        # Only update animations every 0.2 seconds for animated, 0.5 for blinking
        animation_interval = 0.2 if self.current_mode == "animated" else 0.5
        if (current_time - self.last_animation_update) < animation_interval:
            return
            
        self.last_animation_update = current_time
        
        if self.current_mode == "animated":
            self.animation_step = (self.animation_step + 1) % 2
            self.clear_pixels()  # Don't change mode when clearing for animation
            for i in range(DISPLAY_WIDTH + DISPLAY_HEIGHT * 2):
                if (i + self.animation_step) % 2 == 0:
                    if i < DISPLAY_WIDTH:
                        self.draw_pixel(i, 0)
                        self.draw_pixel(i, DISPLAY_HEIGHT-1)
                    else:
                        pos = i - DISPLAY_WIDTH
                        if pos < DISPLAY_HEIGHT:
                            self.draw_pixel(DISPLAY_WIDTH-1, pos)
                        else:
                            self.draw_pixel(0, pos - DISPLAY_HEIGHT)
        elif self.current_mode == "blinking":
            self.animation_step = (self.animation_step + 1) % 2
            if self.animation_step == 0:
                self.set_dashed()
            else:
                self.clear_pixels()  # Don't change mode when clearing for animation

class TimerManager:
    def __init__(self):
        self.current_countdown = None
        self.stopwatch_start = None
        self.done_start = None
        self.last_second = None
        
    def start_countdown(self, name, duration):
        """Start a new countdown"""
        if not isinstance(duration, (int, float)) or duration <= 0:
            return False
            
        self.current_countdown = {
            "name": name,
            "duration": int(duration),
            "remaining": int(duration)
        }
        self.last_second = time.monotonic()
        self.stopwatch_start = None
        self.done_start = None
        return True
        
    def update_countdown(self, current_time):
        """Update countdown state"""
        if not self.current_countdown:
            return None
            
        # Only update when a full second has passed
        if current_time - self.last_second >= 1.0:
            # Decrement remaining time
            self.current_countdown["remaining"] -= 1
            self.last_second = current_time
            
            if self.current_countdown["remaining"] > 0:
                return {
                    "type": "countdown",
                    "name": self.current_countdown["name"],
                    "minutes": self.current_countdown["remaining"] // 60,
                    "seconds": self.current_countdown["remaining"] % 60,
                    "remaining": self.current_countdown["remaining"],
                    "update": True
                }
            else:
                if not self.done_start:  # Only set done_start once when first entering DONE state
                    self.done_start = current_time
                    self.last_second = current_time
                    return {"type": "done", "first": True}
                elif current_time - self.done_start >= DONE_DISPLAY_TIME:
                    self.stopwatch_start = current_time
                    self.last_second = current_time
                    self.current_countdown = None
                    self.done_start = None
                    return {"type": "stopwatch_start"}
                return {"type": "done", "first": False}
                
        elif self.current_countdown["remaining"] > 0:
            return {
                "type": "countdown",
                "name": self.current_countdown["name"],
                "minutes": self.current_countdown["remaining"] // 60,
                "seconds": self.current_countdown["remaining"] % 60,
                "remaining": self.current_countdown["remaining"],
                "update": False
            }
            
        return {"type": "done", "first": False}
            
    def update_stopwatch(self, current_time):
        """Update stopwatch state"""
        if self.stopwatch_start is None:
            return None
            
        elapsed_time = current_time - self.stopwatch_start
        elapsed_seconds = int(elapsed_time)
        
        # Only trigger update when a full second has passed
        if current_time - self.last_second >= 1.0:
            self.last_second = current_time
            return {
                "type": "stopwatch",
                "minutes": elapsed_seconds // 60,
                "seconds": elapsed_seconds % 60,
                "update": True
            }
            
        return {
            "type": "stopwatch",
            "minutes": elapsed_seconds // 60,
            "seconds": elapsed_seconds % 60,
            "update": False
        }

class PresetManager:
    """Manages preset display configurations"""
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.current_preset = None
        self.preset_start = None
        self.preset_duration = None
        
        # Define preset configurations
        self.presets = {
            "on_air": {
                "background": BLACK,
                "text": "ON AIR",
                "text_color": RED,
                "border_mode": "solid",
                "border_color": WHITE,
                "show_radio": False
            },
            "score": {
                "background": 0x00FF00,  # Green
                "text": "SCORE",
                "text_color": 0xFFFF00,  # Yellow
                "border_mode": "animated",
                "border_color": 0xFFFF00,
                "show_radio": False
            },
            "breaking": {
                "background": 0x0000FF,  # Blue
                "text": "BREAKING",
                "text_color": WHITE,
                "border_mode": "blinking",
                "border_color": RED,
                "show_radio": False
            },
            "reset": {
                "background": BLACK,
                "text": "",
                "text_color": WHITE,
                "border_mode": "none",
                "border_color": RED,
                "show_radio": False
            },
            "music": {
                "background": 0x800080,  # Purple background
                "text": "NO TRACK DATA",  # Error message when no track info
                "text_color": 0xFFFFFF,  # White text
                "border_mode": "animated",
                "border_color": 0xFF00FF,  # Magenta border
                "show_radio": False
            }
        }
        
    def start_preset(self, preset_id, name=None, duration=None):
        """Start displaying a preset configuration"""
        if preset_id not in self.presets:
            print(f"Unknown preset: {preset_id}")
            return False
            
        self.current_preset = preset_id
        self.preset_start = time.monotonic()
        self.preset_duration = duration
        return True
        
    def update_preset(self, current_time):
        """Update preset state"""
        if not self.current_preset:
            return None
            
        # Check if preset should expire
        if self.preset_duration and (current_time - self.preset_start >= self.preset_duration):
            preset_id = self.current_preset
            self.current_preset = None
            self.preset_start = None
            self.preset_duration = None
            return {"type": "preset_end", "preset": preset_id}
            
        return {
            "type": "preset",
            "preset": self.current_preset,
            "config": self.presets[self.current_preset]
        }
        
    def clear_preset(self):
        """Clear current preset"""
        self.current_preset = None
        self.preset_start = None
        self.preset_duration = None

class CountdownDisplay:
    def __init__(self):
        print("Initializing display...")
        try:
            self.matrixportal = MatrixPortal(
                status_neopixel=board.NEOPIXEL,
                debug=True
            )
            print("MatrixPortal initialized")
            
            # Create main display group
            self.main_group = displayio.Group()
            self.matrixportal.display.root_group = self.main_group
            
            # Set background
            self.matrixportal.set_background(BLACK)
            
            # Initialize border first (bottom layer)
            self.border_manager = BorderManager(self.matrixportal)
            self.main_group.append(self.border_manager.border_group)
            
            # Initialize text second (top layer)
            self.text_manager = DisplayText(self.matrixportal)
            
            # Initialize preset manager
            self.preset_manager = PresetManager(self.matrixportal)
            
            # Initialize timer
            self.timer_manager = TimerManager()
            
            # Set initial state - start with clear border instead of dashed
            self.border_manager.clear_border()
            self.last_check = time.monotonic()
            
            # Network state tracking
            self.last_mqtt_ping = time.monotonic()
            self.failed_pings = 0
            self.mqtt_client = None
            self.network_pool = None
            
            # Initialize MQTT
            self.setup_mqtt()
            
            print("Display setup complete")
            
        except Exception as e:
            print("Error during initialization:", str(e))
            raise

    def check_wifi_connection(self):
        """Check if WiFi is connected and reconnect if needed"""
        try:
            if not self.matrixportal.network.is_connected:
                print("WiFi disconnected, attempting to reconnect...")
                self.matrixportal.network.connect()
                if self.matrixportal.network.is_connected:
                    print("WiFi reconnected successfully")
                    return True
                else:
                    print("WiFi reconnection failed")
                    return False
            return True
        except Exception as e:
            print("Error checking WiFi:", str(e))
            return False

    def check_mqtt_connection(self):
        """Check MQTT connection and reconnect if needed"""
        try:
            # Check if it's time to ping
            current_time = time.monotonic()
            if current_time - self.last_mqtt_ping >= 60:  # Ping every 60 seconds
                self.last_mqtt_ping = current_time
                try:
                    self.mqtt_client.ping()
                    self.failed_pings = 0  # Reset counter on successful ping
                except Exception as e:
                    print("MQTT ping failed:", str(e))
                    self.failed_pings += 1
                    
                    if self.failed_pings >= MAX_FAILED_PINGS:
                        print("Too many failed pings, reconnecting MQTT...")
                        self.setup_mqtt()
                        self.failed_pings = 0
            return True
        except Exception as e:
            print("Error checking MQTT:", str(e))
            return False

    def setup_mqtt(self):
        """Setup MQTT client with reconnection logic"""
        try:
            # First ensure WiFi is connected
            if not self.check_wifi_connection():
                print("Cannot setup MQTT - WiFi not connected")
                time.sleep(RECONNECT_DELAY)
                return False

            print("\nConnecting to WiFi...")
            self.matrixportal.network.connect()
            print("Connected to WiFi!")
            print("IP Address:", self.matrixportal.network.ip_address)

            # Create the socketpool
            self.network_pool = adafruit_esp32spi_socketpool.SocketPool(self.matrixportal.network._wifi.esp)

            # Set up MQTT client
            print("Connecting to MQTT broker...")
            self.mqtt_client = MQTT.MQTT(
                broker=secrets['mqtt_broker'],
                port=secrets['mqtt_port'],
                username=secrets['mqtt_user'],
                password=secrets['mqtt_password'],
                socket_pool=self.network_pool,
                is_ssl=False,
                keep_alive=60  # Send ping every 60 seconds
            )

            # Setup the callback methods
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.on_subscribe = self.on_subscribe

            print(f"Attempting to connect to {secrets['mqtt_broker']} as {secrets['mqtt_user']}")
            self.mqtt_client.connect()
            self.last_mqtt_ping = time.monotonic()
            return True

        except Exception as e:
            print("Error setting up MQTT:", str(e))
            time.sleep(RECONNECT_DELAY)
            return False

    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        print("Connected to MQTT broker!")
        print(f"Subscribing to {secrets['mqtt_topic']}...")
        try:
            client.subscribe(secrets['mqtt_topic'], qos=0)
            print("Successfully subscribed!")
        except Exception as e:
            print(f"Error subscribing: {e}")

    def on_message(self, client, topic, message):
        """Handle incoming MQTT messages"""
        print("\n=== New Message Received ===")
        print(f"Topic: {topic}")
        print(f"Message: {message}")
        
        try:
            # Parse the JSON message
            data = json.loads(message)
            
            # Clear any existing displays
            self.timer_manager.current_countdown = None
            self.timer_manager.stopwatch_start = None
            self.timer_manager.done_start = None
            self.preset_manager.clear_preset()
            
            # Reset display to default state
            self.text_manager.update_text("", self.text_manager.title_label, 8)
            self.text_manager.update_text("", self.text_manager.timer_label, 20)
            self.border_manager.clear_border()
            
            # Check message mode (defaults to "timer" for backward compatibility)
            mode = data.get("mode", "timer")
            
            if mode == "timer":
                # Set default colors for timer mode
                self.matrixportal.set_background(BLACK)
                self.text_manager.title_label.color = WHITE
                self.text_manager.timer_label.color = WHITE
                self.border_manager.border_palette[1] = RED  # Reset border to default red
                
                if "name" in data and "duration" in data:
                    if self.timer_manager.start_countdown(data["name"], data["duration"]):
                        self.text_manager.update_text(data["name"], self.text_manager.title_label, 8)
                        self.border_manager.set_solid_border()
                        print("Countdown started successfully")
            elif mode == "preset":
                if "preset_id" in data:
                    name = data.get("name", "")  # Optional name override
                    duration = data.get("duration")  # Optional duration
                    artist = data.get("artist", "")  # Optional artist (for music preset)
                    song = data.get("song", "")  # Optional song (for music preset)
                    
                    if self.preset_manager.start_preset(data["preset_id"], name, duration):
                        preset_config = self.preset_manager.presets[data["preset_id"]]
                        
                        # Set the background color
                        self.matrixportal.set_background(preset_config["background"])
                        
                        # Special handling for music preset - two lines with scrolling
                        if data["preset_id"] == "music":
                            # Use two lines: artist on top, song on bottom
                            display_artist = artist if artist else "Unknown Artist"
                            display_song = song if song else "Unknown Song"
                            
                            # Set purple background
                            self.matrixportal.set_background(preset_config["background"])
                            
                            # Set text color to WHITE
                            self.text_manager.title_label.color = WHITE
                            self.text_manager.timer_label.color = WHITE
                            
                            # Set label backgrounds to match purple background
                            self.text_manager.title_label.background_color = preset_config["background"]
                            self.text_manager.timer_label.background_color = preset_config["background"]
                            
                            # Use scrolling for long text (max 10 chars per line for 64px width)
                            self.text_manager.update_text_with_scrolling(
                                display_artist, 
                                self.text_manager.title_label, 
                                8, 
                                max_chars=10
                            )
                            self.text_manager.update_text_with_scrolling(
                                display_song, 
                                self.text_manager.timer_label, 
                                20, 
                                max_chars=10
                            )
                        else:
                            # Regular preset handling
                            display_text = name if name else preset_config["text"]
                            self.text_manager.title_label.color = preset_config["text_color"]
                            self.text_manager.update_text(display_text, self.text_manager.title_label, 8)
                            
                            # Clear timer text
                            self.text_manager.timer_label.color = preset_config["text_color"]
                            self.text_manager.update_text("", self.text_manager.timer_label, 20)
                        
                        # Set border color and mode
                        self.border_manager.border_palette[1] = preset_config["border_color"]
                        if preset_config["border_mode"] == "solid":
                            self.border_manager.set_solid_border()
                        elif preset_config["border_mode"] == "animated":
                            self.border_manager.set_animated()
                        elif preset_config["border_mode"] == "blinking":
                            self.border_manager.set_blinking()
                        elif preset_config["border_mode"] == "none":
                            self.border_manager.clear_border()
                        
                        print(f"Preset {data['preset_id']} started successfully")
        except Exception as e:
            print(f"Error processing message: {e}")
        print("=========================\n")

    def on_subscribe(self, mqtt_client, userdata, topic, granted_qos):
        """Callback when subscribed to a topic"""
        print(f"Subscribed to {topic} with QOS {granted_qos}")

    def check_test_trigger(self):
        """Check for test trigger file"""
        try:
            current_time = time.monotonic()
            if current_time - self.last_check < 1:
                return None
                
            self.last_check = current_time
            
            if TEST_FILE in os.listdir():
                print("Found test file")
                try:
                    with open(TEST_FILE, "r") as f:
                        data = json.loads(f.read())
                    # Don't try to delete the file on read-only filesystem
                    return data
                except Exception as e:
                    print("Error processing test file:", str(e))
        except Exception as e:
            print("Error checking trigger:", str(e))
        return None

    def update(self):
        """Main update loop"""
        try:
            current_time = time.monotonic()
            
            # Feed the watchdog
            watchdog.feed()
            
            # Check network connections
            if not self.check_wifi_connection() or not self.check_mqtt_connection():
                return
            
            # Process any pending MQTT messages
            try:
                self.mqtt_client.loop()
            except Exception as e:
                print("Error in MQTT loop:", str(e))
                self.setup_mqtt()  # Try to reconnect
                return
            
            # Update preset state if active
            if self.preset_manager.current_preset:
                state = self.preset_manager.update_preset(current_time)
                if state:
                    if state["type"] == "preset_end":
                        # Clear display when preset expires
                        self.border_manager.clear_border()
                        self.text_manager.update_text("", self.text_manager.title_label, 8)
                        self.text_manager.update_text("", self.text_manager.timer_label, 20)
                        self.matrixportal.set_background(BLACK)
                return
            
            # Check for new countdown trigger (keep file-based trigger for testing)
            if not self.timer_manager.current_countdown and not self.timer_manager.stopwatch_start and not self.timer_manager.done_start:
                trigger = self.check_test_trigger()
                if trigger:
                    mode = trigger.get("mode", "timer")
                    if mode == "timer":
                        # Set default colors for timer mode
                        self.matrixportal.set_background(BLACK)
                        self.text_manager.title_label.color = WHITE
                        self.text_manager.timer_label.color = WHITE
                        self.border_manager.border_palette[1] = RED  # Reset border to default red
                        
                        if self.timer_manager.start_countdown(trigger["name"], trigger["duration"]):
                            self.text_manager.update_text(trigger["name"], self.text_manager.title_label, 8)
                            self.border_manager.set_solid_border()
                    elif mode == "preset" and "preset_id" in trigger:
                        if self.preset_manager.start_preset(trigger["preset_id"], trigger.get("name"), trigger.get("duration")):
                            preset_config = self.preset_manager.presets[trigger["preset_id"]]
                            
                            # Set the background color
                            self.matrixportal.set_background(preset_config["background"])
                            
                            # Update text and its color
                            display_text = trigger.get("name", "") if trigger.get("name") else preset_config["text"]
                            self.text_manager.title_label.color = preset_config["text_color"]
                            self.text_manager.update_text(display_text, self.text_manager.title_label, 8)
                            
                            # Clear timer text
                            self.text_manager.timer_label.color = preset_config["text_color"]
                            self.text_manager.update_text("", self.text_manager.timer_label, 20)
                            
                            # Set border color and mode
                            self.border_manager.border_palette[1] = preset_config["border_color"]
                            if preset_config["border_mode"] == "solid":
                                self.border_manager.set_solid_border()
                            elif preset_config["border_mode"] == "animated":
                                self.border_manager.set_animated()
                            elif preset_config["border_mode"] == "blinking":
                                self.border_manager.set_blinking()
                            elif preset_config["border_mode"] == "none":
                                self.border_manager.clear_border()
                return
            
            # Update timer state
            if self.timer_manager.current_countdown or self.timer_manager.done_start:
                state = self.timer_manager.update_countdown(current_time)
                if state:
                    if state["type"] == "countdown":
                        # Only update display when we've moved to a new second
                        if state.get("update", False):
                            timer_text = f"{state['minutes']:02d}:{state['seconds']:02d}"
                            self.text_manager.update_text(timer_text, self.text_manager.timer_label, 20)
                            
                            # Set border mode based on remaining time
                            if state["remaining"] <= FINAL_COUNTDOWN:
                                self.border_manager.set_animated()
                            
                    elif state["type"] == "done":
                        # Only update text and border when first entering DONE state
                        if state.get("first", False):
                            self.text_manager.update_text("DONE", self.text_manager.timer_label, 20)
                            self.border_manager.set_solid_border()
                    elif state["type"] == "stopwatch_start":
                        self.text_manager.update_text(STOPWATCH_TEXT, self.text_manager.title_label, 8)
                        self.text_manager.update_text("00:00", self.text_manager.timer_label, 20)
                        self.border_manager.set_blinking()
            else:
                state = self.timer_manager.update_stopwatch(current_time)
                if state:
                    # Ensure blinking border is maintained
                    if self.border_manager.current_mode != "blinking":
                        self.border_manager.set_blinking()
                    
                    # Only update display when we've moved to a new second
                    if state.get("update", False):
                        timer_text = f"{state['minutes']:02d}:{state['seconds']:02d}"
                        self.text_manager.update_text(timer_text, self.text_manager.timer_label, 20)
                elif not state:
                    # Clear everything if no active countdown or stopwatch
                    self.border_manager.clear_border()
                    self.text_manager.update_text("", self.text_manager.title_label, 8)
                    self.text_manager.update_text("", self.text_manager.timer_label, 20)
            
            # Update border animation independently (only if not in DONE state)
            if not (state and state["type"] == "done"):
                self.border_manager.update_animation(current_time)
            
            # Update manual text scrolling (always update, regardless of state)
            self.text_manager.update_scrolling(current_time)
                
        except Exception as e:
            print("Error in update:", str(e))
            # Don't sleep here as it might be a temporary error

    def run(self):
        """Main run loop"""
        print("Starting main loop...")
        while True:
            try:
                self.update()
                time.sleep(0.01)  # Small sleep to prevent CPU overload
            except Exception as e:
                print("Error in main loop:", str(e))
                try:
                    self.setup_mqtt()  # Try to reconnect
                except:
                    pass
                time.sleep(1)

# Main program
print("Creating display object...")
display = CountdownDisplay()
print("Starting display...")
display.run()
