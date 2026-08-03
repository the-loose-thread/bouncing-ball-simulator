#!/usr/bin/env python3
"""Fix Android SDK: make sdkmanager executable, accept licenses, install packages."""
import os
import stat
import subprocess
from pathlib import Path

SDK_DIR = Path.home() / ".buildozer" / "android" / "platform" / "android-sdk"
EXTRACT_DIR = Path("/tmp/cmdline-tools-extract")
TOOLS_BIN = SDK_DIR / "tools" / "bin"

env = os.environ.copy()
env["ANDROID_HOME"] = str(SDK_DIR)
env["ANDROID_SDK_ROOT"] = str(SDK_DIR)

# Ensure repo/ dir exists (sdkmanager needs it)
repo_dir = SDK_DIR / "repo"
repo_dir.mkdir(parents=True, exist_ok=True)
print(f"Repo dir: {repo_dir} (exists: {repo_dir.exists()})")

# Make existing sdkmanager executable
old_sdmgr = TOOLS_BIN / "sdkmanager"
if old_sdmgr.exists():
    os.chmod(old_sdmgr, os.stat(old_sdmgr).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Made executable: {old_sdmgr}")

# Also check extracted one
new_sdmgr = EXTRACT_DIR / "tools" / "bin" / "sdkmanager"
if new_sdmgr.exists():
    os.chmod(new_sdmgr, os.stat(new_sdmgr).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Made executable: {new_sdmgr}")
    sdmgr = new_sdmgr
else:
    sdmgr = old_sdmgr
    print(f"Using existing sdkmanager: {sdmgr}")

# Try accepting licenses using the extracted sdkmanager
if sdmgr.exists():
    print(f"\n=== Running: {sdmgr} --licenses ===")
    result = subprocess.run(
        [str(sdmgr), "--sdk_root=" + str(SDK_DIR), "--licenses"],
        input="y\n" * 100,
        capture_output=True, text=True, env=env, timeout=60
    )
    print(f"Exit code: {result.returncode}")
    out = result.stdout[-1000:] if result.stdout else "(empty)"
    err = result.stderr[-1000:] if result.stderr else "(empty)"
    print(f"stdout (last 1000 chars): {out}")
    print(f"stderr (last 1000 chars): {err}")

    # Install required packages
    print(f"\n=== Installing build-tools + platform-tools + platform ===")
    result2 = subprocess.run(
        [str(sdmgr), "--sdk_root=" + str(SDK_DIR),
         "build-tools;37.0.0", "platform-tools", "platforms;android-31"],
        input="y\n" * 100,
        capture_output=True, text=True, env=env, timeout=300
    )
    print(f"Exit code: {result2.returncode}")
    out2 = result2.stdout[-1000:] if result2.stdout else "(empty)"
    err2 = result2.stderr[-1000:] if result2.stderr else "(empty)"
    print(f"stdout (last 1000 chars): {out2}")
    print(f"stderr (last 1000 chars): {err2}")

# Verify
print("\n=== Final verification ===")
licenses_dir = SDK_DIR / "licenses"
if licenses_dir.exists():
    for f in sorted(licenses_dir.iterdir()):
        content = f.read_text().strip()
        print(f"  License: {f.name} = {content[:30]}...")
else:
    print("  No licenses directory!")

bt_dir = SDK_DIR / "build-tools"
if bt_dir.exists():
    print(f"  Build-tools: {[d.name for d in bt_dir.iterdir()]}")
else:
    print("  No build-tools directory!")

print("\nDone!")
