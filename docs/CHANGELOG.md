# Changelog

All notable changes to the HomeMatrixBoard project will be documented in this file.

## [0.0.1-build.2] - 2024-01-17

### Optimized
- Text position calculation now uses caching
- Position only recalculated when text length changes
- Reduced CPU usage for timer updates

## [0.0.1-build.1] - 2024-01-17

### Added
- Initial implementation of MatrixPortal M4 display controller
- Text display system with dynamic centering
- Border animations (dashed, animated, blinking)
- Countdown timer functionality
- Automatic transition to stopwatch mode
- JSON-based trigger system for starting countdowns

### Features
- Display centered text for titles and timers
- Red border with multiple animation modes:
  - Dashed border (default)
  - Animated "running ants" during final countdown
  - Blinking border during stopwatch mode
- Countdown timer with minutes:seconds display
- "DONE" display with automatic transition to stopwatch
- Stopwatch mode with continuous time tracking

### Technical Details
- Uses CircuitPython with MatrixPortal library
- 64x32 LED matrix display support
- Text centering using 6-pixel character width
- Modular design with separate managers for:
  - Display text
  - Border animations
  - Timer functionality 