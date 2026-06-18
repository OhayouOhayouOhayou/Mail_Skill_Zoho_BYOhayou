@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM Start the tray notifier without a console window
start "" pythonw notifier.py
exit
