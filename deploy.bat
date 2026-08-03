@echo off
REM deploy.bat — one-click helper to create GitHub repo, push, and trigger CI build.
REM Prerequisites: GitHub CLI (gh.exe) installed (we used winget for this).

setlocal
set GH="C:\Program Files\GitHub CLI\gh.exe"

echo Step 1: Authenticating with GitHub (opens browser)...
%GH% auth login
if errorlevel 1 (
    echo.  Failed to authenticate. Aborting.
    exit /b 1
)

echo.
echo Step 2: Creating public repo 'bouncing-ball-simulator' and pushing...
%GH% repo create bouncing-ball-simulator --public --source=. --push
if errorlevel 1 (
    echo.  Repo creation failed. Maybe it already exists? Try:
    echo    git remote add origin https://github.com/YOUR_USERNAME/bouncing-ball-simulator.git
    echo    git push -u origin main
    exit /b 1
)

echo.
echo DONE!  The CI workflow is now running.
echo Visit  https://github.com/YOUR_USERNAME/bouncing-ball-simulator/actions
echo to watch the build.  When it finishes, download the APK artifact
echo and sideload it onto your Pixel 8a!
echo.
echo Tip: Enable Developer Options on your phone, then:
echo   adb install bin/bouncing_ball_debug.apk
echo  or just email the APK to yourself and tap to install.

endlocal
