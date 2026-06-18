"""
Zoho Mail Skill — easy menu launcher.

Just run:  python start.py     (or double-click start.bat on Windows)
Pick a number. No commands to memorize.
"""

import os
import sys
import subprocess
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).parent
PY = sys.executable


def run(*args) -> None:
    subprocess.run([PY, *[str(a) for a in args]], cwd=HERE)


def has_env() -> bool:
    return (HERE / ".env").exists()


MENU = """
╔══════════════════════════════════════════════╗
║          📬  ZOHO MAIL SKILL  📬             ║
╠══════════════════════════════════════════════╣
║  1)  ตั้งค่าครั้งแรก / Setup (OAuth wizard)    ║
║  2)  💬 คุยกับ AI / Chat with AI              ║
║  3)  📥 เช็คเมลเข้า / Check inbox             ║
║  4)  💾 เช็คพื้นที่ / Check storage           ║
║  5)  🗄️  Backup เมล                          ║
║  6)  ✉️  ส่งเมล / Send email                  ║
║  7)  🔔 เฝ้าดูต่อเนื่อง / Monitor             ║
║  8)  🌐 เปิด API ให้ ChatGPT (browser)        ║
║  9)  🩺 ตรวจสอบการเชื่อมต่อ / Doctor          ║
║  S)  ⏰ ตั้งเช็คพื้นที่อัตโนมัติ (กันเมลเต็ม)  ║
║  N)  🔔 เปิดโปรแกรมแจ้งเตือนเมล (tray)        ║
║  0)  ออก / Exit                              ║
╚══════════════════════════════════════════════╝
"""


def main() -> int:
    while True:
        print(MENU)
        if not has_env():
            print("  ⚠️  ยังไม่ได้ตั้งค่า — เลือกข้อ 1 ก่อน (.env ไม่พบ)\n")

        choice = input("เลือกหมายเลข > ").strip()

        if choice == "1":
            run("setup.py")
        elif choice == "2":
            run("chat.py")
        elif choice == "3":
            n = input("กี่ฉบับ? (Enter = 10) > ").strip() or "10"
            run("cli.py", "inbox", n)
            input("\n[Enter เพื่อกลับเมนู]")
        elif choice == "4":
            run("cli.py", "storage")
            input("\n[Enter เพื่อกลับเมนู]")
        elif choice == "5":
            folder = input("โฟลเดอร์ไหน? (Enter = Inbox) > ").strip() or "Inbox"
            n = input("กี่ฉบับ? (Enter = 100) > ").strip() or "100"
            run("cli.py", "backup", folder, n)
            input("\n[Enter เพื่อกลับเมนู]")
        elif choice == "6":
            to = input("ส่งถึงใคร (อีเมล) > ").strip()
            subject = input("หัวข้อ > ").strip()
            body = input("ข้อความ > ").strip()
            if to and subject:
                run("cli.py", "send", to, subject, body)
            else:
                print("ต้องมีอีเมลผู้รับและหัวข้อ")
            input("\n[Enter เพื่อกลับเมนู]")
        elif choice == "7":
            sec = input("เช็คทุกกี่วินาที? (Enter = 60) > ").strip() or "60"
            print("กำลังเฝ้าดู... กด Ctrl+C เพื่อหยุด")
            run("cli.py", "watch", sec)
        elif choice == "8":
            print("กำลังเปิด API server... อ่านวิธีต่อ ChatGPT ใน CHATGPT.md")
            print("กด Ctrl+C เพื่อหยุด")
            run("api_server.py")
        elif choice == "9":
            run("cli.py", "doctor")
            input("\n[Enter เพื่อกลับเมนู]")
        elif choice.lower() == "s":
            run("install_scheduler.py")
            input("\n[Enter เพื่อกลับเมนู]")
        elif choice.lower() == "n":
            print("เปิดโปรแกรมแจ้งเตือน... ดูไอคอนที่ system tray (มุมขวาล่าง)")
            print("ปิดได้โดยคลิกขวาที่ไอคอน → ออก")
            run("notifier.py")
        elif choice in ("0", "q", "exit", "ออก"):
            print("บ๊ายบาย 👋")
            return 0
        else:
            print("ไม่เข้าใจ ลองใหม่อีกครั้ง")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nบ๊ายบาย 👋")
