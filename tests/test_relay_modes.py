import time


def test_tc_rm01_entity_domain_separation(light_switch):
    """TC-RM01: Verify entity exposure matches configured relay presentation modes.

    Gang 1 (relay_1_mode: switch) exposes switch.relay_1 and hides Light output 1.
    Gang 2 (relay_2_mode: light) exposes light.light_output_2 and hides switch.relay_2.
    """
    entities = light_switch._entities

    # Gang 1: Switch mode
    assert "Relay 1" in entities, "Relay 1 switch entity should be exposed in switch mode"
    assert "Light output 1" not in entities, "Light output 1 must be internal when in switch mode"

    # Gang 2: Light mode
    assert "Light output 2" in entities, "Light output 2 light entity should be exposed in light mode"
    assert "Relay 2" not in entities, "Relay 2 switch must be internal when in light mode"


def test_tc_rm02_remote_ha_turn_on_light_toggles_relay_gpio_and_led(light_switch):
    """TC-RM02: Remote Home Assistant light commands engage relay GPIO and gang LEDs."""
    light_switch.drain_logs()

    # 1. Turn on Light output 2 via Native API light command
    light_switch.set_light("Light output 2", True)
    light_switch.assert_log("Setting:")
    light_switch.assert_log("State: ON")
    light_switch.assert_log("Relay 2 is ON")
    assert light_switch.wait_for_entity_state("Light output 2", True, timeout=3.0)

    # 2. Turn off Light output 2 via Native API light command
    light_switch.drain_logs()
    light_switch.set_light("Light output 2", False)
    light_switch.assert_log("Setting:")
    light_switch.assert_log("State: OFF")
    light_switch.assert_log("Relay 2 is OFF")
    assert light_switch.wait_for_entity_state("Light output 2", False, timeout=3.0)


def test_tc_rm03_physical_touch_toggles_light_mode_relay(light_switch):
    """TC-RM03: Physical touch press on light-configured gang toggles the light entity.

    Verifies the internal switch cascade properly routes physical button actions
    to the light entity and synchronizes HA state.
    """
    light_switch.drain_logs()

    # For 2-gang EU device: width = (10 + 2) / 2 = 6. Pos 1..5 is gang 1; pos 6..10 is gang 2.
    # Touch press on Gang 2 (pos 8)
    light_switch.send_touch_frame(0x02, 0x00, 0x08, 0x00)
    time.sleep(0.05)
    light_switch.send_touch_frame(0x01, 0x08, 0x08, 0x00)

    light_switch.assert_log("Toggle relay 2", timeout=3.0)
    light_switch.assert_log("Relay 2 is ON")
    assert light_switch.wait_for_entity_state("Light output 2", True, timeout=3.0)

    # Touch press on Gang 2 again to toggle OFF
    light_switch.drain_logs()
    light_switch.send_touch_frame(0x02, 0x00, 0x08, 0x00)
    time.sleep(0.05)
    light_switch.send_touch_frame(0x01, 0x08, 0x08, 0x00)

    light_switch.assert_log("Toggle relay 2", timeout=3.0)
    light_switch.assert_log("Relay 2 is OFF")
    assert light_switch.wait_for_entity_state("Light output 2", False, timeout=3.0)


def test_tc_rm04_inching_pulse_time_entity_hidden_for_light_mode(light_switch):
    """TC-RM04: Inching pulse timer entities are internal when in light mode.

    The firmware only supports pulse timing for switch-mode relays.
    """
    entities = light_switch._entities

    # Gang 1 (switch mode) retains its pulse time configuration
    # Note: pulse_time_internal defaults to true in stock configs, but entity key exists internally
    # In light mode, SL_RELAY_2_MODE != 1 strictly excludes the number component from the build.
    assert "Relay 2 Pulse Time" not in entities, "Pulse time must not be exposed for light-mode relay"
