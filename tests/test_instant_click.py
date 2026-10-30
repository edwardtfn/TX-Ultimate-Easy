import time
import pytest


def test_tc_ic01_click_fires_immediately_on_press_before_release(instant_switch):
    """TC-IC01: In Instant Click Mode, a single click fires immediately on touch down, before release."""
    instant_switch.drain_logs()

    # Inject PRESS only (Byte 4: 0x02 = PRESS, Byte 6: 0x01 = Gang 1)
    instant_switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)

    # In Instant Click Mode, click action must fire immediately on touch contact
    instant_switch.assert_log("Button 1 action: 'click'")
    instant_switch.assert_log("Toggle relay 1")

    # Release afterwards to leave touch state clean
    time.sleep(0.05)
    instant_switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)
    instant_switch.drain_logs()


def test_tc_ic02_long_press_does_not_fire_long_press_event(instant_switch):
    """TC-IC02: Holding touch down in Instant Click Mode does NOT fire long press event."""
    instant_switch.drain_logs()

    # Touch and hold for 600ms (> 500ms long press threshold)
    instant_switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.60)

    # In Instant Click Mode, software long press timer must NOT trigger long press
    instant_switch.assert_no_log("long_click", duration=0.2)
    instant_switch.assert_no_log("action: 'long_press'", duration=0.2)

    # Release
    instant_switch.send_touch_frame(0x01, 0x11, 0x01, 0x00)
    instant_switch.drain_logs()


def test_tc_ic03_double_click_does_not_fire_double_click_event(instant_switch):
    """TC-IC03: Tapping twice quickly does NOT fire double-click in Instant Click Mode."""
    instant_switch.drain_logs()

    # Tap twice with 120ms interval
    instant_switch.tap(gang=1)
    time.sleep(0.12)
    instant_switch.tap(gang=1)

    # Multi-click detector must be disabled; no double click event
    instant_switch.assert_no_log("action: 'double_click'", duration=0.3)


def test_tc_ic04_rapid_fire_dead_zone_per_gang(instant_switch):
    """TC-IC04: Rapid touches within the dead zone (500ms) on the SAME gang are suppressed."""
    instant_switch.drain_logs()

    # First touch on Gang 1
    instant_switch.tap(gang=1)
    instant_switch.assert_log("Button 1 action: 'click'")

    # Second touch 80ms later (well within 500ms dead zone)
    instant_switch.drain_logs()
    time.sleep(0.08)
    instant_switch.tap(gang=1)

    # Second press must be ignored by dead-zone debounce
    instant_switch.assert_no_log("Button 1 action: 'click'", duration=0.3)

    # Wait past 500ms dead zone
    time.sleep(0.55)
    instant_switch.drain_logs()

    # Third touch after dead zone expired must succeed
    instant_switch.tap(gang=1)
    instant_switch.assert_log("Button 1 action: 'click'")


def test_tc_ic05_multi_gang_simultaneous_touch_independent_debounce(instant_switch):
    """TC-IC05: Multiple gangs touched simultaneously/interleaved are independently debounced."""
    instant_switch.drain_logs()

    # Tap Gang 1
    instant_switch.tap(gang=1)
    instant_switch.assert_log("Button 1 action: 'click'")

    # Immediately tap Gang 2 (50ms gap << 500ms dead zone) - Gang 2 must NOT be blocked
    instant_switch.drain_logs()
    time.sleep(0.05)
    instant_switch.tap(gang=2)
    instant_switch.assert_log("Button 2 action: 'click'")

    # Immediately tap Gang 3 (50ms gap << 500ms dead zone) - Gang 3 must NOT be blocked
    instant_switch.drain_logs()
    time.sleep(0.05)
    instant_switch.tap(gang=3)
    instant_switch.assert_log("Button 3 action: 'click'")


@pytest.mark.parametrize("direction,start,end,expected_gang,expected_log", [
    ("right", 1, 3, 1, "Swipe right"),
    ("left", 3, 1, 3, "Swipe left"),
])
def test_tc_ic06_swipe_in_instant_click_mode(instant_switch, direction, start, end, expected_gang, expected_log):
    """TC-IC06: In Instant Click Mode, swipe registers instant click on initial contact gang, then fires swipe."""
    # Settle debounce window
    time.sleep(0.6)
    instant_switch.drain_logs()
    if direction == "right":
        instant_switch.swipe_right(start_gang=start, end_gang=end)
    else:
        instant_switch.swipe_left(start_gang=start, end_gang=end)

    # Contact clicks immediately
    instant_switch.assert_log(f"Button {expected_gang} action: 'click'")
    # Swipe packet is recognized
    instant_switch.assert_log(expected_log)
    # Release must not cause a second click
    instant_switch.assert_no_log("action: 'double_click'", duration=0.2)



def test_tc_ic08_multi_touch_in_instant_click_mode(instant_switch):
    """TC-IC08: In Instant Click Mode, palm mash registers an instant click on the contact gang, then reports multi-touch."""
    # Settle debounce window
    time.sleep(0.6)
    instant_switch.drain_logs()
    instant_switch.palm_mash(contact_gang=2)
    # Initial slap contact on Gang 2 clicks immediately
    instant_switch.assert_log("Button 2 action: 'click'")
    # Multi-touch event is recognized
    instant_switch.assert_log("Multi-touch released")
    # Release must not cause a second click
    instant_switch.assert_no_log("action: 'double_click'", duration=0.2)


def test_tc_ic09_partial_swipe_in_instant_click_mode(instant_switch):
    """TC-IC09: Partial drag within a gang triggers instant click on touch-down and cleans up on release."""
    time.sleep(0.6)
    instant_switch.drain_logs()
    instant_switch.partial_swipe(start_pos=2, end_pos=3, duration_ms=60.0)
    instant_switch.assert_log("Button 1 action: 'click'")
    instant_switch.assert_no_log("action: 'double_click'", duration=0.2)


def test_tc_ic10_hardware_long_touch_in_instant_click_mode(instant_switch):
    """TC-IC10: Hardware long-touch triggers instant click on contact and logs long-touch release on lift."""
    time.sleep(0.8)
    instant_switch.drain_logs()
    instant_switch.hardware_long_touch(gang=1, hold_ms=150.0)
    instant_switch.assert_log("Button 1 action: 'click'")
    instant_switch.assert_log("Long-touch released at position 1")
