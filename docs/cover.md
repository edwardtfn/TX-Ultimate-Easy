# Cover

Two relays can drive a motorized cover (roller shutter, blind, curtain, awning, etc.) with one relay per direction.
The cover is exposed to Home Assistant as a native `cover` entity and can also be controlled locally from the
touch panel, so it keeps working when Wi-Fi or Home Assistant is unavailable.

The position is time-based (ESPHome [Time Based Cover](https://esphome.io/components/cover/time_based/)),
as the device has no way to measure the real cover position.

> [!WARNING]
> Energizing both directions of a cover motor at the same time can damage the motor.
> This package enforces a software interlock, but it cannot protect against wiring mistakes
> and does not replace a hardware interlock where the motor manufacturer requires one.

## Requirements

- A 2, 3 or 4-gang device (1-gang devices have a single relay and are not supported).
- The `TX-Ultimate-Easy-ESPHome_hw_relays.yaml` package (included in the standard package).
- The relays used by the cover set to `disabled`, so no switch, light or ESP-NOW command can bypass the interlock.

## Setup

1. Add the package to your device YAML and disable the relays used by the cover:

   ```yaml
   substitutions:
     relay_1_mode: disabled  # Used by the cover (open)
     relay_2_mode: disabled  # Used by the cover (close)

   packages:
     remote_package:
       url: https://github.com/edwardtfn/TX-Ultimate-Easy
       ref: main
       refresh: 5min
       files:
         - ESPHome/TX-Ultimate-Easy-ESPHome_core.yaml
         - ESPHome/TX-Ultimate-Easy-ESPHome_standard.yaml
         - ESPHome/TX-Ultimate-Easy-ESPHome_cover.yaml
   ```

2. Optionally, adjust the defaults with substitutions:

   | Substitution | Default | Description |
   | ------------ | ------- | ----------- |
   | `cover_name` | `Cover` | Name of the cover entity in Home Assistant |
   | `cover_device_class` | `shutter` | Any Home Assistant cover device class, like `blind`, `curtain`, `shutter` or `awning` |
   | `cover_open_relay` | `1` | Relay driving the "open" direction |
   | `cover_close_relay` | `2` | Relay driving the "close" direction |
   | `cover_open_duration` | `30` | Initial full travel time to open, in seconds |
   | `cover_close_duration` | `30` | Initial full travel time to close, in seconds |
   | `cover_interlock_wait_time` | `500` | Minimum time between de-energizing one direction and energizing the other, in milliseconds |
   | `cover_has_built_in_endstop` | `false` | Keep the relay energized at the end positions (see [Time Based Cover](https://esphome.io/components/cover/time_based/)) |
   | `cover_manual_control` | `false` | Always run a full travel when fully opening or closing, resyncing the estimated position |

   Invalid combinations (1-gang device, same relay for both directions, relay out of range or not `disabled`)
   are reported as errors when compiling.

3. Flash the device, then in Home Assistant:
   - Measure the time your cover takes for a full travel in each direction and set **Cover open duration** and
     **Cover close duration**. These values are stored on the device and survive reboots.
   - Set the **Button N action** of the buttons you want to use to **Cover open** or **Cover close**.

## Local control

A single click on a button set to **Cover open** or **Cover close** starts the cover in that direction.
A click on any of these buttons while the cover is moving stops it.

Double clicks, long presses, swipes and multi-touch gestures do not control the cover, and are still sent to Home Assistant as events.

## Relay LEDs

The relay LEDs show which direction is active while the cover is moving, using the same settings as regular relays.
To turn this off, set **Relay N light mode** of the cover relays to **Disabled** in Home Assistant.

## Interlock

- The relay of the opposite direction is always turned off before the requested direction is turned on.
- After a relay is turned off, the other one is only turned on once `cover_interlock_wait_time` has passed.
  This applies to direct reversals and to a stop followed by a new command.
- A stop received during this wait cancels the pending command.
- Both cover relays always start off after a boot, regardless of any previously saved state.

> [!NOTE]
> On a direction reversal, the wait time is counted as travel time, so the estimated position can drift slightly.
> A full open or close resyncs it, especially with `cover_manual_control: true`.
