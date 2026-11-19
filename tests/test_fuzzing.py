import time
import random
import pytest


def test_tc_f01_truncated_frames(switch):
    """TC-F01: Send partial UART frames (1 to 14 bytes) and verify firmware recovers safely without crashing."""
    switch.drain_logs()

    # Send incomplete frames of various lengths
    full_frame = bytes([0xAA, 0x55, 0x01, 0x02, 0x02, 0x00, 0x01, 0x00] + [0x00] * 7)
    for length in (1, 2, 4, 7, 10, 14):
        partial = full_frame[:length]
        switch.send_raw_bytes(partial)
        time.sleep(0.02)

    # Firmware must not crash or reboot
    switch.assert_no_log("rst:0x")
    switch.assert_no_log("Guru Meditation Error")

    # Verify parser recovers: valid tap must succeed immediately
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")


def test_tc_f02_corrupted_headers(switch):
    """TC-F02: Send frames with invalid magic headers (e.g. 0x00 0x00, 0xFF 0xFF, 0x55 0xAA)."""
    switch.drain_logs()

    garbage_headers = [
        bytes([0x00, 0x00] + [0x01] * 13),
        bytes([0xFF, 0xFF] + [0x01] * 13),
        bytes([0x55, 0xAA] + [0x01] * 13),
        bytes([0xAA, 0x00] + [0x01] * 13),
    ]

    for frame in garbage_headers:
        switch.send_raw_bytes(frame)
        time.sleep(0.02)

    # No crash
    switch.assert_no_log("Guru Meditation Error")

    # Valid tap recovers
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")


def test_tc_f03_out_of_bounds_positions(switch):
    """TC-F03: Send touch frames with out-of-bounds positions (pos=11, 50, 255)."""
    # Let a click still pending from the previous test (multi-click delay) fire before the log window starts
    time.sleep(0.6)
    switch.drain_logs()

    for invalid_pos in (11, 15, 50, 128, 255):
        # Press with invalid position
        switch.send_touch_frame(0x02, 0x00, invalid_pos, 0x00)
        time.sleep(0.02)
        # Release
        switch.send_touch_frame(0x01, invalid_pos, invalid_pos, 0x00)
        time.sleep(0.02)

    # Out of bounds positions map to button 0 and must not toggle any relays
    switch.assert_no_log("Toggle relay")
    switch.assert_no_log("Toggle virtual relay")
    switch.assert_no_log("Guru Meditation Error")

    # Legitimate position 1 still works
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")


def test_tc_f04_rapid_burst_flood(switch):
    """TC-F04: Flood 60 frames rapidly to verify UART FIFO saturation does not deadlock or crash."""
    switch.drain_logs()

    rng = random.Random(42)
    for _ in range(60):
        # Rapid alternate bytes
        byte4 = rng.choice([0x01, 0x02, 0x03])
        byte6 = rng.randint(0, 10)
        switch.send_touch_frame(byte4, 0x00, byte6, 0x00)
        time.sleep(0.002)

    # Give watchdog and loop a moment to drain
    time.sleep(0.5)

    # Firmware must survive without rebooting
    switch.assert_no_log("rst:0x")
    switch.assert_no_log("Guru Meditation Error")

    # Verify normal operation resumes cleanly
    switch.drain_logs()
    switch.tap(gang=1)
    switch.assert_log("Button 1 action: 'click'")


@pytest.mark.xfail(reason="Stock firmware upstream defect: loop discards partial UART frame between ticks")
def test_tc_f05_touch_packet_split_across_ticks_registers_press(switch):
    """TC-F05: Touch packet split across loop ticks must be buffered and recognized.

    Expected Behavior: When touch sensor data arrives in chunks across separate scheduler ticks,
    the driver must buffer the partial packet and register the press without dropping the event.
    """
    switch.drain_logs()

    # Send first 5 bytes of a valid Gang 1 tap frame
    switch.send_raw_bytes(bytes([0xAA, 0x55, 0x01, 0x02, 0x02]))
    # Wait until loop() has processed the partial buffer (it logs the received bytes) before sending the rest.
    # A fixed delay was not enough under emulation: both halves could arrive before the next loop() pass,
    # so the frame was read whole and the test passed although the defect is present.
    switch.assert_log("- UART-Log -", timeout=2.0, msg="Firmware did not process the partial frame")
    # Send remaining 10 bytes
    switch.send_raw_bytes(bytes([0x00, 0x01, 0x00] + [0x00] * 7))
    time.sleep(0.1)

    # Valid press must be recognized
    # On stock firmware, this fails because loop() discarded state between ticks
    switch.assert_log("Pressed at position 1", timeout=1.0)


@pytest.mark.xfail(reason="Stock firmware upstream defect: 0xAA in the payload restarts the frame, swipe range is lost")
def test_tc_f06_swipe_with_0xaa_channel_bitmap_parsed_safely(switch):
    """TC-F06: Swipe frame containing 0xAA in payload bytes must parse without false header reset.

    Expected Behavior: Payload bytes sharing the sync header value (0xAA) must be accepted as data
    rather than causing an unexpected parser reset mid-frame.
    """
    switch.drain_logs()
    switch.clear_ha_events()

    # Swipe right frame where byte 7 is 0xAA (channels 2, 4, 6, 8)
    frame = bytes([0xAA, 0x55, 0x01, 0x02, 0x03, 0x0C, 0x00, 0xAA] + [0x00] * 7)
    switch.send_raw_bytes(frame)
    time.sleep(0.1)

    # The direction alone is not enough: the truncated frame is still decoded as a swipe right,
    # with an empty channel bitmap. Require the decoded range (channels 2 to 8, buttons 1 to 3 on 3 gangs).
    # Match the complete expected event, so an older swipe event still in transit cannot satisfy the wait.
    switch.assert_log("Swipe right", timeout=1.5)
    event = switch.wait_for_ha_event(
        "swipe", timeout=1.5, action="right",
        **{"swipe-from": 2, "swipe-to": 8, "swipe-from-button": 1, "swipe-to-button": 3},
    )
    assert event is not None, f"No swipe right event with range 2-8 (buttons 1-3). Received: {switch.get_ha_events('swipe')}"
