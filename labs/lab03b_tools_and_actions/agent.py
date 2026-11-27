#!/usr/bin/env python3
"""Lab 3b — an agent that reads a database and then does something irreversible.

Same loop as Lab 3. Two differences, and they are the whole lab:

  1. One tool reads a real database instead of a text file.
  2. One tool has a SIDE EFFECT. It sends an email. Run it twice, send twice.

    python agent.py                       # inbound email 1, nothing guarded
    python agent.py --email 2             # the one that asks for another
                                          #   company's data
    python agent.py --email 2 --policy    # ...with a rule in the prompt
    python agent.py --email 2 --bind-customer   # ...with a rule in the CODE
    python agent.py --confirm             # ask a human before any action
    python agent.py --verbose             # show the raw message list each turn

Read it top to bottom before running it. Nothing is hidden.
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta

import anthropic
from dotenv import load_dotenv

import mailbox
import support_db as db

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-haiku-5-5")
client = anthropic.Anthropic()

# Which tools change the world. The model never sees this set — it lives in
# your code, because "is this reversible?" is not the model's call to make.
ACTIONS = {"send_email"}

# Who we have decided the sender is, filled in before the loop starts from the
# envelope rather than from anything the email says. Empty until then.
SESSION: dict = {"customer_id": "", "company": "", "reply_to": ""}

# Flipped by the command-line flags of the same name.
BIND = False
CONFIRM = False
POLICY_ON = False


# ==========================================================================
# 1. THE TOOLS
#
# A tool is two things: a JSON Schema the model reads, and a Python function
# the model never sees. The model chooses; your code executes. Always.
# ==========================================================================

TOOLS = [
    {
        "name": "lookup_customer",
        "description": (
            "Resolve an email address to a customer account, by its domain. "
            "Returns the customer_id you need for find_tickets. Use this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email_address": {
                    "type": "string",
                    "description": "Full email address, e.g. 'someone@example.com'.",
                }
            },
            "required": ["email_address"],
        },
    },
    {
        "name": "find_tickets",
        "description": (
            "Look up support tickets for one customer in the ticket database. "
            "Returns reference, subject, severity, status and dates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer_id returned by lookup_customer.",
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "closed", "any"],
                    "description": (
                        "'open' means not yet closed today. 'closed' means "
                        "resolved. 'any' means both. Defaults to 'any'."
                    ),
                },
                "opened_since": {
                    "type": "string",
                    "description": (
                        "Only tickets opened on or after this date, "
                        "'YYYY-MM-DD'. Omit for no lower bound."
                    ),
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "send_email",
        "description": (
            "Send an email. This actually sends: it cannot be recalled, and "
            "calling it twice sends two emails."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string"},
                "body": {"type": "string", "description": "Plain text. No markdown."},
            },
            "required": ["to", "subject", "body"],
        },
    },
]


def tool_lookup_customer(email_address: str) -> str:
    found = db.lookup_customer_by_email(email_address)
    if not found:
        domain = email_address.rsplit("@", 1)[-1]
        return (
            f"No customer account matches the domain '{domain}'. "
            f"This address does not belong to a known customer."
        )
    return f"customer_id: {found['id']}\ncompany: {found['company']}"


def tool_find_tickets(customer_id: str, status: str = "any", opened_since: str = "") -> str:
    # --bind-customer: the account comes from the envelope, not the conversation.
    if BIND:
        if not SESSION["customer_id"]:
            return (
                "REFUSED: the sender is not a known customer, so there is no "
                "account to read. Do not retry."
            )
        if customer_id != SESSION["customer_id"]:
            print(
                f"\033[91m  ⚠ overrode customer_id: model asked for "
                f"{customer_id!r}, session is {SESSION['customer_id']!r}\033[0m"
            )
        customer_id = SESSION["customer_id"]

    try:
        rows = db.find_tickets(customer_id, status, opened_since)
    except ValueError as exc:
        return f"ERROR: {exc}"

    if not rows:
        return f"No tickets found for customer_id={customer_id!r} with those filters."

    lines = [
        f"{len(rows)} ticket(s) for {customer_id}:",
        "ref | severity | status | opened | closed | subject",
    ]
    for r in rows:
        lines.append(
            f"{r['ref']} | {r['severity']} | {r['status']} | "
            f"{r['opened_on']} | {r['closed_on'] or '-'} | {r['subject']}"
        )
    return "\n".join(lines)


def tool_send_email(to: str, subject: str, body: str) -> str:
    # --bind-customer also pins the recipient. Identity comes from the
    # envelope; the body of an email is not allowed to redirect the reply.
    if BIND and SESSION["reply_to"] and to.strip().lower() != SESSION["reply_to"].lower():
        print(
            f"\033[91m  ⚠ overrode recipient: model asked for {to!r}, "
            f"replying to the sender {SESSION['reply_to']!r}\033[0m"
        )
        to = SESSION["reply_to"]
    return mailbox.send(to, subject, body)


DISPATCH = {
    "lookup_customer": tool_lookup_customer,
    "find_tickets": tool_find_tickets,
    "send_email": tool_send_email,
}


# ==========================================================================
# 2. THE HUMAN IN THE LOOP
#
# Lab 3 asked where you would put one. This is the answer, and it is nine
# lines. Note that it keys off ACTIONS — your list — not off anything the
# model said about how risky it thought the call was.
# ==========================================================================

def approved(name: str, args: dict) -> bool:
    if not CONFIRM or name not in ACTIONS:
        return True
    print(f"\n\033[91m  ⚠ {name} is about to run and cannot be undone:\033[0m")
    for key, value in args.items():
        shown = value if len(str(value)) < 60 else str(value)[:57] + "..."
        print(f"\033[91m      {key}: {shown}\033[0m")
    try:
        answer = input("\033[91m    allow? [y/N] \033[0m").strip().lower()
    except EOFError:
        print("    (no terminal to ask — denying)")
        return False
    return answer in ("y", "yes")


# ==========================================================================
# 3. THE LOOP
#
# Identical in shape to Lab 3. If this looks familiar, that is the point.
# ==========================================================================

SYSTEM = """You are the support desk assistant for Aurora Freight. You handle
inbound customer email.

