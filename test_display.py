import board
import time
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal

print("Starting basic display test...")

# Release any resources currently in use for the displays
displayio.release_displays()

# Initialize the MatrixPortal
print("Initializing MatrixPortal...")
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
    bit_depth=6,
    width=64,
    height=32,
    debug=True
)

# Set background to red first to verify display is working
print("Setting background to red...")
matrixportal.set_background(0xFF0000)
time.sleep(2)

# Set background to green
print("Setting background to green...")
matrixportal.set_background(0x00FF00)
time.sleep(2)

# Set background to blue
print("Setting background to blue...")
matrixportal.set_background(0x0000FF)
time.sleep(2)

# Add some test text
print("Adding test text...")
text_area = matrixportal.add_text(
    text_position=(0, 16),
    text_font=terminalio.FONT,
    text_color=0xFFFFFF,
    text="TEST"
)

print("Basic test complete. Display should show 'TEST' in white.")
print("If you see this, the display is working correctly.")

while True:
    time.sleep(1) 