# 📬 Mail Skill — Zoho Mail for Claude & ChatGPT

Monitor inbox/outbox, check storage, and backup emails — works with **Claude Code (MCP)** and **ChatGPT / OpenAI Codex (Function Calling)**.

---

## ✨ Features

| Tool | Description |
|---|---|
| `check_inbox` | ดูเมลเข้าล่าสุด / List recent inbox emails |
| `check_sent` | ดูเมลออกล่าสุด / List recent sent emails |
| `read_email` | อ่านเนื้อหาเมลเต็ม / Read full email content |
| `search_email` | ค้นหาเมล / Search by keyword or sender |
| `check_storage` | ตรวจพื้นที่ / Check quota & warn if near full |
| `backup_emails` | สำรองเมล / Export emails to local JSONL file |

---

## ⚡ Quick Start

### 1 — Clone & Install

```bash
git clone https://github.com/OhayouOhayouOhayou/Mail_Skill_Zoho_BYOhayou.git
cd Mail_Skill_Zoho_BYOhayou
pip install -r requirements.txt
```

### 2 — Get Zoho OAuth2 Credentials

1. Go to **https://api-console.zoho.com/**
2. **ADD CLIENT** → choose **Self Client** → Create
3. Copy your **Client ID** and **Client Secret**
4. Click tab **"Generate Code"**, enter scope:
   ```
   ZohoMail.messages.ALL,ZohoMail.accounts.READ
   ```
5. Click **Create** → copy the **Authorization Code** (expires in 10 min)
6. Run this to get your **Refresh Token**:

```bash
# macOS / Linux
curl -X POST "https://accounts.zoho.com/oauth/v2/token" \
  -d "grant_type=authorization_code" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://www.zoho.com/books/api/v3" \
  -d "code=YOUR_AUTHORIZATION_CODE"
```

```powershell
# Windows PowerShell
Invoke-RestMethod -Method Post `
  -Uri "https://accounts.zoho.com/oauth/v2/token" `
  -Body @{
    grant_type    = "authorization_code"
    client_id     = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    redirect_uri  = "https://www.zoho.com/books/api/v3"
    code          = "YOUR_AUTHORIZATION_CODE"
  }
```

Save the `refresh_token` from the response — it never expires.

### 3 — Configure .env

```bash
cp .env.example .env
```

Edit `.env`:

```env
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZOHO_REFRESH_TOKEN=1000.xxxxxxxx.yyyyyyyy
ZOHO_REGION=com
ZOHO_ACCOUNT_EMAIL=you@yourdomain.com
STORAGE_WARN_PERCENT=80
BACKUP_DIR=./backups
POLL_SECONDS=60
```

> **ZOHO_REGION**: `com` (US/Global) · `eu` (Europe) · `in` (India) · `com.au` · `jp`

### 4 — Test Connection

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
import zoho_client as z
print('Account ID:', z.account_id())
print('Storage:', z.get_storage_info())
print('OK - Connected!')
"
```

---

## 🤖 Claude Code Setup (MCP)

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "zoho-mail": {
      "command": "python",
      "args": ["/path/to/Mail_Skill_Zoho_BYOhayou/mcp_server.py"]
    }
  }
}
```

Restart Claude Code, then just ask:

```
ตรวจสอบเมลเข้าล่าสุด 10 ฉบับ
พื้นที่อีเมลยังเหลืออยู่เท่าไร
Backup กล่อง Inbox 500 ฉบับ
```

---

## 💬 ChatGPT / OpenAI Codex Setup

```python
import os, json, openai
from dotenv import load_dotenv
from openai_dispatcher import dispatch

load_dotenv()
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
tools  = json.load(open("openai_tools.json"))

def chat(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    while True:
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages,
            tools=tools, tool_choice="auto",
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        for tc in msg.tool_calls:
            result = dispatch(tc.function.name, json.loads(tc.function.arguments))
            messages.append({
                "role": "tool", "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

print(chat("Check my inbox"))
print(chat("How full is my mailbox?"))
print(chat("Backup Inbox 200 emails"))
```

Add `OPENAI_API_KEY=sk-...` to your `.env`.

---

## 📡 Continuous Monitor

Polls inbox and storage automatically — prints alerts to stdout.

```bash
python monitor.py
```

```
[2026-06-18 10:00:00] Monitor started — polling every 60s | Storage warn at 80%
[2026-06-18 10:00:01] Loaded 47 existing inbox IDs.
[2026-06-18 10:00:02] Storage OK      | 45.3% used (2316.8 MB / 5120.0 MB)
[2026-06-18 10:01:05] NEW MAIL  | From: boss@company.com | Subject: Q3 Report | ID: 9988776
```

**Custom interval:**
```bash
POLL_SECONDS=30 python monitor.py
```

**Run in background (Windows):**
```powershell
Start-Process python -ArgumentList "monitor.py" `
  -RedirectStandardOutput "monitor.log" -WindowStyle Hidden
```

---

## 💾 Backup Emails

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
import zoho_client as z
print(z.backup_folder('Inbox', 500))
"
```

Output: `./backups/backup_inbox_20260618_120000.jsonl`  
Each line is a full email as JSON.

---

## 📁 File Structure

```
Mail_Skill_Zoho_BYOhayou/
├── .env.example          # Config template — copy to .env
├── requirements.txt      # Python dependencies
├── zoho_client.py        # Core — Zoho API + OAuth2 token refresh
├── mcp_server.py         # Claude Code MCP server (stdio)
├── openai_tools.json     # ChatGPT / Codex tool definitions
├── openai_dispatcher.py  # ChatGPT function call handler
├── monitor.py            # Standalone continuous monitor
├── zoho-mail.skill       # Claude Code skill descriptor
└── GUIDE.md              # Full guide in Thai + English
```

---

## 🔒 Security

- `.env` is in `.gitignore` — credentials are **never committed**
- Refresh token never expires — keep it secret
- Use read-only scope (`ZohoMail.messages.READ`) if backup is not needed

---

## 📖 Full Guide

See [GUIDE.md](GUIDE.md) for detailed setup, troubleshooting, Windows Service, auto daily backup, and rate limit tips.

---

## License

MIT
