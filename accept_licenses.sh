#!/bin/bash
# Accept Android SDK licenses for buildozer
SDK_DIR="$HOME/.buildozer/android/platform/android-sdk"
mkdir -p "$SDK_DIR/licenses"

# Standard Android SDK license hashes
printf -- "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6\n" > "$SDK_DIR/licenses/android-sdk-license"
printf -- "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6\n" > "$SDK_DIR/licenses/android-sdk-preview-license"
printf -- "d9ba35bed1766e1911883474ebd7d325d6e0b843\n" > "$SDK_DIR/licenses/intel-android-extra-license"
printf -- "13d8b763091b9c5810c9398376440274" > "$SDK_DIR/licenses/mips-android-sysimage-license"
printf -- "5f2607c710f2e5c0c5c0c2c48f82c75b" > "$SDK_DIR/licenses/google-gdk-license"

echo "SDK dir: $SDK_DIR"
echo "License files created:"
ls -la "$SDK_DIR/licenses/"
echo "---"
echo "License contents:"
cat "$SDK_DIR/licenses/"*
