"""
Zoho Mail Skill - command line interface.

Usage:
    python cli.py doctor                  Check config & connection
    python cli.py inbox [N]               List N recent inbox emails (default 10)
    python cli.py sent [N]                List N recent sent emails
    python cli.py read <messageId>        Read full email content
    python cli.py search <query> [N]      Search emails
    python cli.py storage                 Show storage usage
    python cli.py folders                 List folders + unread counts
    python cli.py backup [folder] [N] [fmt]   Backup (fmt: html|eml|both)
    python cli.py viewbackup [file]       Open a .jsonl backup as readable HTML
    python cli.py send <to> <subject> <body>   Send email (+ signature)
    python cli.py watch [seconds]         Continuous monitor (default 60s)
"""

import sys

# make Unicode (checkmarks, emoji, Thai) safe on Windows cp1252 consoles
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import zoho_client as zc


def _print_messages(msgs: list[dict]) -> None:
    if not msgs:
        print("(no messages)")
        return
    for m in msgs:
        date = (m.get("sentDateInGMT") or "")[:16]
        frm = (m.get("fromAddress") or "")[:32]
        subj = m.get("subject") or "(no subject)"
        flag = "📎" if str(m.get("hasAttachment")) in ("1", "true", "True") else "  "
        print(f"{flag} {date:16} | {frm:32} | {subj}")
        print(f"   id: {m.get('messageId')}")


def cmd_doctor(args=None) -> int:
    print("Checking configuration...")
    try:
        accounts = zc.get_accounts()
        print(f"  ✓ Authentication OK ({len(accounts)} account(s) reachable)")
        acct = zc.account_id()
        print(f"  ✓ Account resolved: id={acct}")
        info = zc.get_storage_info()
        print(f"  ✓ Storage: {info['used_pct']}% used "
              f"({info['used_mb']} / {info['total_mb']} MB)")
        folders = zc.get_folders()
        if folders:
            print(f"  ✓ Folders: {', '.join(f.get('folderName','?') for f in folders[:8])}")
        else:
            print("  • Folders: not accessible (optional 'ZohoMail.folders.READ' scope "
                  "not granted — inbox still works across all folders)")
        print("\nAll good! 🎉")
        return 0
    except Exception as e:
        print(f"\n✗ {e}")
        return 1


def cmd_inbox(args):
    n = int(args[0]) if args else 10
    _print_messages(zc.list_messages("Inbox", limit=n))


def cmd_sent(args):
    n = int(args[0]) if args else 10
    _print_messages(zc.list_sent(limit=n))


def cmd_read(args):
    if not args:
        print("Usage: python cli.py read <messageId>"); return 1
    data = zc.get_message(args[0])
    content = data.get("content") or data.get("summary") or "(empty)"
    print(content)


def cmd_search(args):
    if not args:
        print("Usage: python cli.py search <query> [N]"); return 1
    n = int(args[1]) if len(args) > 1 else 20
    _print_messages(zc.search_messages(args[0], limit=n))


def cmd_storage(args):
    info = zc.get_storage_info()
    bar_len = 30
    filled = int(info["used_pct"] / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    status = "⚠️  WARNING — near full!" if info["is_warning"] else "✓ OK"
    print(f"[{bar}] {info['used_pct']}%")
    print(f"Used : {info['used_mb']} MB")
    print(f"Total: {info['total_mb']} MB")
    print(f"Warn at {info['warn_threshold']}%  →  {status}")


def cmd_folders(args):
    folders = zc.get_folders()
    if not folders:
        print("No folder list available.")
        print("→ This needs the 'ZohoMail.folders.READ' scope. Re-run `python setup.py`")
        print("  with scope: ZohoMail.messages.ALL,ZohoMail.accounts.READ,ZohoMail.folders.READ")
        print("  (Inbox / storage / backup work fine without it.)")
        return
    for f in folders:
        print(f"  {str(f.get('folderName')):20} id={str(f.get('folderId')):20} "
              f"unread={f.get('unreadCount', 0)}")


def cmd_backup(args):
    folder = args[0] if args else "Inbox"
    n = int(args[1]) if len(args) > 1 else 500
    fmt = args[2] if len(args) > 2 else "html"   # html | eml | both
    print(f"Backing up '{folder}' (up to {n} messages, format={fmt})...")

    def progress(done, total):
        print(f"\r  {done}/{total}", end="", flush=True)

    result = zc.backup_folder(folder, n, progress=progress, fmt=fmt)
    print(f"\n✓ Saved {result['saved']} messages "
          f"({result['failed']} failed, {result['attachments_saved']} attachments)")
    if result.get("backup_file"):
        print(f"  HTML data → {result['backup_file']}")
    if result.get("eml_dir"):
        print(f"  .eml      → {result['eml_dir']}")


def cmd_viewbackup(args):
    import view_backup
    sys.argv = ["view_backup"] + list(args)
    return view_backup.main()


def cmd_send(args):
    if len(args) < 3:
        print('Usage: python cli.py send <to> <subject> "<body>"')
        return 1
    to, subject = args[0], args[1]
    body = " ".join(args[2:])
    sig = zc.load_signature()
    print(f"From   : {zc.from_address()}")
    print(f"To     : {to}")
    print(f"Subject: {subject}")
    print(f"Body   : {body[:80]}{'...' if len(body) > 80 else ''}")
    print(f"Signature: {'yes' if sig else 'none (no signature.html / SIGNATURE)'}")
    if input("\nSend this email? (y/n) > ").strip().lower() != "y":
        print("Cancelled.")
        return 0
    result = zc.send_email(to, subject, body)
    print(f"✓ Sent to {to}" if result.get("success") else f"✗ {result}")


def cmd_watch(args):
    import monitor
    if args:
        monitor.POLL_SECONDS = int(args[0])
    monitor.run()


COMMANDS = {
    "doctor": cmd_doctor,
    "inbox": cmd_inbox,
    "sent": cmd_sent,
    "read": cmd_read,
    "search": cmd_search,
    "storage": cmd_storage,
    "folders": cmd_folders,
    "backup": cmd_backup,
    "viewbackup": cmd_viewbackup,
    "send": cmd_send,
    "watch": cmd_watch,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    args = sys.argv[2:]
    fn = COMMANDS.get(cmd)
    if not fn:
        print(f"Unknown command: {cmd}\n")
        print(__doc__)
        return 1
    try:
        return fn(args) or 0
    except zc.ZohoError as e:
        print(f"\n✗ {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
