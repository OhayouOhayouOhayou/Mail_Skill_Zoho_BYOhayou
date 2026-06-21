"""
Zoho Mail Skill — graphical setup wizard.

A click-through installer-style window (like installing an app): choose region,
enter your Client ID/Secret, paste an authorization code, and it connects,
detects your email, and writes .env for you.

    python setup_gui.py

Build it into a double-clickable ZohoMailSetup.exe with build_installer.bat.
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

import httpx

try:
    import branding
except Exception:
    branding = None

ENV_PATH = Path(__file__).with_name(".env")
SCOPE = "ZohoMail.messages.ALL,ZohoMail.accounts.READ,ZohoMail.folders.READ"

REGIONS = [
    ("com", "US / Global  (mail.zoho.com)"),
    ("eu", "Europe  (mail.zoho.eu)"),
    ("in", "India  (mail.zoho.in)"),
    ("com.au", "Australia  (mail.zoho.com.au)"),
    ("jp", "Japan  (mail.zoho.jp)"),
]

ACCENT = "#1a73e8"


class Wizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASEFA Mail — ตัวช่วยติดตั้ง")
        self.geometry("560x440")
        self.resizable(False, False)
        self.configure(bg="white")
        if branding:
            branding.set_window_icon(self)

        # collected values
        self.region = tk.StringVar(value="com")
        self.client_id = tk.StringVar()
        self.client_secret = tk.StringVar()
        self.auth_code = tk.StringVar()
        self.refresh_token = None
        self.email = None
        self.storage_txt = ""

        self.step = 0
        self.steps = [self._step_welcome, self._step_creds, self._step_code, self._step_finish]

        # header
        header = tk.Frame(self, bg=ACCENT, height=64)
        header.pack(fill="x")
        tk.Label(header, text="📬  ตั้งค่า Zoho Mail Skill", bg=ACCENT, fg="white",
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=20, pady=14)
        self.step_lbl = tk.Label(header, text="", bg=ACCENT, fg="white", font=("Segoe UI", 10))
        self.step_lbl.pack(side="right", padx=20)

        # body
        self.body = tk.Frame(self, bg="white")
        self.body.pack(fill="both", expand=True, padx=24, pady=18)

        # footer
        footer = tk.Frame(self, bg="white")
        footer.pack(fill="x", padx=24, pady=(0, 16))
        self.back_btn = ttk.Button(footer, text="◀ ย้อนกลับ", command=self.go_back)
        self.back_btn.pack(side="left")
        self.next_btn = ttk.Button(footer, text="ถัดไป ▶", command=self.go_next)
        self.next_btn.pack(side="right")

        self.show()

    # ── navigation ────────────────────────────────────────────────────────
    def show(self):
        for w in self.body.winfo_children():
            w.destroy()
        self.step_lbl.config(text=f"ขั้นที่ {self.step + 1}/{len(self.steps)}")
        self.back_btn.config(state="normal" if self.step > 0 else "disabled")
        self.steps[self.step]()

    def go_back(self):
        if self.step > 0:
            self.step -= 1
            self.show()

    def go_next(self):
        if not self._validate():
            return
        if self.step < len(self.steps) - 1:
            self.step += 1
            self.show()

    def _validate(self) -> bool:
        if self.step == 1:
            if not self.client_id.get().strip() or not self.client_secret.get().strip():
                messagebox.showwarning("ยังไม่ครบ", "กรุณากรอก Client ID และ Client Secret")
                return False
        if self.step == 2:
            if not self.auth_code.get().strip():
                messagebox.showwarning("ยังไม่ครบ", "กรุณาวาง Authorization Code")
                return False
        return True

    # ── helpers ───────────────────────────────────────────────────────────
    def _title(self, text, sub=""):
        tk.Label(self.body, text=text, bg="white", fg="#202124",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        if sub:
            tk.Label(self.body, text=sub, bg="white", fg="#5f6368",
                     font=("Segoe UI", 9), justify="left", wraplength=500).pack(anchor="w", pady=(2, 12))

    def _entry(self, label, var, show=None):
        tk.Label(self.body, text=label, bg="white", fg="#202124",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 2))
        ttk.Entry(self.body, textvariable=var, width=56, show=show).pack(anchor="w")

    # ── steps ─────────────────────────────────────────────────────────────
    def _step_welcome(self):
        self._title("ยินดีต้อนรับ 👋",
                    "ตัวช่วยนี้จะตั้งค่าเชื่อมต่อ Zoho Mail ให้คุณใน 3 ขั้นตอน\n"
                    "เริ่มจากเลือกศูนย์ข้อมูลที่คุณใช้ล็อกอิน Zoho")
        tk.Label(self.body, text="ภูมิภาค / Data center", bg="white",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        combo = ttk.Combobox(self.body, width=40, state="readonly",
                             values=[r[1] for r in REGIONS])
        combo.current([r[0] for r in REGIONS].index(self.region.get()))
        combo.pack(anchor="w")
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.region.set(REGIONS[combo.current()][0]))
        ttk.Button(self.body, text="🌐 เปิดหน้า Zoho API Console",
                   command=lambda: webbrowser.open("https://api-console.zoho.com/")
                   ).pack(anchor="w", pady=18)
        self.next_btn.config(text="ถัดไป ▶")

    def _step_creds(self):
        self._title("ขั้นที่ 1 — Client ID & Secret",
                    "ที่ api-console.zoho.com → ADD CLIENT → เลือก 'Self Client' → CREATE\n"
                    "แล้วคัดลอกค่ามาวางด้านล่าง")
        self._entry("Client ID", self.client_id)
        self._entry("Client Secret", self.client_secret, show="•")
        self.next_btn.config(text="ถัดไป ▶")

    def _step_code(self):
        self._title("ขั้นที่ 2 — Authorization Code",
                    "ในหน้า Self Client → แท็บ 'Generate Code' → วาง scope ด้านล่าง → "
                    "ตั้งเวลา 10 นาที → CREATE แล้วคัดลอกโค้ดมาวาง")
        tk.Label(self.body, text="Scope (คัดลอกไปวางในช่อง scope):", bg="white",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 2))
        scope_box = tk.Entry(self.body, width=56)
        scope_box.insert(0, SCOPE)
        scope_box.config(state="readonly")
        scope_box.pack(anchor="w")
        self._entry("Authorization Code", self.auth_code)
        self.next_btn.config(text="เชื่อมต่อ ▶")

    def _step_finish(self):
        self._title("ขั้นที่ 3 — เชื่อมต่อ & บันทึก", "กำลังเชื่อมต่อกับ Zoho...")
        self.next_btn.config(state="disabled")
        self.back_btn.config(state="disabled")
        self.status = tk.Label(self.body, text="⏳ กำลังขอ token...", bg="white",
                               fg="#5f6368", font=("Segoe UI", 10), justify="left",
                               wraplength=500)
        self.status.pack(anchor="w", pady=10)
        threading.Thread(target=self._do_connect, daemon=True).start()

    # ── connection work (background thread) ───────────────────────────────
    def _do_connect(self):
        region = self.region.get()
        try:
            token = self._exchange(region)
            self.refresh_token = token
            self._set_status("✅ ได้ refresh token แล้ว\n⏳ กำลังตรวจหาบัญชี...")
            self.email, self.storage_txt = self._detect(region, token)
            self._write_env()
            self._set_status(
                f"🎉 เชื่อมต่อสำเร็จ!\n\n"
                f"อีเมล: {self.email}\n"
                f"พื้นที่: {self.storage_txt}\n\n"
                f"บันทึกการตั้งค่าลง .env แล้ว\n"
                f"ปิดหน้าต่างนี้ แล้วเปิดใช้งานด้วย start.bat ได้เลย",
                done=True)
        except Exception as e:
            self._set_status(f"❌ ไม่สำเร็จ: {e}\n\nกด 'ย้อนกลับ' เพื่อแก้ไขแล้วลองใหม่",
                             error=True)

    def _exchange(self, region) -> str:
        url = f"https://accounts.zoho.{region}/oauth/v2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id.get().strip(),
            "client_secret": self.client_secret.get().strip(),
            "code": self.auth_code.get().strip(),
        }
        body = httpx.post(url, data=data, timeout=20).json()
        if "refresh_token" not in body and "redirect" in str(body).lower():
            data["redirect_uri"] = "https://www.zoho.com/books/api/v3"
            body = httpx.post(url, data=data, timeout=20).json()
        if "refresh_token" not in body:
            raise RuntimeError(body.get("error", str(body)))
        return body["refresh_token"]

    def _detect(self, region, refresh):
        tok = httpx.post(f"https://accounts.zoho.{region}/oauth/v2/token", data={
            "grant_type": "refresh_token",
            "client_id": self.client_id.get().strip(),
            "client_secret": self.client_secret.get().strip(),
            "refresh_token": refresh,
        }, timeout=20).json()
        access = tok.get("access_token")
        acct = httpx.get(f"https://mail.zoho.{region}/api/accounts",
                         headers={"Authorization": f"Zoho-oauthtoken {access}"},
                         timeout=20).json().get("data", [{}])[0]
        email = acct.get("primaryEmailAddress") or acct.get("mailboxAddress") or ""
        used = int(acct.get("usedStorage", 0) or 0)
        total = int(acct.get("allowedStorage", 0) or 0)
        pct = round(used / total * 100, 1) if total else 0
        storage = f"{pct}% ใช้ไป ({round(used/1024)} / {round(total/1024)} MB)"
        return email, storage

    def _write_env(self):
        existing = {}
        if ENV_PATH.exists():
            for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    existing[k.strip()] = v
        existing.update({
            "ZOHO_CLIENT_ID": self.client_id.get().strip(),
            "ZOHO_CLIENT_SECRET": self.client_secret.get().strip(),
            "ZOHO_REFRESH_TOKEN": self.refresh_token,
            "ZOHO_REGION": self.region.get(),
            "ZOHO_ACCOUNT_EMAIL": self.email,
        })
        existing.setdefault("STORAGE_WARN_PERCENT", "80")
        existing.setdefault("BACKUP_DIR", "./backups")
        existing.setdefault("POLL_SECONDS", "60")
        lines = ["# Generated by setup_gui.py"]
        lines += [f"{k}={v}" for k, v in existing.items()]
        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── thread-safe status update ─────────────────────────────────────────
    def _set_status(self, text, done=False, error=False):
        def upd():
            self.status.config(text=text, fg="#188038" if done else
                               ("#d93025" if error else "#5f6368"))
            if done:
                self.next_btn.config(text="เสร็จสิ้น ✓", state="normal", command=self.destroy)
            if error:
                self.back_btn.config(state="normal")
        self.after(0, upd)


if __name__ == "__main__":
    Wizard().mainloop()
