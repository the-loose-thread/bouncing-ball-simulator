# buildozer.spec — Bouncing Ball Simulator for Android

[app]

title = Bouncing Ball Simulator
package.name = bouncesim
package.domain = org.codepuppy
source.dir = .
source.include_exts = py
source.recursive = True
version = 1.3

# Python requirements — kivy provides the UI framework
requirements = python3,kivy,setuptools

# Display
orientation = landscape
fullscreen = 1

# Exclude test files and the pygame desktop version (not needed on Android)
source.exclude_patterns = test_*,bouncing_ball.py,*.md

[buildozer]
log_level = 2

[android]
# Android API level to target
android.api = 31
# Minimum API level (Android 5.0+)
android.minapi = 21
# SDK/NDK versions
android.sdk = 34
android.ndk = 26b
android.arch = arm64-v8a
# Notification permissions for Android Auto
# POST_NOTIFICATIONS: needed on Android 13+ to show notifications
# FOREGROUND_SERVICE: for persistent notifications
android.permissions = POST_NOTIFICATIONS,FOREGROUND_SERVICE
# Java home (commented out — GitHub Actions handles Java setup
# Uncomment + adjust path if building locally on Linux/WSL)
#android.java_home = /usr/lib/jvm/java-17-openjdk-amd64

# python-for-android: use default stable branch for reliable builds
# p4a.branch = master
