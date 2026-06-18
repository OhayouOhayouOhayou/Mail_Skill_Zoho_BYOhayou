"""Zoho Mail API client with automatic token refresh, retry, and folder resolution."""

import os
import time
import json
import datetime
from pathlib import Path

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # env vars may be supplied directly (e.g. Claude settings.json)

REGION = os.getenv("ZOHO_REGION", "com")
BASE_URL = f"https://mail.zoho.{REGION}/api"
ACCOUNTS_URL = f"https://accounts.zoho.{REGION}/oauth/v2/token"

MAX_RETRIES = 4

_token_cache: dict = {"access_token": None, "expires_at": 0}
_account_id_cache: str | None = None
_folder_cache: dict[str, str] = {}   # lower-name -> folderId


class ZohoError(RuntimeError):
    """Friendly error with actionable hint."""


def _require_env(*keys: str) -> None:
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise ZohoError(
            f"Missing config: {', '.join(missing)}.\n"
            "→ Run `python setup.py` to create your .env, or copy .env.example to .env "
            "and fill in the values."
        )


# ── Auth ─────────────────────────────────────────────────────────────────────

def _get_access_token(force: bool = False) -> str:
    now = time.time()
    if not force and _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    _require_env("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN")
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
    data = resp.json() if resp.content else {}
    if "access_token" not in data:
        raise ZohoError(
            f"Token refresh failed ({resp.status_code}): {data}.\n"
            "→ Check ZOHO_CLIENT_ID / SECRET / REFRESH_TOKEN and that ZOHO_REGION "
            f"matches your account (currently '{REGION}')."
        )
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + int(data.get("expires_in", 3600))
    return _token_cache["access_token"]


def _headers() -> dict:
    return {"Authorization": f"Zoho-oauthtoken {_get_access_token()}"}


def _request(method: str, path: str, **kwargs) -> dict:
    """HTTP request with auto token refresh on 401 and backoff on 429/5xx."""
    url = f"{BASE_URL}{path}"
    kwargs.setdefault("timeout", 20)
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES):
        force = attempt > 0 and isinstance(last_exc, _AuthExpired)
        headers = {"Authorization": f"Zoho-oauthtoken {_get_access_token(force=force)}"}
        try:
            resp = httpx.request(method, url, headers=headers, **kwargs)
        except httpx.RequestError as e:
            last_exc = e
            time.sleep(1.5 * (attempt + 1))
            continue

        if resp.status_code == 401:
            last_exc = _AuthExpired()
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            last_exc = ZohoError(f"HTTP {resp.status_code}")
            time.sleep(min(wait, 30))
            continue

        if resp.status_code >= 400:
            raise ZohoError(f"Zoho API error {resp.status_code}: {resp.text[:300]}")
        return resp.json() if resp.content else {}

    raise ZohoError(f"Request failed after {MAX_RETRIES} attempts: {last_exc}")


class _AuthExpired(Exception):
    pass


# ── Account / folders ────────────────────────────────────────────────────────

def get_accounts() -> list[dict]:
    return _request("GET", "/accounts").get("data", [])


def account_id() -> str:
    global _account_id_cache
    if _account_id_cache:
        return _account_id_cache
    _require_env("ZOHO_ACCOUNT_EMAIL")
    email = os.environ["ZOHO_ACCOUNT_EMAIL"].lower()
    accounts = get_accounts()
    for acct in accounts:
        if acct.get("emailAddress", "").lower() == email:
            _account_id_cache = str(acct["accountId"])
            return _account_id_cache
    available = ", ".join(a.get("emailAddress", "?") for a in accounts) or "(none)"
    raise ZohoError(
        f"Account not found for '{email}'. Available: {available}.\n"
        "→ Update ZOHO_ACCOUNT_EMAIL in your .env."
    )


def get_folders() -> list[dict]:
    acct = account_id()
    return _request("GET", f"/accounts/{acct}/folders").get("data", [])


