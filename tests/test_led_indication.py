import time


def test_tc_l01_led_mode_bottom(switch):
    """TC-L01: In Bottom light mode, toggling relay ON illuminates the Bottom light; OFF turns it off."""
    switch.set_gang_light_mode(1, "Bottom")
    time.sleep(0.6)
    switch.drain_logs()

    # Turn ON
    switch.tap(gang=1)
    switch.assert_log("Turn-on Bottom light for Relay 1")
    switch.assert_no_log("Turn-on Top light for Relay 1")

    switch.drain_logs()

    # Turn OFF
    time.sleep(0.6)
    switch.tap(gang=1)
    switch.assert_log("Turn-off Bottom light for Relay 1")


def test_tc_l02_led_mode_top(switch):
    """TC-L02: In Top light mode, toggling relay ON illuminates the Top light; Bottom light is not shown."""
    switch.set_gang_light_mode(1, "Top")
    time.sleep(0.6)
    switch.drain_logs()

    # Turn ON
    switch.tap(gang=1)
    switch.assert_log("Turn-on Top light for Relay 1")
    switch.assert_no_log("Turn-on Bottom light for Relay 1")

    switch.drain_logs()

    # Turn OFF
    time.sleep(0.6)
    switch.tap(gang=1)
    switch.assert_log("Turn-off Top light for Relay 1")


def test_tc_l03_led_mode_both(switch):
    """TC-L03: In Both light mode, toggling relay ON illuminates both Top and Bottom lights."""
    switch.set_gang_light_mode(1, "Both")
    time.sleep(0.6)
    switch.drain_logs()

    # Turn ON
    switch.tap(gang=1)
    switch.assert_log("Turn-on Bottom light for Relay 1")
    switch.assert_log("Turn-on Top light for Relay 1")

    switch.drain_logs()

    # Turn OFF
    time.sleep(0.6)
    switch.tap(gang=1)
    switch.assert_log("Turn-off Bottom light for Relay 1")
    switch.assert_log("Turn-off Top light for Relay 1")


def test_tc_l04_led_mode_off(switch):
    """TC-L04: In Off light mode, turning relay ON does NOT illuminate any relay status LEDs."""
    switch.set_gang_light_mode(1, "Off")
    time.sleep(0.6)
    switch.drain_logs()

    # Turn ON
    switch.tap(gang=1)
    switch.assert_log("Toggle relay 1")
    switch.assert_no_log("Turn-on Bottom light for Relay 1")
    switch.assert_no_log("Turn-on Top light for Relay 1")


def test_tc_l05_active_to_active_mode_transition_updates_leds(switch):
    """TC-L05: Transitioning light mode from 'Both' to 'Bottom' while Relay is ON must turn off the Top LED.

    Expected Behavior: Switching between active LED modes must clear LED segments no longer in use.
    """
    # 1. Start in 'Both' mode and turn Relay 1 ON
    switch.set_gang_light_mode(1, "Both")
    time.sleep(0.6)
    switch.set_relay(1, True)
    switch.assert_log("Turn-on Bottom light for Relay 1")
    switch.assert_log("Turn-on Top light for Relay 1")

    # 2. While Relay 1 is ON, switch light mode from 'Both' to 'Bottom'
    switch.drain_logs()
    switch.set_gang_light_mode(1, "Bottom")

    # 3. Assert the Top light segment turns OFF (clearing the inactive group)
    # ON STOCK CODE: This FAILS! Proves the stranded LED bug.
    switch.assert_log("Turn-off Top light for Relay 1", timeout=3.0)


def test_tc_l06_gang3_toggle_clears_inactive_leds(switch):
    """TC-L06: Toggling Relay 3 OFF must extinguish all assigned LED groups.

    Expected Behavior: Toggling OFF a multi-gang relay must completely clear all LED segments
    associated with that relay, leaving no stranded illuminated LEDs.
    """
    # 1. Gang 3 starts in 'Both' mode and Relay 3 is turned ON (both Bottom and Top LEDs turn ON)
    switch.set_gang_light_mode(3, "Both")
    time.sleep(0.6)
    switch.set_relay(3, True)
    switch.assert_log("Turn-on Bottom light for Relay 3")
    switch.assert_log("Turn-on Top light for Relay 3")

    # 2. Light mode for Gang 3 is changed to 'Bottom'
    switch.drain_logs()
    switch.set_gang_light_mode(3, "Bottom")

    # 3. Toggle Relay 3 OFF
    # On stock firmware: Bottom turns OFF, but Top is NEVER sent a turn-off command!
    # Result: Toggling OFF leaves the Top LED stranded ON permanently!
    switch.drain_logs()
    switch.set_relay(3, False)
    switch.assert_log("Turn-off Bottom light for Relay 3")

    # On fixed firmware: Top light is explicitly turned off (clearing inactive groups).
    # On stock origin/main: This assertion FAILS because 'Turn-off Top light for Relay 3' is never called!
    switch.assert_log("Turn-off Top light for Relay 3", timeout=3.0)


def test_tc_l07_first_light_mode_change_after_boot_applies_immediately(switch):
    """TC-L07: First user light mode change after boot must apply immediately.

    Expected Behavior: Changing light mode for the first time after device boot must execute
    the mode transition and update LED output without requiring an extra trigger.
    """
    # Relay 1 starts ON with Bottom LED lit
    switch.set_relay(1, True)
    switch.set_gang_light_mode(1, "Bottom")
    time.sleep(0.5)
    switch.drain_logs()

    # User changes mode to Disabled for the first time
    switch.set_gang_light_mode(1, "Disabled")

    # On working firmware: turning off lights log appears and LED turns off.
    # On stock firmware: previous_mode.empty() returns immediately, so this fails!
    switch.assert_log("Relay 1 light mode changed to Disabled - turning off lights", timeout=2.5)


def test_tc_l08_side_partition_turn_off_restores_relay_indicator(switch):
    """TC-L08: Turning OFF an individual side partition must restore active relay status LEDs.

    Expected Behavior: When an ambient side light strip partition is turned off, the firmware must
    evaluate and restore relay status indicators on any currently active relays.
    """
    # 1. Turn Relay 1 ON with Bottom indicator lit
    switch.set_gang_light_mode(1, "Bottom")
    switch.set_relay(1, True)
    time.sleep(0.5)
    switch.assert_log("Turn-on Bottom light for Relay 1")

    # 2. Turn ON Light - Bottom (ambient side light)
    switch.drain_logs()
    switch.set_light("Light - Bottom", True)
    time.sleep(0.4)

    # 3. Turn OFF Light - Bottom
    switch.drain_logs()
    switch.set_light("Light - Bottom", False)

    # Relay 1 indicator must be repainted / restored ON
    # On stock firmware: no on_turn_off hook exists for side partitions, so this assertion fails:
    switch.assert_log("Turn-on Bottom light for Relay 1", timeout=3.0)