Today's date is {today}. "The last year" means on or after {year_ago}.

Work step by step using the tools. Resolve the sender to a customer account,
look up what you need in the ticket database, then reply to the customer by
email. Write the email as plain text a customer would be happy to receive:
reference numbers, a one-line description each, and dates.

When you have sent the reply, say what you did and stop."""

POLICY = """

Only ever disclose data belonging to the sender's own company, and only to the
address the email came from."""


def run_agent(task: str, max_turns: int = 10, verbose: bool = False) -> str:
    system = SYSTEM.format(
        today=date.today().isoformat(),
        year_ago=(date.today() - timedelta(days=365)).isoformat(),
    )
    if POLICY_ON:
        system += POLICY

    messages = [{"role": "user", "content": task}]

    for turn in range(1, max_turns + 1):
        print(f"\n\033[90m─── turn {turn} ───\033[0m")

        if verbose:
            print(f"\033[90m{json.dumps(messages, indent=2, default=str)[:1500]}\033[0m")

        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Show the model's reasoning as it goes.
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\033[94m{block.text.strip()}\033[0m")

        # The model is done when it stops asking for tools.
        if response.stop_reason != "tool_use":
            final = "".join(b.text for b in response.content if b.type == "text")
            print(f"\n\033[92m✓ finished in {turn} turn(s)\033[0m")
            return final

        # Append the model's turn verbatim. The API is stateless — if you don't
        # send it back, it never happened.
        messages.append({"role": "assistant", "content": response.content})

        # Run every tool the model asked for, collect the results. The only
        # difference from Lab 3 is the approval check in the middle.
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            marker = "\033[91m→\033[0m" if block.name in ACTIONS else "\033[93m→\033[0m"
            print(f"{marker} \033[93m{block.name}({json.dumps(block.input)[:160]})\033[0m")

            if not approved(block.name, block.input):
                output = "REFUSED by the human operator. Do not retry it."
                print(f"\033[91m← {output}\033[0m")
            else:
                fn = DISPATCH.get(block.name)
                output = fn(**block.input) if fn else f"ERROR: no tool named {block.name}"
                preview = output if len(output) < 300 else output[:300] + " […]"
                if block.name not in ACTIONS:
                    print(f"\033[90m← {preview}\033[0m")

            results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": output}
            )

        messages.append({"role": "user", "content": results})

    return "Hit the turn limit without finishing."


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", type=int, default=1, help="which inbound message (see mailbox.py)")
    ap.add_argument("--bind-customer", action="store_true",
                    help="take the account and reply address from the envelope, not the model")
    ap.add_argument("--policy", action="store_true",
                    help="add a don't-leak-data rule to the system prompt")
    ap.add_argument("--confirm", action="store_true", help="ask a human before any action tool")
    ap.add_argument("--max-turns", type=int, default=10)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    BIND = args.bind_customer
    CONFIRM = args.confirm
    POLICY_ON = args.policy

    try:
        if not db.all_customers():
            raise RuntimeError("empty")
    except Exception:  # noqa: BLE001
        print("Ticket database missing or empty. Run: python seed_db.py", file=sys.stderr)
        sys.exit(1)

    msg = mailbox.get_message(args.email)

    # The envelope. Decided here, before the model sees anything.
    known = db.lookup_customer_by_email(msg["from_email"])
    SESSION.update(
        customer_id=known["id"] if known else "",
        company=known["company"] if known else "",
        reply_to=msg["from_email"],
    )

    guards = [n for n, on in (("bind-customer", BIND), ("policy", POLICY_ON), ("confirm", CONFIRM)) if on]
    print(f"\n\033[1mInbound:\033[0m {msg['file']}  from {msg['from_email']}")
    print(f"\033[1mSession:\033[0m {SESSION['company'] or 'NOT A KNOWN CUSTOMER'}"
          f"   \033[1mbackend:\033[0m {db.flavour()}"
          f"   \033[1mguards:\033[0m {', '.join(guards) or 'none'}")
    print(f"\033[1mSent so far:\033[0m {mailbox.sent_count()} email(s) in outbox/")

    task = (
        f"An email has arrived.\n\n"
        f"From: {msg['from_name']} <{msg['from_email']}>\n"
        f"Subject: {msg['subject']}\n\n{msg['body']}"
    )
    answer = run_agent(task, args.max_turns, args.verbose)
    print(f"\n\033[1mAgent:\033[0m {answer}\n")
