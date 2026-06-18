"""
Zoho Mail MCP Server
Compatible with Claude Code via `mcp` protocol.
Run: python mcp_server.py
"""

import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import zoho_client as zc

app = Server("zoho-mail")


# ── Tool registry ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="check_inbox",
            description="List recent incoming emails from Zoho Mail inbox.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20, "description": "Number of emails to return (max 50)"},
                    "offset": {"type": "integer", "default": 0, "description": "Pagination offset"},
                },
            },
        ),
        Tool(
            name="check_sent",
            description="List recent outgoing (sent) emails from Zoho Mail.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        Tool(
            name="read_email",
            description="Read the full content of a specific email by its message ID.",
            inputSchema={
                "type": "object",
                "required": ["message_id"],
                "properties": {
                    "message_id": {"type": "string", "description": "The messageId from check_inbox or check_sent"},
                },
            },
        ),
        Tool(
            name="search_email",
            description="Search emails in Zoho Mail by keyword, sender, or subject.",
            inputSchema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Search keyword or phrase"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        Tool(
            name="check_storage",
            description="Check Zoho Mail mailbox storage: used space, total quota, and whether it is near the warning threshold.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="backup_emails",
            description="Backup emails from a specified folder to a local JSONL file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "default": "Inbox",
                        "description": "Folder name to backup (e.g. Inbox, Sent, Trash)",
                    },
                    "max_messages": {
                        "type": "integer",
                        "default": 500,
                        "description": "Maximum number of messages to download",
                    },
                },
            },
        ),
    ]


# ── Tool execution ─────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _dispatch, name, arguments)
    except Exception as e:
        result = {"error": str(e)}
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _dispatch(name: str, args: dict):
    if name == "check_inbox":
        msgs = zc.list_messages(folder="Inbox", limit=args.get("limit", 20), offset=args.get("offset", 0))
        return {"folder": "Inbox", "count": len(msgs), "messages": _summarize(msgs)}

    if name == "check_sent":
        msgs = zc.list_sent(limit=args.get("limit", 20), offset=args.get("offset", 0))
        return {"folder": "Sent", "count": len(msgs), "messages": _summarize(msgs)}

    if name == "read_email":
        return zc.get_message(args["message_id"])

    if name == "search_email":
        msgs = zc.search_messages(args["query"], limit=args.get("limit", 20))
        return {"query": args["query"], "count": len(msgs), "messages": _summarize(msgs)}

    if name == "check_storage":
        info = zc.get_storage_info()
        status = "WARNING — storage is near full!" if info["is_warning"] else "OK"
        return {**info, "status": status}

    if name == "backup_emails":
        path = zc.backup_folder(
            folder=args.get("folder", "Inbox"),
            max_messages=args.get("max_messages", 500),
        )
        return {"success": True, "backup_file": path}

    return {"error": f"Unknown tool: {name}"}


def _summarize(msgs: list[dict]) -> list[dict]:
    keys = ["messageId", "subject", "fromAddress", "toAddress", "sentDateInGMT", "summary", "hasAttachment"]
    return [{k: m.get(k) for k in keys} for m in msgs]


# ── Entry point ────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
