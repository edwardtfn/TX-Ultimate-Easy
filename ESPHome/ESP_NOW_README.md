# ESP-NOW Communication for TX Ultimate Easy

This feature enables direct communication between multiple TX Ultimate Easy switches using ESP-NOW, allowing switches to control relays on other switches without going through Home Assistant.

## Overview

- **ESP-NOW Communication**: Switches communicate directly via ESP-NOW (peer-to-peer)
- **Runtime Control**: ESP-NOW works independently of Home Assistant - switches can communicate even if Home Assistant is offline
- **Flexible Mapping**: Each button can be configured to toggle any relay on any target switch
- **Fallback Behavior**: If ESP-NOW is not configured for a button, it falls back to local relay control

## Setup Instructions

### 1. Include ESP-NOW Package

Add the ESP-NOW package to your device configuration:

```yaml
packages:
  remote_package:
    url: https://github.com/edwardtfn/TX-Ultimate-Easy
    ref: stable
    refresh: 5min
    files:
      - ESPHome/TX-Ultimate-Easy-ESPHome_core.yaml
      - ESPHome/TX-Ultimate-Easy-ESPHome_standard.yaml
      - ESPHome/TX-Ultimate-Easy-ESPHome_espnow.yaml # Add this line
```

### 2. Flash Configuration to All Switches

Flash the updated configuration to all switches via Home Assistant.

### 3. Find MAC Addresses

For each switch, note its MAC address:

- In Home Assistant, check the **"ESP-NOW MAC Address"** text sensor
- Or check the device information in Home Assistant

### 4. Configure Each Switch

For each switch, configure which relay each button should toggle by adding substitutions to your `device.yaml` file:

```yaml
substitutions:
  # ... other substitutions ...

  # ESP-NOW target configuration per button
  espnow_target_mac_button_1: "AA:BB:CC:DD:EE:FF" # Target device MAC address
  espnow_target_relay_button_1: 1 # Relay number to toggle (1-4)
  espnow_target_mac_button_2: "00:00:00:00:00:00" # Set to all zeros to disable
  espnow_target_relay_button_2: 1
  espnow_target_mac_button_3: "00:00:00:00:00:00"
  espnow_target_relay_button_3: 1
  espnow_target_mac_button_4: "00:00:00:00:00:00"
  espnow_target_relay_button_4: 1
```

**Configuration Notes**:

- **MAC Address Format**: `AA:BB:CC:DD:EE:FF` (uppercase or lowercase, with colons)
- **Relay Number**: Integer from 1 to 4
- **Disable Button**: Set MAC address to `00:00:00:00:00:00` to disable ESP-NOW for that button (falls back to local relay)
- **Per-Button Configuration**: Each button (1-4) can target a different device and relay

**Example Configuration**:

- Switch 1, Button 1 → Target MAC: Switch 2's MAC, Target Relay: 1
- Switch 1, Button 2 → Target MAC: Switch 3's MAC, Target Relay: 2
- Switch 2, Button 1 → Target MAC: Switch 1's MAC, Target Relay: 1

### 5. Enable ESP-NOW

After flashing, enable ESP-NOW in Home Assistant:

- **"ESP-NOW Send Enabled"**: Enable/disable sending ESP-NOW messages
- **"ESP-NOW Receive Enabled"**: Enable/disable receiving ESP-NOW messages

### 6. Test

Press a button on one switch. The configured relay on the target switch should toggle.

## Configuration Entities

### Switches

- **ESP-NOW Send Enabled**: Enable/disable sending ESP-NOW messages when buttons are pressed
- **ESP-NOW Receive Enabled**: Enable/disable receiving ESP-NOW messages to toggle local relays

### Text Sensors (Read-only)

- **ESP-NOW MAC Address**: Shows this device's MAC address (for sharing with other devices)

## How It Works

1. **Button Press**: When a button is pressed on a switch
2. **ESP-NOW Check**: The system checks if ESP-NOW sending is enabled and a target MAC is configured for that button
3. **Send Command**: If configured, sends an ESP-NOW message to the target device with:
   - Command: `0x01` (toggle)
   - Relay number: 1-4 (from button configuration)
4. **Receive Command**: The target device receives the ESP-NOW message (if receiving is enabled)
5. **Toggle Relay**: The target device toggles the specified relay

## Message Format

ESP-NOW messages use a simple 2-byte format:

- Byte 0: Command (`0x01` = toggle relay)
- Byte 1: Relay number (1-4)

## Troubleshooting

### Button doesn't toggle remote relay

1. Check that **"ESP-NOW Send Enabled"** is ON
2. Verify the target MAC address is correct in `device.yaml` (check "ESP-NOW MAC Address" on target device)
3. Check that the MAC address format is correct: `AA:BB:CC:DD:EE:FF`
4. Verify the MAC address is not `00:00:00:00:00:00` (which disables ESP-NOW for that button)
5. Check device logs for ESP-NOW send/receive messages
6. Recompile and flash the device after changing configuration

### Button toggles local relay instead

- This is the fallback behavior when ESP-NOW is not configured for that button
- Make sure the target MAC address is not `00:00:00:00:00:00` in `device.yaml`
- Verify **"ESP-NOW Send Enabled"** is ON
- Recompile and flash after changing configuration

### ESP-NOW messages not received

1. Check that **"ESP-NOW Receive Enabled"** is ON on the target device
2. Ensure all devices are on the same WiFi network (ESP-NOW works over WiFi)
3. Check that devices are within range
4. Verify the MAC address is correct in the sender's `device.yaml`
5. Check device logs for receive errors

### Configuration changes not taking effect

- Configuration is done via substitutions in `device.yaml`, not through Home Assistant UI
- After changing `device.yaml`, you must recompile and flash the device
- The configuration is compiled into the firmware, so changes require a new build

## Notes

- ESP-NOW works independently of Home Assistant - switches can communicate even if Home Assistant is offline
- Configuration is done via substitutions in `device.yaml` and requires recompiling/flashing
- Each button can be configured independently with its own target MAC and relay number
- If a target MAC is set to `00:00:00:00:00:00`, the button will toggle the local relay (original behavior)
- Sending and receiving can be enabled/disabled independently via Home Assistant switches
