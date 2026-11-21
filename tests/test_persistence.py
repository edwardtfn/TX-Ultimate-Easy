"""Test Cases: NVS Flash Persistence and Reboot State Recovery under QEMU emulation."""
import time


def test_tc_p01_button_action_persists_across_reboot(switch):
    """TC-P01: Configured Button Action (None) survives hard device restart/reboot."""
    # Switch Button 2 action to None
    switch.set_button_action(2, "None")
    assert switch.wait_for_entity_state("Button 2 action", "None", timeout=6.0)

    # Allow ESPHome preferences component to flush dirty state to NVS
    time.sleep(2.0)

    # Perform reboot
    print("\n  [*] Rebooting QEMU emulator to test Button Action persistence...", flush=True)
    switch.restart()

    # Verify Button 2 action is still None
    assert switch.wait_for_entity_state("Button 2 action", "None", timeout=6.0), (
        "Button 2 action did not persist across reboot!"
    )

    # Clean up state back to Relay 2 (toggle)
    switch.set_button_action(2, "Relay 2 (toggle)")
    time.sleep(1.0)


def test_tc_p02_led_mode_persists_across_reboot(switch):
    """TC-P02: Configured Relay LED Mode survives hard device restart/reboot."""
    # Change Relay 1 LED mode to Top
    switch.set_gang_light_mode(1, "Top")
    entity_name = "Relay 1 light mode" if "Relay 1 light mode" in switch._entities else "Gang 1 light mode"
    assert switch.wait_for_entity_state(entity_name, "Top", timeout=6.0)

    # Allow NVS flush
    time.sleep(2.0)

    # Perform reboot
    print("\n  [*] Rebooting QEMU emulator to test LED Mode persistence...", flush=True)
    switch.restart()

    # Verify LED mode is still Top
    assert switch.wait_for_entity_state(entity_name, "Top", timeout=6.0), (
        f"{entity_name} did not persist across reboot!"
    )

    # Clean up state back to Bottom
    switch.set_gang_light_mode(1, "Bottom")
    time.sleep(1.0)


def test_tc_p03_relay_safe_restore_default_off(switch):
    """TC-P03: Relays enforce safe RESTORE_DEFAULT_OFF after device reboot/power restoration."""
    switch.drain_logs()

    # Reboot the device
    print("\n  [*] Rebooting QEMU emulator to test power-on relay safety...", flush=True)
    switch.restart()

    # Following boot, the config dump logs verify all relays default to safe OFF state
    switch.assert_log("Relays states:")
    switch.assert_log("Relay 1: OFF")
    switch.assert_log("Relay 2: OFF")
    switch.assert_log("Relay 3: OFF")


def test_tc_p04_boot_deferred_led_repaint_sequence(switch):
    """TC-P04: Boot engine executes boot_initialize_relays and repaints LEDs upon boot_done."""
    switch.drain_logs()

    print("\n  [*] Rebooting QEMU emulator to trace boot initialization sequence...", flush=True)
    switch.restart()

    # Verify boot completed and initialization flags are set
    switch.assert_log("Boot completed: Yes")
    switch.assert_log("Boot initialization flags:")
    switch.assert_log("Overall:     YES")


def test_tc_p05_relay_last_state_persists_across_reboot(switch):
    """TC-P05: Relay states persist across reboot per RESTORE_DEFAULT_OFF policy.

    Verifies that active relays restore to their last known state after reboot.
    """
    # 1. Turn Relay 1 and Relay 2 ON, Relay 3 OFF
    switch.set_relay(1, True)
    switch.set_relay(2, True)
    switch.set_relay(3, False)
    # Wait for the states to be reported instead of a fixed delay, which was flaky under emulation
    assert switch.wait_for_entity_state("Relay 1", True)
    assert switch.wait_for_entity_state("Relay 2", True)
    assert switch.wait_for_entity_state("Relay 3", False)

    # Allow ESPHome preferences component to flush dirty state to NVS (flash_write_interval: 1s)
    time.sleep(2.0)

    # 2. Hard reboot device
    print("\n  [*] Rebooting QEMU emulator with active relays to test state persistence...", flush=True)
    switch.restart()

    # 3. Verify relays restored to last known states
    switch.assert_log("Relays states:")
    switch.assert_log("Relay 1: ON")
    switch.assert_log("Relay 2: ON")
    switch.assert_log("Relay 3: OFF")

    # 4. Verify subscribed states (reported after the API reconnects)
    assert switch.wait_for_entity_state("Relay 1", True)
    assert switch.wait_for_entity_state("Relay 2", True)
    assert switch.wait_for_entity_state("Relay 3", False)

    # Cleanup: restore relays to OFF
    switch.set_relay(1, False)
    switch.set_relay(2, False)
    time.sleep(0.5)


def test_tc_p06_momentary_action_persists_and_relay_off_after_reboot(switch):
    """TC-P06: The momentary button action survives a reboot, and its relay is not restored on.

    The momentary option has its own NVS code (5), independent of its position in the select.
    A momentary relay is only on while its button is held, so it is turned off after a restart.
    """
    switch.set_button_action(1, "momentary")
    assert switch.wait_for_entity_state("Button 1 action", "Relay 1 (momentary)")
    # Relay 1 on (as if the power was lost while the button was held)
    switch.set_relay(1, True)
    assert switch.wait_for_entity_state("Relay 1", True)

    # Allow ESPHome preferences component to flush dirty state to NVS (flash_write_interval: 1s)
    time.sleep(2.0)

    print("\n  [*] Rebooting QEMU emulator to test momentary action persistence...", flush=True)
    switch.restart()

    switch.assert_log("Momentary relay 1: off (boot)", timeout=30.0)
    assert switch.wait_for_entity_state("Button 1 action", "Relay 1 (momentary)", timeout=6.0), (
        "Button 1 action did not persist across reboot!"
    )
    assert switch.wait_for_entity_state("Relay 1", False)

    # Clean up state back to Relay 1 (toggle)
    switch.set_button_action(1, "Relay 1 (toggle)")
    time.sleep(1.0)
