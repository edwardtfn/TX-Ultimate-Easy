# Memory Optimization Guide

## Overview

The TX Ultimate Easy firmware runs on ESP32 devices with limited memory resources. When combining multiple features (LED effects, BLE proxy, media player, etc.), you may encounter memory constraints that can cause instability or prevent the device from functioning properly.

## Current Memory Usage

### Components with Significant Memory Impact

1. **LED Effects** (High Impact)
   - Addressable effects like Rainbow, Fireworks, and Twinkle require significant memory
   - Main lights (`light_eu`/`light_us`) include 10 different effects
   - Side lights intentionally exclude effects to save memory

2. **BLE Proxy** (High Impact)
   - Bluetooth functionality requires substantial memory allocation
   - Not included by default for this reason
   - Recommended only with ESP-IDF framework

3. **Media Player** (Medium-High Impact)
   - Audio processing and buffering requires memory
   - Buffer size: 250,000 bytes
   - Uses audio resampling which adds overhead

4. **Web Server** (Medium Impact)
   - HTTP server and associated resources
   - Not included in core packages starting v2025.1.0

## Memory Optimization Strategies

### Strategy 1: Use Advanced Configuration

Use the [advanced configuration template](../TX-Ultimate-Easy-ESPHome_advanced.yaml) to selectively include only the components you need:

```yaml
packages:
  remote_package:
    url: https://github.com/edwardtfn/TX-Ultimate-Easy
    ref: main
    refresh: 5min
    files:
      # Include only essential components
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_common.yaml
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_buttons.yaml
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_leds.yaml
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_touch.yaml
      - ESPHome/TX-Ultimate-Easy-ESPHome_standard_hw_relays.yaml
      # Exclude vibration, audio, etc. if not needed
```

### Strategy 2: Disable LED Effects

If you don't use LED effects, you can create a custom LED configuration without them. In your local configuration, override the light definitions:

```yaml
# Example: Override light_eu to remove effects
light:
  - id: light_eu
    name: Light EU
    platform: partition
    default_transition_length: 500ms
    internal: true
    restore_mode: ALWAYS_OFF
    segments:
      - id: light_full
        from: 0
        to: 27
    # No effects defined = saves memory
```

### Strategy 3: Use ESP-IDF Framework

ESP-IDF generally has better memory management than Arduino framework:

```yaml
esp32:
  framework:
    type: esp-idf
    # ESP-IDF is now the default, but you can explicitly specify it
```

### Strategy 4: Monitor Memory Usage

Add logging to monitor memory during boot:

```yaml
logger:
  level: DEBUG  # or INFO
  # Watch for messages about free heap memory
```

Check the ESPHome logs during boot for messages like:
- `Free heap: XXXXX bytes`
- Memory allocation warnings or errors

## ESPHome 2025.11.0-DEV Memory Improvements

The upcoming ESPHome 2025.11.0-DEV release is expected to include memory optimizations that may allow:
- More features to coexist without memory issues
- Better memory management for LED effects
- Improved stability with BLE proxy enabled

## Troubleshooting Memory Issues

### Symptoms of Memory Problems

- Device fails to boot or crashes randomly
- OTA updates fail
- Certain features stop working intermittently
- Boot loops or watchdog resets

### Solutions

1. **Remove unnecessary components** - Use advanced configuration
2. **Disable LED effects** - If you don't use them
3. **Avoid combining BLE proxy with media player** - These are both memory-intensive
4. **Use wired (serial) flashing** - OTA can fail with low memory
5. **Monitor logs** - Watch for "out of memory" errors

## Feature Compatibility Matrix

| Feature Combination | Memory Usage | Stability | Recommended |
|-------------------|--------------|-----------|-------------|
| Core + Relays only | Low | Excellent | ✅ Yes |
| Core + Relays + Vibration | Low-Medium | Excellent | ✅ Yes |
| Core + Relays + LED Effects | Medium | Good | ✅ Yes |
| Core + Relays + Media Player | Medium-High | Good | ✅ Yes (ESP-IDF) |
| Core + Relays + BLE Proxy | Medium-High | Good | ✅ Yes (ESP-IDF) |
| Core + Media Player + LED Effects | High | Fair | ⚠️ Monitor |
| Core + BLE Proxy + LED Effects | High | Fair | ⚠️ Monitor |
| Core + BLE Proxy + Media Player | Very High | Poor | ❌ Not Recommended |
| All Features Combined | Critical | Very Poor | ❌ Not Recommended |

## Additional Resources

- [ESPHome Memory Management](https://esphome.io/guides/faq.html#memory)
- [Advanced Configuration Template](../TX-Ultimate-Easy-ESPHome_advanced.yaml)
- [Project README](../README.md)

## Contributing

If you discover memory optimizations or better configuration strategies, please consider contributing to this documentation or opening a discussion in the repository.