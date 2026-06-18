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
TOKEN_CACHE_FILE = Path(__file__).parent / ".token_cache.json"

_token_cache: dict = {"access_token": None, "expires_at": 0}
_account_id_cache: str | None = None
_folder_cache: dict[str, str] = {}   # lower-name -> folderId


def _load_disk_token() -> None:
    """Reuse a valid access token across separate process runs (avoids token
    endpoint rate limits when calling the CLI repeatedly)."""
    if _token_cache["access_token"]:
        return
    try:
        cached = json.loads(TOKEN_CACHE_FILE.read_text())
        if cached.get("region") == REGION and cached.get("access_token"):
            _token_cache.update(access_token=cached["access_token"],
                                expires_at=cached.get("expires_at", 0))
    except Exception:
        pass


def _save_disk_token() -> None:
    try:
        TOKEN_CACHE_FILE.write_text(json.dumps({
            "region": REGION,
            "access_token": _token_cache["access_token"],
            "expires_at": _token_cache["expires_at"],
        }))
    except Exception:
        pass


class ZohoError(RuntimeError):
    """Friendly error with actionable hint."""


class ZohoScopeError(ZohoError):
    """The granted OAuth scope does not cover this endpoint."""


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
    if not force:
        _load_disk_token()
        if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
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
    _save_disk_token()
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
            if "OAUTHSCOPE" in resp.text.upper():
                raise ZohoScopeError(
                    "This endpoint needs a scope you didn't grant.\n"
                    "→ Re-run `python setup.py` and use scope: "
                    "ZohoMail.messages.ALL,ZohoMail.accounts.READ,ZohoMail.folders.READ"
                )
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


def account_email(acct: dict) -> str:
    """Extract the primary email from a Zoho account object.

    Zoho returns `emailAddress` as a list of {mailId, isPrimary, ...};
    `primaryEmailAddress` / `mailboxAddress` are convenient top-level fields.
    """
    for key in ("primaryEmailAddress", "mailboxAddress"):
        if acct.get(key):
            return str(acct[key])
    ea = acct.get("emailAddress")
    if isinstance(ea, str):
        return ea
    if isinstance(ea, list) and ea:
        primary = next((e for e in ea if e.get("isPrimary")), ea[0])
        return str(primary.get("mailId", ""))
    return ""


def account_id() -> str:
    global _account_id_cache
    if _account_id_cache:
        return _account_id_cache
    accounts = get_accounts()
    if not accounts:
        raise ZohoError("No Zoho Mail accounts returned for these credentials.")

    wanted = (os.getenv("ZOHO_ACCOUNT_EMAIL") or "").strip().lower()
    # if email not set or doesn't look like an email, just use the only/first account
    if not wanted or "@" not in wanted:
        _account_id_cache = str(accounts[0]["accountId"])
        return _account_id_cache

    for acct in accounts:
        if account_email(acct).lower() == wanted:
            _account_id_cache = str(acct["accountId"])
            return _account_id_cache

    # single account → use it anyway rather than failing
    if len(accounts) == 1:
        _account_id_cache = str(accounts[0]["accountId"])
        return _account_id_cache

    available = ", ".join(account_email(a) or "?" for a in accounts) or "(none)"
    raise ZohoError(
        f"Account not found for '{wanted}'. Available: {available}.\n"
        "→ Update ZOHO_ACCOUNT_EMAIL in your .env."
    )


def get_folders() -> list[dict]:
    """List folders. Returns [] if the folders scope was not granted."""
    acct = account_id()
    try:
        return _request("GET", f"/accounts/{acct}/folders").get("data", [])
    except ZohoScopeError:
        return []


def resolve_folder_id(folder: str) -> str | None:
    """Resolve a folder name (e.g. 'Inbox') to its numeric folderId.

    Accepts a numeric id as-is. Returns None if folders can't be listed
    (missing scope) so callers can fall back to an all-folder query.
    """
    if str(folder).isdigit():
        return str(folder)
    if not _folder_cache:
        folders = get_folders()
        if not folders:
            return None  # no folders scope → caller falls back
        for f in folders:
            _folder_cache[str(f.get("folderName", "")).lower()] = str(f.get("folderId"))
    return _folder_cache.get(folder.lower())


# ── Email ────────────────────────────────────────────────────────────────────

def list_messages(folder: str = "Inbox", limit: int = 20, offset: int = 0) -> list[dict]:
    acct = account_id()
    params = {"limit": limit, "start": offset if offset and offset >= 1 else 1}
    folder_id = resolve_folder_id(folder)
    if folder_id:
        params["folderId"] = folder_id
    # else: no folders scope → returns recent messages across all folders
    return _request("GET", f"/accounts/{acct}/messages/view", params=params).get("data", [])


def list_sent(limit: int = 20, offset: int = 0) -> list[dict]:
    return list_messages(folder="Sent", limit=limit, offset=offset)


