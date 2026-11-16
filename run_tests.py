#!/usr/bin/env python3
"""TX Ultimate Easy - Automated Standalone Test Runner.

Usage:
    python run_tests.py                 # Run full test suite (auto-compiles missing firmwares)
    python run_tests.py --compile       # Force re-compile all firmware targets before testing
    python run_tests.py -k test_gestures # Pass any pytest arguments
"""
import os
import sys
import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from tests.builder import (  # noqa: E402
    ensure_all_test_assets,
    find_qemu_binary,
    find_esphome_binary,
)


def main():
    """Main CLI entrypoint for orchestrating QEMU test asset builds and pytest execution."""
    os.chdir(SCRIPT_DIR)

    # Parse runner-specific arguments, passing all other options to pytest
    args = sys.argv[1:]
    force_compile = False
    pytest_args = []

    for arg in args:
        if arg in ("--compile", "--rebuild"):
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

    print(f"[*] Launching pytest with arguments: {pytest_args}\n")
    sys.stdout.flush()

    ret = pytest.main(pytest_args)
    sys.exit(int(ret))


if __name__ == "__main__":
    main()
