import time


def test_tc_ba01_button_action_toggle(switch):
    """TC-BA01: Button action set to 'Relay X (toggle)' toggles the physical relay ON and OFF."""
    switch.set_button_action(1, "Relay 1 (toggle)")
    time.sleep(0.8)
    switch.drain_logs()

    # Tap 1: Turn ON
    switch.tap(gang=1)
    switch.assert_log("Toggle relay 1")
    switch.assert_log("'Relay 1' >> ON")

    switch.drain_logs()

    # Tap 2: Turn OFF
    time.sleep(0.3)
    switch.tap(gang=1)
    switch.assert_log("Toggle relay 1")
    switch.assert_log("'Relay 1' >> OFF")


def test_tc_ba02_button_action_none(switch):
    """TC-BA02: Button action set to 'None' ignores local relay toggling."""
    switch.set_button_action(1, "None")
    time.sleep(1.0)
    switch.drain_logs()

    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")
    switch.assert_no_log("Toggle relay 1")


def test_tc_ba03_button_action_failsafe(switch):
    """TC-BA03: Button action set to 'Relay 1 (API failsafe only)'.

    When API is connected, the switch does not locally toggle the relay, delegating to Home Assistant.
    """
    switch.set_button_action(1, "Relay 1 (API failsafe only)")
    time.sleep(1.0)
    switch.drain_logs()

    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")
    # With API connected, local toggle should not fire
    switch.assert_no_log("Toggle relay 1")


def test_tc_ba04_rapid_cross_gang_taps_fire_all_clicks(switch):
    """TC-BA04: Rapid cross-gang tapping must process all clicks without dropping any gang.

    Expected Behavior: Tapping Gang 1 then immediately Gang 2 within the multi-click window
    must deliver distinct click actions for both gangs.
    """
    switch.set_button_action(1, "Relay 1 (toggle)")
    switch.set_button_action(2, "Relay 2 (toggle)")
    time.sleep(0.5)
    switch.drain_logs()

    # Tap Gang 1, then immediately tap Gang 2 after 50ms (< 250ms window)
    switch.tap(gang=1)
    time.sleep(0.05)
    switch.tap(gang=2)

    # Wait for the multi-click delay window to complete
    time.sleep(0.4)

    # Both Gang 1 and Gang 2 should fire single click actions, not double click
    switch.assert_no_log("action: 'double_click'")
    switch.assert_log("Button 2 action: 'click'", timeout=1.0)

    # Both Gang 1 and Gang 2 should have toggled ON.
    # On stock firmware, Gang 1 was dropped, so this assertion fails:
    switch.assert_log("Toggle relay 1", timeout=1.0)
    switch.assert_log("Toggle relay 2", timeout=1.0)


def test_tc_ba05_hardware_long_touch_release_fires_long_press(switch):
    """TC-BA05: Hardware long-touch release frame (x >= 17) must trigger the button long press action.

    Expected Behavior: When the hardware touch controller issues a long-touch release frame,
    the firmware must process the long press action and emit the event.
    """
    switch.set_button_action(1, "Relay 1 (toggle)")
    time.sleep(0.5)
    switch.drain_logs()

    # Press Gang 1 (pos = 1)
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.65)  # Hold for long press

    # Hardware long-touch release (pos + 16 = 17)
    switch.send_touch_frame(0x01, 0x11, 0x01, 0x00)
    time.sleep(0.2)

    # Low-level driver receives long-touch release
    switch.assert_log("Long touch - Released (x=1)")

    # On properly integrated firmware, this fires long_press.
    # On stock firmware, this action is dropped completely because on_long_touch_release is unhandled.
    switch.assert_log("Button 1 action: 'long_press'", timeout=2.0)


def test_tc_ba06_failsafe_fallback_on_api_disconnect(switch):
    """TC-BA06: Button action set to 'API failsafe only' falls back to local toggle when API drops.

    When Home Assistant / API is connected, tapping delegates to HA without local relay toggle.
    When API client disconnects, the switch immediately falls back to local hardware relay toggling.
    When API reconnects, it reverts to delegating to Home Assistant.
    """
    switch.set_button_action(1, "Relay 1 (API failsafe only)")
    time.sleep(0.5)

    # 1. API is connected -> Local toggle is suppressed
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")
    switch.assert_no_log("Toggle relay 1")

    # 2. Simulate Home Assistant disconnection
    switch.disconnect_api()
    switch.drain_logs()

    # 3. Tap while API is disconnected -> Must locally toggle Relay 1!
    switch.tap(gang=1)
    switch.assert_log("API state: DISCONNECTED")
    switch.assert_log("Toggle relay 1")
    switch.assert_log("'Relay 1' >> ON")

    # 4. Tap again to toggle OFF locally
    time.sleep(0.3)
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Toggle relay 1")
    switch.assert_log("'Relay 1' >> OFF")

    # 5. Reconnect API -> Delegation to HA restored
    switch.reconnect_api()
    time.sleep(0.5)
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")
    switch.assert_no_log("Toggle relay 1")


def test_tc_ba07_decoupled_relay_remote_toggle_led_coherence(switch):
    """TC-BA07: Decoupled relay mode ('None') delegates to HA while maintaining LED sync.

    In smart-bulb / decoupled mode, tapping physical buttons only emits events.
    Remote commands from Home Assistant to the relay must correctly drive the indicator LEDs.
    """
    switch.set_button_action(1, "None")
    switch.set_gang_light_mode(1, "Bottom")
    time.sleep(0.5)
    switch.drain_logs()

    # Physical tap emits event but does NOT toggle relay
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")
    switch.assert_no_log("Toggle relay 1")
    assert switch.get_entity_state("Relay 1") is False

    # Home Assistant automation commands Relay 1 ON via API
    switch.drain_logs()
    switch.set_relay(1, True)
    switch.assert_log("Turn-on Bottom light for Relay 1")
    assert switch.wait_for_entity_state("Relay 1", True, timeout=2.0)

    # Home Assistant automation commands Relay 1 OFF via API
    switch.drain_logs()
    switch.set_relay(1, False)
    switch.assert_log("Turn-off Bottom light for Relay 1")
    assert switch.wait_for_entity_state("Relay 1", False, timeout=2.0)


