import time
import pytest


@pytest.mark.parametrize("gang", [1, 2, 3])
def test_tc_g01_single_click(switch, gang):
    """TC-G01: Single tap on any configured gang registers click action and toggles relay."""
    switch.tap(gang=gang)
    switch.assert_log(f"Button {gang} action: 'click'")
    switch.assert_log(f"Toggle relay {gang}")


def test_tc_g04_double_click(switch):
    """TC-G04: Double-click with 80ms interval registers double_click."""
    switch.double_click(gang=1, interval_ms=80)
    switch.assert_log("Button 1 action: 'double_click'")


def test_tc_g05_multi_click_timeout_registers_two_clicks(switch):
    """TC-G05: Two clicks with gap > multi_click_delay (350ms > 250ms) must register as 2 single clicks."""
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")

    # Wait past multi_click window
    time.sleep(0.35)
    switch.drain_logs()

    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")


def test_tc_g07_swipe_right(switch):
    """TC-G07: Swipe right gesture cleanly suppresses the initial touch-down click in Normal Mode."""
    switch.drain_logs()
    switch.swipe_right(start_gang=1, end_gang=3)
    switch.assert_log("Swipe right")
    # Verify the initial touch-down on Gang 1 was aborted by buttons_reset_state
    switch.assert_no_log("Button 1 action: 'click'", duration=0.3)


def test_tc_g08_swipe_left(switch):
    """TC-G08: Swipe left gesture cleanly suppresses the initial touch-down click in Normal Mode."""
    switch.drain_logs()
    switch.swipe_left(start_gang=3, end_gang=1)
    switch.assert_log("Swipe left")
    # Verify the initial touch-down on Gang 3 was aborted by buttons_reset_state
    switch.assert_no_log("Button 3 action: 'click'", duration=0.3)


def test_tc_g09_multi_touch(switch):
    """TC-G09: Multi-touch / palm mash cleanly suppresses button clicks in Normal Mode."""
    switch.drain_logs()
    switch.palm_mash(contact_gang=2)
    switch.assert_log("Multi-touch")
    # Verify that palm contact did not fire a click
    switch.assert_no_log("action: 'click'", duration=0.3)


def test_tc_g10_stale_press_recovery(switch):
    """TC-G10: A touch press without a release frame is safely recovered on next press."""
    switch.drain_logs()
    # 1. Inject press with NO release
    pos = 1
    switch.send_touch_frame(0x02, 0x00, pos, 0x00)
    time.sleep(0.1)

    # 2. Inject second press after gap > multi_click_delay without release
    time.sleep(0.35)
    switch.send_touch_frame(0x02, 0x00, pos, 0x00)
    time.sleep(0.05)
    # Release second press
    switch.send_touch_frame(0x01, pos, pos, 0x00)

    # Verify stale press detection warning and clean click
    switch.assert_log("Stale press detected")
    switch.assert_log("Button 1 action: 'click'")


def test_tc_g12_partial_swipe_same_gang(switch):
    """TC-G12: A partial swipe / drag within the same gang boundary evaluates as a single click."""
    switch.drain_logs()
    # Contact pos 2 (Gang 1), drag to pos 3 (still Gang 1), release
    switch.partial_swipe(start_pos=2, end_pos=3, duration_ms=60.0)
    switch.assert_log("Button 1 action: 'click'")


def test_tc_g14_multi_click_window_boundaries(switch):
    """TC-G14: Precise boundary timing around the 250ms multi-click detection window.

    - Tap gap of 220ms (< 250ms) evaluates as double_click.
    - Tap gap of 290ms (> 250ms) splits into two single clicks.
    """
    # 1. Gap inside window (220ms < 250ms): must evaluate as double click
    switch.drain_logs()
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.04)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)
    time.sleep(0.22)
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.04)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    switch.assert_log("Button 1 action: 'double_click'", timeout=2.0)
    time.sleep(0.3)

    # 2. Gap outside window (290ms > 250ms): must evaluate as two single clicks
    switch.drain_logs()
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.04)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)
    time.sleep(0.29)
    switch.send_touch_frame(0x02, 0x00, 0x01, 0x00)
    time.sleep(0.04)
    switch.send_touch_frame(0x01, 0x01, 0x01, 0x00)

    # First click fires, then second click fires; no double_click
    switch.assert_log("Button 1 action: 'click'", timeout=2.0)
    switch.assert_no_log("action: 'double_click'", duration=0.3)


def test_tc_g15_triple_click_multiple_click_event(switch):
    """TC-G15: Rapid three clicks trigger the multiple_click action with count=3."""
    switch.drain_logs()
    switch.multi_click(gang=1, count=3, interval_ms=40.0, hold_ms=20.0)
    time.sleep(0.35)

    switch.assert_log("Button 1 action: 'multiple_click'", timeout=2.0)

