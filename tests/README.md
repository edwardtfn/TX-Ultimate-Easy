# TX Ultimate Easy - Standalone QEMU Integration Test Suite

This automated integration test suite runs completely standalone without any agent
driving it. It verifies the firmware using standard `pytest` directly against
**Espressif QEMU ESP32** hardware emulation before flashing physical devices.

All tests run against 100% stock upstream YAML configurations in `ESPHome/`.

---

## Standalone Design & Toolchain Discovery

The test suite is fully self-contained within the repository and automatically manages:

1. **Toolchain Auto-Discovery**:
   - **QEMU (`qemu-system-xtensa`)**: Searches `QEMU_BIN` / `QEMU_SYSTEM_XTENSA` environment
     variables, system `PATH`, and standard Espressif tool directories (`~/.espressif/tools/qemu-xtensa/`).
   - **ESPHome CLI**: Searches `ESPHOME_BIN` environment variable, active Python virtualenv,
     and system `PATH`.
   - **Dummy EFUSE**: Automatically checked and created in `tests/configs/qemu_efuse.bin` if
     missing on a clean clone.

2. **Automated Multi-Target Builds & Flash Caching**:
   - Compiles three isolated firmware targets to local temporary storage (preventing network locks):
     - `test_standard.yaml`: Core + Relays + LEDs + Touchpad + Vibration + Night Mode.
     - `test_instant.yaml`: Core + Relays + LEDs + Touchpad + Vibration +
       **Instant Click Mode** (`instant_click_mode: true`).
     - `test_light.yaml`: Mixed Gang Presentation (`relay_1_mode: switch`, `relay_2_mode: light`).
   - Pads the factory binaries into 8MB raw flash images.
   - Recompiles only when source configuration files change, or when `--compile` is passed.

3. **Multi-QEMU Session Isolation**:
   - Standard firmware runs on ports `4444` (UART0 logs), `4445` (UART1 touch), and `6053` (API).
   - Instant Click firmware runs on ports `4446` (UART0 logs), `4447` (UART1 touch), and `6054` (API).
   - Light Relay Mode runs on ports `4448` (UART0 logs), `4449` (UART1 touch), and `6056` (API).
   - Instant session abort (`pytest.exit`) and automatic process termination cleanup if boot times out.

---

## Test Modules & Expected Behavioral Coverage (71 Automated Tests)

The test suite is partitioned into 11 focused test modules:

1. **`tests/test_button_actions.py` (7 Tests)**:
   - Button action modes: `Toggle`, `None`, and `Failsafe`.
   - Decoupled smart bulb mode: physical tap emits HA event without relay toggle,
     remote HA toggle commands relay with LED coherence.
   - API disconnect failsafe: fallback to local relay toggle when Home Assistant connection drops.
   - Rapid cross-gang taps (`TC-BA04`): rapid taps on Gang 1 then Gang 2 must fire click actions for both gangs.
   - Hardware long-touch release (`TC-BA05`): hardware release code `x >= 17` must trigger button long press action.

2. **`tests/test_gestures.py` (12 Tests)**:
   - Single clicks across all gangs.
   - Double-click detection with inter-tap gap verification.
   - Multi-click gap timeout (ensures clicks separated by >250ms register as separate single clicks).
   - Triple click registering `multiple_click` action with count=3.
   - Realistic Swipe Right and Swipe Left with initial touch-down click suppression.
   - Palm Mash / Multi-Touch (`0x01, 0x0B`) contact suppression.
   - Stale press recovery and partial swipe / intra-gang drag handling.
   - Multi-click window boundary timing.

3. **`tests/test_ha_coherence.py` (4 Tests)**:
   - Remote Home Assistant relay commands synchronizing physical gang LEDs.
   - Simultaneous physical touch and remote API toggle race condition handling.
   - Ambient swipe transitions during active mood lighting.
   - `Lights (all)` override coherence (`TC-HA04`): ambient mood lighting must override relay indicators
     without black hole punch-throughs when individual relays toggle.

