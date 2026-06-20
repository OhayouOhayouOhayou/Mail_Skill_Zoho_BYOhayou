"""
Zoho Mail Skill — desktop app (Windows).

A windowed UI with a sidebar: Dashboard, Realtime monitor, Backup, and Settings
(connection / Client ID, realtime, storage). Run:

    python app.py        (or double-click app.bat)
"""

import os
import sys
import threading
import webbrowser
import subprocess
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass

import zoho_client as zc

try:
    import notifier  # for show_toast()
except Exception:
    notifier = None

ENV_PATH = Path(__file__).with_name(".env")
REGIONS = [("com", "US / Global"), ("eu", "Europe"), ("in", "India"),
           ("com.au", "Australia"), ("jp", "Japan")]

# palette
SIDE = "#1f2430"
SIDE_HOVER = "#2c3344"
ACCENT = "#1a73e8"
BG = "#f4f6f9"
CARD = "#ffffff"
TXT = "#202124"
MUTED = "#5f6368"


# ── env helpers ──────────────────────────────────────────────────────────────

def read_env() -> dict:
    d = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                d[k.strip()] = v
    return d


def write_env(updates: dict) -> None:
    d = read_env()
    d.update({k: v for k, v in updates.items()})
    lines = ["# Zoho Mail Skill — saved by app.py"]
    lines += [f"{k}={v}" for k, v in d.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in updates.items():
        os.environ[k] = str(v)
    _reload_client()


def _reload_client() -> None:
    zc.REGION = os.getenv("ZOHO_REGION", "com")
    zc.BASE_URL = f"https://mail.zoho.{zc.REGION}/api"
    zc.ACCOUNTS_URL = f"https://accounts.zoho.{zc.REGION}/oauth/v2/token"
    zc._account_id_cache = None
    zc._folder_cache.clear()
    zc._token_cache.update(access_token=None, expires_at=0)


# ── realtime monitor ─────────────────────────────────────────────────────────

class Monitor:
    def __init__(self, log, interval=30):
        self.log = log
        self.interval = interval
        self._stop = threading.Event()
        self._seen_in, self._seen_out = set(), set()
        self.thread = None

    def start(self):
        self._stop.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        try:
            for m in zc.list_messages("Inbox", limit=50):
                self._seen_in.add(str(m.get("messageId")))
            for m in zc.list_sent(limit=50):
                self._seen_out.add(str(m.get("messageId")))
            self.log(f"เริ่มเฝ้าดู • ทุก {self.interval} วินาที")
        except Exception as e:
            self.log(f"ผิดพลาดตอนเริ่ม: {e}")
        while not self._stop.is_set():
            try:
                self._check()
            except Exception as e:
                self.log(f"ผิดพลาด: {e}")
            self._stop.wait(self.interval)
        self.log("หยุดเฝ้าดูแล้ว")

    def _check(self):
        for m in zc.list_messages("Inbox", limit=50):
            mid = str(m.get("messageId"))
            if mid not in self._seen_in:
                self._seen_in.add(mid)
                self._alert("📥 เมลเข้า", m.get("fromAddress"), m.get("subject"))
        for m in zc.list_sent(limit=50):
            mid = str(m.get("messageId"))
            if mid not in self._seen_out:
                self._seen_out.add(mid)
                self._alert("📤 เมลออก", m.get("toAddress"), m.get("subject"))

    def _alert(self, kind, who, subj):
        self.log(f"{kind} | {who} | {subj}")
        if notifier:
            try:
                notifier.show_toast(f"{kind} {who}", subj or "(ไม่มีหัวข้อ)")
            except Exception:
                pass


# ── main app ─────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zoho Mail Skill")
        self.geometry("860x580")
        self.minsize(780, 520)
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=6)
        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                        padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#1666d0")])
        style.configure("Card.TFrame", background=CARD)
        style.configure("TProgressbar", thickness=14)

        self.monitor = None

        # layout: sidebar + content
        self.sidebar = tk.Frame(self, bg=SIDE, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        tk.Label(self.sidebar, text="📬  Zoho Mail", bg=SIDE, fg="white",
                 font=("Segoe UI", 14, "bold")).pack(pady=(20, 24), padx=16, anchor="w")

        self.nav_buttons = {}
        for key, label in [("dash", "🏠  หน้าหลัก"), ("realtime", "🔔  เฝ้าดูเมล"),
                           ("backup", "🗄️  สำรองข้อมูล"), ("settings", "⚙️  ตั้งค่า")]:
            b = tk.Label(self.sidebar, text=label, bg=SIDE, fg="#c8cdd8",
                         font=("Segoe UI", 11), anchor="w", padx=18, pady=10, cursor="hand2")
            b.pack(fill="x")
            b.bind("<Button-1>", lambda e, k=key: self.show(k))
            b.bind("<Enter>", lambda e, w=b: w.config(bg=SIDE_HOVER))
            b.bind("<Leave>", lambda e, w=b: w.config(
                bg=ACCENT if self._active == w else SIDE))
            self.nav_buttons[key] = b

        self.status = tk.Label(self, text="", bg="#e8eaed", fg=MUTED, anchor="w",
                               padx=12, font=("Segoe UI", 9))
        self.status.pack(side="bottom", fill="x")

        self._active = None
        self.pages = {}
        self.show("dash")

    def set_status(self, text):
        self.status.config(text=text)

    def show(self, key):
        for w in self.content.winfo_children():
            w.destroy()
        for k, b in self.nav_buttons.items():
            b.config(bg=ACCENT if k == key else SIDE, fg="white" if k == key else "#c8cdd8")
        self._active = self.nav_buttons[key]
        {"dash": self.page_dash, "realtime": self.page_realtime,
         "backup": self.page_backup, "settings": self.page_settings}[key]()

    # ── helpers ───────────────────────────────────────────────────────────
    def _header(self, title, sub=""):
        tk.Label(self.content, text=title, bg=BG, fg=TXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=28, pady=(24, 2))
        if sub:
            tk.Label(self.content, text=sub, bg=BG, fg=MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(0, 12))

    def _card(self):
        c = tk.Frame(self.content, bg=CARD, highlightbackground="#e0e0e0",
                     highlightthickness=1)
        c.pack(fill="x", padx=28, pady=8)
        return c

    def _configured(self) -> bool:
        e = read_env()
        return all(e.get(k) for k in ("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET",
                                      "ZOHO_REFRESH_TOKEN"))

    # ── Dashboard ─────────────────────────────────────────────────────────
    def page_dash(self):
        self._header("หน้าหลัก", "ภาพรวมบัญชีและพื้นที่")
        if not self._configured():
            card = self._card()
            tk.Label(card, text="⚠️ ยังไม่ได้ตั้งค่าการเชื่อมต่อ", bg=CARD, fg="#d93025",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
            tk.Label(card, text="ไปที่หน้า 'ตั้งค่า' เพื่อใส่ Client ID / Secret ก่อน",
                     bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=(0, 14))
            ttk.Button(card, text="ไปหน้าตั้งค่า", style="Accent.TButton",
                       command=lambda: self.show("settings")).pack(anchor="w", padx=18, pady=(0, 16))
            return

        card = self._card()
        self.dash_email = tk.Label(card, text="กำลังโหลด...", bg=CARD, fg=TXT,
                                   font=("Segoe UI", 12, "bold"))
        self.dash_email.pack(anchor="w", padx=18, pady=(16, 6))
        self.dash_bar = ttk.Progressbar(card, length=520, maximum=100)
        self.dash_bar.pack(anchor="w", padx=18, pady=4)
        self.dash_store = tk.Label(card, text="", bg=CARD, fg=MUTED)
        self.dash_store.pack(anchor="w", padx=18, pady=(4, 16))

        row = tk.Frame(self.content, bg=BG)
        row.pack(anchor="w", padx=28, pady=8)
        ttk.Button(row, text="🔄 รีเฟรช", command=self._load_dash).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="🌐 เปิด Zoho Mail",
                   command=lambda: webbrowser.open(
                       f"https://mail.zoho.{os.getenv('ZOHO_REGION','com')}/")).pack(side="left")
        self._load_dash()

    def _load_dash(self):
        self.set_status("กำลังโหลดข้อมูล...")

        def work():
            try:
                info = zc.get_storage_info()
                email = zc.from_address()
                self.after(0, lambda: self._fill_dash(email, info))
            except Exception as e:
                self.after(0, lambda: self.set_status(f"ผิดพลาด: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _fill_dash(self, email, info):
        self.dash_email.config(text=f"📧  {email}")
        self.dash_bar["value"] = info["used_pct"]
        warn = "  ⚠️ ใกล้เต็ม!" if info["is_warning"] else ""
        self.dash_store.config(
            text=f"พื้นที่: {info['used_pct']}%  ({info['used_mb']} / {info['total_mb']} MB){warn}")
        self.set_status("พร้อมใช้งาน")

    # ── Realtime ──────────────────────────────────────────────────────────
    def page_realtime(self):
        self._header("เฝ้าดูเมล (Realtime)", "แจ้งเตือนเมื่อมีเมลเข้า-ออก")
        card = self._card()
        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=18, pady=14)
        self.rt_btn = ttk.Button(top, text="▶ เริ่มเฝ้าดู", style="Accent.TButton",
                                 command=self._toggle_monitor)
        self.rt_btn.pack(side="left")
        interval = read_env().get("NOTIFY_POLL_SECONDS", "30")
        tk.Label(top, text=f"ตรวจทุก {interval} วินาที (เปลี่ยนได้ในหน้าตั้งค่า)",
                 bg=CARD, fg=MUTED).pack(side="left", padx=14)

        self.rt_log = tk.Text(self.content, height=14, bg="#0f1320", fg="#cdd6f4",
                              font=("Consolas", 9), relief="flat", padx=10, pady=8)
        self.rt_log.pack(fill="both", expand=True, padx=28, pady=(8, 20))
        self.rt_log.insert("end", "พร้อมเฝ้าดู กดปุ่ม 'เริ่มเฝ้าดู'\n")
        self.rt_log.config(state="disabled")

    def _rt_log(self, text):
        def upd():
            self.rt_log.config(state="normal")
            self.rt_log.insert("end", f"[{datetime.now():%H:%M:%S}] {text}\n")
            self.rt_log.see("end")
            self.rt_log.config(state="disabled")
        self.after(0, upd)

    def _toggle_monitor(self):
        if self.monitor and self.monitor.thread and self.monitor.thread.is_alive():
            self.monitor.stop()
            self.monitor = None
            self.rt_btn.config(text="▶ เริ่มเฝ้าดู")
            self.set_status("หยุดเฝ้าดู")
        else:
            if not self._configured():
                messagebox.showwarning("ยังไม่ได้ตั้งค่า", "กรุณาตั้งค่าการเชื่อมต่อก่อน")
                return
            interval = int(read_env().get("NOTIFY_POLL_SECONDS", "30"))
            self.monitor = Monitor(self._rt_log, interval)
            self.monitor.start()
            self.rt_btn.config(text="⏹ หยุดเฝ้าดู")
            self.set_status("กำลังเฝ้าดูเมล...")

    # ── Backup ────────────────────────────────────────────────────────────
    def page_backup(self):
        self._header("สำรองข้อมูล", "ดาวน์โหลดเมล + ไฟล์แนบ มาเก็บในเครื่อง")
        card = self._card()
        grid = tk.Frame(card, bg=CARD)
        grid.pack(fill="x", padx=18, pady=14)

        tk.Label(grid, text="โฟลเดอร์", bg=CARD, fg=TXT).grid(row=0, column=0, sticky="w", pady=4)
        self.bk_folder = tk.StringVar(value="Inbox")
        ttk.Entry(grid, textvariable=self.bk_folder, width=20).grid(row=0, column=1, sticky="w", padx=8)

        tk.Label(grid, text="จำนวน", bg=CARD, fg=TXT).grid(row=1, column=0, sticky="w", pady=4)
        self.bk_count = tk.StringVar(value="100")
        ttk.Spinbox(grid, from_=1, to=5000, textvariable=self.bk_count, width=10).grid(
            row=1, column=1, sticky="w", padx=8)

        tk.Label(grid, text="รูปแบบ", bg=CARD, fg=TXT).grid(row=2, column=0, sticky="nw", pady=4)
        self.bk_fmt = tk.StringVar(value="both")
        fmts = tk.Frame(grid, bg=CARD)
        fmts.grid(row=2, column=1, sticky="w", padx=8)
        ttk.Radiobutton(fmts, text="HTML + ไฟล์แนบ (อ่านง่าย)", variable=self.bk_fmt,
                        value="html").pack(anchor="w")
        ttk.Radiobutton(fmts, text=".eml (เปิดบน Zoho/Outlook ได้)", variable=self.bk_fmt,
                        value="eml").pack(anchor="w")
        ttk.Radiobutton(fmts, text="ทั้งสองแบบ", variable=self.bk_fmt,
                        value="both").pack(anchor="w")

        self.bk_btn = ttk.Button(card, text="⬇ เริ่มสำรองข้อมูล", style="Accent.TButton",
                                 command=self._run_backup)
        self.bk_btn.pack(anchor="w", padx=18, pady=(4, 6))
        self.bk_bar = ttk.Progressbar(card, length=520, maximum=100)
        self.bk_bar.pack(anchor="w", padx=18, pady=4)
        self.bk_status = tk.Label(card, text="", bg=CARD, fg=MUTED)
        self.bk_status.pack(anchor="w", padx=18, pady=(2, 16))

        ttk.Button(self.content, text="📂 เปิดโฟลเดอร์ backup",
                   command=self._open_backup_dir).pack(anchor="w", padx=28, pady=4)

    def _run_backup(self):
        if not self._configured():
            messagebox.showwarning("ยังไม่ได้ตั้งค่า", "กรุณาตั้งค่าการเชื่อมต่อก่อน")
            return
        folder = self.bk_folder.get().strip() or "Inbox"
        try:
            count = int(self.bk_count.get())
        except ValueError:
            count = 100
        fmt = self.bk_fmt.get()
        self.bk_btn.config(state="disabled")
        self.bk_bar["value"] = 0

        def prog(done, total):
            self.after(0, lambda: self.bk_bar.config(value=done / total * 100))

        def work():
            try:
                r = zc.backup_folder(folder, count, progress=prog, fmt=fmt)
                msg = (f"✓ สำเร็จ {r['saved']} ฉบับ • ไฟล์แนบ {r['attachments_saved']}")
                if r.get("eml_dir"):
                    msg += f"\n.eml: {r['eml_dir']}"
                if r.get("backup_file"):
                    msg += f"\nHTML data: {r['backup_file']}"
                self.after(0, lambda: self.bk_status.config(text=msg, fg="#188038"))
            except Exception as e:
                self.after(0, lambda: self.bk_status.config(text=f"✗ {e}", fg="#d93025"))
            finally:
                self.after(0, lambda: self.bk_btn.config(state="normal"))
        threading.Thread(target=work, daemon=True).start()

    def _open_backup_dir(self):
        d = Path(os.getenv("BACKUP_DIR", "./backups")).resolve()
        d.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(d)  # type: ignore
        except Exception:
            webbrowser.open(d.as_uri())

    # ── Settings ──────────────────────────────────────────────────────────
    def page_settings(self):
        self._header("ตั้งค่า", "ข้อมูลเชื่อมต่อ + การแจ้งเตือน + พื้นที่")
        e = read_env()
        wrap = tk.Frame(self.content, bg=BG)
        wrap.pack(fill="both", expand=True, padx=28, pady=4)

        self.cfg = {}

        def field(parent, label, key, default="", show=None):
            tk.Label(parent, text=label, bg=CARD, fg=TXT,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(8, 0))
            var = tk.StringVar(value=e.get(key, default))
            ttk.Entry(parent, textvariable=var, width=58, show=show).pack(anchor="w", padx=14)
            self.cfg[key] = var

        # connection card
        c1 = tk.Frame(wrap, bg=CARD, highlightbackground="#e0e0e0", highlightthickness=1)
        c1.pack(fill="x", pady=6)
        tk.Label(c1, text="🔌 การเชื่อมต่อ Zoho", bg=CARD, fg=TXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(c1, text="ภูมิภาค", bg=CARD, fg=TXT, font=("Segoe UI", 9)).pack(anchor="w", padx=14)
        self.region_var = tk.StringVar(value=e.get("ZOHO_REGION", "com"))
        ttk.Combobox(c1, state="readonly", width=30, values=[r[0] for r in REGIONS],
                     textvariable=self.region_var).pack(anchor="w", padx=14, pady=(0, 4))
        field(c1, "Client ID", "ZOHO_CLIENT_ID")
        field(c1, "Client Secret", "ZOHO_CLIENT_SECRET", show="•")
        field(c1, "Refresh Token", "ZOHO_REFRESH_TOKEN", show="•")
        field(c1, "Account Email", "ZOHO_ACCOUNT_EMAIL")
        brow = tk.Frame(c1, bg=CARD)
        brow.pack(anchor="w", padx=14, pady=10)
        ttk.Button(brow, text="🧪 ทดสอบการเชื่อมต่อ",
                   command=self._test_conn).pack(side="left")
        ttk.Button(brow, text="✨ ตัวช่วยขอ Token (wizard)",
                   command=self._open_wizard).pack(side="left", padx=8)
        self.test_lbl = tk.Label(c1, text="", bg=CARD, fg=MUTED)
        self.test_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # realtime + storage card
        c2 = tk.Frame(wrap, bg=CARD, highlightbackground="#e0e0e0", highlightthickness=1)
        c2.pack(fill="x", pady=6)
        tk.Label(c2, text="🔔 แจ้งเตือน & พื้นที่", bg=CARD, fg=TXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        field(c2, "ตรวจเมลทุกกี่วินาที (Realtime)", "NOTIFY_POLL_SECONDS", "30")
        field(c2, "เตือนพื้นที่เมื่อถึง (%)", "STORAGE_WARN_PERCENT", "80")
        field(c2, "Webhook แจ้งเตือน (Slack/Telegram) — ใส่หรือเว้นว่าง", "NOTIFY_WEBHOOK")
        tk.Frame(c2, bg=CARD, height=8).pack()

        ttk.Button(self.content, text="💾 บันทึกการตั้งค่า", style="Accent.TButton",
                   command=self._save_settings).pack(anchor="w", padx=28, pady=10)

    def _save_settings(self):
        updates = {k: v.get().strip() for k, v in self.cfg.items()}
        updates["ZOHO_REGION"] = self.region_var.get().strip() or "com"
        write_env(updates)
        self.set_status("บันทึกการตั้งค่าแล้ว ✓")
        messagebox.showinfo("บันทึกแล้ว", "บันทึกการตั้งค่าเรียบร้อย")

    def _test_conn(self):
        # apply current fields first
        self._save_settings_silent()
        self.test_lbl.config(text="⏳ กำลังทดสอบ...", fg=MUTED)

        def work():
            try:
                email = zc.from_address()
                info = zc.get_storage_info()
                self.after(0, lambda: self.test_lbl.config(
                    text=f"✓ เชื่อมต่อสำเร็จ: {email} • พื้นที่ {info['used_pct']}%",
                    fg="#188038"))
            except Exception as e:
                self.after(0, lambda: self.test_lbl.config(text=f"✗ {e}", fg="#d93025"))
        threading.Thread(target=work, daemon=True).start()

    def _save_settings_silent(self):
        updates = {k: v.get().strip() for k, v in self.cfg.items()}
        updates["ZOHO_REGION"] = self.region_var.get().strip() or "com"
        write_env(updates)

    def _open_wizard(self):
        try:
            subprocess.Popen([sys.executable, str(Path(__file__).with_name("setup_gui.py"))])
        except Exception as e:
            messagebox.showerror("เปิดไม่ได้", str(e))


if __name__ == "__main__":
    App().mainloop()
