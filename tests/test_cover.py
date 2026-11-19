"""Test Cases: Cover package (time-based cover driven by relays 1 and 2, with a software interlock)."""
from aioesphomeapi import CoverOperation

# Travel times are set to 3 s in tests/configs/test_cover.yaml. The emulator runs slower than real time, so
# waits for a full travel leave ample margin.
FULL_TRAVEL_TIMEOUT = 20.0


def _close_fully(sw):
    """Bring the cover to the fully closed position (known state for the test)."""
    sw.cover_command(position=0.0)
    assert sw.wait_for_cover(operation=CoverOperation.IDLE, position=0.0, timeout=FULL_TRAVEL_TIMEOUT), (
        f"Cover did not close fully: {sw.get_cover_state()}"
    )


def _assert_in_order(sw, first: str, second: str):
    """Assert both log patterns were received since the last drain, `first` before `second`."""
    sw.assert_log(second)
    logs = sw.get_recent_logs()
    assert first in logs, f"Expected log pattern '{first}' was not found in logs:\n{logs}"
    assert logs.index(first) < logs.index(second), (
        f"'{first}' must be logged before '{second}':\n{logs}"
    )


def test_tc_cv01_entities(cover_switch):
    """TC-CV01: The cover and its settings are exposed, and the cover relays are not.

    Relays 1 and 2 are 'disabled', so no switch or light can bypass the interlock. Relay 3 stays a regular relay.
    """
    entities = cover_switch._entities

    for name in ("Cover", "Cover open duration", "Cover close duration", "Relay 3"):
        assert name in entities, f"'{name}' should be exposed"
    for name in ("Relay 1", "Relay 2", "Light output 1", "Light output 2"):
        assert name not in entities, f"'{name}' drives a cover relay and must not be exposed"

    for gang in (1, 2, 3):
        options = entities[f"Button {gang} action"].options
        assert "Cover open" in options and "Cover close" in options, (
            f"Button {gang} action is missing the cover actions: {options}"
        )


def test_tc_cv02_full_open_and_close(cover_switch):
    """TC-CV02: A full open energizes only the open relay, and releases it at the end of the travel."""
    _close_fully(cover_switch)

    cover_switch.drain_logs()
    cover_switch.cover_command(position=1.0)
    cover_switch.assert_log("Relay 1: on")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IS_OPENING)

    assert cover_switch.wait_for_cover(operation=CoverOperation.IDLE, position=1.0, timeout=FULL_TRAVEL_TIMEOUT), (
        f"Cover did not open fully: {cover_switch.get_cover_state()}"
    )
    cover_switch.assert_log("Relay 1: off")
    assert "Relay 2: on" not in cover_switch.get_recent_logs(), "The close relay must stay off while opening"

    cover_switch.drain_logs()
    _close_fully(cover_switch)
    cover_switch.assert_log("Relay 2: off")
    assert "Relay 1: on" not in cover_switch.get_recent_logs(), "The open relay must stay off while closing"


def test_tc_cv03_reversal_releases_before_energizing(cover_switch):
    """TC-CV03: Reversing a moving cover turns the active relay off before the opposite one is turned on."""
    _close_fully(cover_switch)

    cover_switch.drain_logs()
    cover_switch.cover_command(position=1.0)
    cover_switch.assert_log("Relay 1: on")

    cover_switch.drain_logs()
    cover_switch.cover_command(position=0.0)
    _assert_in_order(cover_switch, "Relay 1: off", "Relay 2: on")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IS_CLOSING)
    assert "Interlock:" not in cover_switch.get_recent_logs(), "The interlock guard must not be needed"

    cover_switch.drain_logs()
    cover_switch.cover_command(stop=True)
    cover_switch.assert_log("Relay 2: off")


def test_tc_cv04_stop(cover_switch):
    """TC-CV04: A stop releases the active relay and leaves the cover between the end positions."""
    _close_fully(cover_switch)

    cover_switch.drain_logs()
    cover_switch.cover_command(position=1.0)
    cover_switch.assert_log("Relay 1: on")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IS_OPENING)

    cover_switch.drain_logs()
    cover_switch.cover_command(stop=True)
    cover_switch.assert_log("Relay 1: off")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IDLE)
    position = cover_switch.get_cover_state().position
    assert 0.0 < position < 1.0, f"Stopped cover should be between the end positions, got {position}"


def test_tc_cv05_local_buttons(cover_switch):
    """TC-CV05: Buttons set to 'Cover open' / 'Cover close' start the cover, and any of them stops it."""
    cover_switch.set_button_action(1, "Cover open")
    cover_switch.set_button_action(2, "Cover close")
    assert cover_switch.wait_for_entity_state("Button 1 action", "Cover open")
    assert cover_switch.wait_for_entity_state("Button 2 action", "Cover close")
    _close_fully(cover_switch)

    # Open from button 1
    cover_switch.drain_logs()
    cover_switch.tap(1)
    cover_switch.assert_log("Button 1: open")
    cover_switch.assert_log("Relay 1: on")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IS_OPENING)

    # Button 2 stops a moving cover instead of reversing it
    cover_switch.drain_logs()
    cover_switch.tap(2)
    cover_switch.assert_log("Button 2: stop")
    cover_switch.assert_log("Relay 1: off")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IDLE)
    assert "Relay 2: on" not in cover_switch.get_recent_logs()

    # Close from button 2
    cover_switch.drain_logs()
    cover_switch.tap(2)
    cover_switch.assert_log("Button 2: close")
    cover_switch.assert_log("Relay 2: on")
    assert cover_switch.wait_for_cover(operation=CoverOperation.IDLE, position=0.0, timeout=FULL_TRAVEL_TIMEOUT)


def test_tc_cv06_regular_relay_unaffected(cover_switch):
    """TC-CV06: A relay not used by the cover keeps working as a regular relay, and does not move the cover."""
    cover_switch.drain_logs()
    cover_switch.tap(3)
    assert cover_switch.wait_for_entity_state("Relay 3", True), "Button 3 should toggle Relay 3 on"
    cover_switch.tap(3)
    assert cover_switch.wait_for_entity_state("Relay 3", False), "Button 3 should toggle Relay 3 off"
    assert cover_switch.get_cover_state().current_operation == CoverOperation.IDLE
    assert "tx_ultimate_easy.cover" not in cover_switch.get_recent_logs(), "Relay 3 must not drive the cover"
