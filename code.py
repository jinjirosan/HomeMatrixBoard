import board
import time
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label

# Configuration variables
COUNTDOWN_SECONDS = 15  # Total countdown time in seconds
FINAL_COUNTDOWN = 10    # When to start running ants animation
DISPLAY_TEXT = "COUNTDOWN"  # Text to display above timer
STOPWATCH_TEXT = "STOPWATCH"  # Text to display during stopwatch mode
DISPLAY_WIDTH = 64  # Matrix display width in pixels
DONE_DISPLAY_TIME = 10  # How long to show "DONE" message

def center_text_position(text, font):
    """Calculate x position to center text
    Args:
        text (str): Text to center
        font: Font object to use for width calculation
    Returns:
        int: x position for centered text
    """
    text_width = len(text) * 6  # Each character is typically 6 pixels wide in terminalio font
    return (DISPLAY_WIDTH - text_width) // 2

def set_dashed_border(top_border, bottom_border, left_border, right_border):
    """Set normal dashed border
    Args:
        top_border (list): List of Label objects for top border
        bottom_border (list): List of Label objects for bottom border
        left_border (list): List of Label objects for left border
        right_border (list): List of Label objects for right border
    """
    for label in top_border + bottom_border:
        label.text = "-"
    for label in left_border + right_border:
        label.text = "|"

def set_solid_border(top_border, bottom_border, left_border, right_border):
    """Set solid border
    Args:
        top_border (list): List of Label objects for top border
        bottom_border (list): List of Label objects for bottom border
        left_border (list): List of Label objects for left border
        right_border (list): List of Label objects for right border
    """
    for label in top_border + bottom_border:
        label.text = "-"  # Single dash for each label
    for label in left_border + right_border:
        label.text = "|"

def set_animated_border(step, top_border, bottom_border, left_border, right_border):
    """Set animated border pattern based on step
    Args:
        step (int): Animation step (0 or 1)
        top_border (list): List of Label objects for top border
        bottom_border (list): List of Label objects for bottom border
        left_border (list): List of Label objects for left border
        right_border (list): List of Label objects for right border
    """
    for i in range(len(top_border)):
        top_border[i].text = "-" if (i + step) % 2 == 0 else " "
        bottom_border[i].text = "-" if (i + step) % 2 == 0 else " "
    
    for i in range(len(left_border)):
        left_border[i].text = "|" if (i + step) % 2 == 0 else " "
        right_border[i].text = "|" if (i + step) % 2 == 0 else " "

def set_blinking_border(step, top_border, bottom_border, left_border, right_border):
    """Set blinking border - all on or all off
    Args:
        step (int): Animation step (0 or 1)
        top_border (list): List of Label objects for top border
        bottom_border (list): List of Label objects for bottom border
        left_border (list): List of Label objects for left border
        right_border (list): List of Label objects for right border
    """
    char = "-" if step == 1 else " "
    vert_char = "|" if step == 1 else " "
    
    for label in top_border + bottom_border:
        label.text = char
    for label in left_border + right_border:
        label.text = vert_char

print("Starting countdown test...")

