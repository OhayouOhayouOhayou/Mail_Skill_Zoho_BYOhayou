"""
One-shot storage check — designed to be run on a schedule (Task Scheduler / cron).

Checks Zoho mailbox usage once, and if it is at/over STORAGE_WARN_PERCENT it
raises an alert (webhook + Windows notification + log), then exits.

    python storage_alert.py

Exit code: 0 = OK, 1 = warning (near full), 2 = error.
Schedule it with:  python install_scheduler.py
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass

import httpx
import zoho_client as zc

LOG_FILE = Path(__file__).with_name("storage_alerts.log")
WEBHOOK = os.getenv("NOTIFY_WEBHOOK", "").strip()


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(line: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _webhook(text: str) -> None:
    if not WEBHOOK:
        return
    try:
        httpx.post(WEBHOOK, json={"text": text}, timeout=10)
    except Exception as e:
        _log(f"[{_ts()}] webhook failed: {e}")


def _windows_popup(title: str, message: str) -> None:
    """Best-effort desktop notification (only shows in an interactive session)."""
    if os.name != "nt":
        return
    ps = (
        "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');"
        "[System.Windows.Forms.MessageBox]::Show("
        f"'{message}','{title}',"
        "[System.Windows.Forms.MessageBoxButtons]::OK,"
        "[System.Windows.Forms.MessageBoxIcon]::Warning)"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps])
    except Exception:
        pass


def main() -> int:
    try:
        info = zc.get_storage_info()
    except Exception as e:
        line = f"[{_ts()}] ERROR checking storage: {e}"
        print(line)
        _log(line)
        return 2

    pct = info["used_pct"]
    summary = (f"{pct}% used ({info['used_mb']} / {info['total_mb']} MB) "
               f"— threshold {info['warn_threshold']}%")

    if info["is_warning"]:
        msg = f"⚠️ Zoho Mail storage WARNING: {summary}"
        print(f"[{_ts()}] {msg}")
        _log(f"[{_ts()}] WARNING | {summary}")
        _webhook(msg)
        _windows_popup("Zoho Mail — พื้นที่ใกล้เต็ม",
                       f"พื้นที่อีเมลใช้ไป {pct}% แล้ว\nควรลบ/สำรองเมลก่อนเต็ม")
        return 1

    print(f"[{_ts()}] OK | {summary}")
    _log(f"[{_ts()}] OK | {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
