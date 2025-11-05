# LED Effects Configuration Guide

## Overview

The TX Ultimate Easy firmware includes LED effects for the Sonoff TX Ultimate's addressable LED strips. However, these effects are subject to **memory constraints** on ESP32 devices, requiring careful management and optimization.

## Current Implementation Status

### Effects Enabled On:
- **Main Light Groups** (`light_eu` and `light_us`):
  - ✅ 10 different LED effects available
  - ✅ Full effect support with save/restore functionality
  - ✅ Configurable parameters (speed, intensity, etc.)

### Effects Disabled On:
- **Individual LED Segments** (Bottom, Left, Right, Top):
  - ❌ No effects configured
  - ❌ Disabled by default to conserve memory
  - 📝 Uses `light_partition_no_effects_disabled` anchor

## Available Effect Types

When enabled, the following effects are available:

| Effect Name | Description | Key Parameters |
|-------------|-------------|----------------|
| **Rainbow** | Smooth rainbow color transition | `width` (28/32), `speed` (10/50) |
| **Pulse** | Breathing/pulsing light effect | `transition_length` (1s/2s), `update_interval` |
| **Scan** | Knight Rider style scanning | `move_interval` (100ms), `scan_width` (3) |
| **Twinkle** | Random LED twinkling | `twinkle_probability` (5%), `progress_interval` (4ms) |
| **Random Twinkle** | More intense random twinkling | `twinkle_probability` (20%), `progress_interval` (32ms) |
| **Fireworks** | Burst effects resembling fireworks | `update_interval` (32ms), `spark_probability` (10%) |
| **Flicker** | Candle-like flickering | `update_interval` (16ms), `intensity` (5%) |
| **Random** | Random color changes | Built-in ESPHome effect |

## Memory Considerations

### Why Effects Were Limited

ESP32 devices have limited RAM, and LED effects consume memory proportionally to:
1. **Number of LEDs**: More LEDs = more memory per effect
2. **Effect Complexity**: Complex effects (fireworks, twinkle) use more memory
3. **Concurrent Effects**: Running effects on multiple partitions simultaneously

### Memory Optimization Strategy

The current implementation prioritizes:
- ✅ Full effects on main light groups (most commonly used)
- ✅ Basic on/off control for individual segments
- ✅ State persistence using packed attributes (efficient storage)

## Future Roadmap

### ESPHome 2025.11.0-DEV and Beyond

Upcoming ESPHome releases are bringing **memory optimizations** that may allow:

1. **Re-enabling Effects**: Previously removed effects could be restored
2. **More Partitions with Effects**: Individual segments could gain effect support
3. **Additional Effect Types**: New effects without memory penalty

### Developer Notes

If you're considering adding effects back:

```yaml
# Add effects to individual partition by changing anchor:
- id: light_eu_bottom
  name: Light - Bottom EU
  <<: *light_partition_with_effects_eu  # Instead of no_effects
  segments:
    - id: light_full
      from: 6
      to: 12
```

⚠️ **Warning**: Test memory usage after re-enabling effects:
- Monitor heap fragmentation
- Check for crashes/reboots under load
- Verify OTA updates still work (require free heap)

## Implementation Details

### Effect State Management

Effects are saved using packed attributes:
- `led_main_packed_effect`: Stores effect index (16 bits) + speed (8 bits)
- Restored on boot via `light_effect_restore` script
- Index 0 = no effect/solid color

### File Locations

- **Main Configuration**: `ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_leds.yaml`
- **Effect Definitions**: Lines 102-204 (light_eu), Lines 165-219 (light_us)
- **No-Effect Anchor**: Line 244+ (`light_partition_no_effects_disabled`)

## Testing Checklist

When modifying effects:

- [ ] Compile and check memory usage in logs
- [ ] Test all effects individually
- [ ] Verify state persistence across reboots
- [ ] Test OTA updates with effects running
- [ ] Monitor for memory leaks over extended runtime
- [ ] Test with concurrent operations (audio, BLE proxy, etc.)

## Related Issues

- Memory constraints affecting feature set
- Balancing features vs. stability
- ESPHome framework optimizations pending

## References

- [ESPHome Light Effects](https://esphome.io/components/light/index.html#light-effects)
- [ESP32 Memory Management](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/memory-types.html)
- Project Version: 2025.10.1