def resolve_folder_id(folder: str) -> str:
    """Resolve a folder name (e.g. 'Inbox') to its numeric folderId.

    Accepts a numeric id as-is. Case-insensitive on names.
    """
    if str(folder).isdigit():
        return str(folder)
    if not _folder_cache:
        for f in get_folders():
            name = str(f.get("folderName", "")).lower()
            _folder_cache[name] = str(f.get("folderId"))
    fid = _folder_cache.get(folder.lower())
    if not fid:
        names = ", ".join(sorted(_folder_cache.keys())) or "(none)"
        raise ZohoError(f"Folder '{folder}' not found. Available: {names}")
    return fid


# ── Email ────────────────────────────────────────────────────────────────────

def list_messages(folder: str = "Inbox", limit: int = 20, offset: int = 0) -> list[dict]:
    acct = account_id()
    folder_id = resolve_folder_id(folder)
    return _request(
        "GET", f"/accounts/{acct}/messages/view",
        params={"folderId": folder_id, "limit": limit, "start": max(offset, 1) if offset else 1},
    ).get("data", [])


def list_sent(limit: int = 20, offset: int = 0) -> list[dict]:
    return list_messages(folder="Sent", limit=limit, offset=offset)


def get_message(message_id: str) -> dict:
    acct = account_id()
    return _request("GET", f"/accounts/{acct}/messages/{message_id}/content").get("data", {})


def search_messages(query: str, limit: int = 20) -> list[dict]:
    acct = account_id()
    return _request(
        "GET", f"/accounts/{acct}/messages/search",
        params={"searchKey": query, "limit": limit},
    ).get("data", [])


# ── Storage ──────────────────────────────────────────────────────────────────

def get_storage_info() -> dict:
    """Returns used/total MB, percent used, and warning state."""
    acct = account_id()
    data = _request("GET", f"/accounts/{acct}").get("data", {})
    used = int(data.get("usedQuota", 0) or 0)        # bytes
    total = int(data.get("totalQuota", 0) or 0)      # bytes
    pct = round(used / total * 100, 2) if total else 0.0
    threshold = int(os.getenv("STORAGE_WARN_PERCENT", "80"))
    return {
        "used_mb": round(used / 1_048_576, 2),
        "total_mb": round(total / 1_048_576, 2),
        "used_pct": pct,
        "warn_threshold": threshold,
        "is_warning": pct >= threshold,
    }


# ── Backup ───────────────────────────────────────────────────────────────────

def backup_folder(folder: str = "Inbox", max_messages: int = 500,
                  progress=None) -> dict:
    """Download messages to a JSONL file. Returns a summary dict.

    progress: optional callable(done, total) for progress reporting.
    """
    out_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"backup_{folder.lower()}_{stamp}.jsonl"

    batch = 50
    offset = 1
    total = 0
    failed = 0

    with open(out_file, "w", encoding="utf-8") as fh:
        while total < max_messages:
            want = min(batch, max_messages - total)
            msgs = list_messages(folder=folder, limit=want, offset=offset)
            if not msgs:
                break
            for m in msgs:
                try:
                    detail = get_message(str(m["messageId"]))
                    # keep envelope metadata alongside content
                    record = {**{k: m.get(k) for k in
                                 ("messageId", "subject", "fromAddress",
                                  "toAddress", "sentDateInGMT", "hasAttachment")},
                              **detail}
                    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total += 1
                    if progress:
                        progress(total, max_messages)
                except Exception:
                    failed += 1
                time.sleep(0.15)  # be gentle on rate limits
            offset += len(msgs)
            if len(msgs) < want:
                break

    return {
        "success": True,
        "folder": folder,
        "saved": total,
        "failed": failed,
        "backup_file": str(out_file),
        "size_kb": round(out_file.stat().st_size / 1024, 1) if out_file.exists() else 0,
    }
