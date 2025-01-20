# pyright: ignore[reportShadowedImports]
import board
import time
import json
import terminalio
import displayio
import os
import supervisor
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label

print("Starting up...")

# Configuration variables
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
TEST_FILE = "test_trigger.json"
DONE_DISPLAY_TIME = 10  # How long to show "DONE" message
FINAL_COUNTDOWN = 10    # When to start running ants animation
STOPWATCH_TEXT = "STOPWATCH"  # Text to display during stopwatch mode

# Colors
RED = 0xFF0000
WHITE = 0xFFFFFF
BLACK = 0x000000

class DisplayText:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.title_label = None
        self.timer_label = None
        self.text_group = displayio.Group()
        self.setup_text()
        self.matrixportal.display.root_group.append(self.text_group)
        
    def setup_text(self):
        """Initialize and create text labels"""
        # Create title label
        self.title_label = Label(
            terminalio.FONT,
            text="READY",
            color=WHITE,
            x=17,
            y=8
        )
        
        # Create timer label
        self.timer_label = Label(
            terminalio.FONT,
            text="--:--",
            color=WHITE,
            x=22,
            y=20
        )
        
        # Add labels to group
        self.text_group.append(self.title_label)
        self.text_group.append(self.timer_label)
    
    def center_text_position(self, text):
        """Calculate x position to center text"""
        text_width = len(text) * 5
        return (DISPLAY_WIDTH - text_width) // 2
    
    def update_text(self, text, label, y_position):
        """Update text content and position"""
        label.text = text
        label.x = self.center_text_position(text)

class BorderManager:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.animation_step = 0
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
        # Let the main class handle adding to root group
        
    def draw_pixel(self, x, y, on=True):
        """Draw a single border pixel"""
        if 0 <= x < DISPLAY_WIDTH and 0 <= y < DISPLAY_HEIGHT:
            self.border_bitmap[x, y] = 1 if on else 0
            
    def clear_border(self):
        """Clear all border pixels"""
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                self.border_bitmap[i, j] = 0
                
    def set_dashed(self):
        """Set normal dashed border"""
        self.clear_border()
        for x in range(DISPLAY_WIDTH):
            self.draw_pixel(x, 0)
            self.draw_pixel(x, DISPLAY_HEIGHT-1)
        for y in range(DISPLAY_HEIGHT):
            self.draw_pixel(0, y)
            self.draw_pixel(DISPLAY_WIDTH-1, y)
            
    def set_animated(self):
        """Set animated border pattern"""
        self.animation_step = (self.animation_step + 1) % 2
        self.clear_border()
        
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
                        
    def set_blinking(self):
        """Set blinking border"""
        if self.animation_step == 0:
            self.set_dashed()
        else:
            self.clear_border()
        self.animation_step = (self.animation_step + 1) % 2

class TimerManager:
    def __init__(self):
        self.current_countdown = None
        self.stopwatch_start = None
        self.last_update = time.monotonic()
        
    def start_countdown(self, name, duration):
        """Start a new countdown"""
        if not isinstance(duration, (int, float)) or duration <= 0:
            return False
            
        self.current_countdown = {
            "name": name,
            "duration": float(duration),
            "start_time": time.monotonic()
        }
        self.stopwatch_start = None
        return True
        
    def update_countdown(self, current_time):
        """Update countdown state"""
        if not self.current_countdown:
            return None
            
        elapsed = current_time - self.current_countdown["start_time"]
        remaining = max(0, self.current_countdown["duration"] - elapsed)
        
        if remaining > 0:
            return {
                "type": "countdown",
                "name": self.current_countdown["name"],
                "minutes": int(remaining) // 60,
                "seconds": int(remaining) % 60,
                "remaining": remaining
            }
        else:
            self.stopwatch_start = current_time + DONE_DISPLAY_TIME
            self.current_countdown = None
            return {"type": "done"}
            
    def update_stopwatch(self, current_time):
        """Update stopwatch state"""
        if self.stopwatch_start is None:
            return None
            
        elapsed = int(current_time - self.stopwatch_start)
        return {
            "type": "stopwatch",
            "minutes": elapsed // 60,
            "seconds": elapsed % 60
        }

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
            
            # Initialize timer
            self.timer_manager = TimerManager()
            
            # Set initial state
            self.border_manager.set_dashed()
            self.last_check = time.monotonic()
            print("Display setup complete")
            
        except Exception as e:
            print("Error during initialization:", str(e))
            raise

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
            
            # Check for new countdown trigger
            if not self.timer_manager.current_countdown and not self.timer_manager.stopwatch_start:
                trigger = self.check_test_trigger()
                if trigger:
                    if self.timer_manager.start_countdown(trigger["name"], trigger["duration"]):
                        self.text_manager.update_text(trigger["name"], self.text_manager.title_label, 8)
                return
            
            # Update timer state
            if self.timer_manager.current_countdown:
                state = self.timer_manager.update_countdown(current_time)
                if state:
                    if state["type"] == "countdown":
                        if current_time - self.timer_manager.last_update >= 1.0:
                            timer_text = f"{state['minutes']:02d}:{state['seconds']:02d}"
                            self.text_manager.update_text(timer_text, self.text_manager.timer_label, 20)
                            self.timer_manager.last_update = current_time
                            
                        if state["remaining"] <= FINAL_COUNTDOWN:
                            if current_time - self.last_check >= 0.2:
                                self.border_manager.set_animated()
                                self.last_check = current_time
                    elif state["type"] == "done":
                        self.text_manager.update_text("DONE", self.text_manager.timer_label, 20)
                        self.border_manager.set_dashed()
                        time.sleep(DONE_DISPLAY_TIME)
                        self.text_manager.update_text(STOPWATCH_TEXT, self.text_manager.title_label, 8)
            else:
                state = self.timer_manager.update_stopwatch(current_time)
                if state and current_time - self.timer_manager.last_update >= 1.0:
                    timer_text = f"{state['minutes']:02d}:{state['seconds']:02d}"
                    self.text_manager.update_text(timer_text, self.text_manager.timer_label, 20)
                    self.timer_manager.last_update = current_time
                    self.border_manager.set_blinking()
            
            time.sleep(0.05)
                
        except Exception as e:
            print("Error in update:", str(e))

    def run(self):
        """Main run loop"""
        print("Starting main loop...")
        while True:
            try:
                self.update()
                time.sleep(0.1)
            except Exception as e:
                print("Error in main loop:", str(e))
                time.sleep(5)

# Enable serial output
try:
    supervisor.runtime.serial_connected = True
except:
    pass

# Main program
print("Creating display object...")
display = CountdownDisplay()
print("Starting display...")
display.run()
