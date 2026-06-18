"""
Install/uninstall an automatic, recurring storage check.

It registers a Windows Scheduled Task that runs storage_alert.py on a schedule,
so your mailbox is monitored even after you close the terminal or reboot.

    python install_scheduler.py            # install (asks for interval)
    python install_scheduler.py --hourly   # install, run every hour
    python install_scheduler.py --daily    # install, run once a day (09:00)
    python install_scheduler.py --remove    # uninstall

No administrator rights needed (runs as the current user).
macOS/Linux: use cron instead — see the printed hint.
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

TASK_NAME = "ZohoMailStorageCheck"
HERE = Path(__file__).parent.resolve()
SCRIPT = HERE / "storage_alert.py"


def _pythonw() -> str:
    """Prefer pythonw.exe so no console window pops up each run."""
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.exists() else exe)


def install(schedule: str, every: str = "1", at: str = "09:00") -> int:
    if os.name != "nt":
        print("This installer is for Windows. On macOS/Linux add a cron entry, e.g.:")
        print(f'  0 * * * * cd "{HERE}" && {sys.executable} storage_alert.py')
        return 1

    run_cmd = f'"{_pythonw()}" "{SCRIPT}"'
    cmd = ["schtasks", "/Create", "/TN", TASK_NAME, "/TR", run_cmd, "/F"]
    if schedule == "HOURLY":
        cmd += ["/SC", "HOURLY", "/MO", every]
    else:
        cmd += ["/SC", "DAILY", "/ST", at]

    print(f"Installing scheduled task '{TASK_NAME}' ({schedule.lower()})...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Installed. The storage check will now run automatically.")
        print(f"  Alerts go to: webhook (if NOTIFY_WEBHOOK set) + storage_alerts.log + popup")
        print(f"  Change/remove it anytime in Windows 'Task Scheduler' (task: {TASK_NAME})")
        return 0
    print("✗ Failed to install:")
    print(result.stdout or "", result.stderr or "")
    return 1


def remove() -> int:
    if os.name != "nt":
        print("Remove the cron entry you added manually.")
        return 0
    result = subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Removed scheduled task '{TASK_NAME}'.")
        return 0
    print(result.stdout or "", result.stderr or "")
    return 1


def main() -> int:
    args = sys.argv[1:]
    if "--remove" in args:
        return remove()
    if "--hourly" in args:
        return install("HOURLY", every="1")
    if "--daily" in args:
        return install("DAILY")

    # interactive
    print("ตั้งเวลาเช็คพื้นที่อัตโนมัติ / Auto storage check")
    print("  1) ทุกชั่วโมง  (hourly)   ← แนะนำ")
    print("  2) วันละครั้ง  (daily 09:00)")
    print("  3) ทุก N ชั่วโมง")
    choice = input("เลือก (1-3) [1] > ").strip() or "1"
    if choice == "2":
        return install("DAILY")
    if choice == "3":
        n = input("ทุกกี่ชั่วโมง? > ").strip() or "6"
        return install("HOURLY", every=n)
    return install("HOURLY", every="1")


if __name__ == "__main__":
    sys.exit(main())
