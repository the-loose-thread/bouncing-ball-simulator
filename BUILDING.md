# Building the Android APK — Complete Guide & Learned Wisdom

> *A battle-tested reference for building the bouncing ball simulator on
> Android, including all the pitfalls we hit and how to avoid them.*

---

##  Prerequisites

| What | Why |
|------|-----|
| Ubuntu 22.04/24.04 (or WSL) | Tested build environment |
| Java 17 | Required by Android SDK |
| Python 3.10 | Kivy + p4a compatibility |
| ~30 GB free disk | SDK + NDK + caches |
| ~20 min first build | Compilation; cached rebuilds ~2 min |

### System packages (WSL/Linux)
```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends
    git zip unzip openjdk-17-jdk python3
    autoconf automake libtool autopoint pkg-config
    zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5
    libssl-dev libreadline-dev libffi-dev
```

> **Critical:** `automake` and `autopoint` are often forgotten! Without them,
> `autoreconf` fails when building libffi.

### Python packages
```bash
python3 -m pip install --upgrade pip
python3 -m pip install Cython==0.29.37   # ← MUST pin! 3.0+ breaks p4a
python3 -m pip install buildozer
```

> **Cython pinning:** Cython 3.0+ changed string handling, breaking
> python-for-android's compilation of native extensions. Pin to `0.29.37`.

### Cython PATH fix (WSL only)
```bash
# After pip install, cython lands in ~/.local/bin (not in PATH)
ln -sf ~/.local/bin/cython /usr/local/bin/cython
```

---

## Building the APK

### From scratch (first build — 15-30 min)
```bash
cd /path/to/bouncing-ball-simulator
python3 -m buildozer -v android debug
# APK appears at: bin/bouncesim-*.apk
```

### Incremental rebuild (cached — ~2 min)
When only Python source files (`*.py`) change:
```bash
python3 -m buildozer -v android debug
```
Buildozer detects source changes and skips recipe compilation.

### Clean rebuild (if cache is corrupted)
```bash
buildozer android clean
python3 -m buildozer -v android debug
```

### Windows → WSL workflow
Avoid Windows shell quoting issues by writing scripts to files:
```bash
# DON'T: wsl bash -c "export PATH=... && buildozer ..."
# DO:    Write a script, then execute it
```

Use `wsl -u root <cmd>` to avoid sudo password prompts:
```bash
# Instead of: sudo apt-get install ...
# Use:         wsl -u root -- apt-get install ...
```

---

## All Build Bugs Encountered (and Fixed)

### Bug 1: "Aidl not found" — SDK licenses not accepted
```
[ERROR]: Failed to find the following build tools
  aidl (expected version: 34)
```
**Root cause:** `sdkmanager` refuses to install packages until licenses
are accepted. Buildozer doesn't pre-accept them.

**Fix** (in CI workflow, before buildozer runs):
```bash
SDK=$HOME/.buildozer/android/platform/android-sdk
mkdir -p "$SDK/licenses" "$SDK/repo"
echo "8933bad161af41668d7141382f341f108105e63158f6b0129998736862388d6" \
    > "$SDK/licenses/android-sdk-license"
# Repeat for all license files
```

### Bug 2: Windows shell quoting breaks PATH exports
```
/bin/sh: 1: export: not found
```
**Root cause:** Windows PowerShell/cmd interprets quoting differently
from bash, especially with paths containing spaces (e.g., "Program Files").

**Fix:** Use `wsl -u root` and write paths to script files instead of
inline commands.

### Bug 3: `cython` binary not found during p4a build
```
/bin/sh: cython: not found
```
**Root cause:** `pip install Cython` puts the binary in `~/.local/bin`,
which is not in WSL's default PATH for non-interactive shells.

**Fix:**
```bash
ln -sf ~/.local/bin/cython /usr/local/bin/cython
```

### Bug 4: `autoreconf: command not found` (libffi build)
**Root cause:** Ubuntu's `libtool` package doesn't include `autoconf`,
`automake`, or `autopoint` by default.

**Fix (apt packages):**
```bash
apt-get install -y autoconf automake libtool autopoint pkg-config
```

### Bug 5: `LT_SYS_SYMBOL_USCORE` not found in libtool.m4
```
configure.ac: error: possibly undefined macro: LT_SYS_SYMBOL_USCORE
```
**Root cause:** Ubuntu's `libtool` package strips some macros from
`libtool.m4`. libffi's `configure.ac` references `LT_SYS_SYMBOL_USCORE`
which doesn't exist in Ubuntu's version.

**Fix (create dummy macro):**
```bash
echo 'AC_DEFUN([LT_SYS_SYMBOL_USCORE], [:])' \
    >> /usr/share/aclocal/libtool.m4
```
> The `[:]` is a no-op shell builtin — it satisfies autoconf without
> breaking functionality. libffi doesn't actually need the real macro
> behavior.

### Bug 6: pip corrupted in p4a venv
```
BuildDependencyInstallError: ... pip ...
```
**Root cause:** p4a's `build.py` runs `pip install -U pip` to upgrade
pip, but this creates a hybrid broken state with files from two
different pip versions (25.3 + 26.2) in the same venv.

