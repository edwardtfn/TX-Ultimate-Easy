# TX Ultimate Easy

[![Version][version-shield]](https://github.com/edwardtfn/TX-Ultimate-Easy/tags)
[![GitHub Activity][commits-shield]](https://github.com/edwardtfn/TX-Ultimate-Easy/commits/main)
[![License][license-shield]](LICENSE)
[![GitHub Last Commit][last-commit-shield]](https://github.com/edwardtfn/TX-Ultimate-Easy/commits/main)
[![ESPHome][esphome-shield]](https://esphome.io/)
[![Discord][discord-shield]](https://discord.gg/Db6WJWzWuf)
[![Buy me an ice-cream][buymeacoffee-shield]](https://www.buymeacoffee.com/edwardfirmo)

<!-- markdownlint-disable MD013 MD033 -->
| &nbsp;<picture><source media="(prefers-color-scheme: dark)" srcset="Assets/Logo_dark.png"><source media="(prefers-color-scheme: light)" srcset="Assets/Logo_light.png"><img alt="TX Ultimate Easy Logo" src="Assets/Logo_light.png"></picture> | TX Ultimate Easy provides custom ESPHome firmware for Sonoff TX Ultimate devices. Our project focuses on user-friendly configuration through the Home Assistant UI, eliminating the need for manual YAML editing. Whether you're new to home automation or an experienced user, TX Ultimate Easy makes it simple to manage your device. |
| --- | :-- |
<!-- markdownlint-enable MD013 MD033 -->

[version-shield]: https://img.shields.io/github/v/tag/edwardtfn/TX-Ultimate-Easy?label=version
[version]: https://github.com/edwardtfn/TX-Ultimate-Easy/tags
[commits-shield]: https://img.shields.io/github/commit-activity/y/edwardtfn/TX-Ultimate-Easy
[commits]: https://github.com/edwardtfn/TX-Ultimate-Easy/commits/main
[license-shield]: https://img.shields.io/github/license/edwardtfn/TX-Ultimate-Easy
[license]: LICENSE
[last-commit-shield]: https://img.shields.io/github/last-commit/edwardtfn/TX-Ultimate-Easy
[esphome-shield]: https://img.shields.io/badge/powered%20by-ESPHome-blue
[esphome]: https://esphome.io/
[discord-shield]: https://img.shields.io/discord/1243652421692031016?logo=discord
[discord]: https://discord.gg/Db6WJWzWuf
[buymeacoffee-shield]: https://img.shields.io/static/v1?label=Buy%20me%20an%20ice%20cream&message=❄&color=blue
[buymeacoffee]: https://www.buymeacoffee.com/edwardfirmo

> [!WARNING]
> ESPHome builder v2025.8.0+ is required

## Framework Migration to ESP-IDF

> [!IMPORTANT]  
> **ESP-IDF Framework Migration**
> 
> Starting with version **2025.8.0**, TX Ultimate Easy will use **ESP-IDF** as the default framework, following ESPHome's direction towards ESP-IDF for better performance, stability, and feature support.
> 
> **What this means for you:**
> - **New installations**: Will automatically use ESP-IDF (no action required)
> - **Existing Arduino users**: Can continue using Arduino but with limited support
> - **Migration recommended**: For better performance and full feature support
> 
> **Arduino Framework Support:**
> - Still functional but **no longer actively tested**
> - **Limited support** will be provided for Arduino-specific issues
> - May miss out on new features optimized for ESP-IDF

### Migration Guidelines

#### For New Users
No action required - ESP-IDF will be used automatically.

#### For Existing Arduino Users

**Option 1: Migrate to ESP-IDF (Recommended)**
1. **Best practice**: Flash via serial/USB to ensure proper partition setup
2. **Alternative**: If serial flashing isn't possible, flash OTA twice consecutively to improve success rate

**Option 2: Continue with Arduino**
Add this to your YAML configuration to force Arduino framework:
```yaml
esp32:
  framework:
    type: arduino
```

> [!WARNING]  
> **Migration via OTA:** When switching frameworks via OTA, the partition table may not update correctly. Flash twice in succession to ensure both firmware partitions contain the latest firmware and prevent boot failures.

## Integration with Home Assistant

TX Ultimate Easy exposes your device's components (sensors, touch panel, relays, etc.) to Home Assistant,
allowing you to:

- Monitor sensor states and values
- Control device components through the Home Assistant UI
- Use device triggers and states in your Home Assistant automations and scripts
- Configure device behavior through Home Assistant's service calls

All automation capabilities are handled through Home Assistant's
native automation system - this project focuses on providing reliable
device integration rather than implementing its own automation tools.

### Event-Based Automation

TX Ultimate Easy uses Home Assistant's native Events system for reliable automation triggers.
While sensors show the current state (e.g., button pressed/not pressed),
events capture-specific actions like clicks, swipes, and long presses.

For more details, please refer to our **[Events docs](docs/events.md)**.

### Device Configuration
#### Relay Modes
- **Light Mode**: Exposes the relay as a light entity with brightness controls (if supported)
- **Switch Mode**: Exposes the relay as a simple on/off switch entity

#### Button Actions
- **None**: Allows using button events for custom automations
  Example: Trigger scenes or complex automations through Home Assistant
- **Relay Toggle**: Direct control of the associated relay
  Example: Toggle relay state with each press, independent of Home Assistant

#### Automation
All device behaviors can be customized through Home Assistant automations without relying on local device triggers.

## Key Features

- **Home Assistant UI Configuration**: Manage all device settings directly through the Home Assistant interface
- **Zero YAML Knowledge Required**: After initial setup, no manual YAML editing needed
- **Flexible Light Control**: Customize LED behavior and effects
- **Touch Panel Support**: Full support for touch gestures and multi-touch capabilities
- **Advanced Automations**: Create complex automations using Home Assistant's powerful automation engine
- **Bluetooth Proxy Support**: Compatible with ESPHome's bluetooth_proxy component for BLE device integration
- **Audio Feedback**: Built-in speaker support for audible feedback
- **Haptic Feedback**: Vibration motor support for tactile feedback
- **ESP-IDF Framework**: Enhanced performance and stability with ESP-IDF support

## Hardware Support

- Compatible with all Sonoff TX Ultimate variants:
  - EU format (Square, T5-xC-86)
  - US format (Rectangle, T5-xC-120)
  - 1/2/3/4 gang versions

## Prerequisites

Before getting started, ensure you have:

1. A Sonoff TX Ultimate device
2. Home Assistant installation
3. ESPHome add-on installed in Home Assistant
4. Basic knowledge of Home Assistant

## Installation

Follow these steps to get your TX Ultimate device up and running with ESPHome.

### ESPHome Integration Setup

1. Install the ESPHome add-on in Home Assistant if not already installed:
   - Go to Settings → Add-ons → Add-on Store
   - Search for "ESPHome" 
   - Click Install
2. Start the ESPHome add-on and verify it's running
3. Access ESPHome dashboard through Home Assistant

### Setup Device

1. In the ESPHome dashboard, click "+ New Device"
2. Name your device (e.g., "tx-ultimate-living-room")
3. Select ESP32 as your device type
4. Copy this basic configuration to your new device:
   ```yaml
   substitutions:
     name: tx-ultimate-easy
     friendly_name: TX Ultimate Easy

   wifi:
     ssid: !secret wifi_ssid
     password: !secret wifi_password

   packages:
     remote_package:
       url: https://github.com/edwardtfn/TX-Ultimate-Easy
       ref: main  # Or you can specify a version, like `ref: v2024.12.6` or `ref: latest`
       refresh: 5min
       files:
         - ESPHome/TX-Ultimate-Easy-ESPHome_core.yaml      # Core (essential) packages
         - ESPHome/TX-Ultimate-Easy-ESPHome_standard.yaml  # Non-essential, but recommended packages
   ```
   You can also use a specific version tag for better control over updates:
   ```yaml
   ref: v2024.12.2  # Using specific version for controlled updates
   ```
    **Notes:**
      - [Click here](https://github.com/edwardtfn/TX-Ultimate-Easy/tags) for a full list of versions available.
      - [Click here](TX-Ultimate-Easy-ESPHome.yaml)
        for the latest version of this yaml.
5. Click "Save" and then "Install"

> [!IMPORTANT]  
> Starting from version 2025.1.0, non-essential components like `web_server`, `captive_portal`, and `wifi`
> are no longer included in the core package. If you need these components,
> you must add them manually to your local configuration file.
> For example:
> ```yaml
> # Add these to your configuration if needed
> web_server:
> captive_portal:
> wifi:
>   ap: # Access point configuration
> ```

### Optional Features

#### Bluetooth Proxy
TX Ultimate Easy is fully compatible with ESPHome's `bluetooth_proxy` component.
To enable Bluetooth proxy functionality, add the following to your device configuration:

```yaml
bluetooth_proxy:
  # Optional: Configure specific settings
  # active: true
```

**Requirements for Bluetooth Proxy:**
- ESP-IDF framework (default framework, not recommended with Arduino framework)
- Sufficient memory (TX Ultimate Easy components are compatible,
  but adding additional custom components may require memory optimization)

> [!NOTE]
> Bluetooth proxy functionality is provided by ESPHome's native component.
> TX Ultimate Easy ensures compatibility but does not include it by default to maintain optimal memory usage.

### Advanced Settings
For more granular control over components,
you can use our [advanced configuration template](TX-Ultimate-Easy-ESPHome_advanced.yaml).
This template allows you to selectively include specific packages, which can be useful for:

- Troubleshooting specific components
- Reducing memory usage by excluding unused features
- Customizing functionality for specific use cases

Here's an example of the advanced configuration:
```yaml
packages:
  remote_package:
    url: https://github.com/edwardtfn/TX-Ultimate-Easy
    ref: main  # Or you can specify a version, like `ref: v2024.12.6` or `ref: latest`
    refresh: 5min
    files:
      # Core (essential) packages
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_common.yaml            # Basic shared settings
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_buttons.yaml        # Button logic
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_leds.yaml           # LED configuration
      - ESPHome/TX-Ultimate-Easy-ESPHome_core_hw_touch.yaml          # Touch panel support

      # Optional but recommended packages
      - ESPHome/TX-Ultimate-Easy-ESPHome_standard_hw_relays.yaml     # Relay control
      - ESPHome/TX-Ultimate-Easy-ESPHome_standard_hw_vibration.yaml  # Haptic feedback

      # Audio options (use none or choose only one - using both will fail)
      - ESPHome/TX-Ultimate-Easy-ESPHome_standard_media_player.yaml  # Media player (Recommended for most users)
      # - ESPHome/TX-Ultimate-Easy-ESPHome_standard_hw_speaker.yaml  # Basic speaker

# Optional: Add Bluetooth proxy support
bluetooth_proxy:
```

> [!NOTE]
> Use the advanced configuration with caution. Excluding core packages may cause instability or reduced functionality.

### Device Flashing

Initial flashing must be done via serial connection.
We recommend using [ESPHome Web](https://web.esphome.io) for the simplest experience.

<!-- markdownlint-disable MD028 -->
> [!IMPORTANT]  
> **SAFETY WARNINGS**
> - ALWAYS disconnect the device from mains power before opening
> - NEVER work on the device while connected to mains power
> - Ensure the device is completely powered off before making any connections
> - Keep your workspace clean, dry, and static-free
> - Use proper insulated tools when working with electronics
> - If unsure about any step, seek help from an experienced person

> [!CAUTION]
>⚡ **CRITICAL: VOLTAGE WARNING**
> Using a UART adapter with voltage higher than 3.3V WILL DAMAGE YOUR DEVICE.
> Double-check your adapter's voltage before connecting - many common FTDI adapters
> default to 5V which will permanently damage the ESP32 chip.
<!-- markdownlint-enable MD028 -->

#### Required Hardware
- USB-to-UART adapter:
  - 3.3V logic level ONLY (DO NOT use 5V adapters)
  - Must be capable of supplying at least 500mA
  - Common adapters: CP2102, CH340, FTDI (ensure 3.3V setting)
- Small Phillips screwdriver
- 5 wires for connections (including one for BOOT to GND)

#### Flashing Process
1. Open your TX Ultimate device carefully
2. Locate the programming header pins
3. Connect your USB-to-UART adapter:

   | Adapter | Device |
   |---------|--------|
   | GND     | GND    |
   | 3.3V    | 3.3V   |
   | TX      | RX     |
   | RX      | TX     |

4. Put device in flash mode:
   - Temporarily connect the BOOT pin to GND using a jumper wire
   - While holding BOOT to GND, power up the device
   - After device powers up (wait a couple of seconds), remove the BOOT to GND connection
5. Visit [ESPHome Web](https://web.esphome.io)
6. Connect to your device and flash the firmware
7. After successful flash, device will restart and be ready for OTA updates

#### Detailed Visual Guides
<!-- markdownlint-disable MD013 -->
For step-by-step visual instructions, you can reference these existing guides:
- 🇬🇧 [WirelessThings Guide](https://wirelessthings.io/index.php/2023/12/19/how-to-flash-sonoff-tx-ultimate-with-esphome/) - English guide with detailed photos
- 🇪🇸 [Un loco y su tecnología](https://youtu.be/58v8oqSQgXQ?t=143) - Spanish video tutorial
- 🇩🇪 [SmartHome yourself](https://youtu.be/naDLhX89enQ?t=465) - German video tutorial
<!-- markdownlint-enable MD013 -->

Note: While these guides may use different firmware, the physical flashing process remains the same.

#### Subsequent Updates
After initial flashing, all future updates can be done wirelessly (OTA)
through the ESPHome dashboard in your ESPHome add-on.

### Home Assistant Integration

After successful flashing:
1. Ensure your device and Home Assistant are on the same network
2. Device should be automatically discovered within 1–2 minutes
3. Accept the discovery notification in Home Assistant to add device
   Note: If discovery takes longer than 5 minutes, proceed to troubleshooting steps
4. Device will appear in your Home Assistant Devices dashboard

#### Troubleshooting Integration
If the device isn't discovered automatically:
1. Verify your device is powered and connected to your network:
   - Look for the device in your router's client list
   - Consider using [manual IP](https://esphome.io/components/wifi.html#manual-ips) in your device
2. If you missed the discovery notification:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "ESPHome" and enter your device's IP address
3. Still having issues?
   - Check your network allows mDNS/discovery traffic
   - Verify there are no VLANs or network isolation preventing communication
   - Try rebooting both the device and Home Assistant

### Initial Configuration

1. In Home Assistant, navigate to:
   - Settings → Devices & Services → ESPHome
   - Click on your device to access its configuration page
2. Set basic device parameters:
   - Model format (EU/US)
   - Number of gangs (1-4)
   - Relay modes (switch/light)
   - Button actions
3. Optional: Configure advanced features
   - LED behaviors
   - Touch duration
   - Haptic feedback
   - Audio feedback
4. Test your configuration:
   - Verify each relay responds to controls
   - Test configured button actions
   - Confirm LED behavior matches settings
   - Check haptic/audio feedback if enabled

> [!NOTE]  
> Some changes may require a device restart

## Usage

After installation, you can:

1. Configure your device through Home Assistant UI
2. Customize touch behaviors
3. Set up LED patterns and effects
4. Create automations
5. Enable optional features like Bluetooth proxy

## Configuration Options

TX Ultimate Easy offers extensive configuration options:

- Touch panel gestures
- LED colors, patterns, and behaviors
- Relay modes and functions
- Audio and haptic feedback settings
- Network and connectivity options
- Optional Bluetooth proxy functionality

## Contributing

We welcome contributions from the community! Here's how you can help:

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Submit a pull request targeting the `main` branch

Please ensure your code follows our standards:

- Passes all lint checks (YAML, C++, Markdown)
- Includes appropriate documentation
- Follows existing code style

## Support and Community

Need help? Here are your options:

- **Bug Reports & Feature Requests**: Use [GitHub Issues](https://github.com/edwardtfn/TX-Ultimate-Easy/issues)
    for all bug reports and feature requests
- **Community Chat**: Join our [Discord Server](https://discord.gg/Db6WJWzWuf)
    for discussions and community interaction
- **Support the Project**: Consider supporting through Buy Me a Coffee

Note: For proper tracking and resolution:
- All bug reports and feature requests must be submitted through GitHub Issues, not Discord
- Submit issues here: [Issues · edwardtfn/TX-Ultimate-Easy](https://github.com/edwardtfn/TX-Ultimate-Easy/issues)

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/edwardfirmo)

## Acknowledgments

This project builds upon the work of several amazing projects and contributors:

<!-- markdownlint-disable MD013 -->
- [SmartHome yourself - SONOFF TX Ultimate for ESPHome](https://github.com/SmartHome-yourself/sonoff-tx-ultimate-for-esphome)
- [Un loco y su tecnología - Sonoff TX Ultimate with ESPHome](https://www.youtube.com/watch?v=58v8oqSQgXQ)
- [@PxPert](https://github.com/PxPert) - [Sonoff TX Ultimate and Voice Assistant](https://community.home-assistant.io/t/sonoff-tx-ultimate-and-voice-assistant/682214?u=edwardtfn)
<!-- markdownlint-enable MD013 -->

Special thanks to all contributors and community members who help make this project better.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<!-- markdownlint-disable MD033 -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="Assets/Logo_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="Assets/Logo_light.png">
  <img alt="TX Ultimate Easy Logo" src="Assets/Logo_light.png" width="100">
</picture>
<!-- markdownlint-enable MD033 -->