try:
    # Initialize the MatrixPortal
    print("Initializing MatrixPortal...")
    matrixportal = MatrixPortal()
    print("MatrixPortal initialized")

    # First set background to black
    print("Setting black background...")
    matrixportal.set_background(0x000000)
    print("Background set")

    # Create a display group
    group = displayio.Group()
    
    # Define colors
    red = 0xFF0000
    white = 0xFFFFFF
    
    # Store border labels in lists for animation
    top_border = []
    bottom_border = []
    left_border = []
    right_border = []
    
    # Top border - create more labels with single-character spacing
    for x in range(16):  # More labels for complete coverage
        text_label = Label(
            terminalio.FONT,
            text="-",
            color=red,
            x=x*4,  # Tighter spacing (4 pixels between each)
            y=0
        )
        group.append(text_label)
        top_border.append(text_label)
    
    # Bottom border - create more labels with single-character spacing
    for x in range(16):  # More labels for complete coverage
        text_label = Label(
            terminalio.FONT,
            text="-",
            color=red,
            x=x*4,  # Tighter spacing (4 pixels between each)
            y=31
        )
        group.append(text_label)
        bottom_border.append(text_label)
        
    # Left border
    for y in range(4):  # 4 vertical characters
        text_label = Label(
            terminalio.FONT,
            text="|",
            color=red,
            x=-2,  # At true left edge
            y=y*8 + 4  # Start at y=4 and space by 8
        )
        group.append(text_label)
        left_border.append(text_label)
        
    # Right border
    for y in range(4):  # 4 vertical characters
        text_label = Label(
            terminalio.FONT,
            text="|",
            color=red,
            x=61,  # At true right edge
            y=y*8 + 4  # Start at y=4 and space by 8
        )
        group.append(text_label)
        right_border.append(text_label)
    
    # Add configurable text at top - now with auto-centering
    title_label = Label(
        terminalio.FONT,
        text=DISPLAY_TEXT,
        color=white,
        x=center_text_position(DISPLAY_TEXT, terminalio.FONT),  # Auto-centered
        y=8   # Near top
    )
    group.append(title_label)
    
    # Add timer text - also centered
    timer_text = f"{COUNTDOWN_SECONDS//60:02d}:{COUNTDOWN_SECONDS%60:02d}"
    timer_label = Label(
        terminalio.FONT,
        text=timer_text,
        color=white,
        x=center_text_position(timer_text, terminalio.FONT),  # Auto-centered
        y=20   # Below title
    )
    group.append(timer_label)
    
    # Set the display's root group
    matrixportal.display.root_group = group
    print("Display updated")

    # Animation state
    animation_step = 0

    # Set initial border state
    set_dashed_border(top_border, bottom_border, left_border, right_border)

    # Countdown loop
    countdown = COUNTDOWN_SECONDS
    last_second = time.monotonic()
    
    while countdown >= 0:
        current_time = time.monotonic()
        
        # Update countdown every second
        if current_time - last_second >= 1.0:
            countdown -= 1
            last_second = current_time
            
            # Update timer display with centering
            minutes = countdown // 60
            seconds = countdown % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"
            timer_label.text = timer_text
            timer_label.x = center_text_position(timer_text, terminalio.FONT)
        
        # Animate border when countdown <= FINAL_COUNTDOWN
        if countdown <= FINAL_COUNTDOWN and countdown > 0:
            set_animated_border(animation_step, top_border, bottom_border, left_border, right_border)
            animation_step = (animation_step + 1) % 2
            time.sleep(0.2)  # Animation speed
        elif countdown > FINAL_COUNTDOWN:
            set_dashed_border(top_border, bottom_border, left_border, right_border)
            time.sleep(0.1)  # Regular update rate
            
    # After countdown, show centered "DONE" for 10 seconds
    timer_label.text = "DONE"
    timer_label.x = center_text_position("DONE", terminalio.FONT)
    set_solid_border(top_border, bottom_border, left_border, right_border)
    
    done_start = time.monotonic()
    while time.monotonic() - done_start < DONE_DISPLAY_TIME:
        time.sleep(0.1)
    
    # Change title to "STOPWATCH"
    title_label.text = STOPWATCH_TEXT
    title_label.x = center_text_position(STOPWATCH_TEXT, terminalio.FONT)
    
    # Start stopwatch
    stopwatch_start = time.monotonic()
    blink_step = 0
    last_update = stopwatch_start
    
    while True:
        current_time = time.monotonic()
        elapsed = int(current_time - stopwatch_start)
        
        # Update display every second
        if current_time - last_update >= 1.0:
            minutes = elapsed // 60
            seconds = elapsed % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"
            timer_label.text = timer_text
            timer_label.x = center_text_position(timer_text, terminalio.FONT)
            last_update = current_time
        
        # Blink border every 0.5 seconds
        set_blinking_border(blink_step, top_border, bottom_border, left_border, right_border)
        blink_step = (blink_step + 1) % 2
        time.sleep(0.5)  # Slower blink rate

except Exception as e:
    print("Error occurred:", str(e))
    time.sleep(5)
