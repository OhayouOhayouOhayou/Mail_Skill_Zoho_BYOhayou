"""
Zoho Mail — desktop tray notifier.

Runs in the system tray and shows a Windows toast whenever a new email
arrives (inbox) or is sent (sent folder), in near real time. Clicking the
toast opens Zoho Mail in your browser.

    python notifier.py           # run in the tray
    python notifier.py --test    # one poll, print to console (no GUI)

Double-click notifier.bat to start it without a console window.
"""

import os
import sys
import time
import threading
import webbrowser
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

import zoho_client as zc

REGION = os.getenv("ZOHO_REGION", "com")
WEBMAIL_URL = os.getenv("ZOHO_WEBMAIL_URL", f"https://mail.zoho.{REGION}/")
POLL_SECONDS = int(os.getenv("NOTIFY_POLL_SECONDS", "30"))

_seen_in: set[str] = set()
_seen_out: set[str] = set()
_toaster = None


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ── Toast notification ───────────────────────────────────────────────────────

def show_toast(title: str, body: str, url: str = WEBMAIL_URL) -> None:
    """Clickable Windows toast; falls back to console if libs unavailable."""
    global _toaster
    try:
        from windows_toasts import Toast, WindowsToaster
        if _toaster is None:
            _toaster = WindowsToaster("Zoho Mail")
        toast = Toast()
        toast.text_fields = [title, body]
        toast.on_activated = lambda *_: webbrowser.open(url)
        _toaster.show_toast(toast)
    except Exception:
        print(f"[{_ts()}] 🔔 {title} — {body}")


# ── Polling ──────────────────────────────────────────────────────────────────

def _warm_up() -> None:
    try:
        for m in zc.list_messages("Inbox", limit=50):
            _seen_in.add(str(m.get("messageId")))
    except Exception as e:
        print(f"[{_ts()}] warm-up inbox error: {e}")
    try:
        for m in zc.list_sent(limit=50):
            _seen_out.add(str(m.get("messageId")))
    except Exception as e:
        print(f"[{_ts()}] warm-up sent error: {e}")


def poll_once(notify: bool = True) -> int:
    """Check inbox + sent; toast on anything new. Returns number of new items."""
    count = 0
    # incoming
    try:
        for m in zc.list_messages("Inbox", limit=50):
            mid = str(m.get("messageId"))
            if mid and mid not in _seen_in:
                _seen_in.add(mid)
                count += 1
                if notify:
                    show_toast(
                        f"📥 เมลใหม่จาก {m.get('fromAddress', '?')}",
                        m.get("subject") or "(ไม่มีหัวข้อ)",
                    )
    except Exception as e:
        print(f"[{_ts()}] inbox poll error: {e}")
    # outgoing
    try:
        for m in zc.list_sent(limit=50):
            mid = str(m.get("messageId"))
            if mid and mid not in _seen_out:
                _seen_out.add(mid)
                count += 1
                if notify:
                    show_toast(
                        f"📤 ส่งเมลถึง {m.get('toAddress', '?')}",
                        m.get("subject") or "(ไม่มีหัวข้อ)",
                    )
    except Exception as e:
        print(f"[{_ts()}] sent poll error: {e}")
    return count


def _poll_loop() -> None:
    _warm_up()
    print(f"[{_ts()}] Notifier started — polling every {POLL_SECONDS}s")
    while True:
        try:
            poll_once()
        except Exception as e:
            print(f"[{_ts()}] poll error: {e}")
        time.sleep(POLL_SECONDS)


# ── System tray ──────────────────────────────────────────────────────────────

def _make_icon():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (64, 64), "#1a73e8")
    d = ImageDraw.Draw(img)
    # simple envelope glyph
    d.rectangle([12, 20, 52, 46], fill="white")
    d.line([12, 20, 32, 36], fill="#1a73e8", width=3)
    d.line([52, 20, 32, 36], fill="#1a73e8", width=3)
    return img


def run_tray() -> int:
    try:
        import pystray
    except ImportError:
        print("✗ ต้องติดตั้งก่อน: pip install -r requirements-desktop.txt")
        return 1

    threading.Thread(target=_poll_loop, daemon=True).start()

    def _open(icon, item):
        webbrowser.open(WEBMAIL_URL)

    def _check(icon, item):
        n = poll_once()
        if n == 0:
            show_toast("Zoho Mail", "ไม่มีเมลใหม่ตอนนี้")

    def _quit(icon, item):
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("เปิด Zoho Mail", _open, default=True),
        pystray.MenuItem("เช็คเดี๋ยวนี้", _check),
        pystray.MenuItem("ออก", _quit),
    )
    icon = pystray.Icon("zoho-mail", _make_icon(), "Zoho Mail Notifier", menu)
    icon.run()
    return 0


def main() -> int:
    if "--test" in sys.argv:
        _warm_up()
        print(f"[{_ts()}] warm-up done: {len(_seen_in)} inbox, {len(_seen_out)} sent ids")
        print("Polling once (no notifications on existing mail)...")
        n = poll_once(notify=False)
        print(f"New since warm-up: {n}")
        show_toast("Zoho Mail Notifier", "ทดสอบการแจ้งเตือน — คลิกเพื่อเปิด Zoho")
        return 0
    return run_tray()


if __name__ == "__main__":
    sys.exit(main())
