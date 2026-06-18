"""
Local AI chat for your Zoho Mail — powered by OpenRouter.

Talk to your mailbox in plain language, right in the terminal. The AI decides
which tools to call (check inbox, storage, search, backup, ...).

    pip install -r requirements.txt
    # add OPENROUTER_API_KEY to .env   (get one at https://openrouter.ai/keys)
    python chat.py

Pick any model with OPENROUTER_MODEL in .env. Some support free usage.
"""

import os
import sys
import json
from pathlib import Path

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

from openai_dispatcher import dispatch

OPENROUTER_URL = "https://openrouter.ai/api/v1"
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
TOOLS = json.load(open(Path(__file__).parent / "openai_tools.json", encoding="utf-8"))

SYSTEM = (
    "You are a helpful Zoho Mail assistant. Use the available tools to check the "
    "user's inbox and sent mail, read and search emails, check mailbox storage, "
    "list folders, and run backups. When showing emails, present sender, subject "
    "and date compactly. Always reply in the SAME language the user writes "
    "(Thai or English). Before running a backup, confirm the folder and count."
)

QUIT = {"exit", "quit", "bye", "ออก", "จบ", "เลิก", "q"}


def _to_dict(msg) -> dict:
    """Convert an OpenAI/OpenRouter assistant message into a plain dict."""
    out = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        out["tool_calls"] = [{
            "id": tc.id,
            "type": "function",
            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
        } for tc in msg.tool_calls]
    return out


def main() -> int:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print("✗ Missing OPENROUTER_API_KEY.")
        print("→ Get a key at https://openrouter.ai/keys and add to .env:")
        print("    OPENROUTER_API_KEY=sk-or-...")
        print("    OPENROUTER_MODEL=openai/gpt-4o-mini   (optional)")
        return 1

    try:
        from openai import OpenAI
    except ImportError:
        print("✗ The 'openai' package is required. Run: pip install -r requirements.txt")
        return 1

    client = OpenAI(base_url=OPENROUTER_URL, api_key=key)

    print("📬 Zoho Mail AI Chat  |  model:", MODEL)
    print("พิมพ์คำถามได้เลย เช่น 'มีเมลใหม่ไหม', 'พื้นที่ใกล้เต็มหรือยัง'")
    print("(พิมพ์ 'exit' หรือ 'ออก' เพื่อจบ)\n")

    messages = [{"role": "system", "content": SYSTEM}]

    while True:
        try:
            user = input("คุณ > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nบ๊ายบาย 👋")
            return 0
        if not user:
            continue
        if user.lower() in QUIT:
            print("บ๊ายบาย 👋")
            return 0

        messages.append({"role": "user", "content": user})

        # let the model call tools until it produces a final answer
        for _ in range(8):
            try:
                resp = client.chat.completions.create(
                    model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto",
                )
            except Exception as e:
                print(f"✗ AI error: {e}\n")
                break

            msg = resp.choices[0].message
            messages.append(_to_dict(msg))

            if not msg.tool_calls:
                print(f"\nAI  > {msg.content}\n")
                break

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                print(f"  · เรียก {tc.function.name}({args})")
                result = dispatch(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            print("AI  > (หยุดเพราะเรียกเครื่องมือหลายรอบเกินไป)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