4. **`tests/test_led_indication.py` (8 Tests)**:
   - Gang LED indicator modes: `Bottom`, `Top`, `Both`, and `Off`.
   - Active-to-active mode transitions (`TC-L05`): switching from `Both` to `Bottom` must clear the Top LED.
   - Multi-gang LED clearing (`TC-L06`): toggling Relay 3 OFF must extinguish all assigned LED groups.
   - First mode change post-boot (`TC-L07`): changing light mode immediately after boot applies without dropped frames.
   - Side light turn-off restoration (`TC-L08`): turning off ambient side partitions must restore active relay indicators.

5. **`tests/test_relay_modes.py` (4 Tests)**:
   - Entity domain separation: `switch.relay_1` vs `light.light_output_2`.
   - Remote Home Assistant `light.turn_on` and `light.turn_off` commands controlling relay GPIO.
   - Physical touch press on light-configured gang toggling the light entity via internal switch cascade.
   - Inching pulse time exclusion: pulse number entities are strictly excluded for light-mode gangs.

6. **`tests/test_timing_pulse.py` (9 Tests)**:
   - Touch press duration measurement and logging accuracy.
   - Long press duration threshold and touch timeout cancellation.
   - Relay inching / pulse timer auto-off.
   - Inching cancellation on manual turn-off or pulse time disabled (`TC-TP06`).
   - Inching rearm when already ON (`TC-TP07`): commanding `turn_on` on active relay must arm auto-off.
   - Inching triggered and cancelled by physical taps.

7. **`tests/test_night_mode.py` (4 Tests)**:
   - Night mode activation suppressing relay LED updates during quiet hours.
   - Disabling Night Mode evaluating and restoring relay status indicators (`show_relay_status`).
   - Night mode sound suppression toggle.
   - Gestures and palm mash handling during active Night Mode.

8. **`tests/test_persistence.py` (5 Tests)**:
   - Button action configuration persistence across hard reboots.
   - Relay LED indicator mode persistence across hard reboots.
   - Relay default power-on safety (`RESTORE_DEFAULT_OFF`).
   - Boot deferred LED repaint sequence.
   - Relay state restoration across reboot per `RESTORE_DEFAULT_OFF` policy.

9. **`tests/test_haptics.py` (6 Tests)**:
   - Touch vibration feedback on press and release.
   - Vibration modes: `Always`, `Only when turned on`, and `Disabled`.
   - Night mode vibration suppression.
   - Multi-touch vibration triggering.
   - Vibration motor retrigger recovery (`TC-H06`): prompt turn-off without hanging when entering Night Mode.

10. **`tests/test_instant_click.py` (10 Tests)**:
    - Tests dedicated `instant_click_mode: true` firmware build.
    - Click action and relay toggle firing immediately on touch-down (`PRESS`) before finger release.
    - Long press and double-click suppression in instant click mode.
    - Rapid-fire dead zone per-gang debounce (500ms).
    - Multi-gang concurrent independent debounce.
    - Swipes, palm touches, partial drags, and hardware long touches in instant click mode.

11. **`tests/test_fuzzing.py` (6 Tests)**:
    - Truncated UART frames and corrupted sync headers.
    - Out-of-bounds position bytes and rapid FIFO flood handling without crashes.
    - Chunked touch packets across loop ticks (`TC-F05`): split packets must buffer and register a valid press.
    - Payload handling (`TC-F06`): payload bytes containing 0xAA must parse safely without false header reset.

---

## How to Run

From the repository root:

### Windows Batch:
```cmd
run_tests.cmd
```

### Python (Cross-Platform):
```bash
# Run all tests
python run_tests.py

# Force re-compilation of firmware targets
python run_tests.py --compile

# Run a specific test suite or test filter
python run_tests.py -k test_gestures
python run_tests.py -k test_relay_modes
python run_tests.py -k test_ha_coherence
```

### Raw Pytest:
```bash
pytest
```
