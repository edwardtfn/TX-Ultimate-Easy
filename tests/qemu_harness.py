import socket
import subprocess
import threading
import time
import os
import asyncio
from typing import Optional
from aioesphomeapi import APIClient

from tests.builder import find_qemu_binary, ensure_efuse_bin, DEFAULT_BUILD_CACHE_DIR

FLASH_BIN_DEFAULT = os.path.join(DEFAULT_BUILD_CACHE_DIR, "qemu_flash_test.bin")
FLASH_INSTANT_BIN_DEFAULT = os.path.join(DEFAULT_BUILD_CACHE_DIR, "qemu_flash_instant.bin")
FLASH_LIGHT_BIN_DEFAULT = os.path.join(DEFAULT_BUILD_CACHE_DIR, "qemu_flash_light.bin")
EFUSE_BIN_DEFAULT = ensure_efuse_bin()

# Mapping for 3-gang EU device:
# width = (10 + 3) / 3 = 4
# Gang 1: 0..3 (use 1)
# Gang 2: 4..7 (use 5)
# Gang 3: 8..10 (use 9)
GANG_POSITIONS = {
    1: 1,
    2: 5,
    3: 9
}

BUTTON_ACTION_MAP = {
    "none": "None",
    "toggle": "Relay {gang} (toggle)",
    "relay": "Relay {gang} (toggle)",
    "failsafe": "Relay {gang} (API failsafe only)",
}

GANG_MODE_MAP = {
    "disabled": "Disabled",
    "relay": "Relay",
    "virtualrelay": "Virtual Relay",
    "virtual relay": "Virtual Relay",
    "detachedrelay": "Detached Relay",
    "detached relay": "Detached Relay",
    "detachedvirtualrelay": "Detached Virtual Relay",
    "detached virtual relay": "Detached Virtual Relay",
}

LIGHT_MODE_MAP = {
    "bottom": "Bottom",
    "top": "Top",
    "both": "Both",
    "off": "Disabled",
    "disabled": "Disabled",
}


