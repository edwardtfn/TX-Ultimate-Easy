import time
import re


def test_tc_tp01_touch_duration_logged_accurately(switch):
    """TC-TP01: Button press duration is accurately measured and logged by firmware timer."""
    switch.drain_logs()

    # Touch and hold for ~180ms
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.18)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    # Assert duration log appeared
    switch.assert_log("Button press duration:")
    recent = switch.get_recent_logs()
    m = re.search(r"Button press duration:\s+(\d+)\s+ms", recent)
    assert m, f"Could not parse press duration from logs: {recent}"
    duration = int(m.group(1))

    # Duration should be close to 180ms (allow margin for thread scheduling)
    assert 120 <= duration <= 350, f"Measured duration {duration}ms was outside expected window"
    switch.assert_log("Button 1 action: 'click'")
    # Allow multi-click window to close
    time.sleep(0.4)


def test_tc_tp02_long_press_duration_threshold(switch):
    """TC-TP02: Press duration exceeding BUTTON_LONG_PRESS_DELAY (500ms) triggers long press."""
    time.sleep(0.3)
    switch.drain_logs()

    # Touch and hold for ~650ms (> 500ms threshold), then release with normal position 1
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.65)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    # Must log long press
    switch.assert_log("Button 1 action: 'long_press'")
    recent = switch.get_recent_logs()
    m = re.search(r"Button press duration:\s+(\d+)\s+ms", recent)
    assert m, f"Could not parse press duration: {recent}"
    assert int(m.group(1)) >= 500


def test_tc_tp03_touch_timeout_cancellation(switch):
    """TC-TP03: A stuck touch exceeding BUTTON_PRESS_TIMEOUT (10,000ms) is cancelled safely."""
    switch.drain_logs()

    # Touch down and hold past the 10-second timeout threshold
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(10.2)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    # Firmware must log cancellation warning
    switch.assert_log("timed out after 10000 ms")
    # Must NOT fire a click
    switch.assert_no_log("Button 1 action: 'click'", duration=0.3)


def test_tc_tp04_relay_pulse_time_auto_off(switch):
    """TC-TP04: Configured pulse time (inching) automatically turns the relay OFF after delay."""
    # Set Relay 1 pulse time to 1 second
    switch.set_number("Relay 1 Pulse Time", 1.0)
    time.sleep(0.5)
    switch.drain_logs()

    # Turn ON Relay 1
    switch.set_relay(1, True)
    switch.assert_log("'Relay 1' >> ON")

    # Relay should automatically turn OFF after ~1.0 second
    switch.assert_log("'Relay 1' >> OFF", timeout=4.0)

    # Clean up: disable pulse time (0 = disabled)
    switch.set_number("Relay 1 Pulse Time", 0.0)


def test_tc_tp05_relay_pulse_time_aborted_by_manual_turn_off(switch):
    """TC-TP05: Manually turning off relay before pulse time expires cancels the timer cleanly."""
    # Set Relay 1 pulse time to 4 seconds
    switch.set_number("Relay 1 Pulse Time", 4.0)
    time.sleep(0.5)
    switch.drain_logs()

    # Turn ON
    switch.set_relay(1, True)
    switch.assert_log("'Relay 1' >> ON")

    # Manually turn OFF after 0.5s (before 4s expires)
    time.sleep(0.5)
    switch.drain_logs()
    switch.set_relay(1, False)
    switch.assert_log("'Relay 1' >> OFF")

    # Wait past the original 4-second mark to verify timer does not fire an extra transition
    switch.assert_no_log("'Relay 1' >> ON", duration=4.5)

    # Clean up
    switch.set_number("Relay 1 Pulse Time", 0.0)


def test_tc_tp06_pulse_timer_aborts_when_disabled(switch):
    """TC-TP06: Setting pulse time to 0.0 while relay is running must abort the pulse timer.

    Expected Behavior: Setting pulse time to 0 while a relay is actively timing out must cancel
    the pending auto-off and leave the relay in its active ON state.
    """
    # 1. Configure 4.0-second pulse
    switch.set_number("Relay 1 Pulse Time", 4.0)
    time.sleep(0.5)
    switch.drain_logs()

    # 2. Turn ON Relay 1 (inching timer starts)
    switch.set_relay(1, True)
    switch.assert_log("'Relay 1' >> ON")

    # 3. After 1s, user sets pulse time to 0.0 (abort / disable inching)
    time.sleep(1.0)
    switch.drain_logs()
    switch.set_number("Relay 1 Pulse Time", 0.0)
    time.sleep(0.5)

    # 4. Wait past the original 4-second expiration time
    time.sleep(3.5)

    # On working firmware, the relay remains ON because inching was aborted.
    # On stock firmware, this fails because pulse_1_delay ran to completion and shut off Relay 1!
    assert switch.get_entity_state("Relay 1") is True, "Relay 1 turned off despite pulse time being set to 0.0!"


def test_tc_tp07_inching_rearms_when_relay_already_on(switch):
    """TC-TP07: Configuring pulse time and commanding turn_on while relay is already ON must start inching.

    Expected Behavior: Re-issuing turn_on commands or updating pulse duration on an active relay
    must arm or restart the auto-off timer.
    """
    # Start with pulse disabled and relay ON
    switch.set_number("Relay 1 Pulse Time", 0.0)
    switch.set_relay(1, True)
    time.sleep(0.5)
    assert switch.get_entity_state("Relay 1") is True

    # Now user sets pulse time to 2.0s
    switch.set_number("Relay 1 Pulse Time", 2.0)
    time.sleep(0.3)
    switch.drain_logs()

    # Command turn_on again via API
    switch.set_relay(1, True)

    # Should inch off after 2.0s
    # On stock firmware, this fails: the relay remains ON indefinitely!
    assert switch.wait_for_entity_state("Relay 1", False, timeout=4.0), "Relay did not inch off when commanded while already ON!"


def test_tc_tp08_inching_triggered_by_physical_tap(switch):
    """TC-TP08: Physical capacitive tap on the switch triggers inching pulse timer."""
    # 1. Set Relay 1 Pulse Time to 1.5s
    switch.set_number("Relay 1 Pulse Time", 1.5)
    time.sleep(0.5)
    switch.drain_logs()

    # 2. Physically tap Gang 1
    switch.tap(gang=1)
    switch.assert_log("'Relay 1' >> ON", timeout=2.0)

    # 3. Relay automatically inches off after 1.5s
    switch.assert_log("'Relay 1' >> OFF", timeout=4.0)

    # Clean up
    switch.set_number("Relay 1 Pulse Time", 0.0)


def test_tc_tp09_inching_cancelled_by_manual_physical_tap_off(switch):
    """TC-TP09: Inching timer is cancelled cleanly when user manually taps off the relay."""
    # 1. Set Relay 1 Pulse Time to 4.0s
    switch.set_number("Relay 1 Pulse Time", 4.0)
    time.sleep(0.5)
    switch.drain_logs()

    # 2. Physically tap Gang 1 (turns ON)
    switch.tap(gang=1)
    switch.assert_log("'Relay 1' >> ON", timeout=2.0)

    # 3. Manually tap Gang 1 again after 0.6s (turns OFF before pulse expires)
    time.sleep(0.6)
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("'Relay 1' >> OFF", timeout=2.0)

    # 4. Wait past original 4.0s pulse timer to verify no spurious transitions
    switch.assert_no_log("'Relay 1' >> ON", duration=4.0)

    # Clean up
    switch.set_number("Relay 1 Pulse Time", 0.0)


