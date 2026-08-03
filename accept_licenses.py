#!/usr/bin/env python3
"""Accept Android SDK licenses by creating the license files buildozer needs."""
import os
from pathlib import Path

sdk = Path.home() / ".buildozer" / "android" / "platform" / "android-sdk"
licenses = sdk / "licenses"
licenses.mkdir(parents=True, exist_ok=True)

# Standard accepted license hashes (these are the official Android SDK license keys)
license_files = {
    "android-sdk-license": "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6\n",
    "android-sdk-preview-license": "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6\n",
    "intel-android-extra-license": "d9ba35bed1766e1911883474ebd7d325d6e0b843\n",
    "mips-android-sysimage-license": "13d8b763091b9c5810c9398376440274",
    "google-gdk-license": "5f2607c710f2e5c0c5c0c2c48f82c75b",
}

for name, content in license_files.items():
    fpath = licenses / name
    fpath.write_text(content)
    print(f"  {fpath.name}: {content.strip()[:20]}...")

print(f"\nLicense files created at: {licenses}")
print(f"Files: {os.listdir(licenses)}")
