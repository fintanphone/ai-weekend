#!/usr/bin/env python3
"""Lab 2 — turning a model into a software component.

Two ways to get structured data out of a model, compared head to head:

  A. Ask nicely in the prompt, then parse.       (fragile)
  B. Define a schema and force a tool call.      (reliable)

    python structured.py               # run both, 5 trials each
    python structured.py --trials 20   # more trials, sharper contrast
"""

import argparse
import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
client = anthropic.Anthropic()

TICKETS = [
    """Hi, this is Dervla Nolan from Aurora Freight. Our API integration started
    returning 502s at about 14:30 yesterday. It's blocking our overnight customs
    filing so it's pretty urgent. Ref AF-7741.""",
    """morning - dashboard colours look a bit off on the new release? not a big
    deal, just flagging. tom @ Kestrel Analytics""",
    """URGENT URGENT our entire production database is unreachable, every
    customer is down, we are losing money by the minute. Priya Raghavan,
    Meridian Health. This is ticket MH-0031 I think.""",
]

# The schema both methods are trying to satisfy.
SCHEMA = {
    "type": "object",
    "properties": {
        "customer_name": {"type": "string", "description": "Full name of the person who wrote in"},
        "company": {"type": "string"},
        "issue_summary": {"type": "string", "description": "One sentence, factual, no speculation"},
        "severity": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "description": "critical means production is down for all users",
        },
        "reference_id": {
            "type": ["string", "null"],
            "description": "Ticket reference if the customer gave one, otherwise null",
        },
    },
    "required": ["customer_name", "company", "issue_summary", "severity", "reference_id"],
}


# --------------------------------------------------------------------------
# Method A — ask in the prompt
# --------------------------------------------------------------------------

PROMPT_A = """Extract the details from this support ticket as JSON.

Return ONLY a JSON object with keys: customer_name, company, issue_summary,
severity (one of: low, medium, high, critical), reference_id (or null).
No markdown, no code fences, no explanation.

Ticket:
{ticket}"""


def method_a(ticket: str) -> dict | None:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": PROMPT_A.format(ticket=ticket)}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    # The defensive cleanup every codebase ends up with. This is the smell.
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------
# Method B — declare a tool, force the call
# --------------------------------------------------------------------------

TOOL = {
    "name": "record_ticket",
    "description": "Record a parsed support ticket in the tracking system.",
    "input_schema": SCHEMA,
}


def method_b(ticket: str) -> dict | None:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        tools=[TOOL],
        # This is the whole trick: the model MUST call this tool, and the API
        # validates its arguments against the schema before you ever see them.
        tool_choice={"type": "tool", "name": "record_ticket"},
        messages=[{"role": "user", "content": f"Parse this support ticket:\n\n{ticket}"}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    return None


# --------------------------------------------------------------------------

def validate(obj) -> tuple[bool, str]:
    """Would this actually survive contact with a downstream system?"""
    if obj is None:
        return False, "unparseable"
    missing = set(SCHEMA["required"]) - set(obj.keys())
    if missing:
        return False, f"missing {sorted(missing)}"
    if obj.get("severity") not in ["low", "medium", "high", "critical"]:
        return False, f"bad severity: {obj.get('severity')!r}"
    return True, "ok"


def run(trials: int) -> None:
    print(f"\nModel: {MODEL}   Tickets: {len(TICKETS)}   Trials each: {trials}\n")

    for label, fn in [("A: prompt-based", method_a), ("B: tool schema", method_b)]:
        passes, failures = 0, []
        total = len(TICKETS) * trials

        for ticket in TICKETS:
            for _ in range(trials):
                try:
                    result = fn(ticket)
                except Exception as exc:  # noqa: BLE001
                    failures.append(f"{type(exc).__name__}")
                    continue
                ok, reason = validate(result)
                if ok:
                    passes += 1
                else:
                    failures.append(reason)

        pct = 100 * passes / total if total else 0
        print(f"{label:<18} {passes}/{total} valid  ({pct:.0f}%)")
        if failures:
            for reason in sorted(set(failures)):
                print(f"{'':<18}   ↳ {reason} × {failures.count(reason)}")
        print()

    print("Now look at one actual result from each method:\n")
    print("A:", json.dumps(method_a(TICKETS[2]), indent=2))
    print("\nB:", json.dumps(method_b(TICKETS[2]), indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=5)
    args = ap.parse_args()
    run(args.trials)
