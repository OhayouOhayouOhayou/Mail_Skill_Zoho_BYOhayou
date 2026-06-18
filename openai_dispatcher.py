"""
Dispatcher for OpenAI / ChatGPT Codex function calling.
Call dispatch(tool_name, arguments_dict) from your ChatGPT integration loop.

Example:
    import openai, json
    from openai_dispatcher import dispatch

    tools = json.load(open("openai_tools.json"))
    messages = [{"role": "user", "content": "How full is my mailbox?"}]

    while True:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            print(msg.content)
            break
        messages.append(msg)
        for tc in msg.tool_calls:
            result = dispatch(tc.function.name, json.loads(tc.function.arguments))
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })
"""

import zoho_client as zc


def dispatch(name: str, args: dict) -> dict:
    try:
        return _run(name, args)
    except Exception as e:
        return {"error": str(e)}


def _run(name: str, args: dict) -> dict:
    if name == "check_inbox":
        msgs = zc.list_messages("Inbox", args.get("limit", 20), args.get("offset", 0))
        return {"folder": "Inbox", "count": len(msgs), "messages": _slim(msgs)}

    if name == "check_sent":
        msgs = zc.list_sent(args.get("limit", 20), args.get("offset", 0))
        return {"folder": "Sent", "count": len(msgs), "messages": _slim(msgs)}

    if name == "read_email":
        return zc.get_message(args["message_id"])

    if name == "search_email":
        msgs = zc.search_messages(args["query"], args.get("limit", 20))
        return {"query": args["query"], "count": len(msgs), "messages": _slim(msgs)}

    if name == "check_storage":
        info = zc.get_storage_info()
        return {**info, "status": "WARNING — near full!" if info["is_warning"] else "OK"}

    if name == "backup_emails":
        return zc.backup_folder(args.get("folder", "Inbox"), args.get("max_messages", 500))

    if name == "list_folders":
        return {"folders": [
            {"name": f.get("folderName"), "id": f.get("folderId"), "unread": f.get("unreadCount")}
            for f in zc.get_folders()
        ]}

    return {"error": f"Unknown function: {name}"}


def _slim(msgs: list[dict]) -> list[dict]:
    keys = ["messageId", "subject", "fromAddress", "toAddress", "sentDateInGMT", "summary", "hasAttachment"]
    return [{k: m.get(k) for k in keys} for m in msgs]
