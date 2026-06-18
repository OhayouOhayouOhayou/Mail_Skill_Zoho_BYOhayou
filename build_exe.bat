@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Building ZohoMailNotifier.exe ...
echo.

REM Install build + runtime deps
pip install pyinstaller -r requirements.txt -r requirements-desktop.txt

REM Build a single-file, windowed (no console) executable.
REM The .env is read at runtime from the same folder as the exe, so keep
REM .env next to ZohoMailNotifier.exe (do NOT bundle secrets into the exe).
pyinstaller --noconfirm --onefile --windowed ^
  --name ZohoMailNotifier ^
  --collect-all windows_toasts ^
  notifier.py

echo.
echo Done. Find it at: dist\ZohoMailNotifier.exe
echo Put a copy of your .env next to the exe, then double-click to run.
pause