**Fix (patch p4a's build.py):**
```bash
# In p4a's build.py, change:
pip install -U pip
# To:
pip install --force-reinstall pip==25.3
```

The line is at `pythonforandroid/build.py` line 878:
```python
"pip install -U pip"
# → patched to:
"pip install --force-reinstall pip==25.3"
```

### Bug 7: CI workflow YAML syntax error
```
YAMLException: bad indentation of a mapping entry
```
**Root cause:** Using `${{ }}` expressions inside YAML `run:` blocks
confuses the YAML parser, especially with `printf` and backslashes.

**Fix:** Rewrote CI workflow to use simple `echo` and `tee` commands
without inline `${{ }}` expressions. See `build-apk.yml` for the working
version.

---

## CI Workflow (`.github/workflows/build-apk.yml`)

### Key steps that prevent build failures:
1. Install `automake`, `autopoint` (Bug 4)
2. Create dummy `LT_SYS_SYMBOL_USCORE` macro (Bug 5)
3. Pre-create SDK license files (Bug 1)
4. Pin `Cython==0.29.37` (Cython pinning requirement)
5. **Retry logic**: if first build fails, patch p4a `build.py` and retry (Bug 6)

### Retry logic (in CI workflow):
```yaml
- name: Build APK (debug)
  run: |
    python -m buildozer -v android debug > build_output.log 2>&1
    BUILD_EXIT=$?
    if [ $BUILD_EXIT -ne 0 ]; then
      P4A_PY=$(find $HOME/.buildozer -path "*/python-for-android/pythonforandroid/build.py")
      sed -i 's|pip install -U pip|pip install --force-reinstall pip==25.3|' "$P4A_PY"
      rm -rf .buildozer/android/platform/build-*_*/build/venv
      python -m buildozer -v android debug
    fi
```

---

## Android Auto Notification

### Issue: Notification doesn't appear on car screen
Even though the notification is created successfully, it doesn't show
up on the Android Auto car display.

### Root cause: `VISIBILITY_SECRET` + broken `setCategory`
1. **Missing `setVisibility()`** → default is `VISIBILITY_SECRET`, which
   hides the notification from lock screen, Android Auto, and head-up
   displays.
2. **`setCategory()` used reflection** → broken code called
   `builder().getClass().getDeclaredField()` on a *new* builder instance,
   which would never find `CATEGORY_SERVICE`.

### Fix (`car_notification.py`):
```python
# CRITICAL: must be VISIBILITY_PUBLIC for Android Auto
builder.setVisibility(Notification.VISIBILITY_PUBLIC)

# Use the actual constant, not reflection
builder.setCategory(Notification.CATEGORY_SERVICE)

# Ensure Android Auto displays it
builder.setLocalOnly(False)

# Don't auto-dismiss on tap
builder.setAutoCancel(False)
```

### Debugging with Toast
```python
# Success feedback
_toast(activity, "Android Auto notification created!")

# Error feedback (for debugging)
except Exception as exc:
    _toast(activity, f"Notification error: {exc}")
```

### How to verify:
1. **App HUD** → bottom-left shows `v1.2 - AA Fixed`
2. **Toast on open** → "Android Auto notification created!"
3. **Phone notification tray** → persistent "Bouncing Ball Simulator"
4. **Android Auto** → notification in car screen's status area

### Testing in the car:
1. Install v1.2 APK (uninstall v1.1 first!)
2. Open app → verify Toast appears
3. Check phone notification shade → verify notification exists
4. Connect to Android Auto → notification should appear on car screen
5. Tap notification → app launches with bouncing ball

---

## File Reference

| File | Purpose |
|------|---------|
| `ball_physics.py` | Shared physics engine (GRAVITY=900, RESTITUTION=0.96) |
| `main.py` | Kivy app (Android entry point + desktop) |
| `car_notification.py` | Android Auto notification via PyJNIus |
| `bouncing_ball.py` | pygame desktop version |
| `test_bouncing_ball.py` | 11 pytest tests (all passing) |
| `buildozer.spec` | APK packaging config (arm64-v8a, v1.2) |
| `.github/workflows/build-apk.yml` | CI workflow with all fixes |
| `deploy.bat` | One-click GitHub deploy helper |
| `BUILDING.md` | This file |
| `README.md` | Project overview + Android Auto docs |

---

## Common Gotchas

- **Version mismatch:** Always bump `version` in `buildozer.spec` for new
  builds. Old debug APKs can't be "updated" — must uninstall first.
- **Cache persistence:** The SDK/NDK at `~/.buildozer/android/platform/`
  persists across builds. The compiled recipes in
  `other_builds/` also persist. Clear only `build-*/` for fast rebuilds.
- **p4a source location:**
  `~/.buildozer/android/platform/python-for-android/` — this is the
  python-for-android source that gets patched for the pip fix.
- **APK output:** `bin/bouncesim-{version}-arm64-v8a_armeabi-v7a-debug.apk`
  (both architectures included by default in buildozer 1.6.0).

---

## Quick Debug Checklist

```
Build fails immediately?
  → Check SDK licenses → Bug 1

  → Check system packages → Bug 4

  → Check Cython version → pin to 0.29.37

Notification not on car screen?
  → Check VISIBILITY_PUBLIC → Bug (Android Auto visibility)
  → Check Toast feedback → did notification actually get created?
  → Check phone notification tray first
  → Check notification channel in Settings → Apps → [App] → Notifications

APK installs but app crashes?
  → Check logcat: adb logcat | grep python
```

---

*Authored by Molly, the digital puppy — built, tested, and debugged one
bouncing ball at a time.* 
