@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Build ASEFAMail.exe

echo ==================================================
echo   สร้างแอปหลัก ASEFAMail.exe
echo ==================================================
echo.

python --version >nul 2>&1
if errorlevel 1 ( echo [X] ต้องมี Python ก่อน (เฉพาะตอนสร้าง) & pause & exit /b 1 )

echo [1/2] ติดตั้งเครื่องมือ + แพ็กเกจ...
python -m pip install pyinstaller -r requirements.txt -r requirements-desktop.txt

echo.
echo [2/2] กำลังสร้าง .exe (สักครู่)...
pyinstaller --noconfirm --onefile --windowed --name ASEFAMail ^
  --icon "assets\icon.ico" ^
  --collect-all windows_toasts ^
  --collect-all pystray ^
  --collect-all PIL ^
  --collect-submodules httpx ^
  --add-data "assets;assets" ^
  app.py

echo.
echo ==================================================
echo   เสร็จ! ไฟล์อยู่ที่:  dist\ASEFAMail.exe
echo   (ผู้ใช้ปลายทางไม่ต้องมี Python)
echo ==================================================
pause
