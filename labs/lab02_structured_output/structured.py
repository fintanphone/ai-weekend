#!/usr/bin/env python3
"""Lab 2 — turning a model into a software component.

Two ways to get structured data out of an API model, compared head to head:

  A. Ask nicely in the prompt, then parse.       (fragile)
  B. Define a schema and force a tool call.      (reliable)

    python structured.py                 # both, 3 trials each
    python structured.py --tier 2        # only the ambiguous tickets
    python structured.py --trials 10     # sharper contrast
    python structured.py --misses        # show which trap caught it

Tickets, schema and scoring live in tickets.py, shared with
structured_local.py so the API and local numbers are directly comparable.
"""

import argparse
import json
import os

import anthropic
from dotenv import load_dotenv

import tickets as T

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
client = anthropic.Anthropic()

TOOL = {
    "name": "record_ticket",
    "description": "Record a parsed support ticket in the tracking system.",
    "input_schema": T.SCHEMA,
}


# --------------------------------------------------------------------------
# Method A — ask in the prompt
# --------------------------------------------------------------------------

def method_a(text: str):
    resp = client.messages.create(
        model=MODEL, max_tokens=600,
        messages=[{"role": "user",
                   "content": T.PROMPT_A.format(rules=T.RULES, ticket=text)}],
    )
    out = "".join(b.text for b in resp.content if b.type == "text").strip()

    # The defensive cleanup every codebase ends up with. This is the smell.
    if out.startswith("```"):
        out = out.split("```")[1].removeprefix("json").strip()

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------
# Method B — declare a tool, force the call
# --------------------------------------------------------------------------

def method_b(text: str):
    resp = client.messages.create(
        model=MODEL, max_tokens=600, tools=[TOOL],
        # The whole trick: the model MUST call this tool, and the API validates
        # its arguments against the schema before you ever see them.
        tool_choice={"type": "tool", "name": "record_ticket"},
        messages=[{"role": "user",
                   "content": f"{T.RULES}\n\nParse this support ticket:\n\n{text}"}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    return None


METHODS = [("A: prompt-based", method_a), ("B: tool schema", method_b)]


def run(trials: int, tier: str, misses: bool) -> None:
    cases = T.select(tier)
    tiers = sorted({c["tier"] for c in cases})
    print(f"\n  model {MODEL}   tickets {len(cases)} (tier {tier})   trials {trials}\n")

    header = f"  {'method':<18} {'valid':>13} {'fields right':>14}"
    for ti in tiers:
        header += f" {'tier ' + str(ti):>9}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    all_misses = []
    for name, fn in METHODS:
        valid = attempts = got = possible = 0
        per_tier = {ti: [0, 0] for ti in tiers}

        for case in cases:
            for _ in range(trials):
                attempts += 1
                try:
                    result = fn(case["text"])
                except Exception as exc:  # noqa: BLE001
                    all_misses.append((name, case["id"], type(exc).__name__))
                    continue

                if T.is_valid(result):
                    valid += 1
                s, total, wrong = T.accuracy(result, case["expect"])
                got += s
                possible += total
                per_tier[case["tier"]][0] += s
                per_tier[case["tier"]][1] += total
                for w in wrong:
                    all_misses.append((name, case["id"], w))

        vpct = 100 * valid / attempts if attempts else 0
        apct = 100 * got / possible if possible else 0
        row = f"  {name:<18} {valid}/{attempts} ({vpct:>3.0f}%)".ljust(34)
        row += f"{got}/{possible} ({apct:>3.0f}%)".rjust(14)
        for ti in tiers:
            g, p = per_tier[ti]
            row += f" {(100 * g / p if p else 0):>8.0f}%"
        print(row)

    if misses and all_misses:
        print("\n  \033[93mwhat went wrong\033[0m")
        seen = {}
        for method, cid, what in all_misses:
            seen.setdefault((method, cid), []).append(what)
        for (method, cid), whats in sorted(seen.items()):
            case = next(c for c in cases if c["id"] == cid)
            print(f"    {method:<18} {cid:<20} {max(set(whats), key=whats.count)}")
            print(f"    {'':<18} \033[90mtrap: {case['traps']}\033[0m")

    print("""
  Method B cannot produce a malformed record — the API validates arguments
  against the schema first. It can still produce a WRONG one. Compare the
  tier 2 column against tier 1 to see the difference, then run
  structured_local.py and compare against your own GPU.
""")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--tier", default="all", choices=["1", "2", "all"])
    ap.add_argument("--misses", action="store_true")
    args = ap.parse_args()
    run(args.trials, args.tier, args.misses)
