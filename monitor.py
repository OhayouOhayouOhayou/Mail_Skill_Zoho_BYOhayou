"""
Continuous background monitor — polls inbox and storage on a schedule.
Run standalone: python monitor.py
Prints alerts to stdout; integrate with your notification system as needed.
"""

import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import zoho_client as zc

load_dotenv()

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
STORAGE_WARN = int(os.getenv("STORAGE_WARN_PERCENT", "80"))

_seen_ids: set[str] = set()


def check_new_inbox():
    msgs = zc.list_messages(folder="Inbox", limit=50)
    new = [m for m in msgs if str(m.get("messageId")) not in _seen_ids]
    for m in new:
        mid = str(m.get("messageId"))
        _seen_ids.add(mid)
        print(
            f"[{_ts()}] NEW MAIL  | From: {m.get('fromAddress')}"
            f" | Subject: {m.get('subject')} | ID: {mid}"
        )
    return len(new)


def check_storage():
    info = zc.get_storage_info()
    pct = info["used_pct"]
    if info["is_warning"]:
        print(
            f"[{_ts()}] STORAGE WARNING  | {pct}% used"
            f" ({info['used_mb']} MB / {info['total_mb']} MB)"
        )
    else:
        print(f"[{_ts()}] Storage OK      | {pct}% used ({info['used_mb']} MB / {info['total_mb']} MB)")
    return info


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run():
    print(f"[{_ts()}] Monitor started — polling every {POLL_SECONDS}s | Storage warn at {STORAGE_WARN}%")
    # warm up seen IDs so we don't spam on first run
    try:
        msgs = zc.list_messages(folder="Inbox", limit=50)
        for m in msgs:
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
    run()
