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
