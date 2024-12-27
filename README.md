# TX Ultimate Easy

[![Version][version-shield]](https://github.com/edwardtfn/TX-Ultimate-Easy/tags)
[![GitHub Activity][commits-shield]](https://github.com/edwardtfn/TX-Ultimate-Easy/commits/main)
[![License][license-shield]](LICENSE)
[![GitHub Last Commit][last-commit-shield]](https://github.com/edwardtfn/TX-Ultimate-Easy/commits/main)
[![ESPHome][esphome-shield]](https://esphome.io/)
[![Discord][discord-shield]](https://discord.gg/Db6WJWzWuf)
[![Buy me an ice-cream][buymeacoffee-shield]](https://www.buymeacoffee.com/edwardfirmo)

<!-- markdownlint-disable MD013 -->
| &nbsp;![TX Ultimate Easy Logo](Assets/Logo.webp) | TX Ultimate Easy provides custom ESPHome firmware for Sonoff TX Ultimate devices. Our project focuses on user-friendly configuration through the Home Assistant UI, eliminating the need for manual YAML editing. Whether you're new to home automation or an experienced user, TX Ultimate Easy makes it simple to manage your device. |
| --- | :-- |
<!-- markdownlint-enable MD013 -->

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
- **BLE Proxy Support**: Optional Bluetooth Low Energy proxy functionality
- **Audio Feedback**: Built-in speaker support for audible feedback
- **Haptic Feedback**: Vibration motor support for tactile feedback

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

### 1. ESPHome Integration Setup

1. Install ESPHome add-on in Home Assistant if not already installed:
   - Go to Settings → Add-ons → Add-on Store
   - Search for "ESPHome" 
   - Click Install
2. Start the ESPHome add-on and verify it's running
3. Access ESPHome dashboard through Home Assistant

### 2. Device Configuration

1. In ESPHome dashboard, click "+ New Device"
2. Name your device (e.g., "tx-ultimate-living-room")
3. Select ESP32 as your device type
4. Copy this basic configuration to your new device:
   ```yaml
   substitutions:
     name: tx-ultimate-easy  # Change this to your device name
     friendly_name: TX Ultimate Easy
   
   packages:
     remote_package:
       url: https://github.com/edwardtfn/TX-Ultimate-Easy
       ref: main  # For latest stable release
       # ref: dev  # For testing new features
       files:
         - ESPHome/TX-Ultimate-Easy-ESPHome.yaml
   
   wifi:
     ssid: !secret wifi_ssid
     password: !secret wifi_password
   ```
5. Click "Save" and then "Install"

### 3. Device Flashing

Initial flashing must be done via serial connection.
We recommend using [ESPHome Web](https://web.esphome.io) for the simplest experience.

#### Required Hardware
- USB-to-UART adapter (3.3V)
- Small Phillips screwdriver
- 5 wires for connections (including one for BOOT to GND)

#### Flashing Process
1. Open your TX Ultimate device carefully
2. Locate the programming header pins
3. Connect your USB-to-UART adapter:
   - GND → GND
   - 3.3V → 3.3V
   - TX → RX
   - RX → TX
4. Put device in flash mode:
   - Connect the BOOT pin to GND using a jumper wire
   - Power up the device (keeping BOOT connected to GND)
   - Remove the BOOT to GND connection
5. Visit [ESPHome Web](https://web.esphome.io)
6. Connect to your device and flash the firmware
7. After successful flash, device will restart and be ready for OTA updates

#### Detailed Visual Guides
For step-by-step visual instructions, you can reference these existing guides:
- 🇬🇧 [WirelessThings Guide](https://wirelessthings.net/how-to-flash-sonoff-tx-ultimate-with-esphome) -
  English guide with detailed photos
- 🇪🇸 [Un loco y su tecnología](https://youtu.be/58v8oqSQgXQ?t=143) - Spanish video tutorial
- 🇩🇪 [SmartHome yourself](https://youtu.be/naDLhX89enQ?t=465) - German video tutorial

Note: While these guides may use different firmware, the physical flashing process remains the same.

#### Subsequent Updates
After initial flashing, all future updates can be done wirelessly (OTA)
through the ESPHome dashboard in your ESPHome add-on.

### 4. Home Assistant Integration

After successful flashing:
1. Device will automatically be discovered by Home Assistant
2. Accept the discovery notification to add device
3. Device will appear in your Home Assistant Devices dashboard

### 5. Initial Configuration

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
   - Touch sensitivity
   - Haptic feedback
   - Audio feedback

## Usage

After installation, you can:

1. Configure your device through Home Assistant UI
2. Customize touch behaviors
3. Set up LED patterns and effects
4. Create automations
5. Enable optional features like BLE proxy

## Configuration Options

TX Ultimate Easy offers extensive configuration options:

- Touch panel sensitivity and gestures
- LED colors, patterns, and behaviors
- Relay modes and functions
- Audio and haptic feedback settings
- Network and connectivity options

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

- [SmartHome yourself - SONOFF TX Ultimate for ESPHome](https://github.com/SmartHome-yourself/sonoff-tx-ultimate-for-esphome)
- [Un loco y su tecnología - Sonoff TX Ultimate with ESPHome](https://www.youtube.com/watch?v=58v8oqSQgXQ)
- [@PxPert](https://github.com/PxPert) -
  [Sonoff TX Ultimate and Voice Assistant](https://community.home-assistant.io/t/sonoff-tx-ultimate-and-voice-assistant/682214?u=edwardtfn)

Special thanks to all contributors and community members who help make this project better.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<!-- markdownlint-disable MD033 -->
<img src="Assets/Logo.webp" alt="TX Ultimate Easy Logo" width="100"/>
<!-- markdownlint-enable MD033 -->
