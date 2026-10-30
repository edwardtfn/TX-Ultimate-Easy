import time


def test_tc_nm02_night_mode_suppresses_relay_led_updates(switch):
    """TC-NM02: When Night Mode is active, toggling physical relays does not alter relay status LEDs."""
    switch.set_night_mode(True)
    time.sleep(0.8)
    switch.drain_logs()

    # Toggle Relay 1
    switch.set_relay(1, True)
    switch.assert_log("'Relay 1' Turning ON")
    # Night mode guard must suppress LED painting
    switch.assert_log("Night mode active - skipping LED update")
    switch.assert_no_log("Turn-on Bottom light for Relay 1")


def test_tc_nm03_disable_night_mode_restores_relay_indicators(switch):
    """TC-NM03: Disabling Night Mode repaints the relay status LEDs for active relays."""
    # Ensure relay 1 is ON
    switch.set_relay(1, True)
    switch.set_night_mode(True)
    time.sleep(1.0)
    switch.drain_logs()

    # Turn Night Mode OFF
    switch.set_night_mode(False)
    switch.assert_log("'Night Mode' >> OFF")
    # Relay status must be re-evaluated
    switch.assert_log("Turn-on Bottom light for Relay 1")
    # Allow repaint to complete
    time.sleep(1.5)


def test_tc_nm05_night_mode_suppress_sound_toggle(switch):
    """TC-NM05: Night Mode sound suppression toggle operates correctly."""
    switch.set_switch("Night Mode - Suppress Sound", False)
    assert switch.wait_for_entity_state("Night Mode - Suppress Sound", False, timeout=6.0)

    switch.drain_logs()
    switch.set_switch("Night Mode - Suppress Sound", True)
    assert switch.wait_for_entity_state("Night Mode - Suppress Sound", True, timeout=6.0)


def test_tc_nm06_swipe_and_palm_during_active_night_mode(switch):
    """TC-NM06: Gestures operate during Night Mode while haptic feedback remains suppressed."""
    switch.set_switch("Night Mode - Suppress Vibration", True)
    switch.set_night_mode(True)
    time.sleep(0.5)
    switch.drain_logs()

    # 1. Swipe right during night mode
    switch.swipe_right(start_gang=1, end_gang=3)
    switch.assert_log("Swipe right")
    switch.assert_no_log("'Vibration motor' >> ON", duration=0.3)

    # 2. Palm mash during night mode
    switch.drain_logs()
    switch.palm_mash(contact_gang=2)
    switch.assert_log("Multi-touch")
    switch.assert_no_log("'Vibration motor' >> ON", duration=0.3)

    # Night mode must remain ON
    assert switch.get_entity_state("Night Mode") is True

    # Cleanup
    switch.set_night_mode(False)

