# Changelog

All notable changes to the HomeMatrixBoard project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-01-18

### Added
- Robust MQTT connection handling with exponential backoff
- Memory-efficient connection management
- Automatic subscription recovery
- Connection status monitoring in serial output

### Changed
- Optimized MQTT timeout configurations:
  - Socket timeout: 0.1s
  - Receive timeout: 0.2s
  - MQTT loop timeout: 0.1s
- Improved error handling and recovery
- Updated documentation with connection management details

### Fixed
- Stack exhaustion during MQTT subscription
- Connection timeout mismatches
- Memory leaks in connection handling
- Unreliable reconnection behavior

## [1.0.0] - 2024-01-17

### Added
- Preset display system with multiple modes:
  - "On Air" preset with radio symbol
  - "Score" preset with animated border
  - "Breaking" preset with blinking border
- Custom text and duration support for presets
- Dynamic border animations
- Radio symbol for "On Air" preset

### Changed
- Improved text positioning system
- Enhanced border animation handling
- Better display state management

## [0.2.0] - 2024-01-17

### Added
- MQTT integration with broker
- Topic-based message routing
- Secure authentication
- Access control for displays
- Webhook integration
- Display-specific topics

### Changed
- Moved to MQTT-based communication
- Enhanced security with ACL
- Improved message handling

## [0.1.0] - 2024-01-17

### Added
- Initial implementation of MatrixPortal M4 display controller
- Basic countdown timer functionality
- Text display with centering
- Border animations:
  - Solid border
  - Dashed border
  - Animated "running ants"
  - Blinking mode
- Automatic stopwatch mode after countdown
- JSON-based configuration

### Technical Features
- CircuitPython implementation
- 64x32 LED matrix support
- Modular design with managers:
  - DisplayText
  - BorderManager
  - TimerManager
  - PresetManager 