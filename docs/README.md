# HomeMatrixBoard Documentation

## Overview
HomeMatrixBoard is a CircuitPython project for the Adafruit MatrixPortal M4, providing a versatile display system for countdowns and stopwatch functionality.

## Hardware Requirements
- Adafruit MatrixPortal M4
- 64x32 RGB LED Matrix
- USB-C power supply

## Software Requirements
- CircuitPython 9.2.3 or later
- Required libraries:
  - adafruit_matrixportal
  - adafruit_display_text
  - terminalio
  - displayio

## Features
### Display System
- 64x32 pixel resolution
- White text on black background
- Red border with animations
- Dynamic text centering

### Timer Modes
1. **Countdown Mode**
   - Displays title and remaining time
   - Final countdown animation
   - Automatic transition to stopwatch

2. **Stopwatch Mode**
   - Continuous time tracking
   - Blinking border animation
   - Clear time display

### Trigger System
- Uses JSON file for countdown initialization
- Format:
  ```json
  {
    "name": "Test Timer",
    "duration": 20
  }
  ```
- File name: `test_trigger.json`

## Usage
1. Power up the MatrixPortal M4
2. Default display shows "READY"
3. Create `test_trigger.json` to start countdown
4. Display transitions through:
   - Countdown with title
   - "DONE" message
   - Stopwatch mode

## Technical Notes
- Text centering uses 6-pixel character width
- Border animations run at different speeds:
  - Running ants: 0.2s updates
  - Blinking: 1.0s updates
- Display updates every 0.05s 