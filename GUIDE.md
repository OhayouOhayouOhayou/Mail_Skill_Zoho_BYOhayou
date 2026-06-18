# คู่มือการใช้งาน Zoho Mail Skill

## สารบัญ
1. [ภาพรวมระบบ](#1-ภาพรวมระบบ)
2. [ความต้องการระบบ](#2-ความต้องการระบบ)
3. [การตั้งค่า Zoho OAuth2 (สำคัญมาก)](#3-การตั้งค่า-zoho-oauth2)
4. [การติดตั้ง Python และ Dependencies](#4-การติดตั้ง)
5. [การตั้งค่าสำหรับ Claude Code (MCP)](#5-claude-code-mcp)
6. [การตั้งค่าสำหรับ ChatGPT / Codex](#6-chatgpt--codex)
7. [การใช้งาน Monitor แบบ Continuous](#7-monitor)
8. [การ Backup อีเมล](#8-backup)
9. [ตัวอย่าง Prompt ภาษาไทย / อังกฤษ](#9-ตัวอย่าง-prompt)
10. [แก้ปัญหาที่พบบ่อย](#10-troubleshooting)

---

## 1. ภาพรวมระบบ

```
┌─────────────────────────────────────────────────────┐
│                   Zoho Mail Skill                   │
├────────────────────┬────────────────────────────────┤
│   Claude Code      │     ChatGPT / Codex            │
│   (MCP Server)     │     (Function Calling)         │
│   mcp_server.py    │     openai_tools.json          │
│                    │     openai_dispatcher.py        │
├────────────────────┴────────────────────────────────┤
│              zoho_client.py (Core)                  │
│         Zoho Mail REST API  +  OAuth2               │
└─────────────────────────────────────────────────────┘
```

### เครื่องมือทั้งหมด

| ชื่อ Tool | ทำอะไร |
|---|---|
| `check_inbox` | ดูเมลเข้าล่าสุด |
| `check_sent` | ดูเมลออกล่าสุด |
| `read_email` | อ่านเนื้อหาเมลแบบเต็ม |
| `search_email` | ค้นหาเมลด้วย keyword |
| `check_storage` | ตรวจพื้นที่ / แจ้งเตือนเมื่อใกล้เต็ม |
| `backup_emails` | สำรองข้อมูลเมลเป็นไฟล์ JSONL |

---

## 2. ความต้องการระบบ

- **Python** 3.11 ขึ้นไป
- **บัญชี Zoho Mail** (Free หรือ Paid)
- **Internet connection** เพื่อเรียก Zoho API
- สำหรับ Claude Code: **Claude Code CLI** ติดตั้งแล้ว
- สำหรับ ChatGPT: **OpenAI Python SDK** (`pip install openai`)

---

## 3. การตั้งค่า Zoho OAuth2

นี่คือขั้นตอนที่สำคัญที่สุด ต้องทำก่อนทุกอย่าง

### 3.1 สร้าง OAuth Application

1. ไปที่ https://api-console.zoho.com/
2. เข้าสู่ระบบด้วยบัญชี Zoho ของคุณ
3. คลิก **"ADD CLIENT"**
4. เลือกประเภท **"Self Client"** (เหมาะสำหรับการใช้งานส่วนตัว)
5. คลิก **"CREATE"**
6. บันทึก **Client ID** และ **Client Secret** ไว้

### 3.2 สร้าง Refresh Token

1. ในหน้า Self Client ที่สร้างไว้ คลิกแท็บ **"Generate Code"**
2. กรอก Scope ดังนี้ (แนะนำให้ครบทั้ง 3):
   ```
   ZohoMail.messages.ALL,ZohoMail.accounts.READ,ZohoMail.folders.READ
   ```
   > - `messages.ALL` = อ่าน + backup เมล
   > - `accounts.READ` = ดูข้อมูลบัญชี + พื้นที่
   > - `folders.READ` = กรองตามโฟลเดอร์ + คำสั่ง `folders` (ถ้าไม่ใส่ inbox/storage/backup ยังทำงานได้)
3. เลือก **Time Duration**: 10 minutes
4. กรอก **Scope Description**: ใส่อะไรก็ได้ เช่น "Mail Monitor"
5. คลิก **"CREATE"** → จะได้ **Authorization Code** (ใช้ได้ 10 นาที)

### 3.3 แลก Authorization Code เป็น Refresh Token

เปิด Terminal แล้วรันคำสั่งนี้ (แทนค่าให้ถูกต้อง):

```bash
curl -X POST "https://accounts.zoho.com/oauth/v2/token" \
  -d "grant_type=authorization_code" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://www.zoho.com/books/api/v3" \
  -d "code=YOUR_AUTHORIZATION_CODE"
```

**บน Windows PowerShell:**
```powershell
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

**ผลลัพธ์ที่ได้:**
```json
{
  "access_token": "...",
  "refresh_token": "1000.xxxxxxxx.yyyyyyyy",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

บันทึก **`refresh_token`** ไว้ — ใช้ไม่หมดอายุ (จนกว่าจะ revoke)

### 3.4 กำหนด Region ให้ถูกต้อง

| คุณใช้ Zoho ที่ไหน | ZOHO_REGION |
|---|---|
| zoho.**com** (US/Global) | `com` |
| zoho.**eu** (Europe) | `eu` |
| zoho.**in** (India) | `in` |
| zoho.**com.au** (Australia) | `com.au` |
| zoho.**jp** (Japan) | `jp` |

### 3.5 ตั้งค่าไฟล์ .env

```bash
# คัดลอก template
copy .env.example .env
```

แก้ไขไฟล์ `.env`:
```env
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZOHO_REFRESH_TOKEN=1000.xxxxxxxxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyy
ZOHO_REGION=com
ZOHO_ACCOUNT_EMAIL=yourname@yourdomain.com
STORAGE_WARN_PERCENT=80
BACKUP_DIR=./backups
POLL_SECONDS=60
```

---

## 4. การติดตั้ง

```bash
# ไปยังโฟลเดอร์โปรเจกต์
cd D:\zoho-mail

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### ทดสอบว่าเชื่อมต่อได้

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import zoho_client as z
print('Account ID:', z.account_id())
print('Storage:', z.get_storage_info())
print('OK!')
"
```

ถ้าเห็น `OK!` แสดงว่าเชื่อมต่อสำเร็จ

---

## 5. Claude Code (MCP)

### 5.1 เพิ่ม MCP Server

เปิดไฟล์ `.claude/settings.json` (อยู่ใน home directory หรือ project directory):

```json
{
  "mcpServers": {
    "zoho-mail": {
      "command": "python",
      "args": ["D:/zoho-mail/mcp_server.py"],
      "env": {
        "ZOHO_CLIENT_ID": "1000.XXXXXXXXXX",
        "ZOHO_CLIENT_SECRET": "xxxxxxxxxxxxxxxx",
        "ZOHO_REFRESH_TOKEN": "1000.xxxx.yyyy",
        "ZOHO_ACCOUNT_EMAIL": "you@domain.com",
        "ZOHO_REGION": "com",
        "STORAGE_WARN_PERCENT": "80",
        "BACKUP_DIR": "D:/zoho-mail/backups"
      }
    }
  }
}
```

> **Tip**: ถ้าไม่ต้องการใส่ credentials ใน settings.json ให้ใช้ไฟล์ .env แทน แล้วไม่ต้องใส่ "env" block

### 5.2 รีสตาร์ท Claude Code

ปิดและเปิด Claude Code ใหม่ หรือรันคำสั่ง:
```
/mcp
```
แล้วตรวจสอบว่า `zoho-mail` ปรากฏใน list

### 5.3 ทดสอบใน Claude Code

พิมพ์ใน chat:
```
ตรวจสอบเมลเข้าล่าสุด 5 ฉบับ
```
Claude จะเรียก `check_inbox` อัตโนมัติ

---

## 6. ChatGPT / Codex

### 6.1 ติดตั้ง OpenAI SDK

```bash
pip install openai
```

### 6.2 สร้างสคริปต์ Integration

สร้างไฟล์ `chatgpt_example.py`:

```python
import os, json, openai
from dotenv import load_dotenv
from openai_dispatcher import dispatch

load_dotenv()

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
tools = json.load(open("openai_tools.json"))

def chat(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        
        # ถ้าไม่มี tool call = จบแล้ว
        if not msg.tool_calls:
            return msg.content
        
        # เพิ่ม assistant message
        messages.append(msg)
        
        # เรียก tool แต่ละตัว
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = dispatch(tc.function.name, args)
            print(f"[Tool] {tc.function.name}({args}) → {list(result.keys())}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

# ทดสอบ
if __name__ == "__main__":
    print(chat("พื้นที่อีเมลใช้ไปแล้วเท่าไร"))
    print(chat("ดูเมลเข้าล่าสุด 5 ฉบับ"))
```

เพิ่ม `OPENAI_API_KEY` ใน `.env`:
```env
OPENAI_API_KEY=sk-...
```

รัน:
```bash
python chatgpt_example.py
```

### 6.3 สำหรับ Codex / Assistants API

ใช้ tool definitions จาก `openai_tools.json` ได้เลย รูปแบบเข้ากันได้กับ:
- `gpt-4o`, `gpt-4o-mini`
- `gpt-4-turbo`
- `o1`, `o3` (รองรับ function calling)
- OpenAI Assistants API

---

## 7. Monitor แบบ Continuous

### 7.1 รัน Monitor

```bash
python monitor.py
```

**ตัวอย่าง Output:**
```
[2026-06-18 10:00:00] Monitor started — polling every 60s | Storage warn at 80%
[2026-06-18 10:00:01] Loaded 47 existing inbox IDs.
[2026-06-18 10:00:02] Storage OK      | 45.3% used (2316.8 MB / 5120.0 MB)
[2026-06-18 10:01:02] NEW MAIL  | From: boss@company.com | Subject: Q3 Report | ID: 123456
[2026-06-18 10:01:02] Storage OK      | 45.3% used (2316.8 MB / 5120.0 MB)
```

### 7.2 ปรับ Interval

```bash
# ตรวจทุก 30 วินาที
POLL_SECONDS=30 python monitor.py

# ตรวจทุก 5 นาที
POLL_SECONDS=300 python monitor.py
```

### 7.3 รันเป็น Background Service (Windows)

**วิธีที่ 1 — Task Scheduler:**
1. เปิด Task Scheduler → Create Basic Task
2. Trigger: At startup
3. Action: `python D:\zoho-mail\monitor.py`
4. ✅ Run whether user is logged on or not

**วิธีที่ 2 — PowerShell Background:**
```powershell
Start-Process python -ArgumentList "D:\zoho-mail\monitor.py" `
  -RedirectStandardOutput "D:\zoho-mail\monitor.log" `
  -WindowStyle Hidden
```

**วิธีที่ 3 — NSSM (Non-Sucking Service Manager):**
```bash
nssm install ZohoMailMonitor python D:\zoho-mail\monitor.py
nssm start ZohoMailMonitor
```

### 7.4 เชื่อมกับ Notification

แก้ไข `monitor.py` ที่ฟังก์ชัน `check_new_inbox()` เพื่อส่ง notification:

```python
# ตัวอย่าง: ส่ง Windows notification
import subprocess

def notify(title: str, message: str):
    subprocess.run([
        "powershell", "-Command",
        f'[System.Windows.MessageBox]::Show("{message}", "{title}")'
    ])

# ใน check_new_inbox() เพิ่ม:
notify("New Email", f"From: {m.get('fromAddress')}\n{m.get('subject')}")
```

---

## 8. Backup

### 8.1 Backup ผ่าน Command Line

```bash
# Backup Inbox (500 ฉบับ)
python -c "
import zoho_client as z
path = z.backup_folder('Inbox', 500)
print('Saved to:', path)
"

# Backup Sent (100 ฉบับ)
python -c "
import zoho_client as z
print(z.backup_folder('Sent', 100))
"
```

### 8.2 Backup ผ่าน Claude / ChatGPT

```
Backup กล่อง Inbox ทั้งหมด 1000 ฉบับ
```

```
สำรองข้อมูลอีเมลใน Sent box ไว้ 200 ฉบับ
```

### 8.3 รูปแบบไฟล์ Backup

ไฟล์จะถูกบันทึกที่ `./backups/` ชื่อรูปแบบ:
```
backup_inbox_20260618_120000.jsonl
```

แต่ละบรรทัดเป็น JSON ของเมล 1 ฉบับ:
```json
{"messageId":"123","subject":"Hello","fromAddress":"a@b.com","content":"..."}
```

### 8.4 อ่านไฟล์ Backup

```python
import json

with open("backups/backup_inbox_20260618_120000.jsonl") as f:
    emails = [json.loads(line) for line in f]

print(f"Total: {len(emails)} emails")
for e in emails[:5]:
    print(e["subject"], "-", e["fromAddress"])
```

### 8.5 Backup อัตโนมัติรายวัน

เพิ่มใน Windows Task Scheduler หรือสร้างไฟล์ `auto_backup.py`:

```python
import schedule, time, zoho_client as z
from dotenv import load_dotenv

load_dotenv()

def daily_backup():
    print("Starting daily backup...")
    path = z.backup_folder("Inbox", 1000)
    print(f"Done: {path}")

schedule.every().day.at("02:00").do(daily_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

```bash
pip install schedule
python auto_backup.py
```

---

## 9. ตัวอย่าง Prompt

### ตรวจสอบเมล

```
ดูเมลเข้าล่าสุด 10 ฉบับ
Show me the last 10 inbox emails
```

```
มีเมลใหม่ไหมวันนี้
Any new emails today?
```

```
ค้นหาเมลจาก noreply@github.com
Search for emails from boss@company.com
```

```
อ่านเนื้อหาเมล ID 123456789
Read email with message ID 123456789
```

### ตรวจสอบพื้นที่

```
พื้นที่อีเมลยังเหลืออยู่เท่าไร ใกล้เต็มไหม
How much storage is left? Is it almost full?
```

```
ตรวจสอบ quota ของกล่องอีเมล
Check my mailbox storage quota
```

### Backup

```
Backup กล่อง Inbox ไว้ก่อนเลย
Please backup my Inbox now
```

```
สำรองข้อมูลอีเมล Sent 200 ฉบับล่าสุด
Backup the last 200 sent emails
```

```
ช่วย backup ทั้ง Inbox และ Sent box ให้ด้วย
Backup both Inbox and Sent folders, 500 each
```

---

## 10. Troubleshooting

### ❌ Token refresh failed

**สาเหตุ:** Client ID / Secret / Refresh Token ผิด หรือ Region ไม่ถูก

**แก้ไข:**
1. ตรวจสอบค่าใน `.env` ให้ถูกต้อง
2. ตรวจสอบ `ZOHO_REGION` ให้ตรงกับ domain ของคุณ
3. ลอง generate refresh token ใหม่ที่ api-console.zoho.com

---

### ❌ Account not found for ...

**สาเหตุ:** `ZOHO_ACCOUNT_EMAIL` ไม่ตรงกับบัญชีใน Zoho

**แก้ไข:**
```python
# ดู email ที่มีในบัญชีของคุณ
python -c "
import httpx, zoho_client as z
r = httpx.get(f'{z.BASE_URL}/accounts', headers=z._headers())
for a in r.json().get('data', []):
    print(a.get('emailAddress'))
"
```
แล้วนำ email ที่ได้ไปใส่ใน `.env`

---

### ❌ MCP server ไม่ขึ้นใน Claude Code

**แก้ไข:**
1. ทดสอบ server รันได้ก่อน: `python mcp_server.py` (ควร hang รอ input)
2. ตรวจ path ใน settings.json ใช้ forward slash: `D:/zoho-mail/mcp_server.py`
3. ตรวจ Python path: `where python` แล้วใส่ full path ใน settings.json

---

### ❌ Storage แสดง 0 MB

**สาเหตุ:** Scope ไม่มี `ZohoMail.accounts.READ`

**แก้ไข:** Generate token ใหม่พร้อม scope ที่ถูกต้อง:
```
ZohoMail.messages.READ,ZohoMail.accounts.READ
```

---

### ❌ Backup ช้ามาก

**สาเหตุ:** แต่ละเมลต้องเรียก API แยก (rate limit)

**แก้ไข:** ลด `max_messages` หรือเพิ่ม delay ระหว่าง request:
```python
# ใน zoho_client.py ฟังก์ชัน backup_folder เพิ่ม:
import time
time.sleep(0.2)  # หลังแต่ละ message
```

---

### Rate Limits ของ Zoho Mail API

| ประเภท | Limit |
|---|---|
| API calls / day | 100,000 (Paid) / 1,000 (Free) |
| API calls / minute | 60 |
| Max messages per request | 200 |

หากเจอ error `429 Too Many Requests` ให้เพิ่ม `POLL_SECONDS` หรือลด batch size