def _find_folder_for_message(message_id: str, pool: int = 200) -> str | None:
    mid = str(message_id)
    for m in list_messages(folder="Inbox", limit=pool):
        if str(m.get("messageId")) == mid:
            return str(m.get("folderId"))
    return None


def get_message(message_id: str, folder_id: str | None = None) -> dict:
    """Fetch full message content. The Zoho content endpoint requires the
    folder path; if folder_id isn't supplied we look it up from recent mail."""
    acct = account_id()
    if folder_id is None:
        folder_id = _find_folder_for_message(message_id)
    if not folder_id:
        raise ZohoError(
            f"Could not locate folder for message {message_id}. "
            "Pass it via the message list, or the message may be older than the search pool."
        )
    return _request(
        "GET",
        f"/accounts/{acct}/folders/{folder_id}/messages/{message_id}/content",
    ).get("data", {})


def search_messages(query: str, limit: int = 20, pool: int = 200) -> list[dict]:
    """Search by keyword in subject / from / to.

    Zoho's server-side search API is unreliable across plans, so we fetch a
    pool of recent messages and filter locally — works with the minimal scope.
    """
    q = query.lower()
    candidates = list_messages(folder="Inbox", limit=pool)
    matches = [
        m for m in candidates
        if q in (m.get("subject") or "").lower()
        or q in (m.get("fromAddress") or "").lower()
        or q in (m.get("toAddress") or "").lower()
    ]
    return matches[:limit]


# ── Sending ──────────────────────────────────────────────────────────────────

def from_address() -> str:
    """The primary email address to send mail from."""
    wanted = (os.getenv("ZOHO_ACCOUNT_EMAIL") or "").strip()
    if wanted and "@" in wanted:
        return wanted
    accounts = get_accounts()
    return account_email(accounts[0]) if accounts else ""


def load_signature() -> str:
    """Signature from signature.html (preferred) or the SIGNATURE env var."""
    sig_file = Path(__file__).parent / "signature.html"
    if sig_file.exists():
        return sig_file.read_text(encoding="utf-8").strip()
    return os.getenv("SIGNATURE", "").strip()


def send_email(to: str, subject: str, body: str,
               cc: str | None = None, bcc: str | None = None,
               html: bool = True, signature: bool = True) -> dict:
    """Send an email via Zoho Mail, optionally appending your signature.

    Requires the ZohoMail.messages.ALL (or .CREATE) scope.
    `to`, `cc`, `bcc` may be comma-separated lists of addresses.
    """
    acct = account_id()
    content = body
    if signature:
        sig = load_signature()
        if sig:
            content += ("<br><br>" if html else "\n\n") + sig

    payload = {
        "fromAddress": from_address(),
        "toAddress": to,
        "subject": subject,
        "content": content,
        "mailFormat": "html" if html else "plaintext",
    }
    if cc:
        payload["ccAddress"] = cc
    if bcc:
        payload["bccAddress"] = bcc

    resp = _request("POST", f"/accounts/{acct}/messages", json=payload)
    return {
        "success": True,
        "from": payload["fromAddress"],
        "to": to,
        "subject": subject,
        "signature_attached": bool(signature and load_signature()),
        "response": resp.get("data", resp),
    }


# ── Storage ──────────────────────────────────────────────────────────────────

def get_storage_info() -> dict:
    """Returns used/total MB, percent used, and warning state.

    Zoho reports usedStorage / allowedStorage in KB.
    """
    acct = account_id()
    data = next((a for a in get_accounts() if str(a.get("accountId")) == acct), {})
    used_kb = int(data.get("usedStorage", 0) or 0)
    total_kb = int(data.get("allowedStorage", 0) or 0)
    pct = round(used_kb / total_kb * 100, 2) if total_kb else 0.0
    threshold = int(os.getenv("STORAGE_WARN_PERCENT", "80"))
    return {
        "used_mb": round(used_kb / 1024, 2),
        "total_mb": round(total_kb / 1024, 2),
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
    processed = 0       # advance by attempts (not just successes) to guarantee termination
    saved = 0
    failed = 0

    with open(out_file, "w", encoding="utf-8") as fh:
        while processed < max_messages:
            want = min(batch, max_messages - processed)
            msgs = list_messages(folder=folder, limit=want, offset=offset)
            if not msgs:
                break
            for m in msgs:
                try:
                    detail = get_message(str(m["messageId"]), folder_id=str(m.get("folderId")))
                    record = {**{k: m.get(k) for k in
                                 ("messageId", "subject", "fromAddress",
                                  "toAddress", "sentDateInGMT", "hasAttachment", "folderId")},
                              **detail}
                    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                    saved += 1
                except Exception:
                    failed += 1
                processed += 1
                if progress:
                    progress(processed, max_messages)
                time.sleep(0.15)  # be gentle on rate limits
            offset += len(msgs)
            if len(msgs) < want:
                break

    return {
        "success": True,
        "folder": folder,
        "saved": saved,
        "failed": failed,
        "backup_file": str(out_file),
        "size_kb": round(out_file.stat().st_size / 1024, 1) if out_file.exists() else 0,
    }
