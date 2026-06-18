"""
Interactive setup wizard for Zoho Mail Skill.

Walks you through OAuth2 and writes a ready-to-use .env file.
No manual curl required.

    python setup.py
"""

import sys
from pathlib import Path

import httpx

REGIONS = {
    "1": ("com", "US / Global  (mail.zoho.com)"),
    "2": ("eu", "Europe       (mail.zoho.eu)"),
    "3": ("in", "India        (mail.zoho.in)"),
    "4": ("com.au", "Australia (mail.zoho.com.au)"),
    "5": ("jp", "Japan        (mail.zoho.jp)"),
}

ENV_PATH = Path(__file__).parent / ".env"


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def banner(text: str) -> None:
    print("\n" + "=" * 58)
    print(f"  {text}")
    print("=" * 58)


def choose_region() -> str:
    banner("STEP 1/4 — Choose your Zoho data center")
    print("Where do you log in to Zoho Mail?\n")
    for k, (_, label) in REGIONS.items():
        print(f"  {k}. {label}")
    while True:
        choice = ask("\nSelect (1-5)", "1")
        if choice in REGIONS:
            region = REGIONS[choice][0]
            print(f"→ Region: {region}")
            return region
        print("Invalid choice, try again.")


def get_credentials() -> tuple[str, str]:
    banner("STEP 2/4 — Create a Self Client")
    print(
        "1. Open https://api-console.zoho.com/ in your browser\n"
        "2. Click ADD CLIENT  →  choose 'Self Client'  →  CREATE\n"
        "3. Copy the Client ID and Client Secret below.\n"
    )
    client_id = ask("Client ID")
    client_secret = ask("Client Secret")
    if not client_id or not client_secret:
        print("\nClient ID and Secret are required. Aborting.")
        sys.exit(1)
    return client_id, client_secret


def get_auth_code() -> str:
    banner("STEP 3/4 — Generate an Authorization Code")
    print(
        "In the Self Client page:\n"
        "1. Click the 'Generate Code' tab\n"
        "2. Scope:  ZohoMail.messages.ALL,ZohoMail.accounts.READ\n"
        "3. Duration: 10 minutes  →  any description  →  CREATE\n"
        "4. Copy the generated code and paste it here.\n"
    )
    code = ask("Authorization Code")
    if not code:
        print("\nAuthorization Code is required. Aborting.")
        sys.exit(1)
    return code


def exchange_for_refresh_token(region: str, cid: str, secret: str, code: str) -> str:
    url = f"https://accounts.zoho.{region}/oauth/v2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": cid,
        "client_secret": secret,
        "code": code,
    }
    print("\n→ Exchanging code for refresh token...")
    resp = httpx.post(url, data=data, timeout=20)
    body = resp.json() if resp.content else {}

    # some setups require a redirect_uri; retry once with the common placeholder
    if "refresh_token" not in body and "redirect" in str(body).lower():
        data["redirect_uri"] = "https://www.zoho.com/books/api/v3"
        resp = httpx.post(url, data=data, timeout=20)
        body = resp.json() if resp.content else {}

    if "refresh_token" not in body:
        print(f"\n✗ Failed: {body}")
        print(
            "\nCommon causes:\n"
            "  • The code expired (valid only ~10 min) — generate a new one\n"
            "  • Wrong region — make sure it matches where you generated the code\n"
            "  • Client ID/Secret mismatch"
        )
        sys.exit(1)
    print("✓ Refresh token obtained.")
    return body["refresh_token"]


def detect_email(region: str, refresh_token: str, cid: str, secret: str) -> str:
    """Fetch the access token and list accounts to auto-detect the email."""
    token_url = f"https://accounts.zoho.{region}/oauth/v2/token"
    tok = httpx.post(token_url, data={
        "grant_type": "refresh_token",
        "client_id": cid, "client_secret": secret,
        "refresh_token": refresh_token,
    }, timeout=20).json()
    access = tok.get("access_token")
    if not access:
        return ask("Account email")

    accounts = httpx.get(
        f"https://mail.zoho.{region}/api/accounts",
        headers={"Authorization": f"Zoho-oauthtoken {access}"},
        timeout=20,
    ).json().get("data", [])

    emails = [a.get("emailAddress") for a in accounts if a.get("emailAddress")]
    if not emails:
        return ask("Account email")
    if len(emails) == 1:
        print(f"→ Detected account: {emails[0]}")
        return emails[0]

    print("\nMultiple accounts found:")
    for i, e in enumerate(emails, 1):
        print(f"  {i}. {e}")
    while True:
        idx = ask("Choose account", "1")
        if idx.isdigit() and 1 <= int(idx) <= len(emails):
            return emails[int(idx) - 1]


def write_env(values: dict) -> None:
    banner("STEP 4/4 — Writing .env")
    if ENV_PATH.exists():
        if ask(".env already exists. Overwrite? (y/n)", "n").lower() != "y":
            print("Keeping existing .env. Here are your values to add manually:\n")
            for k, v in values.items():
                print(f"{k}={v}")
            return
    lines = [
        "# Generated by setup.py",
        f"ZOHO_CLIENT_ID={values['ZOHO_CLIENT_ID']}",
        f"ZOHO_CLIENT_SECRET={values['ZOHO_CLIENT_SECRET']}",
        f"ZOHO_REFRESH_TOKEN={values['ZOHO_REFRESH_TOKEN']}",
        f"ZOHO_REGION={values['ZOHO_REGION']}",
        f"ZOHO_ACCOUNT_EMAIL={values['ZOHO_ACCOUNT_EMAIL']}",
        "STORAGE_WARN_PERCENT=80",
        "BACKUP_DIR=./backups",
        "POLL_SECONDS=60",
        "",
    ]
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Saved to {ENV_PATH}")


def main() -> None:
    print("\n📬  Zoho Mail Skill — Setup Wizard")
    region = choose_region()
    cid, secret = get_credentials()
    code = get_auth_code()
    refresh = exchange_for_refresh_token(region, cid, secret, code)
    email = detect_email(region, refresh, cid, secret)

    write_env({
        "ZOHO_CLIENT_ID": cid,
        "ZOHO_CLIENT_SECRET": secret,
        "ZOHO_REFRESH_TOKEN": refresh,
        "ZOHO_REGION": region,
        "ZOHO_ACCOUNT_EMAIL": email,
    })

    banner("Done! 🎉")
    print(
        "Verify with:\n"
        "  python cli.py doctor\n\n"
        "Then try:\n"
        "  python cli.py inbox\n"
        "  python cli.py storage\n"
        "  python cli.py backup Inbox 200\n"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
