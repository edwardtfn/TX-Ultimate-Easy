import pytest
from tests.builder import ensure_all_test_assets
from tests.qemu_harness import (
    QemuHarness,
    FLASH_INSTANT_BIN_DEFAULT,
    FLASH_LIGHT_BIN_DEFAULT,
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


@pytest.fixture(scope="session")
def qemu_instant_switch():
    """Session-scoped QEMU harness instance running Instant Click Mode firmware."""
    print("\n[*] Initializing QEMU Instant-Click switch harness (session scope)...")
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


@pytest.fixture(scope="session")
def qemu_light_switch():
    """Session-scoped QEMU harness instance running Light Relay Mode firmware."""
    print("\n[*] Initializing QEMU Light Relay Mode switch harness (session scope)...")
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
