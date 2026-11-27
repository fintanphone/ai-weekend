#!/usr/bin/env python3
"""A fake mail system. Reads inbox/, and "sends" by writing to outbox/.

    python mailbox.py           # list the inbox
    python mailbox.py --sent    # list what has been sent so far

Nothing leaves your machine. But note that `send` still has a side effect: a
file appears, and running the agent twice sends twice. That is the entire
difference between this lab and Lab 3, where every tool was read-only.
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
INBOX = HERE / "inbox"
OUTBOX = HERE / "outbox"


def _parse(text: str) -> dict:
    head, _, body = text.partition("\n\n")
    fields = dict(
        re.match(r"([A-Za-z-]+):\s*(.*)", line).groups()
        for line in head.strip().splitlines()
        if re.match(r"([A-Za-z-]+):\s*(.*)", line)
    )
    sender = fields.get("From", "")
    match = re.search(r"<([^>]+)>", sender)
    return {
        "from_name": sender.split("<")[0].strip(),
        "from_email": (match.group(1) if match else sender).strip(),
        "subject": fields.get("Subject", ""),
        "body": body.strip(),
    }


def read_inbox() -> list[dict]:
    msgs = []
    for path in sorted(INBOX.glob("*.txt")):
        msg = _parse(path.read_text())
        msg["file"] = path.name
        msgs.append(msg)
    return msgs


def get_message(n: int) -> dict:
    msgs = read_inbox()
    if not 1 <= n <= len(msgs):
        raise SystemExit(f"--email must be 1..{len(msgs)}. Run: python mailbox.py")
    return msgs[n - 1]


def send(to: str, subject: str, body: str) -> str:
    """The side effect. Writes a file and prints it; returns the tool result."""
    OUTBOX.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = re.sub(r"[^a-z0-9.@_-]", "_", to.lower())
    path = OUTBOX / f"{stamp}_{safe}.eml"
    path.write_text(f"To: {to}\nSubject: {subject}\nDate: {datetime.now():%c}\n\n{body}\n")

    width = 74
    print(f"\n\033[95m┌─ EMAIL SENT {'─' * (width - 14)}┐\033[0m")
    for label, value in (("To", to), ("Subject", subject)):
        print(f"\033[95m│\033[0m {label + ':':9}{value[:width - 12]}")
    print(f"\033[95m├{'─' * width}┤\033[0m")
    for line in body.splitlines():
        print(f"\033[95m│\033[0m {line[:width - 2]}")
    print(f"\033[95m└{'─' * width}┘\033[0m")
    print(f"\033[90m  written to outbox/{path.name}\033[0m")

    return f"Sent to {to} ({len(body)} chars). Saved as outbox/{path.name}"


def sent_count() -> int:
    return len(list(OUTBOX.glob("*.eml"))) if OUTBOX.exists() else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sent", action="store_true", help="list the outbox instead")
    args = ap.parse_args()

    if args.sent:
        files = sorted(OUTBOX.glob("*.eml")) if OUTBOX.exists() else []
        print(f"\n  outbox: {len(files)} message(s)")
        for f in files:
            print(f"    {f.name}")
        print()
    else:
        print()
        for i, m in enumerate(read_inbox(), 1):
            print(f"  [{i}] {m['file']}")
            print(f"      from    {m['from_name']} <{m['from_email']}>")
            print(f"      subject {m['subject']}")
            gist = next((l for l in m["body"].splitlines() if len(l) > 25), "")
            print(f"      {gist[:66]}...\n")
