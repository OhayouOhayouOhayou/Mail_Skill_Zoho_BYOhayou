@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Build ZohoMailSetup.exe

echo ==================================================
echo   สร้างตัวติดตั้ง ZohoMailSetup.exe
echo ==================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [X] ต้องมี Python ก่อน (เฉพาะตอน "สร้าง" เท่านั้น)
  echo     ผู้ใช้ปลายทางไม่ต้องมี Python ถ้าใช้ไฟล์ .exe ที่ได้
  pause & exit /b 1
)

echo [1/2] ติดตั้งเครื่องมือ build...
python -m pip install pyinstaller -r requirements.txt -r requirements-desktop.txt

echo.
echo [2/2] กำลังสร้าง .exe (ใช้เวลาสักครู่)...
REM Windowed (ไม่มีหน้าต่างดำ) + รวมไฟล์โปรเจกต์ที่จำเป็นไว้ในตัว exe
pyinstaller --noconfirm --onefile --windowed --name ZohoMailSetup ^
  --collect-submodules httpx ^
  --add-data "cli.py;." ^
  --add-data "zoho_client.py;." ^
  --add-data "openai_tools.json;." ^
  setup_gui.py

echo.
echo ==================================================
echo   เสร็จ! ไฟล์อยู่ที่:  dist\ZohoMailSetup.exe
echo   ส่งไฟล์นี้ให้ผู้ใช้ดับเบิลคลิกเพื่อตั้งค่าได้เลย
echo ==================================================
pause
