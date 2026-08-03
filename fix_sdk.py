#!/usr/bin/env python3
"""Fix Android SDK license + build-tools installation for buildozer."""
import os
import subprocess
import zipfile
import shutil
from pathlib import Path

SDK_DIR = Path.home() / ".buildozer" / "android" / "platform" / "android-sdk"
TOOLS_BIN = SDK_DIR / "tools" / "bin"
NEW_CLI = Path("/tmp/cmdline-tools")

print(f"SDK dir: {SDK_DIR}")
print(f"Exists: {SDK_DIR.exists()}")

# Step 1: Create the repo directory (sdkmanager needs it)
repo_dir = SDK_DIR / "repo"
repo_dir.mkdir(parents=True, exist_ok=True)
print(f"Created repo/ dir: {repo_dir}")

# Step 2: Also create licenses dir with accepted hashes
licenses = SDK_DIR / "licenses"
licenses.mkdir(parents=True, exist_ok=True)
license_hashes = {
    "android-sdk-license": "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6\n",
    "android-sdk-preview-license": "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6\n",
    "intel-android-extra-license": "d9ba35bed1766e1911883474ebd7d325d6e0b843\n",
    "mips-android-sysimage-license": "13d8b763091b9c5810c9398376440274",
    "google-gdk-license": "5f2607c710f2e5c0c5c0c2c48f82c75b",
}
for name, hsh in license_hashes.items():
    (licenses / name).write_text(hsh)
    print(f"  License: {name} -> {hsh.strip()[:20]}...")

# Step 3: Extract fresh commandline-tools and accept licenses
zip_path = SDK_DIR / "commandlinetools-linux-6514223_latest.zip"
if zip_path.exists():
    shutil.rmtree(NEW_CLI, ignore_errors=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall("/tmp")
    print(f"Extracted commandline-tools to {NEW_CLI}")
    
    new_sdmgr = NEW_CLI / "bin" / "sdkmanager"
    if new_sdmgr.exists():
        print(f"New sdkmanager found at: {new_sdmgr}")
        
        # Accept licenses
        env = os.environ.copy()
        env["ANDROID_HOME"] = str(SDK_DIR)
        env["ANDROID_SDK_ROOT"] = str(SDK_DIR)
        
        print("\n=== Accepting licenses ===")
        result = subprocess.run(
            [str(new_sdmgr), "--sdk_root=" + str(SDK_DIR), "--licenses"],
            input="y\n" * 50,
            capture_output=True, text=True, env=env, timeout=60
        )
        print(f"Exit code: {result.returncode}")
        print(f"stdout: {result.stdout[-500:]}")
        print(f"stderr: {result.stderr[-500:]}")
        
        # Install required packages
        print("\n=== Installing build-tools + platform-tools ===")
        result2 = subprocess.run(
            [str(new_sdmgr), "--sdk_root=" + str(SDK_DIR),
             "build-tools;37.0.0", "platform-tools", "platforms;android-31"],
            input="y\n" * 50,
            capture_output=True, text=True, env=env, timeout=120
        )
        print(f"Exit code: {result2.returncode}")
        print(f"stdout: {result2.stdout[-500:]}")
        print(f"stderr: {result2.stderr[-500:]}")

# Step 4: Check what's in the SDK
print("\n=== SDK directory contents ===")
if SDK_DIR.exists():
    for item in sorted(SDK_DIR.iterdir()):
        print(f"  {item.name}")

print("\n=== build-tools directory ===")
bt_dir = SDK_DIR / "build-tools"
if bt_dir.exists():
    for item in sorted(bt_dir.iterdir()):
        print(f"  {item.name}")
else:
    print("  (not found)")

print("\n=== licenses directory ===")
if licenses.exists():
    for item in sorted(licenses.iterdir()):
        print(f"  {item.name}")
