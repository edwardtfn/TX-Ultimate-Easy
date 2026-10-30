#!/usr/bin/env python3
"""TX Ultimate Easy - Automated Standalone Test Runner.

Usage:
    python run_tests.py                 # Run full test suite (auto-compiles missing firmwares)
    python run_tests.py --compile       # Force re-compile all firmware targets before testing
    python run_tests.py -k test_gestures # Pass any pytest arguments
"""
import os
import sys
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from tests.builder import (  # noqa: E402
    ensure_all_test_assets,
    find_qemu_binary,
    find_esphome_binary,
)


def find_pytest_cmd() -> list:
    """Find pytest executable or use current python -m pytest."""
    if "PYTEST_BIN" in os.environ and os.path.exists(os.environ["PYTEST_BIN"]):
        return [os.environ["PYTEST_BIN"]]

    # 1. Check in same directory as current sys.executable
    py_dir = os.path.dirname(sys.executable)
    for name in ("pytest.exe", "pytest"):
        p = os.path.join(py_dir, name)
        if os.path.exists(p):
            return [p]

    # 2. Check in same directory as esphome
    try:
        esphome_bin = find_esphome_binary()
        esphome_dir = os.path.dirname(esphome_bin)
        for name in ("pytest.exe", "pytest"):
            p = os.path.join(esphome_dir, name)
            if os.path.exists(p):
                # Also run with the python interpreter in that directory if possible
                py_p = os.path.join(esphome_dir, "python.exe")
                if os.path.exists(py_p):
                    return [py_p, "-m", "pytest"]
                return [p]
    except Exception:
        pass

    # 3. Check system PATH
    which = shutil.which("pytest") or shutil.which("pytest.exe")
    if which:
        return [which]

    return [sys.executable, "-m", "pytest"]


def main():
    os.chdir(SCRIPT_DIR)

    # Parse arguments
    args = sys.argv[1:]
    force_compile = False
    pytest_args = []

    for arg in args:
        if arg in ("--compile", "--rebuild", "-c"):
            force_compile = True
        else:
            pytest_args.append(arg)

    print("=" * 70)
    print(" TX Ultimate Easy — Standalone QEMU Integration Test Runner")
    print("=" * 70)

    try:
        qemu_bin = find_qemu_binary()
        print(f"[*] Found QEMU emulator:  {qemu_bin}")
    except FileNotFoundError as e:
        print(f"[!] Warning: {e}")

    try:
        esphome_bin = find_esphome_binary()
        print(f"[*] Found ESPHome tool:    {esphome_bin}")
    except FileNotFoundError as e:
        print(f"[!] Warning: {e}")

    # Build / prepare flash images
    print("[*] Checking test firmware binaries and QEMU flash images...")
    ensure_all_test_assets(force=force_compile)

    # Launch pytest
    pytest_cmd = find_pytest_cmd() + pytest_args
    print(f"[*] Executing test runner: {' '.join(pytest_cmd)}\n")
    sys.stdout.flush()

    res = subprocess.run(pytest_cmd)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
