"""
HTTP API for the Zoho Mail Skill — lets ChatGPT (browser) call it via a
Custom GPT Action.

    pip install -r requirements-api.txt
    python api_server.py

Then expose it publicly (see CHATGPT.md) and import the OpenAPI schema
( https://YOUR-PUBLIC-URL/openapi.json ) into a Custom GPT.

Auth: every request must send  Authorization: Bearer <API_KEY>
(API_KEY is read from .env; if unset, one is generated and printed at startup).
"""

import os
import sys
import secrets

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import zoho_client as zc

# ── API key ──────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY") or secrets.token_urlsafe(24)
if not os.getenv("API_KEY"):
    print("\n" + "!" * 60)
    print("  No API_KEY in .env — generated a temporary one:")
    print(f"  {API_KEY}")
    print("  Add this to .env as API_KEY=... to keep it stable.")
    print("!" * 60 + "\n")

PUBLIC_URL = os.getenv("PUBLIC_URL", "").rstrip("/")

app = FastAPI(
    title="Zoho Mail Skill API",
    version="1.0.0",
    description="Monitor inbox/sent, check storage, search, and backup Zoho Mail.",
)


def auth(authorization: str = Header(None, description="Bearer <API_KEY>")):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _slim(msgs):
    keys = ["messageId", "subject", "fromAddress", "toAddress",
            "sentDateInGMT", "hasAttachment", "folderId"]
    return [{k: m.get(k) for k in keys} for m in msgs]


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/inbox", operation_id="check_inbox", summary="List recent inbox emails")
def check_inbox(limit: int = Query(10, le=50), authorization: str = Header(None)):
    auth(authorization)
    msgs = zc.list_messages("Inbox", limit=limit)
    return {"folder": "Inbox", "count": len(msgs), "messages": _slim(msgs)}


@app.get("/sent", operation_id="check_sent", summary="List recent sent emails")
def check_sent(limit: int = Query(10, le=50), authorization: str = Header(None)):
    auth(authorization)
    msgs = zc.list_sent(limit=limit)
    return {"folder": "Sent", "count": len(msgs), "messages": _slim(msgs)}


@app.get("/read/{message_id}", operation_id="read_email", summary="Read full email content")
def read_email(message_id: str, authorization: str = Header(None)):
    auth(authorization)
    return zc.get_message(message_id)


@app.get("/search", operation_id="search_email", summary="Search emails by keyword")
def search_email(query: str, limit: int = Query(20, le=50), authorization: str = Header(None)):
    auth(authorization)
    msgs = zc.search_messages(query, limit=limit)
    return {"query": query, "count": len(msgs), "messages": _slim(msgs)}


@app.get("/storage", operation_id="check_storage", summary="Check mailbox storage usage")
def check_storage(authorization: str = Header(None)):
    auth(authorization)
    info = zc.get_storage_info()
    return {**info, "status": "WARNING — near full!" if info["is_warning"] else "OK"}


@app.get("/folders", operation_id="list_folders", summary="List folders + unread counts")
def list_folders(authorization: str = Header(None)):
    auth(authorization)
    return {"folders": [
        {"name": f.get("folderName"), "id": f.get("folderId"), "unread": f.get("unreadCount")}
        for f in zc.get_folders()
    ]}


class BackupRequest(BaseModel):
    folder: str = "Inbox"
    max_messages: int = 100


@app.post("/backup", operation_id="backup_emails", summary="Backup a folder to a local file")
def backup_emails(req: BackupRequest, authorization: str = Header(None)):
    auth(authorization)
    return zc.backup_folder(req.folder, min(req.max_messages, 300))


# ── OpenAPI with public server URL (for Custom GPT import) ────────────────────

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version,
                         description=app.description, routes=app.routes)
    if PUBLIC_URL:
        schema["servers"] = [{"url": PUBLIC_URL}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting Zoho Mail API on http://localhost:{port}")
    print(f"OpenAPI schema: http://localhost:{port}/openapi.json")
    if not PUBLIC_URL:
        print("⚠️  Set PUBLIC_URL in .env to your public tunnel URL before importing into a Custom GPT.")
    uvicorn.run(app, host="0.0.0.0", port=port)
