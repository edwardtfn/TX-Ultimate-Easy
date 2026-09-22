# ESP-NOW

Switches can control relays on other TX Ultimate Easy devices directly (peer-to-peer), without Home Assistant.

**Setup:**

1. Add the package to your device YAML:

   ```yaml
   packages:
     remote_package:
       url: https://github.com/edwardtfn/TX-Ultimate-Easy
       ref: main
       refresh: 5min
       files:
         - ESPHome/TX-Ultimate-Easy-ESPHome_core.yaml
         - ESPHome/TX-Ultimate-Easy-ESPHome_standard.yaml
         - ESPHome/TX-Ultimate-Easy-ESPHome_espnow.yaml
   ```

2. Get each switch’s MAC from the **"ESP-NOW MAC Address"** text sensor in Home Assistant.

3. In your device YAML, set per-button target MAC and relay (1–4). For buttons you don’t want on ESP-NOW, don’t set anything (they use local relay only).

   ```yaml
   substitutions:
     espnow_target_mac_button_1: "AA:BB:CC:DD:EE:FF"
     espnow_target_relay_button_1: 1
     # Only set espnow_target_mac_button_2..4 and espnow_target_relay_button_2..4 if you want those buttons to control a remote relay
   ```

4. Recompile and flash. In Home Assistant, set **"ESP-NOW Send"** on the devices that should send, and turn on **"ESP-NOW Receive Enabled"** on the devices that should receive.
   - **Off**: never send (default).
   - **Always**: send whenever a configured button is clicked.
   - **API failsafe only**: send only while the device is not connected to Home Assistant (API or Wi-Fi disconnected), matching the "API failsafe only" button action.

Works without Home Assistant. Config is in YAML only; changes need recompile and flash.
