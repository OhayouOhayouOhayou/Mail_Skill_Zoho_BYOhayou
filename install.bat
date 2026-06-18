@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Zoho Mail Skill - ตัวช่วยติดตั้ง

echo ==================================================
echo      Zoho Mail Skill  -  ตัวช่วยติดตั้ง
echo ==================================================
echo.

REM ── 1) ตรวจสอบ Python ───────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
  echo [X] ไม่พบ Python บนเครื่อง
  echo.
  echo     กรุณาติดตั้ง Python 3.11 ขึ้นไป จาก:
  echo       https://www.python.org/downloads/
  echo     ** ตอนติดตั้งให้ติ๊ก "Add Python to PATH" ด้วย **
  echo.
  echo     ติดตั้งเสร็จแล้วค่อยดับเบิลคลิก install.bat อีกครั้ง
  echo.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo [OK] พบ %%v
echo.

REM ── 2) ติดตั้งแพ็กเกจหลัก ─────────────────────────────
echo [1/4] กำลังติดตั้งแพ็กเกจหลัก (รอสักครู่)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [X] ติดตั้งแพ็กเกจไม่สำเร็จ - เช็คอินเทอร์เน็ตแล้วลองใหม่
  pause
  exit /b 1
)
echo [OK] ติดตั้งแพ็กเกจหลักแล้ว
echo.

REM ── 2.5) ฟีเจอร์เสริม (เลือกได้) ──────────────────────
set /p WANTNOTIFY="ติดตั้งโปรแกรมแจ้งเตือนเมล realtime (tray) ด้วยไหม? (y/n) "
if /i "%WANTNOTIFY%"=="y" (
  echo กำลังติดตั้งส่วนแจ้งเตือน...
  python -m pip install -r requirements-desktop.txt
)
echo.

REM ── 3) ตั้งค่าเชื่อมต่อ Zoho (ผู้ใช้กรอก Client ID เอง) ─
echo [2/4] ตั้งค่าเชื่อมต่อ Zoho
echo       (เตรียม Client ID + Client Secret จาก api-console.zoho.com)
echo.
python setup.py
if errorlevel 1 (
  echo.
  echo [!] ตั้งค่ายังไม่เสร็จ - รัน install.bat ใหม่ หรือ "python setup.py" ได้ทีหลัง
  pause
  exit /b 1
)
echo.

REM ── 4) ตรวจสอบการเชื่อมต่อ ───────────────────────────
echo [3/4] ตรวจสอบการเชื่อมต่อ...
python cli.py doctor
echo.

REM ── 4.5) ตั้งเช็คพื้นที่อัตโนมัติ (เลือกได้) ──────────
set /p WANTSCHED="ตั้งให้เช็คพื้นที่อัตโนมัติทุกชั่วโมง (กันเมลเต็ม) ไหม? (y/n) "
if /i "%WANTSCHED%"=="y" (
  python install_scheduler.py --hourly
)
echo.

echo [4/4] เสร็จสิ้น!
echo ==================================================
echo   เปิดใช้งานได้เลยโดยดับเบิลคลิก  start.bat
echo ==================================================
pause
