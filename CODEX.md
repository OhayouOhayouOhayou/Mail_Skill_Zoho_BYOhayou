# 🤖 ใช้งานบน OpenAI Codex

Codex CLI คือ agent ในเทอร์มินัล (คล้าย Claude Code) ที่รันคำสั่ง/โค้ดได้
ใช้ Zoho Mail Skill ได้ **2 แบบ**

> ติดตั้ง Codex CLI: `npm install -g @openai/codex` แล้วล็อกอินด้วยบัญชี OpenAI

---

## แบบที่ 1 — ให้ Codex รัน CLI เอง (ง่ายสุด ไม่ต้องตั้งค่าอะไร)

Codex รัน shell ได้อยู่แล้ว เปิด Codex ในโฟลเดอร์โปรเจกต์:

```bash
cd D:/zoho-mail
codex
```

แล้วพิมพ์สั่งงานเป็นภาษาคนได้เลย Codex จะรัน `python cli.py ...` ให้:

```
เช็คเมลเข้า 10 ฉบับล่าสุดให้หน่อย
พื้นที่อีเมลเหลือเท่าไร
ส่งเมลหา boss@company.com หัวข้อ "รายงาน" บอกว่างานเสร็จแล้ว
backup กล่อง Inbox 200 ฉบับ
```

เบื้องหลัง Codex จะเรียกคำสั่งเหล่านี้:
| สั่ง | คำสั่งที่ Codex รัน |
|---|---|
| เช็คเมล | `python cli.py inbox 10` |
| เช็คพื้นที่ | `python cli.py storage` |
| ส่งเมล | `python cli.py send <to> "<subject>" "<body>"` |
| backup | `python cli.py backup Inbox 200` |

ไฟล์ [AGENTS.md](AGENTS.md) ในโปรเจกต์จะบอก Codex เองว่ามีคำสั่งอะไรบ้าง

---

## แบบที่ 2 — เชื่อมเป็น MCP Server (Codex เรียก tool ได้ตรงๆ)

Codex CLI รองรับ MCP เหมือน Claude แก้ไฟล์ `~/.codex/config.toml`
(บน Windows: `C:\Users\<ชื่อ>\.codex\config.toml`):

```toml
[mcp_servers.zoho-mail]
command = "python"
args = ["D:/zoho-mail/mcp_server.py"]
```

ถ้าอยากระบุ credentials ตรงนี้แทนไฟล์ `.env`:
```toml
[mcp_servers.zoho-mail]
command = "python"
args = ["D:/zoho-mail/mcp_server.py"]

[mcp_servers.zoho-mail.env]
ZOHO_CLIENT_ID = "1000...."
ZOHO_CLIENT_SECRET = "...."
ZOHO_REFRESH_TOKEN = "1000...."
ZOHO_REGION = "com"
ZOHO_ACCOUNT_EMAIL = "you@domain.com"
```

จากนั้นเปิด Codex ใหม่ มันจะเห็น tool 8 ตัว:
`check_inbox`, `check_sent`, `read_email`, `search_email`, `check_storage`,
`list_folders`, `backup_emails`, `send_email`

ตรวจว่า MCP ถูกโหลด: ในบาง Codex ใช้ `/mcp` หรือดูตอน start

---

## แบบที่ 3 — เขียนสคริปต์เอง (Codex/แอปของคุณ ผ่าน OpenAI SDK)

ถ้าจะ build แอปด้วย OpenAI API โดยตรง ใช้ `openai_tools.json` +
`openai_dispatcher.py` ได้เลย (ดูตัวอย่างใน [README.md](README.md))

---

## แบบไหนดี?

| สถานการณ์ | แนะนำ |
|---|---|
| อยากเริ่มเร็ว ไม่ตั้งค่า | **แบบ 1** (Codex รัน cli.py) |
| อยากให้ Codex เรียก tool เนียนๆ ใช้บ่อย | **แบบ 2** (MCP) |
| สร้างแอป/automation เอง | **แบบ 3** (SDK) |

> ก่อนใช้ทุกแบบ ต้องตั้งค่า `.env` ให้เรียบร้อยก่อน (รัน `python setup.py`)
