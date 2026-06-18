# 📋 Summary — Zoho Mail Skill

สรุปสิ่งที่ทำ, ปัญหาที่แก้, และฟีเจอร์ทั้งหมดของโปรเจกต์

- **Repo:** https://github.com/OhayouOhayouOhayou/Mail_Skill_Zoho_BYOhayou
- **สถานะ:** ใช้งานได้จริง — ทดสอบกับเมล `csd@asefa.co.th` ผ่านแล้ว
- **ภาษา:** Python 3.11+ | **แพลตฟอร์ม:** Windows (รองรับ Mac/Linux บางส่วน)

---

## 1. โปรเจกต์นี้คืออะไร

ชุดเครื่องมือ "ผู้ช่วยอีเมล Zoho" ที่ **เช็ค / ค้นหา / อ่าน / ส่ง / สำรอง / เฝ้าดู**
เมลให้อัตโนมัติ ใช้ได้หลายช่องทาง ตั้งแต่กดเมนู ไปจนถึงสั่งงานด้วย AI
(Claude, ChatGPT, Codex, OpenRouter)

---

## 2. ฟีเจอร์ทั้งหมด

### 2.1 จัดการเมล (8 ความสามารถหลัก)
| ฟังก์ชัน | ทำอะไร |
|---|---|
| `check_inbox` | ดูเมลเข้าล่าสุด |
| `check_sent` | ดูเมลออกล่าสุด |
| `read_email` | อ่านเนื้อหาเมลเต็ม |
| `search_email` | ค้นหาเมล (หัวข้อ/ผู้ส่ง/ผู้รับ) |
| `check_storage` | เช็คพื้นที่ + เตือนเมื่อใกล้เต็ม |
| `list_folders` | ดูโฟลเดอร์ + จำนวนยังไม่อ่าน |
| `backup_emails` | สำรองเมลเป็นไฟล์ JSONL |
| `send_email` | ส่งเมล + แนบ Signature อัตโนมัติ |

### 2.2 ทำงานเบื้องหลัง / แจ้งเตือน
| ฟีเจอร์ | รายละเอียด |
|---|---|
| **Realtime Monitor** (`monitor.py`) | เฝ้าดูเมลเข้า + พื้นที่ ต่อเนื่อง แจ้งเข้า webhook |
| **Auto Storage Check** (`storage_alert.py` + `install_scheduler.py`) | Windows Scheduled Task เช็คพื้นที่อัตโนมัติทุกชั่วโมง **กันเมลเต็มจนรับส่งไม่ได้** |
| **Tray Notifier** (`notifier.py`) | โปรแกรมใน system tray เด้ง toast เมลเข้า-ออก realtime คลิกแล้วเปิด Zoho |

### 2.3 ช่องทางใช้งาน (6 แบบ)
| ช่องทาง | ไฟล์ | ต้องมี AI? |
|---|---|---|
| เมนูกดเลข | `start.bat` / `start.py` | ❌ |
| Command line | `cli.py` | ❌ |
| AI ในเครื่อง (OpenRouter) | `chat.py` | ✅ |
| Claude Code | `mcp_server.py` (MCP) | ✅ |
| OpenAI Codex | MCP / CLI ([CODEX.md](CODEX.md)) | ✅ |
| ChatGPT เว็บ | `api_server.py` (Custom GPT) | ✅ |

### 2.4 การติดตั้ง (3 แบบ)
| แบบ | ไฟล์ | เหมาะกับ |
|---|---|---|
| ตัวติดตั้ง .exe (แบบ Word) | `installer.iss` → `ZohoMail-Setup.exe` | ผู้ใช้ทั่วไป ไม่ต้องมี Python |
| หน้าต่าง GUI wizard | `setup_gui.py` | กดผ่านหน้าต่าง |
| One-click batch | `install.bat` | สาย command line |
| OAuth wizard (CLI) | `setup.py` | ตั้งค่าผ่านเทอร์มินัล |

---

## 3. ปัญหาที่เจอและแก้ไข

ระหว่างทดสอบกับ Zoho API จริง พบว่าโครงสร้าง API ต่างจากเอกสารหลายจุด —
แก้ครบทุกข้อ:

| # | ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|---|
| 1 | ดึง account ไม่ได้ (`'list' object has no attribute 'lower'`) | `emailAddress` เป็น **list** ไม่ใช่ string | ใช้ `primaryEmailAddress` / parse `mailId` |
| 2 | พื้นที่แสดงผิด/เป็น 0 | ใช้ field `usedQuota/totalQuota` (ไม่มีจริง) | เปลี่ยนเป็น `usedStorage/allowedStorage` หน่วย **KB** |
| 3 | อ่านเมล/backup ไม่ได้ (404) | content endpoint ต้องมี **folder path** | ใช้ `/folders/{folderId}/messages/{id}/content` |
| 4 | Backup **วนไม่จบ** (infinite loop) | นับเฉพาะที่สำเร็จ พอ fail หมด total ไม่ขยับ | นับตาม "ที่พยายาม" (attempts) แทน |
| 5 | ค้นหาเมล error 400 | Zoho server-side search ใช้ไม่ได้ | เปลี่ยนเป็น **client-side filter** จากเมลล่าสุด |
| 6 | โฟลเดอร์ดึงไม่ได้ (`INVALID_OAUTHSCOPE`) | scope ไม่มี `folders.READ` | **degrade graceful** — fallback ไป query ทุกโฟลเดอร์ inbox/storage/backup ยังทำงาน |
| 7 | `folderId Invalid data type` | ส่งชื่อ "Inbox" แทนเลข folderId | เพิ่ม `resolve_folder_id()` แปลงชื่อ→เลข |
| 8 | Token endpoint โดน **rate-limit** | ทุก process ขอ token ใหม่ | **cache token ลงดิสก์** ใช้ซ้ำข้าม process |
| 9 | ตัวหนังสือ crash บน Windows (`UnicodeEncodeError`) | console เป็น cp1252 | บังคับ **UTF-8 stdout** ทุก entry point |
| 10 | MCP หา `.env` ไม่เจอ | รันจากโฟลเดอร์อื่น | โหลด `.env` จาก**โฟลเดอร์โค้ดเสมอ** |
| 11 | ติดตั้งยาก ต้องพิมพ์ `curl` เอง | — | OAuth wizard (CLI + GUI) แลก token อัตโนมัติ |

---

## 4. ความปลอดภัย

- `.env`, `signature.html`, `.token_cache.json`, `storage_alerts.log` — อยู่ใน `.gitignore` ไม่หลุดขึ้น git
- API server มี **Bearer API key** ป้องกันการเรียกจากคนอื่น
- ส่งเมลเป็น action กระทบภายนอก — **ยืนยันก่อนส่งทุกครั้ง**

> ⚠️ Client Secret + Refresh Token ที่เคยแชร์ตอนตั้งค่า ควร revoke แล้วสร้างใหม่ที่ api-console.zoho.com

---

## 5. โครงสร้างไฟล์

```
แกนหลัก
  zoho_client.py        Zoho API + OAuth + retry + token cache + fallback
  cli.py                Command-line interface (doctor/inbox/send/...)

ติดตั้ง
  install.bat           ติดตั้งครบในคลิกเดียว
  setup.py              OAuth wizard (CLI)
  setup_gui.py          OAuth wizard (GUI หน้าต่าง)
  build_installer.bat   สร้าง ZohoMailSetup.exe
  installer.iss         Inno Setup → ZohoMail-Setup.exe (แบบ Word)

ใช้งาน / แจ้งเตือน
  start.py / start.bat  เมนูกดเลข
  chat.py               AI ในเครื่อง (OpenRouter)
  monitor.py            เฝ้าดู realtime + webhook
  storage_alert.py      เช็คพื้นที่ครั้งเดียว (สำหรับ schedule)
  install_scheduler.py  ตั้ง Windows Task เช็คพื้นที่อัตโนมัติ
  notifier.py           โปรแกรม tray เด้ง toast
  notifier.bat          เปิด notifier (ไม่มีหน้าต่างดำ)
  build_exe.bat         สร้าง ZohoMailNotifier.exe

เชื่อม AI
  mcp_server.py         MCP server (Claude / Codex)
  openai_tools.json     Tool schema (ChatGPT / Codex / OpenAI SDK)
  openai_dispatcher.py  ตัวกระจายคำสั่ง
  api_server.py         HTTP API (ChatGPT Custom GPT)

เอกสาร
  README.md  INSTALL.md  GUIDE.md  CHATGPT.md  CODEX.md  AGENTS.md  Summary.md
  signature.html.example   .env.example
```

---

## 6. สถานะการทดสอบ

| ฟีเจอร์ | สถานะ |
|---|---|
| doctor / inbox / sent / read | ✅ ทดสอบกับ API จริง |
| storage (27.92% used) | ✅ ทดสอบจริง |
| search (client-side) | ✅ ทดสอบจริง |
| backup (3 ฉบับ, 0 fail) | ✅ ทดสอบจริง |
| auto storage check (scheduled) | ✅ ทดสอบจริง (Task รัน, exit 0) |
| tray notifier toast | ✅ toast เด้งจริง |
| GUI wizard (หน้าต่าง) | ✅ เปิด/render ทุกขั้นผ่าน |
| send_email | ⏳ โค้ดพร้อม ยังไม่ได้ส่งจริง (รออนุญาต) |
| build .exe (PyInstaller/Inno) | ⏳ script พร้อม ยังไม่ได้ build จริง |

---

## 7. สิ่งที่ทำต่อได้ (ถ้าต้องการ)

- ทดสอบส่งเมลจริง (send_email)
- Build `.exe` / ตัวติดตั้ง Inno Setup จริง
- Deploy `api_server.py` ขึ้น cloud → URL ถาวรสำหรับ ChatGPT (ไม่ต้องเปิดเครื่อง)
- เพิ่มฟังก์ชัน: ลบเมล, mark read, ตอบกลับอัตโนมัติ
- แจ้งเตือนเข้า Telegram/Line (ตั้ง `NOTIFY_WEBHOOK`)
