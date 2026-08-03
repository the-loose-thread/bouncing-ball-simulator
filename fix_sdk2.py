#!/usr/bin/env python3
"""Fix Android SDK: inspect zip, find sdkmanager, accept licenses, install build-tools."""
import os
import subprocess
import zipfile
import shutil
from pathlib import Path

SDK_DIR = Path.home() / ".buildozer" / "android" / "platform" / "android-sdk"
ZIP_PATH = SDK_DIR / "commandlinetools-linux-6514223_latest.zip"
EXTRACT_DIR = Path("/tmp/cmdline-tools-extract")

print(f"SDK dir: {SDK_DIR}")

# Step 1: Inspect the zip contents
print("\n=== Zip file contents (first 20 entries) ===")
if ZIP_PATH.exists():
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = zf.namelist()
        for n in names[:20]:
            print(f"  {n}")
        print(f"  ... ({len(names)} total entries)")
else:
    print(f"  Zip file not found at {ZIP_PATH}")

# Step 2: Extract to a clean directory
shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(ZIP_PATH) as zf:
    zf.extractall(str(EXTRACT_DIR))
print(f"\nExtracted to {EXTRACT_DIR}")
print("Directory tree:")
for item in sorted(EXTRACT_DIR.rglob("*")):
    if item.is_file():
        print(f"  {item.relative_to(EXTRACT_DIR)}")

# Step 3: Find sdkmanager
print("\n=== Finding sdkmanager ===")
sdkmanagers = list(EXTRACT_DIR.rglob("sdkmanager"))
for s in sdkmanagers:
    print(f"  Found: {s}")

if not sdkmanagers:
    print("  No sdkmanager found!")
else:
    sdmgr = sdkmanagers[0]
    
    env = os.environ.copy()
    env["ANDROID_HOME"] = str(SDK_DIR)
    env["ANDROID_SDK_ROOT"] = str(SDK_DIR)
    
    # Accept licenses
    print(f"\n=== Accepting licenses via {sdmgr} ===")
    result = subprocess.run(
        [str(sdmgr), "--sdk_root=" + str(SDK_DIR), "--licenses"],
        input="y\n" * 100,
        capture_output=True, text=True, env=env, timeout=60
    )
    print(f"Exit code: {result.returncode}")
    # Show last 800 chars of output
    out = result.stdout[-800:] if result.stdout else "(empty)"
    err = result.stderr[-800:] if result.stderr else "(empty)"
    print(f"stdout (last 800): {out}")
    print(f"stderr (last 800): {err}")

    # Install required packages
    print(f"\n=== Installing build-tools;37.0.0 + platform-tools + platform;android-31 ===")
    result2 = subprocess.run(
        [str(sdmgr), "--sdk_root=" + str(SDK_DIR),
         "build-tools;37.0.0", "platform-tools", "platforms;android-31"],
        input="y\n" * 100,
        capture_output=True, text=True, env=env, timeout=300
    )
    print(f"Exit code: {result2.returncode}")
    out2 = result2.stdout[-800:] if result2.stdout else "(empty)"
    err2 = result2.stderr[-800:] if result2.stderr else "(empty)"
    print(f"stdout (last 800): {out2}")
    print(f"stderr (last 800): {err2}")

# Step 4: Verify
print("\n=== Verification ===")
licenses_dir = SDK_DIR / "licenses"
if licenses_dir.exists():
    print(f"Licenses: {[f.name for f in licenses_dir.iterdir()]}")
else:
    print("No licenses directory!")

bt_dir = SDK_DIR / "build-tools"
if bt_dir.exists():
    print(f"Build-tools: {[d.name for d in bt_dir.iterdir()]}")
else:
    print("No build-tools directory!")

print("\nDone!")
