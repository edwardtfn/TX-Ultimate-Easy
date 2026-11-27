import pytest
from tests.builder import ensure_all_test_assets
from tests.qemu_harness import (
    QemuHarness,
    FLASH_INSTANT_BIN_DEFAULT,
    FLASH_LIGHT_BIN_DEFAULT,
    FLASH_COVER_BIN_DEFAULT,
    FLASH_NVS_SMALL_BIN_DEFAULT,
)


def pytest_sessionstart(session):
    """Ensure all required firmware binaries and flash images are prepared before tests run."""
    ensure_all_test_assets()


@pytest.fixture(scope="session")
def qemu_switch():
    """Session-scoped QEMU harness instance running Standard firmware."""
    print("\n[*] Initializing QEMU switch harness (session scope)...")
    try:
        harness = QemuHarness()
    except Exception as exc:
        pytest.exit(f"\n[!] FATAL: QEMU firmware failed to initialize/boot: {exc}\nAborting test session.", returncode=1)
    try:
        yield harness
    finally:
        print("\n[*] Shutting down QEMU switch harness...")
        harness.close()


@pytest.fixture
def switch(qemu_switch):
    """Per-test fixture providing access to the live switch."""
    qemu_switch.reset_state()
    return qemu_switch


# The Instant Click, Light Relay Mode and Cover emulators are module-scoped: each is used by one module only, and
# shutting it down afterwards keeps it from competing for CPU with the standard emulator for the rest of the
# session, which adds to the timing jitter.
@pytest.fixture(scope="module")
def qemu_instant_switch():
    """Module-scoped QEMU harness instance running Instant Click Mode firmware."""
    print("\n[*] Initializing QEMU Instant-Click switch harness (module scope)...")
    try:
        harness = QemuHarness(
            log_port=4446,
            touch_port=4447,
            api_port=6054,
            flash_bin=FLASH_INSTANT_BIN_DEFAULT,
        )
    except Exception as exc:
        pytest.exit(f"\n[!] FATAL: Instant-click QEMU firmware failed to initialize/boot: {exc}\nAborting test session.", returncode=1)
    try:
        yield harness
    finally:
        print("\n[*] Shutting down QEMU Instant-Click switch harness...")
        harness.close()


@pytest.fixture
def instant_switch(qemu_instant_switch):
    """Per-test fixture providing access to the live instant-click switch."""
    qemu_instant_switch.reset_state()
    return qemu_instant_switch


@pytest.fixture(scope="module")
def qemu_light_switch():
    """Module-scoped QEMU harness instance running Light Relay Mode firmware."""
    print("\n[*] Initializing QEMU Light Relay Mode switch harness (module scope)...")
    try:
        harness = QemuHarness(
            log_port=4448,
            touch_port=4449,
            api_port=6056,
            flash_bin=FLASH_LIGHT_BIN_DEFAULT,
        )
    except Exception as exc:
        pytest.exit(
            f"\n[!] FATAL: Light mode QEMU firmware failed to initialize/boot: {exc}\nAborting test session.",
            returncode=1,
        )
    try:
        yield harness
    finally:
        print("\n[*] Shutting down QEMU Light Relay Mode switch harness...")
        harness.close()


@pytest.fixture
def light_switch(qemu_light_switch):
    """Per-test fixture providing access to the live light-mode switch."""
    qemu_light_switch.reset_state()
    return qemu_light_switch


@pytest.fixture(scope="module")
def qemu_cover_switch():
    """Module-scoped QEMU harness instance running Cover firmware."""
    print("\n[*] Initializing QEMU Cover switch harness (module scope)...")
    try:
        harness = QemuHarness(
            log_port=4450,
            touch_port=4451,
            api_port=6058,
            flash_bin=FLASH_COVER_BIN_DEFAULT,
        )
    except Exception as exc:
        pytest.exit(
            f"\n[!] FATAL: Cover QEMU firmware failed to initialize/boot: {exc}\nAborting test session.",
            returncode=1,
        )
    try:
        yield harness
    finally:
        print("\n[*] Shutting down QEMU Cover switch harness...")
        harness.close()


@pytest.fixture
def cover_switch(qemu_cover_switch):
    """Per-test fixture providing access to the live cover switch, with the cover stopped."""
    qemu_cover_switch.reset_state()
    qemu_cover_switch.cover_command(stop=True)
    return qemu_cover_switch


@pytest.fixture(scope="module")
def qemu_nvs_small_switch():
    """Module-scoped QEMU harness instance running the small NVS partition firmware."""
    print("\n[*] Initializing QEMU small NVS switch harness (module scope)...")
    try:
        harness = QemuHarness(
            log_port=4452,
            touch_port=4453,
            api_port=6060,
            flash_bin=FLASH_NVS_SMALL_BIN_DEFAULT,
        )
    except Exception as exc:
        pytest.exit(
            f"\n[!] FATAL: Small NVS QEMU firmware failed to initialize/boot: {exc}\nAborting test session.",
            returncode=1,
        )
    try:
        yield harness
    finally:
        print("\n[*] Shutting down QEMU small NVS switch harness...")
        harness.close()


@pytest.fixture
def nvs_small_switch(qemu_nvs_small_switch):
    """Per-test fixture providing access to the live small NVS switch."""
    qemu_nvs_small_switch.reset_state()
    return qemu_nvs_small_switch
