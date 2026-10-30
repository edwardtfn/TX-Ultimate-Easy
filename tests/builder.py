"""Standalone Firmware Builder and Toolchain Locator for TX Ultimate Easy Tests."""
import os
import sys
import shutil
import tempfile
import subprocess

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(REPO_DIR, "tests")
CONFIGS_DIR = os.path.join(TESTS_DIR, "configs")
DEFAULT_BUILD_CACHE_DIR = os.path.join(tempfile.gettempdir(), f"tx_ultimate_{os.path.basename(REPO_DIR)}")


def find_esphome_binary() -> str:
    """Locate the esphome executable across env, venv, and system PATH."""
    if "ESPHOME_BIN" in os.environ and os.path.exists(os.environ["ESPHOME_BIN"]):
        return os.environ["ESPHOME_BIN"]

    # Same directory as current python interpreter
    py_dir = os.path.dirname(sys.executable)
    for name in ("esphome.exe", "esphome"):
        p = os.path.join(py_dir, name)
        if os.path.exists(p):
            return p

    # Standard venv location on Windows
    local_venv = r"C:\Users\Al\AppData\Local\esphome-venv\Scripts\esphome.exe"
    if os.path.exists(local_venv):
        return local_venv

    which = shutil.which("esphome") or shutil.which("esphome.exe")
    if which:
        return which

    raise FileNotFoundError("Could not locate 'esphome' executable. Please set ESPHOME_BIN or activate your venv.")


def find_qemu_binary() -> str:
    """Locate the qemu-system-xtensa executable across env, Espressif tools, and PATH."""
    for env_var in ("QEMU_BIN", "QEMU_SYSTEM_XTENSA"):
        if env_var in os.environ and os.path.exists(os.environ[env_var]):
            return os.environ[env_var]

    which = shutil.which("qemu-system-xtensa") or shutil.which("qemu-system-xtensa.exe")
    if which:
        return which

    # Scan ~/.espressif/tools/qemu-xtensa for Windows/Linux
    espressif_root = os.path.expanduser("~/.espressif/tools/qemu-xtensa")
    if os.path.isdir(espressif_root):
        for root, _, files in os.walk(espressif_root):
            for f in files:
                if f in ("qemu-system-xtensa.exe", "qemu-system-xtensa"):
                    return os.path.join(root, f)

    default_known = r"C:\Users\Al\.espressif\tools\qemu-xtensa\esp_develop_9.2.2_20260417\qemu\bin\qemu-system-xtensa.exe"
    if os.path.exists(default_known):
        return default_known

    raise FileNotFoundError(
        "Could not locate 'qemu-system-xtensa'. Please set QEMU_BIN environment variable or install Espressif QEMU."
    )


def ensure_efuse_bin() -> str:
    """Ensure the 124-byte dummy efuse binary exists."""
    efuse_path = os.path.join(CONFIGS_DIR, "qemu_efuse.bin")
    if not os.path.exists(efuse_path):
        os.makedirs(CONFIGS_DIR, exist_ok=True)
        # Default efuse with MAC and basic config
        data = bytearray(124)
        data[13] = 0x80
        data[22] = 0x10
        with open(efuse_path, "wb") as f:
            f.write(data)
    return efuse_path


def build_and_pad_firmware(
    config_filename: str,
    output_flash_name: str,
    force: bool = False,
    build_cache_dir: str = DEFAULT_BUILD_CACHE_DIR,
) -> str:
    """Compile an ESPHome YAML config to a local temp build dir and generate an 8MB padded QEMU flash image."""
    config_path = os.path.join(CONFIGS_DIR, config_filename)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config YAML not found: {config_path}")

    target_name = os.path.splitext(config_filename)[0]
    target_build_dir = os.path.join(build_cache_dir, target_name)
    output_flash_path = os.path.join(build_cache_dir, output_flash_name)
    factory_bin = os.path.join(target_build_dir, "build", "firmware.factory.bin")

    os.makedirs(target_build_dir, exist_ok=True)

    # Check if rebuild is necessary
    needs_build = force or not os.path.exists(output_flash_path) or not os.path.exists(factory_bin)
    if not needs_build:
        flash_mtime = os.path.getmtime(output_flash_path)
        # Check if source config or repo files are newer
        if os.path.getmtime(config_path) > flash_mtime:
            needs_build = True
        else:
            esphome_dir = os.path.join(REPO_DIR, "ESPHome")
            if os.path.isdir(esphome_dir):
                for fname in os.listdir(esphome_dir):
                    fpath = os.path.join(esphome_dir, fname)
                    if os.path.isfile(fpath) and os.path.getmtime(fpath) > flash_mtime:
                        needs_build = True
                        break
            components_dir = os.path.join(REPO_DIR, "components")
            if not needs_build and os.path.isdir(components_dir):
                for root, _, files in os.walk(components_dir):
                    for fname in files:
                        fpath = os.path.join(root, fname)
                        if os.path.getmtime(fpath) > flash_mtime:
                            needs_build = True
                            break

    if needs_build:
        esphome_exe = find_esphome_binary()
        print(f"[*] Compiling firmware target '{target_name}' using {esphome_exe}...")

        # Read config, inject build_path to local temp to ensure smooth compilation (avoids SMB file locking issues)
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Generate a temporary config located in target_build_dir
        abs_components = os.path.join(REPO_DIR, "components").replace("\\", "/")
        abs_esphome = os.path.join(REPO_DIR, "ESPHome").replace("\\", "/")
        abs_stubs = os.path.join(CONFIGS_DIR, "qemu_stubs.h").replace("\\", "/")

        content = content.replace("../../components", abs_components)
        content = content.replace("../../ESPHome", abs_esphome)
        content = content.replace("qemu_stubs.h", abs_stubs)

        # Inject build_path under esphome
        build_path_str = target_build_dir.replace("\\", "/")
        if "build_path:" not in content:
            content = content.replace("esphome:\n", f"esphome:\n  build_path: {build_path_str}\n")

        temp_config_path = os.path.join(target_build_dir, f"{target_name}.yaml")
        with open(temp_config_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Execute esphome compile
        cmd = [esphome_exe, "compile", temp_config_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if res.returncode != 0:
            print(f"[!] Compilation failed for {target_name}:\n{res.stdout}")
            raise RuntimeError(f"ESPHome compilation failed for {target_name}")

        if not os.path.exists(factory_bin):
            raise FileNotFoundError(f"Expected factory binary not found at {factory_bin}")

        # Pad to 8MB
        with open(factory_bin, "rb") as f:
            bin_data = f.read()

        target_size = 8 * 1024 * 1024
        padded = bin_data + b"\xFF" * (target_size - len(bin_data))
        with open(output_flash_path, "wb") as f:
            f.write(padded)
        print(f"[+] Prepared 8MB QEMU flash image: {output_flash_path} ({len(padded)} bytes)")

    return output_flash_path


def ensure_all_test_assets(force: bool = False, build_cache_dir: str = DEFAULT_BUILD_CACHE_DIR):
    """Ensure all QEMU flash images and efuse assets exist prior to running tests."""
    ensure_efuse_bin()
    std_flash = build_and_pad_firmware(
        "test_standard.yaml", "qemu_flash_test.bin", force=force, build_cache_dir=build_cache_dir
    )
    inst_flash = build_and_pad_firmware(
        "test_instant.yaml", "qemu_flash_instant.bin", force=force, build_cache_dir=build_cache_dir
    )
    light_flash = build_and_pad_firmware(
        "test_light.yaml", "qemu_flash_light.bin", force=force, build_cache_dir=build_cache_dir
    )
    return std_flash, inst_flash, light_flash