class QemuHarness:
    """Harness to interact with ESPHome running inside Espressif QEMU.

    Provides:
      - TCP serial logging connection (UART0, port 4444)
      - TCP touch UART frame injection (UART1, port 4445)
      - ESPHome Native API client (OpenEth port 6053) for runtime mode/entity control
      - Background reader thread ensuring zero lost log lines
      - High-level gesture and fuzzing methods
    """

    def __init__(
        self,
        log_port: int = 4444,
        touch_port: int = 4445,
        api_port: int = 6053,
        auto_start_qemu: bool = True,
        qemu_bin: Optional[str] = None,
        flash_bin: Optional[str] = None,
        efuse_bin: Optional[str] = None,
    ):
        self.qemu_bin = qemu_bin or find_qemu_binary()
        self.flash_bin = flash_bin or FLASH_BIN_DEFAULT
        self.efuse_bin = efuse_bin or EFUSE_BIN_DEFAULT
        self.log_port = log_port
        self.touch_port = touch_port
        self.api_port = api_port
        self.proc: Optional[subprocess.Popen] = None
        self.log_sock: Optional[socket.socket] = None
        self.touch_sock: Optional[socket.socket] = None

        # User compatibility: switch.sock refers to log socket
        self.sock: Optional[socket.socket] = None

        self._log_buffer = ""
        self._log_lock = threading.RLock()
        self._reader_running = False
        self._reader_thread: Optional[threading.Thread] = None
        self._last_drain_idx = 0

        self.api_client: Optional[APIClient] = None
        self._api_loop: Optional[asyncio.AbstractEventLoop] = None
        self._entities = {}

        try:
            if auto_start_qemu:
                print("  [+] Starting QEMU process...", flush=True)
                self._start_qemu(self.qemu_bin, self.flash_bin, self.efuse_bin)

            print("  [+] Connecting serial sockets...", flush=True)
            self._connect_sockets()
            print("  [+] Starting log reader thread...", flush=True)
            self._start_log_reader()
            print("  [+] Waiting for firmware boot...", flush=True)
            self._wait_for_boot()
            print("  [+] Initializing Native API client...", flush=True)
            self._init_api_client()
            print("  [+] Harness ready!", flush=True)
        except Exception:
            self.close()
            raise

    def _start_qemu(self, qemu_bin: str, flash_bin: str, efuse_bin: str):
        if not os.path.exists(flash_bin):
            raise FileNotFoundError(f"Flash image not found: {flash_bin}")

        qemu_cmd = [
            qemu_bin,
            "-nographic",
            "-M", "esp32",
            "-m", "4M",
            "-drive", f"file={flash_bin},if=mtd,format=raw",
            "-drive", f"file={efuse_bin},if=none,format=raw,id=efuse",
            "-global", "driver=nvram.esp32.efuse,property=drive,value=efuse",
            "-nic", f"user,model=open_eth,hostfwd=tcp::{self.api_port}-:6053",
            "-serial", f"tcp:127.0.0.1:{self.log_port},server,nowait",
            "-serial", f"tcp:127.0.0.1:{self.touch_port},server,nowait",
        ]
        self.proc = subprocess.Popen(
            qemu_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _connect_sockets(self, timeout: float = 15.0):
        time.sleep(1.0)
        start = time.time()
        while time.time() - start < timeout:
            s_log = None
            s_touch = None
            try:
                s_log = socket.create_connection(("127.0.0.1", self.log_port), timeout=2.0)
                s_touch = socket.create_connection(("127.0.0.1", self.touch_port), timeout=2.0)
                self.log_sock = s_log
                self.touch_sock = s_touch
                self.sock = self.log_sock
                return
            except (ConnectionRefusedError, socket.timeout, OSError):
                if s_log:
                    s_log.close()
                if s_touch:
                    s_touch.close()
                time.sleep(0.5)
        raise TimeoutError(f"Could not connect to QEMU serial ports {self.log_port}/{self.touch_port} within {timeout}s")

    def _start_log_reader(self):
        self._reader_running = True
        self._reader_thread = threading.Thread(target=self._log_reader_loop, daemon=True)
        self._reader_thread.start()

    def _log_reader_loop(self):
        self.log_sock.settimeout(0.5)
        while self._reader_running:
            try:
                chunk = self.log_sock.recv(4096)
                if not chunk:
                    break
                text = chunk.decode(errors="ignore")
                with self._log_lock:
                    self._log_buffer += text
            except socket.timeout:
                continue
            except Exception:
                break

    def _wait_for_boot(self, timeout: float = 120.0):
        start = time.time()
        while time.time() - start < timeout:
            with self._log_lock:
                booted = (
                    "Boot completed: Yes" in self._log_buffer
                    or "Address: tx-qemu-test.local:6053" in self._log_buffer
                )
            if booted:
                time.sleep(1.0)
                self.drain_logs()
                return
            time.sleep(0.3)
        raise TimeoutError(f"QEMU firmware failed to boot within {timeout}s. Logs received ({len(self._log_buffer)} bytes):\n{self._log_buffer[-500:]}")

    def _run_api_loop(self):
        asyncio.set_event_loop(self._api_loop)
        self._api_loop.run_forever()

    async def _async_init_api(self):
        self.api_client = APIClient("127.0.0.1", self.api_port, password="", noise_psk=None)
        await self.api_client.connect(login=True)
        self._states = {}

        def _on_state(state):
            self._states[state.key] = getattr(state, "state", None)

        self.api_client.subscribe_states(_on_state)
        entities, _ = await self.api_client.list_entities_services()
        self._entities = {e.name: e for e in entities}

    def disconnect_api(self):
        """Disconnect the Native API client to simulate Home Assistant connection loss."""
        if self.api_client and self._api_loop:
            future = asyncio.run_coroutine_threadsafe(self.api_client.disconnect(), self._api_loop)
            future.result(timeout=4.0)
            time.sleep(0.5)

    async def _async_reconnect_api(self):
        await self.api_client.connect(login=True)
        def _on_state(state):
            self._states[state.key] = getattr(state, "state", None)
        self.api_client.subscribe_states(_on_state)

    def reconnect_api(self):
        """Reconnect the Native API client after simulated connection loss."""
        if self.api_client and self._api_loop:
            future = asyncio.run_coroutine_threadsafe(self._async_reconnect_api(), self._api_loop)
            future.result(timeout=4.0)
            time.sleep(0.5)

    def _init_api_client(self):
        try:
            self._api_loop = asyncio.new_event_loop()
            self._api_thread = threading.Thread(target=self._run_api_loop, daemon=True)
            self._api_thread.start()

            future = asyncio.run_coroutine_threadsafe(self._async_init_api(), self._api_loop)
            future.result(timeout=10.0)
            time.sleep(0.5)
            print(f"  [+] Connected to ESPHome Native API ({len(self._entities)} entities)", flush=True)
        except Exception as e:
            print(f"  [!] Warning: ESPHome Native API init failed ({e}), continuing in serial-only mode", flush=True)
            self.api_client = None

    def close(self):
        self._reader_running = False
        if self.api_client and self._api_loop:
            try:
                future = asyncio.run_coroutine_threadsafe(self.api_client.disconnect(), self._api_loop)
                future.result(timeout=3.0)
            except Exception:
                pass
            try:
                self._api_loop.call_soon_threadsafe(self._api_loop.stop)
            except Exception:
                pass
        if self.log_sock:
            try:
                self.log_sock.close()
            except Exception:
                pass
        if self.touch_sock:
            try:
                self.touch_sock.close()
            except Exception:
                pass
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()
        self.proc = None

    def restart(self):
        """Cleanly restart QEMU and reconnect API/sockets to test NVS persistence across boots."""
        self.close()
        time.sleep(0.5)
        self._log_buffer = ""
        self._last_drain_idx = 0
        self._start_qemu(self.qemu_bin, self.flash_bin, self.efuse_bin)
        self._connect_sockets()
        self._start_log_reader()
        self._wait_for_boot()
        self._init_api_client()

    # --- Log Inspection & Synchronization ---

    def drain_logs(self):
        """Reset the search window to ignore logs received prior to this call."""
        with self._log_lock:
            self._last_drain_idx = len(self._log_buffer)

    def get_recent_logs(self) -> str:
        with self._log_lock:
            return self._log_buffer[self._last_drain_idx:]

    def read_logs_until(self, expected_str: str, timeout: float = 4.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            with self._log_lock:
                recent = self._log_buffer[self._last_drain_idx:]
                if expected_str in recent:
                    return True
            time.sleep(0.05)
        return False

    def assert_log(self, expected_str: str, timeout: float = 7.0, msg: Optional[str] = None):
        assert self.read_logs_until(expected_str, timeout=timeout), (
            msg or f"Expected log pattern '{expected_str}' was not found in logs:\n{self.get_recent_logs()}"
        )

    def assert_no_log(self, unexpected_str: str, duration: float = 1.0, msg: Optional[str] = None):
        time.sleep(duration)
        recent = self.get_recent_logs()
        assert unexpected_str not in recent, (
            msg or f"Unexpected log pattern '{unexpected_str}' appeared in logs:\n{recent}"
        )

    # --- Touch Frame Injection ---

    def send_touch_frame(self, byte4: int, byte5: int, byte6: int, byte7: int = 0x00):
        """Send a standard 15-byte Sonoff TX Ultimate touch frame."""
        frame = bytes([0xAA, 0x55, 0x01, 0x02, byte4, byte5, byte6, byte7] + [0x00] * 7)
        self.touch_sock.sendall(frame)

    def send_raw_bytes(self, data: bytes):
        """Send raw bytes directly to the touch UART for fuzzing/breaking tests."""
        self.touch_sock.sendall(data)

    # --- High-Level Gestures ---

    def tap(self, gang: int = 1, hold_ms: float = 50.0):
        """Simulate a standard tap on the specified gang."""
        pos = GANG_POSITIONS.get(gang, 1)
        # Press
        self.send_touch_frame(0x02, 0x00, pos, 0x00)
        time.sleep(hold_ms / 1000.0)
        # Release
        self.send_touch_frame(0x01, pos, pos, 0x00)

    def double_click(self, gang: int = 1, interval_ms: float = 80.0):
        """Simulate a double-click on the specified gang with a configured inter-tap gap."""
        self.tap(gang=gang)
        time.sleep(interval_ms / 1000.0)
        self.tap(gang=gang)

    def multi_click(self, gang: int = 1, count: int = 3, interval_ms: float = 40.0, hold_ms: float = 20.0):
        """Simulate N rapid clicks on the specified gang."""
        for i in range(count):
            self.tap(gang=gang, hold_ms=hold_ms)
            if i < count - 1:
                time.sleep(interval_ms / 1000.0)

    def long_press(self, gang: int = 1, duration_ms: float = 600.0):
        """Simulate a long press on the specified gang."""
        pos = GANG_POSITIONS.get(gang, 1)
        # Press
        self.send_touch_frame(0x02, 0x00, pos, 0x00)
        time.sleep(duration_ms / 1000.0)
        # Long release offset is position + 16 (0x10)
        self.send_touch_frame(0x01, pos + 16, pos, 0x00)

    def swipe_right(self, start_gang: int = 1, end_gang: int = 3, transit_ms: float = 60.0):
        """Simulate a realistic physical swipe-right / swipe-down gesture.

        Real-world sequence:
        1. Touch-down (PRESS) at start_gang.
        2. Transit across capacitive channels (transit_ms delay).
        3. Touch IC recognizes swipe and emits SWIPE_RIGHT frame.
        4. Finger lifts off (RELEASE) at end_gang.
        """
        pos_start = GANG_POSITIONS.get(start_gang, 2)
        pos_end = GANG_POSITIONS.get(end_gang, 8)
        # 1. Contact
        self.send_touch_frame(0x02, 0x00, pos_start, 0x00)
        time.sleep(transit_ms / 1000.0)
        # 2. Gesture crossing frame
        self.send_touch_frame(0x03, 0x0C, 0x00, 0xFF)
        time.sleep(0.02)
        # 3. Lift-off
        self.send_touch_frame(0x01, pos_end, pos_end, 0x00)

    def swipe_left(self, start_gang: int = 3, end_gang: int = 1, transit_ms: float = 60.0):
        """Simulate a realistic physical swipe-left / swipe-up gesture.

        Real-world sequence:
        1. Touch-down (PRESS) at start_gang.
        2. Transit across capacitive channels (transit_ms delay).
        3. Touch IC recognizes swipe and emits SWIPE_LEFT frame.
        4. Finger lifts off (RELEASE) at end_gang.
        """
        pos_start = GANG_POSITIONS.get(start_gang, 8)
        pos_end = GANG_POSITIONS.get(end_gang, 2)
        # 1. Contact
        self.send_touch_frame(0x02, 0x00, pos_start, 0x00)
        time.sleep(transit_ms / 1000.0)
        # 2. Gesture crossing frame
        self.send_touch_frame(0x03, 0x0D, 0x00, 0xFF)
        time.sleep(0.02)
        # 3. Lift-off
        self.send_touch_frame(0x01, pos_end, pos_end, 0x00)

    def multi_touch(self, contact_gang: int = 2):
        """Simulate a realistic multi-touch / palm mash gesture.

        Real-world sequence:
        1. Palm makes initial physical contact (e.g. center gang).
        2. Multi-sensor saturation triggers MULTI_TOUCH frame (0x01, 0x0B).
        3. Palm lifts off (RELEASE).
        """
        pos = GANG_POSITIONS.get(contact_gang, 5)
        # 1. Palm slap contact
        self.send_touch_frame(0x02, 0x00, pos, 0x00)
        time.sleep(0.03)
        # 2. Multi-touch report
        self.send_touch_frame(0x01, 0x0B, 0x00, 0x00)
        time.sleep(0.03)
        # 3. Lift-off
        self.send_touch_frame(0x01, pos, pos, 0x00)

    def palm_mash(self, contact_gang: int = 2):
        """Alias for multi_touch representing a physical palm slap."""
        self.multi_touch(contact_gang=contact_gang)

    def partial_swipe(self, start_pos: int = 2, end_pos: int = 3, duration_ms: float = 60.0):
        """Simulate a short/hesitant drag below the hardware swipe threshold.

        The finger lands, drags slightly within or across gangs, and releases
        without generating a SWIPE UART packet.
        """
        self.send_touch_frame(0x02, 0x00, start_pos, 0x00)
        time.sleep(duration_ms / 1000.0)
        self.send_touch_frame(0x01, end_pos, end_pos, 0x00)

    def hardware_long_touch(self, gang: int = 1, hold_ms: float = 200.0):
        """Simulate a hardware-detected long touch (touch IC reports position + 16 on release)."""
        pos = GANG_POSITIONS.get(gang, 2)
        self.send_touch_frame(0x02, 0x00, pos, 0x00)
        time.sleep(hold_ms / 1000.0)
        self.send_touch_frame(0x01, pos + 16, pos, 0x00)

    # --- Mode & Configuration Controls (Native API) ---

    def set_button_action(self, gang: int, action: str):
        """Set Button action at runtime: 'None', 'Relay X (toggle)', 'Relay X (API failsafe only)'."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        template = BUTTON_ACTION_MAP.get(action.lower().strip(), action)
        normalized = template.format(gang=gang)
        entity_name = f"Button {gang} action"
        entity = self._entities.get(entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found. Available: {list(self._entities.keys())}")
        self.drain_logs()
        self._api_loop.call_soon_threadsafe(self.api_client.select_command, entity.key, normalized)
        time.sleep(0.5)

    def set_gang_mode(self, gang: int, mode: str):
        """Set Gang mode at runtime if entity exists."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        normalized = GANG_MODE_MAP.get(mode.lower().strip(), mode)
        entity_name = f"Gang {gang} mode"
        entity = self._entities.get(entity_name)
        if not entity:
            # Fallback to button action if stock
            return
        self.drain_logs()
        self._api_loop.call_soon_threadsafe(self.api_client.select_command, entity.key, normalized)
        time.sleep(0.5)

    def set_gang_light_mode(self, gang: int, light_mode: str):
        """Set Gang / Relay light mode at runtime: 'Bottom', 'Top', 'Both', 'Disabled' ('Off')."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        normalized = LIGHT_MODE_MAP.get(light_mode.lower().strip(), light_mode)
        # Check stock name first (Relay X light mode), then refactored name (Gang X light mode)
        entity_name = f"Relay {gang} light mode"
        if entity_name not in self._entities:
            entity_name = f"Gang {gang} light mode"
        entity = self._entities.get(entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")
        self.drain_logs()
        self._api_loop.call_soon_threadsafe(self.api_client.select_command, entity.key, normalized)
        time.sleep(0.5)

    def set_switch(self, name: str, state: bool):
        """Set a switch entity by name."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity = self._entities.get(name)
        if not entity:
            raise ValueError(f"Entity '{name}' not found. Available switches: {[k for k, v in self._entities.items() if 'switch' in str(type(v)).lower()]}")
        self._api_loop.call_soon_threadsafe(self.api_client.switch_command, entity.key, state)
        time.sleep(0.5)

    def set_select(self, name: str, option: str):
        """Set a select entity by name."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity = self._entities.get(name)
        if not entity:
            raise ValueError(f"Entity '{name}' not found")
        self._api_loop.call_soon_threadsafe(self.api_client.select_command, entity.key, option)
        time.sleep(0.5)

    def set_number(self, name: str, value: float):
        """Set a number entity by name."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity = self._entities.get(name)
        if not entity:
            raise ValueError(f"Entity '{name}' not found")
        self._api_loop.call_soon_threadsafe(self.api_client.number_command, entity.key, float(value))
        time.sleep(0.5)

    def set_light(self, name: str, state: bool):
        """Turn a light entity on or off by name."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity = self._entities.get(name)
        if not entity:
            raise ValueError(f"Entity '{name}' not found")
        self._api_loop.call_soon_threadsafe(self.api_client.light_command, entity.key, state)
        time.sleep(0.5)

    def press_button(self, name: str):
        """Press a button entity by name."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity = self._entities.get(name)
        if not entity:
            raise ValueError(f"Entity '{name}' not found")
        self._api_loop.call_soon_threadsafe(self.api_client.button_command, entity.key)
        time.sleep(0.5)

    def set_vibration_feedback(self, mode: str):
        """Set touch vibration feedback mode: 'Disabled', 'On press', 'On release', 'Always'."""
        self.set_select("Touch - Vibration feedback", mode)

    def set_vibration_duration(self, duration_ms: float):
        """Set touch vibration duration in ms."""
        self.set_number("Vibrate duration", duration_ms)

    def set_night_mode(self, state: bool):
        """Toggle Night Mode on/off."""
        self.set_switch("Night Mode", state)

    def set_relay(self, gang: int, state: bool):
        """Directly toggle or set physical relay state via API."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity_name = f"Relay {gang}"
        entity = self._entities.get(entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")
        self._api_loop.call_soon_threadsafe(self.api_client.switch_command, entity.key, state)
        time.sleep(0.3)

    def set_light(self, light_name: str, state: bool):
        """Directly set a light entity state via API."""
        if not self.api_client or not self._api_loop:
            raise RuntimeError("ESPHome Native API client is not connected")
        entity = self._entities.get(light_name)
        if not entity:
            raise ValueError(f"Entity '{light_name}' not found")
        import functools
        self._api_loop.call_soon_threadsafe(
            functools.partial(self.api_client.light_command, entity.key, state=state)
        )
        time.sleep(0.3)

    def get_entity_state(self, name: str, timeout: float = 4.0):
        """Get the current subscribed state of an entity by name, waiting for state packet if needed."""
        entity = self._entities.get(name)
        if not entity:
            return None
        start = time.time()
        while time.time() - start < timeout:
            if hasattr(self, "_states") and entity.key in self._states:
                val = self._states[entity.key]
                if val is not None:
                    return val
            time.sleep(0.1)
        return None

    def wait_for_entity_state(self, name: str, expected_state, timeout: float = 6.0) -> bool:
        """Wait until an entity's subscribed state matches expected value."""
        entity = self._entities.get(name)
        if not entity:
            return False
        start = time.time()
        while time.time() - start < timeout:
            if hasattr(self, "_states") and entity.key in self._states:
                if self._states[entity.key] == expected_state:
                    return True
            time.sleep(0.1)
        return False

    def reset_state(self):
        """Reset relays, virtual relays, and gang modes to default test state."""
        if not self.api_client or not self._api_loop:
            self.drain_logs()
            return

        changed = False
        for g in (1, 2, 3):
            # 1. Reset physical relays to OFF
            r_name = f"Relay {g}"
            if self.get_entity_state(r_name) is True:
                entity = self._entities.get(r_name)
                if entity:
                    self._api_loop.call_soon_threadsafe(self.api_client.switch_command, entity.key, False)
                    changed = True

            # Reset pulse times to 0.0 (disabled)
            pt_name = f"Relay {g} Pulse Time"
            pt_val = self.get_entity_state(pt_name)
            if pt_val is not None and float(pt_val) != 0.0:
                entity = self._entities.get(pt_name)
                if entity:
                    self._api_loop.call_soon_threadsafe(self.api_client.number_command, entity.key, 0.0)
                    changed = True

            # 2. Reset virtual relays to OFF if they exist
            vr_name = f"Virtual Relay {g}"
            if vr_name in self._entities and self.get_entity_state(vr_name) is True:
                entity = self._entities.get(vr_name)
                if entity:
                    self._api_loop.call_soon_threadsafe(self.api_client.switch_command, entity.key, False)
                    changed = True

            # 3. Reset gang modes or button actions
            m_name = f"Gang {g} mode"
            if m_name in self._entities and self.get_entity_state(m_name) != "Relay":
                entity = self._entities.get(m_name)
                if entity:
                    self._api_loop.call_soon_threadsafe(self.api_client.select_command, entity.key, "Relay")
                    changed = True

            ba_name = f"Button {g} action"
            default_ba = f"Relay {g} (toggle)"
            if ba_name in self._entities and self.get_entity_state(ba_name) != default_ba:
                entity = self._entities.get(ba_name)
                if entity:
                    self._api_loop.call_soon_threadsafe(self.api_client.select_command, entity.key, default_ba)
                    changed = True

        # 5. Reset Night Mode to OFF if present
        nm_name = "Night Mode"
        if self.get_entity_state(nm_name) is True:
            entity = self._entities.get(nm_name)
            if entity:
                self._api_loop.call_soon_threadsafe(self.api_client.switch_command, entity.key, False)
                changed = True

        if changed:
            time.sleep(2.5)
        self.drain_logs()
