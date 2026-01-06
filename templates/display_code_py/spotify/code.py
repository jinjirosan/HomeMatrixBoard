# pyright: ignore[reportShadowedImports]
"""
MatrixPortal M4 Display Code Template - Spotify Integration Enabled

This template includes:
- Spotify music preset support (two-line display with artist/song)
- Automatic text scrolling for long text
- Memory-optimized initialization (bit_depth=6)
- All standard timer and preset modes
- MQTT connection with automatic reconnection

REQUIRED LIBRARIES:
- adafruit_matrixportal
- adafruit_display_text (including scrolling_label.mpy)
- adafruit_minimqtt
- adafruit_esp32spi

REQUIRED FILES:
- secrets.py (with WiFi and MQTT credentials)

See documentation/spotify_integration.md for setup instructions.
"""
import board
import time
import json
import terminalio
import displayio
import os
import supervisor
import microcontroller
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_display_text.scrolling_label import ScrollingLabel
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_esp32spi import adafruit_esp32spi_socketpool

print("\n" * 2)
print("=" * 40)
print("MatrixPortal M4 Startup - Spotify Enabled")
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
        self.setup_text()
        
    def setup_text(self):
        """Initialize and create text labels"""
        # Create title label with empty text
        self.title_label = Label(
            terminalio.FONT,
            text="",
            color=WHITE,
            background_color=BLACK,  # Add black background for better readability
            background_tight=False,  # Add padding around text
            padding_left=1,         # Add left padding
            padding_right=1,        # Add right padding
            x=0,
            y=8
        )
        
        # Create timer label
        self.timer_label = Label(
            terminalio.FONT,
            text="",
            color=WHITE,
            background_color=BLACK,  # Add black background for better readability
            background_tight=False,  # Add padding around text
            padding_left=1,         # Add left padding
            padding_right=1,        # Add right padding
            x=0,
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
        """Update text with scrolling if it's too long"""
        text_width = len(text) * 6
        max_width = max_chars * 6
        
        # Remove old scrolling label if it exists
        if hasattr(label, '_scrolling_label'):
            self.text_group.remove(label._scrolling_label)
            delattr(label, '_scrolling_label')
        
        if text_width > max_width:
            # Use scrolling label for long text
            scrolling_label = ScrollingLabel(
                terminalio.FONT,
                text=text,
                color=label.color,
                max_characters=max_chars,
                animate_time=0.3,
                x=0,
                y=y_position
            )
            label._scrolling_label = scrolling_label
            # Hide the regular label and show scrolling one
            label.text = ""
            label.x = -1000  # Move off screen
            if scrolling_label not in self.text_group:
                self.text_group.append(scrolling_label)
        else:
            # Use regular label for short text
            self.update_text(text, label, y_position)

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
        self.border_palette.make_transparent(0)  # Make index 0 transparent
        self.border_palette[0] = 0x000000  # Black (will be transparent)
        self.border_palette[1] = RED   # Initial border color
        
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
    """Manages preset display configurations including Spotify music preset"""
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.current_preset = None
        self.preset_start = None
        self.preset_duration = None
        
        # Create radio symbol bitmap (16x16 pixels)
        self.radio_bitmap = displayio.Bitmap(16, 16, 2)
        self.radio_palette = displayio.Palette(2)
        self.radio_palette[0] = BLACK  # Set to black first
        self.radio_palette.make_transparent(0)  # Then make it transparent
        self.radio_palette[1] = RED   # Symbol color
        
        # Draw radio waves symbol (three arcs)
        # Small arc
        for i in range(5):
            self.radio_bitmap[7+i, 7] = 1
            self.radio_bitmap[7+i, 8] = 1
        # Medium arc
        for i in range(7):
            self.radio_bitmap[6+i, 5] = 1
            self.radio_bitmap[6+i, 6] = 1
        # Large arc
        for i in range(9):
            self.radio_bitmap[5+i, 3] = 1
            self.radio_bitmap[5+i, 4] = 1
        
        # Create radio symbol tile grid
        self.radio_grid = displayio.TileGrid(
            self.radio_bitmap,
            pixel_shader=self.radio_palette,
            x=(DISPLAY_WIDTH - 16) // 2,  # Center horizontally
            y=16  # Position below text
        )
        
        # Create radio symbol group and hide it by default
        self.radio_group = displayio.Group()
        self.radio_group.append(self.radio_grid)
        self.radio_group.hidden = True  # Hide the radio symbol by default
        
        # Define preset configurations
        self.presets = {
            "on_air": {
                "background": BLACK,     # Black background
                "text": "ON AIR",
                "text_color": RED,      # Red text
                "border_mode": "solid",
                "border_color": WHITE,
                "show_radio": True      # Flag to show radio symbol
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
                "background": BLACK,     # Black background
                "text": "",             # No text
                "text_color": WHITE,    # Default text color
                "border_mode": "none",  # No border
                "border_color": RED,    # Default border color
                "show_radio": False     # No radio symbol
            },
            "music": {
                "background": 0x800080,  # Purple background (Spotify preset)
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
        # Initialize connection management variables first
        self.last_wifi_check = 0
        self.last_mqtt_check = 0
        self.wifi_retry_count = 0
        self.mqtt_retry_count = 0
        self.max_retry_interval = 300  # Maximum retry interval in seconds
        self.setup_complete = False
        self.last_successful_connection = 0
        self.mqtt_client = None
        self.network_pool = None
        self.startup_time = time.monotonic()
        
        # Add connection quality monitoring
        self.last_heartbeat = 0
        self.heartbeat_interval = 30  # Send heartbeat every 30 seconds
        self.last_message_received = 0
        self.connection_quality = 100  # Track connection quality (percentage)
        self.message_counter = 0  # Track total messages
        self.failed_message_counter = 0  # Track failed messages

        print("Initializing display...")
        try:
            print("Init display")
            # Release any existing displays to free memory
            displayio.release_displays()
            
            # Initialize MatrixPortal with memory optimizations
            self.matrixportal = MatrixPortal(
                status_neopixel=board.NEOPIXEL,
                bit_depth=6,        # Reduce from default 8-bit to save memory
                width=64,            # Explicitly set dimensions
                height=32,
                debug=False          # Disable debug to save memory
            )
            
            # Wait for initial WiFi connection and report it
            print("Connecting to WiFi...")
            while not self.matrixportal.network.is_connected:
                try:
                    self.matrixportal.network.connect()
                    if self.matrixportal.network.is_connected:
                        print("WiFi connected successfully")
                        print(f"IP Address: {self.matrixportal.network.ip_address}")
                        break
                except Exception as e:
                    print(f"WiFi connection error: {e}")
                    time.sleep(1)
            
            # Report initial WiFi connection
            self.report_health_event("wifi_connected", {
                "ip": self.matrixportal.network.ip_address,
                "ssid": secrets['ssid'],
                "reset_cause": str(microcontroller.cpu.reset_reason),
                "firmware_version": "1.1.0"
            })
            
            # Create main display group
            print("Init background")
            self.main_group = displayio.Group()
            
            # Create background layer (bottom)
            self.background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
            self.background_palette = displayio.Palette(1)
            self.background_palette[0] = BLACK
            self.background = displayio.TileGrid(
                self.background_bitmap,
                pixel_shader=self.background_palette
            )
            
            # Initialize border (middle layer)
            self.border_manager = BorderManager(self.matrixportal)
            
            # Initialize text (top layer)
            self.text_manager = DisplayText(self.matrixportal)
            
            # Initialize preset manager (includes Spotify music preset)
            self.preset_manager = PresetManager(self.matrixportal)
            
            # Add layers in correct order (bottom to top)
            self.main_group.append(self.background)        # Bottom layer
            self.main_group.append(self.border_manager.border_group)  # Middle layer
            self.main_group.append(self.text_manager.text_group)      # Top layer
            self.main_group.append(self.preset_manager.radio_group)   # Radio symbol layer
            
            # Set the display's root group
            self.matrixportal.display.root_group = self.main_group
            
            # Initialize timer manager
            self.timer_manager = TimerManager()
            
            # Set initial state
            self.border_manager.clear_border()
            self.last_check = time.monotonic()
            
            # Initialize MQTT
            self.setup_mqtt()
            
            print("Display setup complete")
            
        except Exception as e:
            print("Error during initialization:", str(e))
            raise

    def get_retry_interval(self, retry_count):
        """Calculate retry interval with exponential backoff"""
        base_delay = 3
        max_delay = self.max_retry_interval
        delay = min(base_delay * (2 ** retry_count), max_delay)
        return delay

    def report_health_event(self, event_type, data=None):
        """Report health events to MQTT"""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            print(f"Cannot publish health event: {event_type}")
            return
            
        try:
            # Initialize data dict if None
            if data is None:
                data = {}
                
            health_data = {
                "event": event_type,
                "timestamp": time.monotonic(),
                "uptime": time.monotonic() - self.startup_time,
                "data": data
            }
            
            # Publish to health topic
            self.mqtt_client.publish(
                f"{secrets['mqtt_topic']}/health",
                json.dumps(health_data)
            )
            print(f"Published health event: {event_type}")
        except Exception as e:
            print(f"Error publishing health event: {e}")

    def report_error(self, error_type, details):
        """Report errors to MQTT"""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            print(f"Cannot publish error: {error_type}")
            return
            
        try:
            error_data = {
                "type": error_type,
                "timestamp": time.monotonic(),
                "uptime": time.monotonic() - self.startup_time,
                "details": details,
                "system_state": {
                    "wifi_connected": self.matrixportal.network.is_connected,
                    "mqtt_connected": self.mqtt_client.is_connected() if self.mqtt_client else False,
                    "retry_count": self.mqtt_retry_count
                }
            }
            self.mqtt_client.publish(
                f"{secrets['mqtt_topic']}/errors",
                json.dumps(error_data)
            )
        except Exception as e:
            print(f"Error publishing error: {e}")

    def check_wifi_connection(self):
        """Check and maintain WiFi connection with exponential backoff"""
        current_time = time.monotonic()
        
        # Only check periodically
        if current_time - self.last_wifi_check < self.get_retry_interval(self.wifi_retry_count):
            return False

        self.last_wifi_check = current_time
        
        try:
            if not self.matrixportal.network.is_connected:
                print("WiFi disconnected, attempting to reconnect...")
                self.report_error("wifi_disconnected", {
                    "retry_count": self.wifi_retry_count,
                    "last_success": self.last_successful_connection
                })
                
                self.matrixportal.network.connect()
                if self.matrixportal.network.is_connected:
                    print("WiFi reconnected successfully")
                    print(f"IP Address: {self.matrixportal.network.ip_address}")
                    self.wifi_retry_count = 0
                    self.last_successful_connection = current_time
                    self.report_health_event("wifi_connected", {
                        "ip": self.matrixportal.network.ip_address,
                        "signal": self.get_wifi_signal_strength()
                    })
                    return True
                else:
                    self.wifi_retry_count += 1
                    retry_interval = self.get_retry_interval(self.wifi_retry_count)
                    print(f"Could not reconnect to WiFi. Retrying in {retry_interval} seconds...")
                    return False
            else:
                self.wifi_retry_count = 0
                return True
        except Exception as e:
            error_msg = str(e)
            print(f"Error during WiFi connection check: {error_msg}")
            self.report_error("wifi_error", {
                "error": error_msg,
                "retry_count": self.wifi_retry_count
            })
            self.wifi_retry_count += 1
            retry_interval = self.get_retry_interval(self.wifi_retry_count)
            print(f"Retrying in {retry_interval} seconds...")
            return False

    def check_mqtt_connection(self):
        """Check and maintain MQTT connection with exponential backoff"""
        current_time = time.monotonic()
        
        # Only check periodically
        if current_time - self.last_mqtt_check < self.get_retry_interval(self.mqtt_retry_count):
            return False

        self.last_mqtt_check = current_time
        
        if not self.mqtt_client:
            print("MQTT client not initialized, attempting setup...")
            return self.setup_mqtt()

        try:
            if not self.mqtt_client.is_connected():
                print("\n=== MQTT Reconnection Attempt ===")
                self.report_error("mqtt_disconnected", {
                    "retry_count": self.mqtt_retry_count,
                    "last_success": self.last_successful_connection
                })
                
                print(f"Last successful connection: {time.monotonic() - self.last_successful_connection:.2f}s ago")
                print(f"Current retry count: {self.mqtt_retry_count}")
                print(f"WiFi status: {'Connected' if self.matrixportal.network.is_connected else 'Disconnected'}")
                print("Attempting to reconnect...")
                
                # Add delay before reconnection to allow socket cleanup
                time.sleep(1.0)
                self.mqtt_client.reconnect()
                
                if self.mqtt_client.is_connected():
                    print("MQTT reconnected successfully")
                    self.mqtt_retry_count = 0
                    self.last_successful_connection = current_time
                    
                    # Report successful reconnection
                    self.report_health_event("mqtt_connected", {
                        "uptime": time.monotonic() - self.startup_time
                    })
                    
                    # Resubscribe with delay
                    time.sleep(0.5)  # Wait for connection to stabilize
                    try:
                        self.mqtt_client.subscribe(secrets['mqtt_topic'])
                        print(f"Resubscribed to {secrets['mqtt_topic']}")
                        print("==============================\n")
                        return True
                    except Exception as e:
                        error_msg = str(e)
                        print(f"Resubscription failed: {error_msg}")
                        self.report_error("mqtt_subscription_failed", {
                            "error": error_msg
                        })
                        print("==============================\n")
                        return False
                else:
                    self.mqtt_retry_count += 1
                    retry_interval = self.get_retry_interval(self.mqtt_retry_count)
                    print(f"Could not reconnect to MQTT. Retrying in {retry_interval} seconds...")
                    print("==============================\n")
                    return False
            else:
                self.mqtt_retry_count = 0
                return True
        except Exception as e:
            error_msg = str(e)
            print("\n=== MQTT Connection Error ===")
            self.report_error("mqtt_error", {
                "error": error_msg,
                "retry_count": self.mqtt_retry_count
            })
            print(f"Error details: {error_msg}")
            print(f"WiFi status: {'Connected' if self.matrixportal.network.is_connected else 'Disconnected'}")
            print(f"Time since last success: {time.monotonic() - self.last_successful_connection:.2f}s")
            print(f"Current retry count: {self.mqtt_retry_count}")
            self.mqtt_retry_count += 1
            retry_interval = self.get_retry_interval(self.mqtt_retry_count)
            print(f"Retrying in {retry_interval} seconds...")
            print("===========================\n")
            return False

    def on_connect(self, client, userdata, flags, rc):
        """Minimal connect callback"""
        print(f"\n=== MQTT Connected ===")
        print(f"Connection result: {rc}")
        self.connection_quality = 100

    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        print(f"\n=== MQTT Disconnected ===")
        print(f"Disconnect reason: {rc}")
        # Don't try to publish when disconnected
        self.last_successful_connection = 0

    def on_publish(self, client, userdata, topic):
        """Callback when message is published"""
        print(f"Message published to {topic}")

    def publish_status(self, status):
        """Publish device status with connection check"""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            print("Cannot publish status: MQTT not connected")
            return
            
        try:
            status_data = {
                "status": status,
                "uptime": time.monotonic() - self.startup_time,
                "wifi": {
                    "connected": self.matrixportal.network.is_connected,
                    "ip": self.matrixportal.network.ip_address if self.matrixportal.network.is_connected else None,
                    "ssid": secrets['ssid']
                },
                "connection_quality": self.connection_quality,
                "message_success_rate": self.get_message_success_rate()
            }
            self.mqtt_client.publish(
                f"{secrets['mqtt_topic']}/status",
                json.dumps(status_data)
            )
            print(f"Published status: {status}")
        except Exception as e:
            print(f"Error publishing status: {e}")
            # Reset connection quality on publish failure
            self.connection_quality = max(0, self.connection_quality - 10)

    def get_wifi_signal_strength(self):
        """Get WiFi signal strength (RSSI) - currently not supported"""
        return None  # RSSI not reliably available on this hardware

    def get_message_success_rate(self):
        """Calculate message success rate"""
        if self.message_counter == 0:
            return 100
        return ((self.message_counter - self.failed_message_counter) / self.message_counter) * 100

    def check_connection_quality(self):
        """Monitor connection quality"""
        current_time = time.monotonic()

        # Send heartbeat periodically
        if current_time - self.last_heartbeat >= self.heartbeat_interval:
            self.last_heartbeat = current_time
            self.publish_status("online")

        # Update connection quality based on message success rate
        self.connection_quality = self.get_message_success_rate()

    def on_message(self, client, topic, message):
        """Handle incoming MQTT messages with acknowledgment"""
        print("\n=== New Message Received ===")
        print(f"Topic: {topic}")
        print(f"Message: {message}")
        
        self.message_counter += 1
        self.last_message_received = time.monotonic()
        
        try:
            # Parse the JSON message
            data = json.loads(message)
            
            # Process the message
            success = self.process_message(data)
            
            # Send acknowledgment if message_id is present
            message_id = data.get("message_id")
            if message_id and success:
                ack_data = {
                    "message_id": message_id,
                    "status": "success",
                    "timestamp": time.monotonic()
                }
                self.mqtt_client.publish(
                    f"{secrets['mqtt_topic']}/ack",
                    json.dumps(ack_data)
                )
            elif message_id:
                self.failed_message_counter += 1
                ack_data = {
                    "message_id": message_id,
                    "status": "failed",
                    "timestamp": time.monotonic()
                }
                self.mqtt_client.publish(
                    f"{secrets['mqtt_topic']}/ack",
                    json.dumps(ack_data)
                )
                    
        except Exception as e:
            print(f"Error processing message: {e}")
            self.failed_message_counter += 1
            if "message_id" in locals():
                try:
                    self.mqtt_client.publish(
                        f"{secrets['mqtt_topic']}/ack",
                        json.dumps({
                            "message_id": message_id,
                            "status": "error",
                            "error": str(e),
                            "timestamp": time.monotonic()
                        })
                    )
                except Exception as pub_error:
                    print(f"Error publishing error acknowledgment: {pub_error}")
        print("=========================\n")

    def process_message(self, data):
        """Process the message and return success status"""
        try:
            # Clear any existing displays
            self.timer_manager.current_countdown = None
            self.timer_manager.stopwatch_start = None
            self.timer_manager.done_start = None
            self.preset_manager.clear_preset()
            
            # Reset display to default state
            self.text_manager.update_text("", self.text_manager.title_label, 8)
            self.text_manager.update_text("", self.text_manager.timer_label, 20)
            self.border_manager.clear_border()
            
            # Hide radio symbol by default
            self.preset_manager.radio_group.hidden = True
            
            # Check message mode (defaults to "timer" for backward compatibility)
            mode = data.get("mode", "timer")
            
            if mode == "timer":
                # Set default colors for timer mode
                self.set_background(BLACK)
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
                        
                        # First set the background color
                        self.set_background(preset_config["background"])
                        
                        # Special handling for music preset - two lines with scrolling
                        if data["preset_id"] == "music":
                            # Use two lines: artist on top, song on bottom
                            display_artist = artist if artist else "Unknown Artist"
                            display_song = song if song else "Unknown Song"
                            
                            self.text_manager.title_label.color = preset_config["text_color"]
                            self.text_manager.timer_label.color = preset_config["text_color"]
                            
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
                        
                        # Show/hide radio symbol based on preset configuration
                        self.preset_manager.radio_group.hidden = not preset_config.get("show_radio", False)
                        
                        print(f"Preset {data['preset_id']} started successfully")
            return True  # Return True if message was processed successfully
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return False

    def update(self):
        """Main update loop with improved connection handling"""
        current_time = time.monotonic()

        # Check connection quality first
        self.check_connection_quality()

        # Handle network checks independently from timer updates
        need_network_check = (current_time - self.last_wifi_check >= self.get_retry_interval(self.wifi_retry_count)) or \
                           (current_time - self.last_mqtt_check >= self.get_retry_interval(self.mqtt_retry_count))

        if need_network_check:
            # Check WiFi connection first
            if not self.check_wifi_connection():
                return  # Don't proceed with MQTT check if WiFi is down

            # Check MQTT connection
            if not self.check_mqtt_connection():
                return  # Don't proceed with MQTT operations if connection is down

        # Process MQTT messages with improved error handling
        if self.mqtt_client and self.mqtt_client.is_connected():
            try:
                self.mqtt_client.loop(timeout=1.0)  # Match socket timeout
            except OSError as e:
                if "Failed to send" in str(e):
                    # Enhanced logging for socket failures
                    print("\n=== Socket Send Failure Detected ===")
                    print(f"Error details: {e}")
                    print(f"Current WiFi status: {'Connected' if self.matrixportal.network.is_connected else 'Disconnected'}")
                    print(f"Current MQTT status: {'Connected' if self.mqtt_client.is_connected() else 'Disconnected'}")
                    print(f"Time since last successful connection: {time.monotonic() - self.last_successful_connection:.2f}s")
                    print(f"WiFi retry count: {self.wifi_retry_count}")
                    print(f"MQTT retry count: {self.mqtt_retry_count}")
                    print("Triggering reconnection sequence...")
                    print("================================\n")
                    
                    # Socket send failure - trigger reconnection
                    self.mqtt_retry_count += 1
                    try:
                        self.mqtt_client.disconnect()
                        print("MQTT client disconnected cleanly")
                    except Exception as disc_error:
                        print(f"Error during disconnect: {disc_error}")
                elif "pystack" not in str(e):  # Only log non-pystack errors
                    print(f"Error in MQTT loop: {e}")

        # Update display state regardless of network status
        try:
            # Check for new countdown trigger (keep file-based trigger for testing)
            if not self.timer_manager.current_countdown and not self.timer_manager.stopwatch_start and \
               not self.timer_manager.done_start and not self.preset_manager.current_preset:
                trigger = self.check_test_trigger()
                if trigger:
                    mode = trigger.get("mode", "timer")
                    if mode == "timer":
                        # Set default colors for timer mode
                        self.set_background(BLACK)
                        self.text_manager.title_label.color = WHITE
                        self.text_manager.timer_label.color = WHITE
                        self.border_manager.border_palette[1] = RED  # Reset border to default red
                        
                        if self.timer_manager.start_countdown(trigger["name"], trigger["duration"]):
                            self.text_manager.update_text(trigger["name"], self.text_manager.title_label, 8)
                            self.border_manager.set_solid_border()
                    elif mode == "preset" and "preset_id" in trigger:
                        if self.preset_manager.start_preset(trigger["preset_id"], trigger.get("name"), trigger.get("duration")):
                            preset_config = self.preset_manager.presets[trigger["preset_id"]]
                            
                            # First set the background color
                            self.set_background(preset_config["background"])
                            
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
                        self.set_background(BLACK)
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
                
        except Exception as e:
            print(f"Error in display update: {e}")

    def run(self):
        """Main run loop"""
        print("Starting main loop...")
        while True:
            try:
                self.update()
                time.sleep(0.01)  # Small sleep to prevent CPU overload
            except Exception as e:
                print("Error in main loop:", str(e))
                time.sleep(0.1)  # Slightly longer sleep on error

    def set_background(self, color):
        """Set the background color"""
        self.background_palette[0] = color

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

    def setup_mqtt(self):
        """Set up MQTT connection with proper error handling"""
        try:
            print("Connecting to MQTT broker...")
            
            # Create socket pool with buffer management
            pool = adafruit_esp32spi_socketpool.SocketPool(self.matrixportal.network._wifi.esp)
            
            # Set up MQTT client with optimized settings
            self.mqtt_client = MQTT.MQTT(
                broker=secrets['mqtt_broker'],
                port=secrets['mqtt_port'],
                username=secrets['mqtt_user'],
                password=secrets['mqtt_password'],
                socket_pool=pool,
                is_ssl=False,
                keep_alive=30,  # More frequent keepalive
                socket_timeout=1.0,  # Base timeout
                recv_timeout=2.0     # Must be > socket_timeout
            )

            # Set up minimal callbacks to save memory
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.on_connect = self.on_connect

            # Connect to MQTT broker
            print(f"Attempting to connect to {secrets['mqtt_broker']} as {secrets['mqtt_user']}")
            self.mqtt_client.connect()
            
            if self.mqtt_client.is_connected():
                print("Connected to MQTT broker!")
                self.mqtt_retry_count = 0
                self.last_successful_connection = time.monotonic()
                
                # Subscribe only to main topic
                try:
                    self.mqtt_client.subscribe(secrets['mqtt_topic'])
                    print(f"Subscribed to {secrets['mqtt_topic']}")
                    return True
                except Exception as e:
                    print(f"Initial subscription failed: {e}")
                    return False
            else:
                print("Failed to connect to MQTT broker")
                return False

        except Exception as e:
            print(f"Error setting up MQTT: {e}")
            self.mqtt_retry_count += 1
            retry_interval = self.get_retry_interval(self.mqtt_retry_count)
            print(f"Retrying in {retry_interval} seconds...")
            return False

# Main program
print("Creating display object...")
display = CountdownDisplay()
print("Starting display...")
display.run()

