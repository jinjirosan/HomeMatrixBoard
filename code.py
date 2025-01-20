# pyright: ignore[reportShadowedImports]
import board
import time
import json
import terminalio
import displayio
import os
import supervisor
from adafruit_matrixportal.matrixportal import MatrixPortal

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

class CountdownDisplay:
    def __init__(self):
        print("Initializing display...")
        try:
            self.matrixportal = MatrixPortal(
                status_neopixel=board.NEOPIXEL,
                debug=True
            )
            print("MatrixPortal initialized")
            
            # Create a bitmap for the border
            self.border_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 2)
            self.border_palette = displayio.Palette(2)
            self.border_palette[0] = BLACK  # Background
            self.border_palette[1] = RED    # Border color
            
            # Create a TileGrid using the bitmap and palette
            self.border_grid = displayio.TileGrid(
                self.border_bitmap,
                pixel_shader=self.border_palette
            )
            
            # Create a group for the border
            self.border_group = displayio.Group()
            self.border_group.append(self.border_grid)
            
            # Add border group to the display
            self.matrixportal.display.root_group.append(self.border_group)
            
            # Set up the display
            self.setup_display()
            print("Display setup complete")
            
        except Exception as e:
            print("Error during initialization:", str(e))
            raise
        
    def setup_display(self):
        """Initialize the display and create all necessary labels"""
        try:
            # Clear the display first
            self.matrixportal.set_background(BLACK)
            
            # Add title label (centered at y=8)
            self.title_label = self.matrixportal.add_text(
                text_position=(self.center_text_position("READY"), 8),  # Dynamic centering
                text_font=terminalio.FONT,
                text_color=WHITE,
                text="READY"
            )
            
            # Add timer label (centered at y=20)
            self.timer_label = self.matrixportal.add_text(
                text_position=(self.center_text_position("--:--"), 20),  # Dynamic centering
                text_font=terminalio.FONT,
                text_color=WHITE,
                text="--:--"
            )
            
            # Initialize text tracking variables
            self.current_title_text = "READY"
            self.current_timer_text = "--:--"
            
            # Initialize other variables
            self.last_check = time.monotonic()
            self.last_update = time.monotonic()
            self.current_countdown = None
            self.animation_step = 0
            self.stopwatch_start = None
            
            # Draw initial border
            self.set_dashed_border()
            
        except Exception as e:
            print("Error in setup_display:", str(e))
            raise

    def draw_border_pixel(self, x, y, on=True):
        """Draw a single border pixel"""
        if 0 <= x < DISPLAY_WIDTH and 0 <= y < DISPLAY_HEIGHT:
            self.border_bitmap[x, y] = 1 if on else 0

    def set_dashed_border(self):
        """Set normal dashed border"""
        # Clear previous border
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                self.border_bitmap[i, j] = 0
                
        # Draw top and bottom edges
        for x in range(DISPLAY_WIDTH):
            self.draw_border_pixel(x, 0)  # Top
            self.draw_border_pixel(x, DISPLAY_HEIGHT-1)  # Bottom
            
        # Draw left and right edges
        for y in range(DISPLAY_HEIGHT):
            self.draw_border_pixel(0, y)  # Left
            self.draw_border_pixel(DISPLAY_WIDTH-1, y)  # Right

    def set_animated_border(self):
        """Set animated border pattern"""
        self.animation_step = (self.animation_step + 1) % 2
        
        # Clear previous border
        for i in range(DISPLAY_WIDTH):
            for j in range(DISPLAY_HEIGHT):
                self.border_bitmap[i, j] = 0
        
        # Draw animated border
        for i in range(DISPLAY_WIDTH + DISPLAY_HEIGHT * 2):
            if (i + self.animation_step) % 2 == 0:
                if i < DISPLAY_WIDTH:
                    # Top edge
                    self.draw_border_pixel(i, 0)
                    # Bottom edge
                    self.draw_border_pixel(i, DISPLAY_HEIGHT-1)
                else:
                    pos = i - DISPLAY_WIDTH
                    if pos < DISPLAY_HEIGHT:
                        # Right edge
                        self.draw_border_pixel(DISPLAY_WIDTH-1, pos)
                    else:
                        # Left edge
                        self.draw_border_pixel(0, pos - DISPLAY_HEIGHT)

    def set_solid_border(self):
        """Set solid border"""
        self.set_dashed_border()  # Same as dashed for now

    def set_blinking_border(self):
        """Set blinking border"""
        if self.animation_step == 0:
            self.set_dashed_border()
        else:
            # Clear all border pixels
            for i in range(DISPLAY_WIDTH):
                for j in range(DISPLAY_HEIGHT):
                    self.border_bitmap[i, j] = 0
        self.animation_step = (self.animation_step + 1) % 2

    def center_text_position(self, text):
        """Calculate x position to center text"""
        # Each character is 5 pixels wide in terminalio font
        text_width = len(text) * 5
        return (DISPLAY_WIDTH - text_width) // 2

    def update_text_display(self, text, label_index, y_position):
        """Update text and ensure it's centered"""
        # Just update the text - the label was created with proper centering
        self.matrixportal.set_text(text, label_index)

    def check_test_trigger(self):
        """Check for test trigger file"""
        try:
            current_time = time.monotonic()
            if current_time - self.last_check < 1:  # Check once per second
                return None
                
            self.last_check = current_time
            
            if TEST_FILE in os.listdir():
                print("Found test file")
                try:
                    with open(TEST_FILE, "r") as f:
                        content = f.read()
                        print("Raw file content:", content)
                        data = json.loads(content)
                        print("Parsed JSON:", data)
                    
                    try:
                        os.remove(TEST_FILE)
                        print("Test file removed successfully")
                    except Exception as e:
                        print("Error removing test file:", str(e))
                    
                    return data
                except json.JSONDecodeError as e:
                    print("JSON decode error:", str(e))
                except Exception as e:
                    print("Error reading test file:", str(e))
        except Exception as e:
            print("Error checking trigger:", str(e))
        return None

    def start_countdown(self, name, duration):
        """Start a new countdown"""
        try:
            print(f"Starting countdown: {name} for {duration} seconds")
            
            # Validate inputs
            if not isinstance(duration, (int, float)):
                print(f"Invalid duration type: {type(duration)}")
                return
                
            if duration <= 0:
                print("Duration must be positive")
                return
            
            self.current_countdown = {
                "name": name,
                "duration": float(duration),
                "start_time": time.monotonic()
            }
            print("Countdown object created:", self.current_countdown)
            
            # Update display with centered text
            self.update_text_display(str(name), self.title_label, 8)
            print("Display updated with new countdown")
            
            # Reset stopwatch
            self.stopwatch_start = None
            
        except Exception as e:
            print("Error starting countdown:", str(e))

    def update_stopwatch(self):
        """Update stopwatch display"""
        try:
            current_time = time.monotonic()
            
            if self.stopwatch_start is None:
                self.stopwatch_start = current_time
                self.last_update = current_time
                self.update_text_display(STOPWATCH_TEXT, self.title_label, 8)
            
            # Update display every second
            if current_time - self.last_update >= 1.0:
                elapsed = int(current_time - self.stopwatch_start)
                minutes = elapsed // 60
                seconds = elapsed % 60
                timer_text = f"{minutes:02d}:{seconds:02d}"
                self.update_text_display(timer_text, self.timer_label, 20)
                self.current_timer_text = timer_text
                self.last_update = current_time
                
                # Update border every second (on the same timing as the text)
                self.set_blinking_border()
            
        except Exception as e:
            print("Error updating stopwatch:", str(e))

    def update(self):
        """Main update loop"""
        try:
            if self.current_countdown is None and self.stopwatch_start is None:
                trigger = self.check_test_trigger()
                if trigger:
                    print("Trigger detected:", trigger)
                    self.start_countdown(trigger["name"], trigger["duration"])
                return

            current_time = time.monotonic()

            if self.current_countdown is not None:
                elapsed = current_time - self.current_countdown["start_time"]
                remaining = max(0, self.current_countdown["duration"] - elapsed)

                if remaining > 0:
                    # Update display every second
                    if current_time - self.last_update >= 1.0:
                        minutes = int(remaining) // 60
                        seconds = int(remaining) % 60
                        timer_text = f"{minutes:02d}:{seconds:02d}"
                        self.update_text_display(timer_text, self.timer_label, 20)
                        self.current_timer_text = timer_text
                        self.last_update = current_time
                    
                    # Update borders based on remaining time
                    if remaining <= FINAL_COUNTDOWN:
                        if current_time - self.last_check >= 0.2:  # Animation timing
                            self.set_animated_border()
                            self.last_check = current_time
                    # Don't update border if not in final countdown
                else:
                    print("Countdown finished")
                    self.update_text_display("DONE", self.timer_label, 20)
                    self.current_timer_text = "DONE"
                    self.set_solid_border()  # Set border once when showing DONE
                    time.sleep(DONE_DISPLAY_TIME)
                    
                    # Switch to stopwatch mode
                    self.current_countdown = None
                    self.stopwatch_start = current_time
                    self.update_text_display(STOPWATCH_TEXT, self.title_label, 8)
            else:
                # In stopwatch mode
                self.update_stopwatch()
                
            # Small delay to prevent too frequent updates
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
