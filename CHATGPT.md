# 💬 ใช้งานบน ChatGPT (Browser) ผ่าน Custom GPT

คู่มือนี้ทำให้คุณพิมพ์คุยกับ ChatGPT บนเว็บ แล้วให้มันเช็คเมล / พื้นที่ / backup
Zoho Mail ของคุณได้ โดยใช้ **Custom GPT + Actions**

> ต้องใช้ **ChatGPT Plus** ขึ้นไป (Custom GPT เปิดให้เฉพาะผู้ใช้แบบเสียเงิน)

---

## ภาพรวมการทำงาน

```
ChatGPT (เบราว์เซอร์)
      │  เรียก Action (HTTPS)
      ▼
Public URL (cloudflared / ngrok)   ←─ tunnel
      ▼
api_server.py  (เครื่องคุณ :8000)
      ▼
Zoho Mail API
```

ChatGPT เรียกได้เฉพาะ URL สาธารณะ (https) — เครื่องคุณอยู่หลังบ้าน เลยต้องเปิด
**tunnel** ให้เป็น URL สาธารณะชั่วคราว

---

## ขั้นตอนที่ 1 — ติดตั้งและตั้งค่า

```bash
pip install -r requirements-api.txt
```

เพิ่มใน `.env`:
```env
# ตั้ง API_KEY เป็นอะไรก็ได้ที่เดายาก (ความลับระหว่างคุณกับ ChatGPT)
API_KEY=ตั้งรหัสลับยาวๆ_ของคุณเอง
PORT=8000
```

> `API_KEY` คือกุญแจกันคนอื่นมายิง API ของคุณ — ถ้าไม่ตั้ง ระบบจะสุ่มให้
> และพิมพ์ออกมาตอนเริ่ม server

---

## ขั้นตอนที่ 2 — รัน API server

```bash
python api_server.py
```
เห็นข้อความ `Starting Zoho Mail API on http://localhost:8000` = ใช้ได้
**เปิดหน้าต่างนี้ทิ้งไว้**

---

## ขั้นตอนที่ 3 — เปิด Public URL ด้วย Tunnel

เปิด Terminal **หน้าต่างใหม่** (อย่าปิดอันที่รัน server)

### ตัวเลือก A — Cloudflared (แนะนำ ฟรี ไม่ต้องสมัคร)

ดาวน์โหลด: https://github.com/cloudflare/cloudflared/releases
(เลือก `cloudflared-windows-amd64.exe`) แล้วรัน:

```bash
cloudflared tunnel --url http://localhost:8000
```

จะได้ URL แบบ `https://random-words.trycloudflare.com` — **คัดลอกไว้**

### ตัวเลือก B — ngrok

```bash
ngrok http 8000
```
ได้ URL แบบ `https://xxxx.ngrok-free.app` (ต้องสมัครบัญชีฟรีก่อน)

---

## ขั้นตอนที่ 4 — บอก URL ให้ server แล้ว restart

หยุด server (Ctrl+C) แล้วเพิ่ม URL ที่ได้ลงใน `.env`:
```env
PUBLIC_URL=https://random-words.trycloudflare.com
```
รัน `python api_server.py` ใหม่อีกครั้ง

> ขั้นนี้ทำให้ schema มี `servers` ที่ถูกต้อง ตอน ChatGPT import จะได้รู้ว่ายิงไปไหน

ทดสอบว่า public ใช้ได้ (เปิดในเบราว์เซอร์):
```
https://random-words.trycloudflare.com/openapi.json
```
ถ้าเห็น JSON = พร้อมแล้ว

---

## ขั้นตอนที่ 5 — สร้าง Custom GPT

1. ไปที่ https://chatgpt.com/gpts/editor  (หรือ Explore GPTs → **+ Create**)
2. แท็บ **Configure** → ตั้งชื่อ เช่น "Zoho Mail Assistant"
3. เลื่อนลงล่าง → **Create new action**
4. ในหน้า Action:
   - **Authentication** → เลือก **API Key**
     - Auth Type: **Bearer**
     - API Key: ใส่ค่า `API_KEY` ที่ตั้งใน `.env`
   - **Schema** → กด **Import from URL** แล้ววาง:
     ```
     https://random-words.trycloudflare.com/openapi.json
     ```
     (หรือเปิด URL นั้น คัดลอก JSON มาวางในช่อง schema)
5. จะเห็น Actions โผล่มา 7 ตัว: `check_inbox`, `check_sent`, `read_email`,
   `search_email`, `check_storage`, `list_folders`, `backup_emails`
6. กด **Save / Update** (มุมขวาบน) → เลือก Only me

---

## ขั้นตอนที่ 6 — คุยได้เลย! 🎉

ในหน้าต่าง Preview ของ Custom GPT พิมพ์:

```
มีเมลใหม่อะไรบ้าง 5 ฉบับล่าสุด
พื้นที่อีเมลใช้ไปเท่าไรแล้ว ใกล้เต็มไหม
ค้นหาเมลที่มีคำว่า invoice
backup กล่อง Inbox 50 ฉบับ
```

ครั้งแรกที่เรียก ChatGPT จะถามยืนยัน "Allow action?" → กด **Allow / Always Allow**

---

## 💡 Instructions แนะนำ (วางในช่อง Instructions ของ Custom GPT)

```
You are a Zoho Mail assistant. Use the provided actions to check the user's
inbox and sent mail, read emails, search, check mailbox storage, and run
backups. When listing emails, show sender, subject, and date in a compact
table. Reply in the same language the user writes (Thai or English). Before
running a backup, confirm the folder and number of messages.
```

---

## ⚠️ ข้อควรรู้

| เรื่อง | รายละเอียด |
|---|---|
| URL เปลี่ยนทุกครั้ง | cloudflared/ngrok ฟรีจะได้ URL ใหม่ทุกครั้งที่รัน → ต้องอัปเดต `PUBLIC_URL` + re-import schema ใน GPT |
| ต้องเปิดเครื่องไว้ | API รันบนเครื่องคุณ ถ้าปิดเครื่อง/ปิด tunnel ChatGPT จะเรียกไม่ได้ |
| URL ถาวร | ถ้าอยากได้ URL ไม่เปลี่ยน ใช้ Cloudflare Named Tunnel หรือ deploy ขึ้น cloud (Render/Railway/Fly.io) |
| backup ช้า | ผ่าน Action จำกัด ~300 ฉบับ และอาจ timeout ถ้าเยอะ — backup เยอะๆ ใช้ `python cli.py backup` บนเครื่องดีกว่า |
| ความปลอดภัย | อย่าแชร์ `API_KEY` และ public URL ให้คนอื่น ใครมีทั้งคู่จะเข้าถึงเมลคุณได้ |

---

## อยากได้ URL ถาวร / ไม่ต้องเปิดเครื่อง?

Deploy `api_server.py` ขึ้น cloud ฟรีได้ เช่น **Render.com** หรือ **Railway.app**:
- ใส่ env vars (ZOHO_*, API_KEY) ในแดชบอร์ดของ service
- ตั้ง start command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
- ได้ URL ถาวร เช่น `https://your-app.onrender.com` → ใช้ใน Custom GPT ได้เลย

บอกผมได้ถ้าอยากให้ทำไฟล์ deploy (Dockerfile / render.yaml) ให้ครับ
