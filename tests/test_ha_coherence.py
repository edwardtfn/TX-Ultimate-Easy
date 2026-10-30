import time


def test_tc_ha01_remote_relay_toggle_updates_gang_led(switch):
    """TC-HA01: Toggling relay remotely via Home Assistant API updates physical LED status indicators."""
    switch.set_gang_light_mode(1, "Bottom")
    time.sleep(0.5)
    switch.drain_logs()

    # HA turns ON Relay 1
    switch.set_relay(1, True)
    switch.assert_log("Turn-on Bottom light for Relay 1")

    switch.drain_logs()

    # HA turns OFF Relay 1
    switch.set_relay(1, False)
    switch.assert_log("Turn-off Bottom light for Relay 1")


def test_tc_ha03_simultaneous_touch_and_remote_api_toggle(switch):
    """TC-HA03: Concurrent physical capacitive tap and remote HA API toggle must resolve cleanly."""
    switch.drain_logs()

    # Send physical tap and API toggle nearly simultaneously
    switch.tap(gang=1)
    switch.set_relay(1, False)

    time.sleep(0.5)

    # System must remain coherent without kernel panic or crash
    switch.assert_no_log("Guru Meditation Error")
    switch.assert_no_log("rst:0x")
    # Verify entity state is a valid boolean
    state = switch.get_entity_state("Relay 1")
    assert isinstance(state, bool)


def test_tc_ha04_lights_all_overrides_relay_indicators(switch):
    """TC-HA04: When 'Lights (all)' is ON, ambient lighting overrides all gang LEDs.

    Design Intent:
    1. 'Lights (all)' ambient mode takes absolute visual precedence over relay status LEDs.
    2. When 'Lights (all)' is active, toggling physical relays must NOT change or extinguish
       gang LED partitions (preventing black holes or color corruptions in the ambient strip).
    3. Turning 'Lights (all)' OFF must restore gang LED states matching current relay states.
    """
    # 1. Setup: Relay 1 is ON with Bottom indicator lit; Relay 2 is OFF
    switch.set_number("Relay 1 Pulse Time", 0.0)
    switch.set_number("Relay 2 Pulse Time", 0.0)
    switch.set_gang_light_mode(1, "Bottom")
    switch.set_gang_light_mode(2, "Bottom")
    time.sleep(0.5)

    switch.set_relay(1, True)
    switch.set_relay(2, False)
    switch.assert_log("'Relay 1' >> ON")
    switch.assert_log("Turn-on Bottom light for Relay 1")
    time.sleep(0.3)
    switch.drain_logs()

    # 2. Turn ON Lights (all) - ambient lighting takes over the entire strip
    switch.set_light("Lights (all)", True)
    time.sleep(0.6)
    switch.drain_logs()

    # 3. Toggle Relay 1 OFF while Lights (all) is active
    switch.set_relay(1, False)
    switch.assert_log("'Relay 1' >> OFF")

    # In intended design: relay LED must NOT be updated while Lights (all) is ON.
    # On stock firmware: This FAILS because show_relay_status blindly turns off
    # the partition, cutting a black hole into the active ambient strip!
    switch.assert_no_log("Turn-off Bottom light for Relay 1", duration=1.0)

    # 4. Toggle Relay 2 ON while Lights (all) is active
    switch.drain_logs()
    switch.set_relay(2, True)
    switch.assert_log("'Relay 2' >> ON")
    # Relay 2 must not alter the ambient LEDs
    switch.assert_no_log("Turn-on Bottom light for Relay 2", duration=1.0)

    # 5. Turn OFF Lights (all)
    switch.drain_logs()
    switch.set_light("Lights (all)", False)

    # Firmware must restore gang LEDs matching current relay states:
    # Relay 2 is ON -> Bottom indicator turns ON
    switch.assert_log("Turn-on Bottom light for Relay 2", timeout=5.0)
    # Relay 1 is OFF -> Bottom indicator must NOT turn ON
    switch.assert_no_log("Turn-on Bottom light for Relay 1", duration=0.5)


def test_tc_ha05_swipe_during_active_ambient_lighting(switch):
    """TC-HA05: Swiping while Lights (all) is active reports the gesture without disrupting ambient lighting."""
    switch.drain_logs()
    # Turn ON ambient light
    switch.set_light("Lights (all)", True)
    time.sleep(0.5)
    switch.drain_logs()

    # Perform swipe right across strip
    switch.swipe_right(start_gang=1, end_gang=3)
    switch.assert_log("Swipe right")

    # Ambient light must still be active
    assert switch.get_entity_state("Lights (all)") is True

    # Clean up
    switch.set_light("Lights (all)", False)


