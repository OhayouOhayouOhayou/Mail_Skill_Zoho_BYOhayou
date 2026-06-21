@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Build ASEFA-Mail-Setup.exe (ทั้งหมดในคลิกเดียว)

echo ==================================================
echo   Build แอป + ตัวติดตั้ง ทั้งหมดในรอบเดียว
echo ==================================================
echo.

python --version >nul 2>&1
if errorlevel 1 ( echo [X] ต้องมี Python ก่อน & pause & exit /b 1 )

echo [1/4] ติดตั้งเครื่องมือ + แพ็กเกจ...
python -m pip install pyinstaller -r requirements.txt -r requirements-desktop.txt >nul

echo [2/4] Build แอปหลัก ASEFAMail.exe...
python -m PyInstaller --noconfirm --onefile --windowed --name ASEFAMail ^
  --icon "assets\icon.ico" --collect-all windows_toasts --collect-all pystray ^
  --collect-all PIL --collect-submodules httpx --add-data "assets;assets" app.py
if errorlevel 1 ( echo [X] build แอปไม่สำเร็จ & pause & exit /b 1 )

echo [3/4] Build ตัวแจ้งเตือน ZohoMailNotifier.exe...
python -m PyInstaller --noconfirm --onefile --windowed --name ZohoMailNotifier ^
  --icon "assets\icon.ico" --collect-all windows_toasts --collect-all pystray ^
  --collect-all PIL --add-data "assets;assets" notifier.py

echo [4/4] Compile ตัวติดตั้งด้วย Inno Setup...
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo [!] ไม่พบ Inno Setup — ติดตั้งก่อนด้วย:  winget install JRSoftware.InnoSetup
  echo     แล้วรัน build_all.bat อีกครั้ง  ^(แอป .exe สร้างเสร็จแล้วใน dist\^)
  pause & exit /b 1
)
"%ISCC%" "installer.iss"

echo.
echo ==================================================
echo   เสร็จ! ตัวติดตั้งอยู่ที่:  Output\ASEFA-Mail-Setup.exe
echo   ส่งไฟล์นี้ไฟล์เดียวให้พนักงานทั้งองค์กรได้เลย
echo ==================================================
pause
