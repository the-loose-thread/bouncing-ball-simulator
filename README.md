# Code Puppy Playground

A safe little sandbox for experimenting with Code Puppy. Here we've built a
**bouncing ball simulator** with shared physics, running on desktop (pygame),
desktop (Kivy), and Android (via Buildozer).

## Project structure

| File | Purpose |
|---|---|
| `ball_physics.py` | Pure physics engine — no GUI deps, shared by all versions |
| `bouncing_ball.py` | pygame desktop version |
| `main.py` | Kivy app (Android entry point + desktop fallback) |
| `car_notification.py` | Android Auto notification support (PyJNIus) |
| `test_bouncing_ball.py` | pytest suite — 11 tests covering physics |
| `buildozer.spec` | Android APK packaging config |
| `.github/workflows/build-apk.yml` | CI workflow — builds APK on every push |
| `deploy.bat` | One-click helper: create GitHub repo → push → trigger CI |

## Running tests

```bash
python -m pytest test_bouncing_ball.py -v
```

## Running the desktop simulator

```bash
python bouncing_ball.py      # pygame version
python main.py               # Kivy version
```

## Building the Android APK

The APK is built automatically by **GitHub Actions** whenever you push to `main`.

### Quick deploy

1. Install the GitHub CLI (if not already):
   ```bash
   winget install --id GitHub.cli --accept-package-agreements --accept-source-agreements
   ```
2. Authenticate once:
   ```bash
   "C:\Program Files\GitHub CLI\gh.exe" auth login
   ```
3. Run the deploy helper:
   ```bash
   deploy.bat
   ```
   This creates the GitHub repo, pushes your code, and triggers the CI build.
4. Visit the **Actions** tab on your repo, find the completed run,
   and download the **`bouncing-ball-simulator-apk`** artifact.
5. Install on your Pixel 8a (enable Developer Options first):
   ```bash
   adb install bin/bouncing_ball_debug.apk
   ```
   (Or email the APK to your phone and tap to install — enable
   "Install unknown apps" for your browser/email app first.)

## Android Auto

The app creates a **persistent notification** that appears in the
Android Auto notification tray on your car's screen.  Tapping it
launches the bouncing ball simulator.

**How it works:**
- `car_notification.py` uses PyJNIus (bundled with Kivy for Android)
to create an Android `Notification` with `CATEGORY_SERVICE`.
- The notification is **ongoing** (non-dismissable) and includes a
`PendingIntent` that relaunches `PythonActivity` via the app icon.
- On desktop, the module is a graceful **no-op** (returns `False`).
- Requires `POST_NOTIFICATIONS` + `FOREGROUND_SERVICE` permissions
  (already declared in `buildozer.spec`).

**To use in your car:**
1. Install the APK on your phone.
2. Connect to Android Auto (USB or wireless).
3. Swipe down to reveal the notification tray on the car screen.
4. Find "Bouncing Ball Simulator" — tap it.
5. The app launches — the ball starts bouncing on your car display!

**Architecture:**
```
┌─────────────────┐     ┌────────────────────────┐
│ car_screen      │────│ Android Auto           │
│ notification   │  → │  notification tray     │
│ (PyJNIus)      │     │                        │
└─────────────────┘     └──────────┬──────────────┘
                                     │
                                     ▼
                            ┌──────────────────────┐
                            │ Kivy App (main.py)   │
                            │ BallWorld + Physics  │
                            └──────────────────────┘
```

