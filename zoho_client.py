"""Zoho Mail API client with automatic token refresh."""

import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("ZOHO_REGION", "com")
BASE_URL = f"https://mail.zoho.{REGION}/api"
ACCOUNTS_URL = f"https://accounts.zoho.{REGION}/oauth/v2/token"

_token_cache: dict = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    resp = httpx.post(
        ACCOUNTS_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["ZOHO_CLIENT_ID"],
            "client_secret": os.environ["ZOHO_CLIENT_SECRET"],
            "refresh_token": os.environ["ZOHO_REFRESH_TOKEN"],
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Token refresh failed: {data}")
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + int(data.get("expires_in", 3600))
    return _token_cache["access_token"]


def _headers() -> dict:
    return {"Authorization": f"Zoho-oauthtoken {_get_access_token()}"}


def get_account_id() -> str:
    """Return the numeric Zoho account ID for the configured email."""
    resp = httpx.get(f"{BASE_URL}/accounts", headers=_headers(), timeout=15)
    resp.raise_for_status()
    email = os.environ["ZOHO_ACCOUNT_EMAIL"].lower()
    for acct in resp.json().get("data", []):
        if acct.get("emailAddress", "").lower() == email:
            return str(acct["accountId"])
    raise ValueError(f"Account not found for {email}")


_account_id_cache: str | None = None


def account_id() -> str:
    global _account_id_cache
    if not _account_id_cache:
        _account_id_cache = get_account_id()
    return _account_id_cache


# ── Email ──────────────────────────────────────────────────────────────────

def list_messages(folder: str = "Inbox", limit: int = 20, offset: int = 0) -> list[dict]:
    acct = account_id()
    resp = httpx.get(
        f"{BASE_URL}/accounts/{acct}/messages/view",
        headers=_headers(),
        params={"folderId": folder, "limit": limit, "start": offset},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def list_sent(limit: int = 20, offset: int = 0) -> list[dict]:
    return list_messages(folder="Sent", limit=limit, offset=offset)


def get_message(message_id: str) -> dict:
    acct = account_id()
    resp = httpx.get(
        f"{BASE_URL}/accounts/{acct}/messages/{message_id}/content",
        headers=_headers(),
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


def search_messages(query: str, limit: int = 20) -> list[dict]:
    acct = account_id()
    resp = httpx.get(
        f"{BASE_URL}/accounts/{acct}/messages/search",
        headers=_headers(),
        params={"searchKey": query, "limit": limit},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


# ── Storage ────────────────────────────────────────────────────────────────

def get_storage_info() -> dict:
    """Returns used_mb, total_mb, used_pct."""
    acct = account_id()
    resp = httpx.get(
        f"{BASE_URL}/accounts/{acct}",
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    used = int(data.get("usedQuota", 0))       # bytes
    total = int(data.get("totalQuota", 1))     # bytes
    return {
        "used_mb": round(used / 1_048_576, 2),
        "total_mb": round(total / 1_048_576, 2),
        "used_pct": round(used / total * 100, 2),
        "warn_threshold": int(os.getenv("STORAGE_WARN_PERCENT", "80")),
        "is_warning": (used / total * 100) >= int(os.getenv("STORAGE_WARN_PERCENT", "80")),
    }


# ── Backup ─────────────────────────────────────────────────────────────────

def backup_folder(folder: str = "Inbox", max_messages: int = 500) -> str:
    """Download messages and save as JSON lines. Returns output file path."""
    import json
    import datetime
    from pathlib import Path

    out_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"backup_{folder.lower()}_{stamp}.jsonl"

    batch = 50
    offset = 0
    total = 0

    with open(out_file, "w", encoding="utf-8") as fh:
        while total < max_messages:
            msgs = list_messages(folder=folder, limit=min(batch, max_messages - total), offset=offset)
            if not msgs:
                break
            for m in msgs:
                try:
                    detail = get_message(str(m["messageId"]))
                    fh.write(json.dumps(detail, ensure_ascii=False) + "\n")
                    total += 1
                except Exception:
                    pass
            offset += len(msgs)
            if len(msgs) < batch:
                break

    return str(out_file)
