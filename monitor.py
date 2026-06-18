"""
Continuous background monitor — polls inbox and storage on a schedule.

    python monitor.py

Alerts are printed to stdout. Set NOTIFY_WEBHOOK in .env to also push alerts
to Slack / Discord / Telegram / any webhook (JSON {"text": "..."} payload).
"""

import time
import os
from datetime import datetime

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import zoho_client as zc

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
STORAGE_WARN = int(os.getenv("STORAGE_WARN_PERCENT", "80"))
WEBHOOK = os.getenv("NOTIFY_WEBHOOK", "").strip()

_seen_ids: set[str] = set()
_storage_alerted = False   # prevents repeated storage warnings


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def notify(text: str) -> None:
    """Print and optionally push to a webhook."""
    print(text)
    if WEBHOOK:
        try:
            httpx.post(WEBHOOK, json={"text": text}, timeout=10)
        except Exception as e:
            print(f"[{_ts()}] (webhook failed: {e})")


def check_new_inbox() -> int:
    msgs = zc.list_messages(folder="Inbox", limit=50)
    new = [m for m in msgs if str(m.get("messageId")) not in _seen_ids]
    for m in new:
        mid = str(m.get("messageId"))
        _seen_ids.add(mid)
        notify(
            f"[{_ts()}] 📥 NEW MAIL | From: {m.get('fromAddress')}"
            f" | Subject: {m.get('subject')}"
        )
    return len(new)


def check_storage() -> dict:
    global _storage_alerted
    info = zc.get_storage_info()
    pct = info["used_pct"]
    if info["is_warning"]:
        if not _storage_alerted:   # alert once when crossing threshold
            notify(
                f"[{_ts()}] ⚠️ STORAGE WARNING | {pct}% used "
                f"({info['used_mb']} / {info['total_mb']} MB) — threshold {STORAGE_WARN}%"
            )
            _storage_alerted = True
        else:
            print(f"[{_ts()}] storage still high: {pct}%")
    else:
        _storage_alerted = False   # reset once it drops back
        print(f"[{_ts()}] Storage OK | {pct}% used "
              f"({info['used_mb']} / {info['total_mb']} MB)")
    return info


def run() -> None:
    notify(f"[{_ts()}] Monitor started — every {POLL_SECONDS}s | warn at {STORAGE_WARN}%"
           + (" | webhook ON" if WEBHOOK else ""))
    # warm up: record existing IDs so we don't alert on the backlog
    try:
        for m in zc.list_messages(folder="Inbox", limit=50):
            _seen_ids.add(str(m.get("messageId")))
        print(f"[{_ts()}] Loaded {len(_seen_ids)} existing inbox IDs.")
    except Exception as e:
        print(f"[{_ts()}] Init error: {e}")

    while True:
        try:
            check_new_inbox()
            check_storage()
        except Exception as e:
            print(f"[{_ts()}] ERROR: {e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")
