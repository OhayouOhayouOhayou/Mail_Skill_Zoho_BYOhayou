"""
Turn a .jsonl backup into a readable HTML page you can open in any browser.

    python view_backup.py                       # newest file in backups/
    python view_backup.py backups/backup_x.jsonl

Creates an .html next to the .jsonl and opens it in your browser.
"""

import os
import sys
import json
import glob
import html
import webbrowser
from pathlib import Path
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _fmt_date(v) -> str:
    try:
        # Zoho sentDateInGMT is epoch milliseconds
        ts = int(v) / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(v or "")


def build(jsonl_path: Path) -> Path:
    emails = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    emails.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    rows = []
    for i, m in enumerate(emails):
        subj = html.escape(m.get("subject") or "(ไม่มีหัวข้อ)")
        frm = html.escape(m.get("fromAddress") or "")
        to = html.escape(m.get("toAddress") or "")
        date = html.escape(_fmt_date(m.get("sentDateInGMT")))
        clip = "📎" if str(m.get("hasAttachment")) in ("1", "true", "True") else ""
        body = m.get("content") or "(ไม่มีเนื้อหา)"
        # sandbox the email HTML inside an iframe so its styles don't leak
        srcdoc = html.escape(body, quote=True)

        att_html = ""
        atts = m.get("attachments") or []
        if atts:
            links = []
            for a in atts:
                nm = html.escape(a.get("name") or "ไฟล์แนบ")
                if a.get("file"):
                    rel = os.path.relpath(a["file"], jsonl_path.parent).replace("\\", "/")
                    kb = round((a.get("size") or 0) / 1024, 1)
                    links.append(f'<a href="{html.escape(rel)}" download>📎 {nm} ({kb} KB)</a>')
                else:
                    links.append(f'<span style="color:#d93025">📎 {nm} (โหลดไม่สำเร็จ)</span>')
            att_html = '<div class="att">ไฟล์แนบ: ' + " &nbsp; ".join(links) + "</div>"

        rows.append(f"""
        <details>
          <summary><span class="subj">{clip} {subj}</span>
            <span class="meta">{frm} · {date}</span></summary>
          <div class="hdr"><b>From:</b> {frm}<br><b>To:</b> {to}<br><b>Date:</b> {date}</div>
          {att_html}
          <iframe sandbox srcdoc="{srcdoc}" loading="lazy"></iframe>
        </details>""")

    page = f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<title>Email Backup — {html.escape(jsonl_path.name)}</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 900px;
         margin: 0 auto; padding: 20px; background: #f5f5f5; color: #202124; }}
  h1 {{ font-size: 18px; }}
  .count {{ color: #5f6368; font-size: 13px; margin-bottom: 16px; }}
  details {{ background: #fff; border-radius: 8px; margin-bottom: 8px; padding: 10px 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,.08); }}
  summary {{ cursor: pointer; display: flex; justify-content: space-between; gap: 12px; }}
  .subj {{ font-weight: 600; }}
  .meta {{ color: #5f6368; font-size: 12px; white-space: nowrap; }}
  .hdr {{ font-size: 12px; color: #5f6368; margin: 10px 0; border-top: 1px solid #eee; padding-top: 8px; }}
  .att {{ font-size: 13px; margin: 6px 0 10px; }}
  .att a {{ color: #1a73e8; text-decoration: none; margin-right: 6px; }}
  iframe {{ width: 100%; height: 480px; border: 1px solid #e0e0e0; border-radius: 6px; background: #fff; }}
</style></head><body>
  <h1>📬 Email Backup</h1>
  <div class="count">ไฟล์: {html.escape(jsonl_path.name)} · {len(emails)} ฉบับ · คลิกหัวข้อเพื่อเปิดอ่าน</div>
  {''.join(rows)}
</body></html>"""

    out = jsonl_path.with_suffix(".html")
    out.write_text(page, encoding="utf-8")
    return out


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        files = sorted(glob.glob("backups/*.jsonl"))
        if not files:
            print("ไม่พบไฟล์ backup ใน backups/ — รัน `python cli.py backup` ก่อน")
            return 1
        path = Path(files[-1])

    if not path.exists():
        print(f"ไม่พบไฟล์: {path}")
        return 1

    out = build(path)
    print(f"✓ สร้างไฟล์อ่านง่ายแล้ว: {out}")
    try:
        webbrowser.open(out.resolve().as_uri())
        print("  เปิดในเบราว์เซอร์ให้แล้ว")
    except Exception:
        print("  เปิดไฟล์นี้ในเบราว์เซอร์ได้เลย")
    return 0


if __name__ == "__main__":
    sys.exit(main())
