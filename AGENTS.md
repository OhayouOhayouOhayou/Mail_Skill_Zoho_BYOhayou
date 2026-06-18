# AGENTS.md — Zoho Mail Skill

Guidance for AI coding agents (OpenAI Codex, etc.) working in this repo.

## What this project does
A Zoho Mail toolkit: check inbox/sent, read, search, storage usage, backup,
and send email (with signature). Usable from a CLI, a menu, an MCP server
(Claude/Codex), an HTTP API (ChatGPT Custom GPT), and a local AI chat.

## How to operate the mailbox (preferred: use the CLI)
Run these from the project root. Config is read from `.env`.

```bash
python cli.py doctor                       # verify connection
python cli.py inbox [N]                     # list recent inbox emails
python cli.py sent [N]                      # list recent sent emails
python cli.py read <messageId>             # read full email
python cli.py search <query> [N]           # search by keyword (subject/from/to)
python cli.py storage                       # storage usage + warning
python cli.py folders                       # folders + unread (needs folders scope)
python cli.py backup <folder> <N>          # backup to backups/*.jsonl
python cli.py send <to> "<subject>" "<body>"   # send email (asks to confirm)
```

## Programmatic use
- `import zoho_client as zc` and call `zc.list_messages`, `zc.get_storage_info`,
  `zc.send_email`, `zc.backup_folder`, etc.
- Tool schemas for function-calling are in `openai_tools.json`; route calls
  through `openai_dispatcher.dispatch(name, args)`.

## Rules
- **Sending email is outward-facing — confirm with the user before sending.**
- Never print or commit `.env`, `signature.html`, or `.token_cache.json`
  (already in `.gitignore`).
- Don't run unbounded backups; pass a sensible `max_messages`.

## Setup
`python setup.py` runs an interactive OAuth wizard that writes `.env`.
Required env: `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`,
`ZOHO_REGION`, `ZOHO_ACCOUNT_EMAIL`.
