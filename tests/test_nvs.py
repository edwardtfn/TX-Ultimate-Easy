"""Test Cases: NVS usage (where settings are saved) and behaviour when NVS is full, under QEMU emulation."""
import re
import time

# Most NVS entries the standard test build may use once every saved setting has been written.
# The build saves 25 entities: about 82 entries when all of them are written (a saved value takes 3 NVS entries,
# a light 4). Before the relay indicators and other derived lights stopped being saved, it saved 52 entities:
# about 189 entries. The limit sits between the two, so the derived lights cannot quietly start saving again.
NVS_ENTRY_BUDGET = 120

# Size of the NVS partition in tests/configs/nvs_small_partitions.csv
NVS_SMALL_PARTITION_SIZE = 0x5000

# Dummy settings saved per API call: each emulated flash write takes ~0.2 s, so this stays well under the watchdog
NVS_FILL_CHUNK = 20
# Upper bound of dummy settings: a 20 KB NVS partition holds far fewer, so filling always ends with a failed write
NVS_FILL_MAX = 400

NVS_STATS_RE = re.compile(
    r"NVS partition:\s+Size:\s+(\d+) bytes\s+Entries used:\s+(\d+)\s+Entries free:\s+(\d+)\s+Entries:\s+(\d+)"
)


def read_nvs_stats(sw) -> dict:
    """Reconnect the API to trigger the config dump, and return the NVS figures it logs."""
    sw.drain_logs()
    sw.disconnect_api()
    sw.reconnect_api()
    # The config dump runs 5 s after a client connects (DUMP_CONFIG_CALLER_DELAY)
    sw.assert_log("Namespaces:", timeout=20.0)
    match = NVS_STATS_RE.search(sw.get_recent_logs())
    assert match, f"NVS figures not found in the config dump:\n{sw.get_recent_logs()}"
    size, used, free, total = (int(value) for value in match.groups())
    return {"size": size, "used": used, "free": free, "total": total}


def write_every_setting(sw):
    """Change, then restore, every setting the standard build saves, so all of them are written to NVS."""
    for gang in (1, 2, 3):
        sw.set_relay(gang, True)
        sw.set_gang_light_mode(gang, "Both")
    for light in ("Lights (all)", "Light - Bottom", "Light - Left", "Light - Right", "Light - Top"):
        sw.set_light(light, True)
        sw.set_light(light, False)
    sw.set_night_mode(True)
    sw.set_night_mode(False)
    sw.set_button_action(1, "None")
    sw.set_button_action(1, "Relay 1 (toggle)")
    for gang in (1, 2, 3):
        sw.set_relay(gang, False)
        sw.set_gang_light_mode(gang, "Bottom")
    # Allow the preferences component to flush everything to NVS (flash_write_interval: 1s in the test builds)
    time.sleep(3.0)


def test_tc_n01_nvs_stats_logged(switch):
    """TC-N01: The config dump reports the NVS partition size and entry usage."""
    stats = read_nvs_stats(switch)
    assert stats["size"] > 0
    assert stats["total"] > 0
    assert stats["used"] + stats["free"] <= stats["total"]


def test_tc_n02_nvs_usage_within_budget(switch):
    """TC-N02: With every setting written, NVS usage stays within budget (derived lights are not saved)."""
    write_every_setting(switch)
    stats = read_nvs_stats(switch)
    print(f"\n  [*] NVS entries used: {stats['used']} of {stats['total']} (budget {NVS_ENTRY_BUDGET})", flush=True)
    assert stats["used"] <= NVS_ENTRY_BUDGET, (
        f"NVS uses {stats['used']} entries, over the budget of {NVS_ENTRY_BUDGET}: "
        "check for new entities that save derived state (restore_mode / restore_value)"
    )


def test_tc_n03_nvs_small_partition_detected(nvs_small_switch):
    """TC-N03: The small NVS test build reports its 20 KB partition."""
    stats = read_nvs_stats(nvs_small_switch)
    assert stats["size"] == NVS_SMALL_PARTITION_SIZE


def test_tc_n04_full_nvs_degrades_safely(nvs_small_switch):
    """TC-N04: When NVS is full, saving fails with a logged error, but the device keeps working and still boots.

    Emulates a device whose NVS was filled by settings left behind over many releases.
    """
    sw = nvs_small_switch
    sw.drain_logs()

    # 1. Fill NVS with dummy settings until a write fails
    filled = False
    for start in range(0, NVS_FILL_MAX, NVS_FILL_CHUNK):
        sw.execute_action("test_nvs_fill", {"start": start, "count": NVS_FILL_CHUNK})
        sw.assert_log(f"Dummy settings {start} to {start + NVS_FILL_CHUNK - 1}:", timeout=20.0)
        if "NOT saved" in sw.get_recent_logs():
            filled = True
            break
    assert filled, f"NVS did not fill up with {NVS_FILL_MAX} dummy settings"
    sw.assert_log("failed. Last error=")
    print(f"\n  [*] NVS full after {start + NVS_FILL_CHUNK} dummy settings", flush=True)

    # 2. The device keeps working: relays still switch, and their state is still reported
    sw.drain_logs()
    sw.set_relay(1, True)
    assert sw.wait_for_entity_state("Relay 1", True), "Relay 1 did not turn on with a full NVS"
    sw.set_relay(1, False)
    assert sw.wait_for_entity_state("Relay 1", False), "Relay 1 did not turn off with a full NVS"

    # 3. The device still boots with a full NVS, and relays still work afterwards
    print("\n  [*] Rebooting QEMU emulator with a full NVS...", flush=True)
    sw.restart()
    sw.assert_log("Boot completed: Yes", timeout=20.0)
    sw.set_relay(2, True)
    assert sw.wait_for_entity_state("Relay 2", True), "Relay 2 did not turn on after booting with a full NVS"
    sw.set_relay(2, False)
    assert sw.wait_for_entity_state("Relay 2", False)
