# TX Ultimate Easy - Standalone QEMU Integration Test Suite

This automated integration test suite runs completely standalone without any agent
driving it. It verifies the firmware using standard `pytest` directly against
**Espressif QEMU ESP32** hardware emulation before flashing physical devices.

All tests build the unmodified YAML packages in `ESPHome/` and `components/`. The wrapper configurations in
`tests/configs/` only adapt them to the emulator: they remove `wifi` in favour of the `OPENETH` Ethernet
emulation, move the touch UART to the emulated pins, and stub the RMT LED driver calls (`qemu_stubs.h`).
They also raise `BUTTON_LONG_PRESS_DELAY` from 500 ms to 2000 ms: emulator timing jitter has measured 50 ms taps
as ~900 ms presses, so the default threshold turned taps into long presses. The tests take the threshold and the
long-press hold from `LONG_PRESS_DELAY_MS` and `LONG_PRESS_HOLD_MS` in `tests/qemu_harness.py`.

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
   - Compiles five isolated firmware targets to local temporary storage (preventing network locks):
     - `test_standard.yaml`: Core (Buttons + LEDs + Touchpad) + Relays + Vibration + Night Mode.
     - `test_instant.yaml`: Core (Buttons + LEDs + Touchpad) + Relays +
       **Instant Click Mode** (`instant_click_mode: true`).
     - `test_light.yaml`: Mixed Gang Presentation (`relay_1_mode: switch`, `relay_2_mode: light`).
     - `test_cover.yaml`: Core + Relays + Cover (relays 1 and 2 drive the cover, relay 3 is a regular relay).
     - `test_nvs_small.yaml`: The standard build with a small (20 KB) NVS partition (`nvs_small_partitions.csv`)
       and a `test_nvs_fill` API action that fills it with dummy settings.
   - Pads the factory binaries into 8MB raw flash images.
   - Recompiles only when the content of a source file (`ESPHome/`, `components/`, `versioning/`,
     the test configuration, stubs or partition table) or the ESPHome compiler changes, or when `--compile` is passed. The flash images are recreated from the factory
     binaries on every run, so each session starts with a clean flash.

3. **Multi-QEMU Session Isolation**:
   - Standard firmware runs on ports `4444` (UART0 logs), `4445` (UART1 touch), and `6053` (API).
   - Instant Click firmware runs on ports `4446` (UART0 logs), `4447` (UART1 touch), and `6054` (API).
   - Light Relay Mode runs on ports `4448` (UART0 logs), `4449` (UART1 touch), and `6056` (API).
   - Cover firmware runs on ports `4450` (UART0 logs), `4451` (UART1 touch), and `6058` (API).
   - Small NVS firmware runs on ports `4452` (UART0 logs), `4453` (UART1 touch), and `6060` (API).
   - The standard emulator runs for the whole session. The Instant Click, Light Relay Mode, Cover and Small NVS
     emulators run only during their own module (`test_instant_click.py`, `test_relay_modes.py`, `test_cover.py`,
     `test_nvs.py`), so at most two run at once.
   - Instant session abort (`pytest.exit`) and automatic process termination cleanup if boot times out.

---

## Test Modules & Expected Behavioral Coverage (96 Collected Tests)

The test suite is partitioned into 13 focused test modules:

1. **`tests/test_button_actions.py` (12 Tests)**:
   - Button action modes: `Toggle`, `None`, and `Failsafe`.
   - Decoupled smart bulb mode: physical tap emits HA event without relay toggle,
     remote HA toggle commands relay with LED coherence.
   - API disconnect failsafe: fallback to local relay toggle when Home Assistant connection drops.
   - Rapid cross-gang taps (`TC-BA04`): rapid taps on Gang 1 then Gang 2 must fire click actions for both gangs.
   - Hardware long-touch release (`TC-BA05`): hardware release code `x >= 17` must trigger button long press action.
   - Momentary action (`TC-BA08` to `TC-BA11`): the relay is on while the button is held and off on any end of the
     touch (release, long-touch release, swipe, multi-touch, or the touch moving to another button).
   - Momentary hold limit (`TC-BA12`): a momentary relay is released when its release frame never arrives.

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

7. **`tests/test_night_mode.py` (7 Tests)**:
   - Night mode activation suppressing relay LED updates during quiet hours.
   - Disabling Night Mode evaluating and restoring relay status indicators (`show_relay_status`).
   - Night mode sound suppression toggle.
   - Gestures and palm mash handling during active Night Mode.
   - Relay LEDs shown over the Night Mode color (`TC-NM07`) when `Night Mode - Suppress Relay LEDs` is off,
     suppressed again when it is turned back on (`TC-NM08`), and never painted over `Lights (all)` (`TC-NM09`).

8. **`tests/test_persistence.py` (6 Tests)**:
   - Button action configuration persistence across hard reboots.
   - Relay LED indicator mode persistence across hard reboots.
   - Relay default power-on safety (`RESTORE_DEFAULT_OFF`).
   - Boot deferred LED repaint sequence.
   - Relay state restoration across reboot per `RESTORE_DEFAULT_OFF` policy.
   - Momentary button action persistence, with its relay turned off after the reboot (`TC-P06`).

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

11. **`tests/test_fuzzing.py` (7 Tests)**:
    - Truncated UART frames and corrupted sync headers.
    - Out-of-bounds position bytes and rapid FIFO flood handling without crashes.
    - Chunked touch packets across loop ticks (`TC-F05`): split packets must buffer and register a valid press.
    - Payload handling (`TC-F06`): payload bytes containing 0xAA must parse safely without false header reset.
    - Chunked release packets (`TC-F07`): a split release must still release the button.

12. **`tests/test_cover.py` (7 Tests)**:
    - Tests dedicated cover firmware build (`TX-Ultimate-Easy-ESPHome_cover.yaml`).
    - Entity exposure: the cover and its travel times are exposed, the cover relays are not.
    - Full open and close energizing only the relay of the requested direction.
    - Direction reversal (`TC-CV03`): the active relay must turn off before the opposite one turns on.
    - Stop from Home Assistant and from the buttons (`Cover open` / `Cover close` button actions).
    - A relay not used by the cover keeps working as a regular relay.
    - Cover button actions persist across reboot (`TC-CV07`), as their NVS codes differ from their select indexes.

13. **`tests/test_nvs.py` (4 Tests)**:
    - NVS partition size and entry usage reported in the config dump (`TC-N01`).
    - NVS usage within budget once every setting is written (`TC-N02`): derived lights must not be saved.
    - Small NVS build reports its 20 KB partition (`TC-N03`).
    - Full NVS (`TC-N04`): the failed write is logged, relays keep working, and the device still boots.

---

## How to Run

From the repository root:

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

### Raw Pytest

```bash
pytest
```
