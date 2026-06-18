# 📦 วิธีติดตั้ง (Installation)

ติดตั้งครั้งแรกใช้เวลา ~10 นาที ทำตามลำดับนี้

---

## สิ่งที่ต้องมีก่อน

- **Python 3.11+** — ดาวน์โหลด https://www.python.org/downloads/
  > ตอนติดตั้ง Python **ติ๊ก ✅ "Add Python to PATH"** ด้วย (สำคัญ)
  > เช็คว่ามีแล้ว: เปิด Terminal/PowerShell พิมพ์ `python --version`
- **บัญชี Zoho Mail** (ฟรีหรือเสียเงินก็ได้)

---

## 🖱️ มี 3 แบบให้เลือก

| แบบ | เหมาะกับ | วิธี |
|---|---|---|
| **A. ตัวติดตั้ง .exe (แบบ Word)** | ผู้ใช้ทั่วไป ไม่ต้องมี Python | ดับเบิลคลิก `ZohoMail-Setup.exe` → wizard 1-2-3 |
| **B. หน้าต่างตั้งค่า (GUI)** | มี Python แล้ว อยากกดผ่านหน้าต่าง | `python setup_gui.py` |
| **C. install.bat (เมนู)** | สาย command line | ดับเบิลคลิก `install.bat` |

> แบบ A ต้อง "สร้าง" ตัวติดตั้งก่อน (ดูหัวข้อ [สร้างตัวติดตั้ง](#-สร้างตัวติดตั้ง-exe-แบบ-word) ล่างสุด)
> — สร้างครั้งเดียว แล้วแจกไฟล์ `.exe` ให้ใครก็ได้ใช้โดยไม่ต้องลง Python

---

## 🚀 แบบ C — ดับเบิลคลิก `install.bat`

หลังเอาโค้ดมาลงเครื่องแล้ว (ขั้นที่ 1 ด้านล่าง) แค่**ดับเบิลคลิก `install.bat`**
มันจะทำให้อัตโนมัติ:
1. เช็คว่ามี Python ไหม
2. ติดตั้งแพ็กเกจหลัก
3. ถามว่าจะลงตัวแจ้งเตือน tray ด้วยไหม
4. เปิดตัวตั้งค่า Zoho (คุณกรอก **Client ID / Secret / Authorization Code** เอง)
5. ตรวจสอบการเชื่อมต่อ
6. ถามว่าจะตั้งเช็คพื้นที่อัตโนมัติไหม

เสร็จแล้วเปิดใช้งานด้วย `start.bat` ได้เลย

> ถ้าอยากทำเองทีละขั้น (หรือใช้ Mac/Linux) ทำตามด้านล่าง

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

---

## 🏗️ สร้างตัวติดตั้ง .exe (แบบ Word)

ทำครั้งเดียวบนเครื่องที่มี Python แล้วได้ไฟล์ `.exe` ที่แจกให้คนอื่น
ดับเบิลคลิกใช้ได้เลย **โดยไม่ต้องลง Python**

**ขั้นที่ 1 — สร้างหน้าต่างตั้งค่าเป็น exe**
```bash
build_installer.bat      →  dist\ZohoMailSetup.exe
```

**ขั้นที่ 2 (ถ้าอยากได้ตัวแจ้งเตือนด้วย)**
```bash
build_exe.bat            →  dist\ZohoMailNotifier.exe
```

**ขั้นที่ 3 — แพ็กเป็นตัวติดตั้งจริง (มี shortcut/Start Menu แบบ Word)**
1. ติดตั้ง **Inno Setup** (ฟรี): https://jrsoftware.org/isdl.php
2. เปิดไฟล์ `installer.iss` ด้วย Inno Setup → กด **Compile**
3. ได้ไฟล์ `Output\ZohoMail-Setup.exe`

ส่งไฟล์ `ZohoMail-Setup.exe` ให้ผู้ใช้ → ดับเบิลคลิก → ติดตั้งลงเครื่อง +
สร้างไอคอน → เปิด wizard ให้กรอก Client ID/Secret เอง → เสร็จ

> ผู้ใช้ปลายทางแค่เตรียม Client ID + Secret + Authorization Code จาก
> api-console.zoho.com มากรอกในหน้าต่าง wizard เท่านั้น
