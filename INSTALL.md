# 📦 วิธีติดตั้ง (Installation)

ติดตั้งครั้งแรกใช้เวลา ~10 นาที ทำตามลำดับนี้

---

## สิ่งที่ต้องมีก่อน

- **Python 3.11+** — ดาวน์โหลด https://www.python.org/downloads/
  > ตอนติดตั้ง Python **ติ๊ก ✅ "Add Python to PATH"** ด้วย (สำคัญ)
  > เช็คว่ามีแล้ว: เปิด Terminal/PowerShell พิมพ์ `python --version`
- **บัญชี Zoho Mail** (ฟรีหรือเสียเงินก็ได้)

---

## ขั้นที่ 1 — เอาโค้ดมาลงเครื่อง

**วิธี A — git** (ถ้ามี git)
```bash
git clone https://github.com/OhayouOhayouOhayou/Mail_Skill_Zoho_BYOhayou.git
cd Mail_Skill_Zoho_BYOhayou
```

**วิธี B — ดาวน์โหลด ZIP**
ไปที่หน้า GitHub → ปุ่มเขียว **Code** → **Download ZIP** → แตกไฟล์ →
เปิด PowerShell ในโฟลเดอร์นั้น

---

## ขั้นที่ 2 — ติดตั้งแพ็กเกจหลัก

```bash
pip install -r requirements.txt
```

---

## ขั้นที่ 3 — เชื่อมต่อ Zoho (สร้าง .env อัตโนมัติ)

```bash
python setup.py
```

ตัวช่วยจะถามทีละขั้น:
1. เลือกภูมิภาค (com / eu / in / com.au / jp)
2. ใส่ **Client ID + Client Secret** — เอามาจาก https://api-console.zoho.com/
   → ADD CLIENT → **Self Client** → CREATE
3. ใส่ **Authorization Code** — แท็บ "Generate Code"
   scope: `ZohoMail.messages.ALL,ZohoMail.accounts.READ,ZohoMail.folders.READ`
4. ระบบแลก token + หาอีเมลให้เอง แล้วเขียนไฟล์ `.env`

> รายละเอียดการขอ key แบบเต็ม ดู [GUIDE.md](GUIDE.md) ข้อ 3

---

## ขั้นที่ 4 — ทดสอบว่าใช้ได้

```bash
python cli.py doctor
```
เห็น **"All good! 🎉"** = พร้อมใช้งาน ✅

---

## ขั้นที่ 5 — เริ่มใช้งาน

**ง่ายสุด — ดับเบิลคลิก** `start.bat` (ได้เมนูกดเลข)

หรือพิมพ์คำสั่ง:
```bash
python cli.py inbox        # เมลเข้า
python cli.py storage      # พื้นที่
python cli.py send ...     # ส่งเมล
```

---

## (เสริม) ติดตั้งฟีเจอร์เพิ่ม — ทำเฉพาะอันที่อยากใช้

| อยากได้ | ทำเพิ่ม |
|---|---|
| 🔔 **แจ้งเตือนเมล realtime (tray)** | `pip install -r requirements-desktop.txt` แล้วดับเบิลคลิก `notifier.bat` |
| ⏰ **เช็คพื้นที่อัตโนมัติ กันเมลเต็ม** | `python install_scheduler.py --hourly` |
| 🤖 **คุยกับ AI ในเครื่อง** | ใส่ `OPENROUTER_API_KEY` ใน `.env` → `python chat.py` |
| 🌐 **ใช้บน ChatGPT (เบราว์เซอร์)** | `pip install -r requirements-api.txt` → ดู [CHATGPT.md](CHATGPT.md) |
| 🧠 **ใช้บน Claude Code** | ดู [README.md](README.md) หัวข้อ MCP |
| 💻 **ใช้บน Codex** | ดู [CODEX.md](CODEX.md) |
| ✍️ **มี Signature ตอนส่งเมล** | `copy signature.html.example signature.html` แล้วแก้ |

---

## ติดปัญหา?

| อาการ | แก้ |
|---|---|
| `python` ไม่รู้จัก | ติดตั้ง Python ใหม่ + ติ๊ก "Add to PATH" |
| `pip` ไม่รู้จัก | ใช้ `python -m pip install ...` แทน |
| doctor แดง / token error | เช็ค Client ID/Secret/Region ใน `.env` หรือรัน `python setup.py` ใหม่ |
| ตัวหนังสือเพี้ยน | ปกติ — เป็นแค่หน้าจอ console เก่า ไม่กระทบการทำงาน |

ดูปัญหาอื่นๆ ใน [GUIDE.md](GUIDE.md) ข้อ 10
