import time


def test_tc_h01_vibration_feedback_on_press(switch):
    """TC-H01: When vibration feedback is 'On press', touch-down immediately pulses the vibration motor."""
    switch.set_vibration_feedback("On press")
    time.sleep(0.5)
    switch.drain_logs()

    # Inject PRESS only
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)

    # Motor must activate on press
    switch.assert_log("'Vibration motor' >> ON", timeout=3.0)

    # Motor auto-shuts off after duration
    switch.assert_log("'Vibration motor' >> OFF", timeout=3.0)

    # Send release
    switch.drain_logs()
    time.sleep(0.05)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    # No second vibration on release
    switch.assert_no_log("'Vibration motor' >> ON", duration=0.5)


def test_tc_h02_vibration_feedback_on_release(switch):
    """TC-H02: When vibration feedback is 'On release', press does nothing; lift-off pulses motor."""
    switch.set_vibration_feedback("On release")
    time.sleep(0.5)
    switch.drain_logs()

    # 1. Inject PRESS
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    # Must NOT vibrate on press
    switch.assert_no_log("'Vibration motor' >> ON", duration=0.3)

    # 2. Inject RELEASE
    switch.drain_logs()
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)
    # Must vibrate on release
    switch.assert_log("'Vibration motor' >> ON", timeout=3.0)


def test_tc_h03_vibration_feedback_disabled(switch):
    """TC-H03: When vibration feedback is 'Disabled', touches produce zero haptic vibration."""
    switch.set_vibration_feedback("Disabled")
    time.sleep(0.5)
    switch.drain_logs()

    switch.tap(gang=1)
    switch.assert_no_log("'Vibration motor' >> ON", duration=0.5)


def test_tc_h04_night_mode_suppresses_vibration(switch):
    """TC-H04: Active Night Mode with suppress_vibration prevents motor activation."""
    switch.set_vibration_feedback("Always")
    switch.set_switch("Night Mode - Suppress Vibration", True)
    switch.set_night_mode(True)
    time.sleep(0.5)
    switch.drain_logs()

    switch.tap(gang=1)
    # Night mode guard must suppress vibration
    switch.assert_no_log("'Vibration motor' >> ON", duration=0.5)

    # Cleanup: turn night mode off
    switch.set_night_mode(False)
    time.sleep(0.5)


def test_tc_h05_multi_touch_triggers_vibration(switch):
    """TC-H05: Multi-touch / palm event triggers vibration feedback when enabled."""
    switch.set_vibration_feedback("Always")
    time.sleep(0.5)
    switch.drain_logs()

    switch.palm_mash(contact_gang=2)
    switch.assert_log("'Vibration motor' >> ON", timeout=3.0)


def test_tc_h06_vibration_motor_retrigger_recovery(switch):
    """TC-H06: Retriggering vibration while entering Night Mode must shut off motor without hanging.

    Expected Behavior: Vibration pulses must terminate cleanly and turn off the motor promptly
    even when subsequent pulses are suppressed by Night Mode.
    """
    # A pulse long enough to still be running when the suppressed retrigger arrives
    switch.set_vibration_duration(500)
    switch.set_vibration_feedback("Always")
    switch.set_switch("Night Mode - Suppress Vibration", True)
    switch.drain_logs()

    # Touch down to start the 500ms pulse
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    switch.assert_log("'Vibration motor' >> ON", timeout=1.0)
    switch.drain_logs()

    # Enter Night Mode without the usual settle delay, then release while the pulse is still running
    switch.set_night_mode(True, settle=0)
    time.sleep(0.1)
    assert "'Vibration motor' >> OFF" not in switch.get_recent_logs(), "Pulse ended before the retrigger"
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    # The suppressed retrigger cancels the running pulse, so it must turn the motor off itself.
    # Before the fix, the motor stayed on until the 2s safety cutoff.
    switch.assert_log("'Vibration motor' >> OFF", timeout=0.3)

    # Cleanup
    switch.set_night_mode(False)
    switch.set_vibration_duration(15)
