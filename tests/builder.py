"""Standalone Firmware Builder and Toolchain Locator for TX Ultimate Easy Tests."""
import os
import sys
import shutil
import tempfile
import subprocess
import hashlib
from typing import Optional

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(REPO_DIR, "tests")
CONFIGS_DIR = os.path.join(TESTS_DIR, "configs")
# Partition table with a small NVS partition, used by test_nvs_small.yaml
NVS_SMALL_PARTITIONS = "nvs_small_partitions.csv"
_REPO_HASH = hashlib.sha256(REPO_DIR.encode("utf-8")).hexdigest()[:8]
DEFAULT_BUILD_CACHE_DIR = os.path.join(tempfile.gettempdir(), f"tx_ultimate_{os.path.basename(REPO_DIR)}_{_REPO_HASH}")


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

    # Check standard virtualenv locations across OS platforms
    candidates = []
    if "LOCALAPPDATA" in os.environ:
        candidates.append(os.path.join(os.environ["LOCALAPPDATA"], "esphome-venv", "Scripts", "esphome.exe"))
    candidates.append(os.path.expanduser("~/.esphome/bin/esphome"))
    candidates.append(os.path.expanduser("~/esphome-venv/bin/esphome"))
    candidates.append(os.path.expanduser("~/esphome-venv/Scripts/esphome.exe"))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

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

    raise FileNotFoundError(
        "Could not locate 'qemu-system-xtensa'. Please set QEMU_BIN environment variable or install Espressif QEMU."
    )


BUILD_INFO_FILENAME = ".build_info"


def get_compiler_identity(esphome_exe: str) -> str:
    """Return the path and reported version of the ESPHome compiler, used to invalidate cached builds."""
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    # Audit: fixed argument list with shell=False
    res = subprocess.run(
        [esphome_exe, "version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
        encoding="utf-8", errors="replace",  # ESPHome prints UTF-8; the Windows default code page cannot decode it
    )
    return f"{os.path.realpath(esphome_exe)}\n{res.stdout.strip()}"


def compute_build_fingerprint(esphome_exe: str, config_path: str) -> str:
    """Return a SHA-256 fingerprint of the compiler identity and of every file the firmware is built from."""
    sources = [config_path, os.path.join(CONFIGS_DIR, "qemu_stubs.h"), os.path.join(CONFIGS_DIR, NVS_SMALL_PARTITIONS)]
    for source_dir in ("ESPHome", "components", "versioning"):
        for root, dirs, files in os.walk(os.path.join(REPO_DIR, source_dir)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            sources.extend(os.path.join(root, fname) for fname in files)
    digest = hashlib.sha256(get_compiler_identity(esphome_exe).encode("utf-8"))
    for src in sorted(sources):
        if not os.path.isfile(src):
            continue
        digest.update(os.path.relpath(src, REPO_DIR).replace("\\", "/").encode("utf-8") + b"\0")
        with open(src, "rb") as f:
            digest.update(hashlib.sha256(f.read()).digest())
    return digest.hexdigest()


def read_build_info(path: str) -> Optional[str]:
    """Return the build fingerprint stored with a cached build, or None if there is none."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_build_info(path: str, fingerprint: str):
    """Store the build fingerprint of a successful build next to its output."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(fingerprint)


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
    _retry: bool = False,
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

    # Check if rebuild is necessary. The cache key is a fingerprint of the compiler identity and of the
    # path and content of every source file, so edits, deletions, equal timestamps and edits made while
    # a build was running are all detected. It is computed before compiling and stored only when the build
    # succeeded and the sources are unchanged after it.
    esphome_exe = find_esphome_binary()
    build_info_path = os.path.join(target_build_dir, BUILD_INFO_FILENAME)
    fingerprint = compute_build_fingerprint(esphome_exe, config_path)
    needs_build = force or not os.path.exists(factory_bin) or read_build_info(build_info_path) != fingerprint

    if needs_build:
        # Invalidate the cache first, so a failed or interrupted build is never trusted later
        if os.path.exists(build_info_path):
            os.remove(build_info_path)
        print(f"[*] Compiling firmware target '{target_name}' using {esphome_exe}...")

        # Read config, inject build_path to local temp to ensure smooth compilation (avoids SMB file locking issues)
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Generate a temporary config located in target_build_dir
        abs_components = os.path.join(REPO_DIR, "components").replace("\\", "/")
        abs_esphome = os.path.join(REPO_DIR, "ESPHome").replace("\\", "/")
        abs_stubs = os.path.join(CONFIGS_DIR, "qemu_stubs.h").replace("\\", "/")
        abs_partitions = os.path.join(CONFIGS_DIR, NVS_SMALL_PARTITIONS).replace("\\", "/")

        content = content.replace("../../components", abs_components)
        content = content.replace("../../ESPHome", abs_esphome)
        content = content.replace("qemu_stubs.h", abs_stubs)
        content = content.replace(f"partitions: {NVS_SMALL_PARTITIONS}", f"partitions: {abs_partitions}")

        # Inject build_path under esphome
        build_path_str = target_build_dir.replace("\\", "/")
        if "build_path:" not in content:
            content = content.replace("esphome:\n", f"esphome:\n  build_path: {build_path_str}\n")

        temp_config_path = os.path.join(target_build_dir, f"{target_name}.yaml")
        with open(temp_config_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Execute esphome compile with static command arguments
        cmd = [esphome_exe, "compile", temp_config_path]
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        # Audit: internal compile command using isolated temp configuration path with shell=False
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
            encoding="utf-8", errors="replace",  # ESPHome prints UTF-8; the Windows default code page cannot decode it
        )

        if res.returncode != 0:
            print(f"[!] Compilation failed for {target_name}:\n{res.stdout}")
            raise RuntimeError(f"ESPHome compilation failed for {target_name}")

        if not os.path.exists(factory_bin):
            raise FileNotFoundError(f"Expected factory binary not found at {factory_bin}")

        # Only trust the build if no source changed while it ran: otherwise the binary may come from a
        # different source than the fingerprint describes (e.g. a file edited, then reverted). Do not use it
        # for this run either: rebuild once from the current sources, then give up.
        if compute_build_fingerprint(esphome_exe, config_path) != fingerprint:
            if _retry:
                raise RuntimeError(
                    f"Sources changed while '{target_name}' was compiling, twice. Stop editing and run the tests again."
                )
            print(f"[!] Sources changed while '{target_name}' was compiling; rebuilding from the current sources...")
            return build_and_pad_firmware(config_filename, output_flash_name, force=True, build_cache_dir=build_cache_dir, _retry=True)

        write_build_info(build_info_path, fingerprint)

    # Always recreate the flash image from the factory binary, so every session starts from a clean flash
    # (no NVS state left over from a previous session) and never from an image modified by QEMU.
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
    cover_flash = build_and_pad_firmware(
        "test_cover.yaml", "qemu_flash_cover.bin", force=force, build_cache_dir=build_cache_dir
    )
    nvs_small_flash = build_and_pad_firmware(
        "test_nvs_small.yaml", "qemu_flash_nvs_small.bin", force=force, build_cache_dir=build_cache_dir
    )
    return std_flash, inst_flash, light_flash, cover_flash, nvs_small_flash
