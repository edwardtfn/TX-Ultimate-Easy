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

TX Ultimate Easy exposes your device's components (sensors, touch panel, relays, etc.) to Home Assistant, allowing you to:

- Monitor sensor states and values
- Control device components through the Home Assistant UI
- Use device triggers and states in your Home Assistant automations and scripts
- Configure device behavior through Home Assistant's service calls

All automation capabilities are handled through Home Assistant's native automation system - this project focuses on providing reliable
device integration rather than implementing its own automation tools.

### Event-Based Automation

TX Ultimate Easy uses Home Assistant's native Events system for reliable automation triggers.
While sensors show the current state (e.g., button pressed/not pressed), events capture-specific actions like clicks, swipes, and long presses.

To view available events:

1. Go to Developer Tools in Home Assistant
2. Select the "Events" tab
3. Enter `esphome.tx_ultimate_easy` in the "Event to subscribe to" field
4. Click "Start listening"
5. Interact with your device to see events in real-time

Example event trigger in automation (YAML):

```yaml
triggers:
  - platform: event
    event_type: esphome.tx_ultimate_easy
    event_data:
      device_name: your_device_name
      component: bs_button_1
      event: click
actions:
  - action: light.toggle
    target:
      entity_id: light.living_room
```

**Common event types**:
- `click`: Single press and release
- `double_click`: Two quick presses
- `long_press`: Press and hold
- `swipe_left`: Left swipe gesture
- `swipe_right`: Right swipe gesture

You can also create event-based automations through the Home Assistant UI by selecting "Event" as the trigger type and filtering by your device.

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

Detailed installation instructions coming soon. The process will include:

1. Initial ESPHome setup
2. Device flashing
3. Home Assistant integration
4. Basic configuration

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

- **Bug Reports & Feature Requests**: Use [GitHub Issues](https://github.com/edwardtfn/TX-Ultimate-Easy/issues) for all bug reports and feature requests
- **Community Chat**: Join our [Discord Server](https://discord.gg/Db6WJWzWuf) for discussions and community interaction
- **Support the Project**: Consider supporting through Buy Me a Coffee

Note: For proper tracking and resolution:
- All bug reports and feature requests must be submitted through GitHub Issues, not Discord
- Submit issues here: [Issues · edwardtfn/TX-Ultimate-Easy](https://github.com/edwardtfn/TX-Ultimate-Easy/issues)

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/edwardfirmo)

## Acknowledgments

This project builds upon the work of several amazing projects and contributors:

- [SmartHome yourself - SONOFF TX Ultimate for ESPHome](https://github.com/SmartHome-yourself/sonoff-tx-ultimate-for-esphome)
- [Un loco y su tecnología - Sonoff TX Ultimate with ESPHome](https://www.youtube.com/watch?v=58v8oqSQgXQ)

Special thanks to all contributors and community members who help make this project better.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<!-- markdownlint-disable MD033 -->
<img src="Assets/Logo.webp" alt="TX Ultimate Easy Logo" width="100"/>
<!-- markdownlint-enable MD033 -->
