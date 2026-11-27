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

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-haiku-5-5")
client = anthropic.Anthropic()

# Rebuilt by --schema. See the note above tickets.schema(): the lax variant
# makes reference_id nullable and tells the model "null if none", and on a hard
# ticket it accepts that invitation.
SCHEMA_VARIANT = "lax"

TOOL = {
    "name": "record_ticket",
    "description": "Record a parsed support ticket in the tracking system.",
    "input_schema": T.schema(SCHEMA_VARIANT),
}


# --------------------------------------------------------------------------
# Method A — ask in the prompt
# --------------------------------------------------------------------------

# How much work the defensive cleanup is actually doing. On a strong model
# method A can score 100% while never once returning clean JSON — the repair
# line is holding it up, and a pass rate alone hides that completely.
REPAIR = {"fired": 0, "attempts": 0, "enabled": True}

# Transport failures are not model failures, and conflating them silently
# corrupts the table. METHODS is the OUTER loop, so a rate limit that starts
# partway through wipes out one whole method and looks like a catastrophic
# result for it. Measured: a strict-schema run came back 8/30 valid with
# APIConnectionError on 22 calls, purely because it was the third suite in
# quick succession.
#
# This is Lab 9's reliability concern arriving six labs early. Retries are
# reported, never hidden — a number you had to retry for is a different number.
RETRIES = {"count": 0, "gave_up": 0}


def call_with_retry(fn, text, attempts: int = 4):
    """Call fn(text), backing off on transport and rate-limit errors."""
    import random
    import time

    for i in range(attempts):
        try:
            return fn(text)
        except Exception as exc:  # noqa: BLE001
            name = type(exc).__name__
            transient = name in ("APIConnectionError", "APITimeoutError",
                                 "RateLimitError", "InternalServerError",
                                 "APIStatusError", "ConnectionError")
            if not transient or i == attempts - 1:
                if transient:
                    RETRIES["gave_up"] += 1
                raise
            RETRIES["count"] += 1
            # exponential, with jitter so three laptops don't resynchronise
            time.sleep(2 ** i + random.random())
    raise RuntimeError("unreachable")


def method_a(text: str):
    resp = client.messages.create(
        model=MODEL, max_tokens=600,
        messages=[{"role": "user",
                   "content": T.PROMPT_A.format(rules=T.RULES, ticket=text)}],
    )
    out = "".join(b.text for b in resp.content if b.type == "text").strip()
    REPAIR["attempts"] += 1

    # The defensive cleanup every codebase ends up with. This is the smell.
    if out.startswith("```"):
        REPAIR["fired"] += 1
        if REPAIR["enabled"]:
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
    print(f"\n  model {MODEL}   tickets {len(cases)} (tier {tier})   "
          f"trials {trials}   schema {SCHEMA_VARIANT}\n")

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
                    result = call_with_retry(fn, case["text"])
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

    if RETRIES["count"] or RETRIES["gave_up"]:
        print(f"\n  \033[93m{RETRIES['count']} call(s) were retried after a "
              f"transport or rate-limit error"
              + (f"; {RETRIES['gave_up']} still failed" if RETRIES["gave_up"]
                 else ", all eventually succeeded")
              + ".\033[0m")
        print("  \033[90mThose are not model failures. If any still failed, "
              "re-run before trusting the\n  numbers — METHODS is the outer "
              "loop, so a rate limit hits one method, not both.\033[0m")

    if REPAIR["attempts"]:
        n, tot = REPAIR["fired"], REPAIR["attempts"]
        pct = 100 * n / tot
        if n == 0:
            print(f"\n  \033[90mMethod A returned clean JSON every time "
                  f"({tot} responses) — the repair line never fired.\033[0m")
        else:
            state = "repaired" if REPAIR["enabled"] else "LEFT BROKEN (--raw)"
            print(f"\n  \033[93mMethod A wrapped its answer in a code fence "
                  f"{n}/{tot} times ({pct:.0f}%) — {state}.\033[0m")
            print(f"  \033[90mThat is three lines of your code propping up "
                  f"method A's score. Run --raw to see the\n  rate without "
                  f"them. Method B needs no such line, on any model.\033[0m")

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
    ap.add_argument("--raw", action="store_true",
                    help="disable method A's code-fence repair, to see the "
                         "unaided parse rate")
    ap.add_argument("--schema", default="lax", choices=T.SCHEMA_VARIANTS,
                    help="lax (default) makes reference_id nullable and says "
                         "'null if none'; strict removes both; honest keeps "
                         "the null but fixes the prose")
    ap.add_argument("--model",
                    help="model for THIS run, overriding WORKSHOP_MODEL in "
                         ".env — e.g. --model claude-haiku-5-5. An export only "
                         "lasts as long as the shell; this is explicit and "
                         "appears in the header.")
    args = ap.parse_args()
    REPAIR["enabled"] = not args.raw
    SCHEMA_VARIANT = args.schema
    TOOL["input_schema"] = T.schema(SCHEMA_VARIANT)
    if args.model:
        MODEL = args.model
    run(args.trials, args.tier, args.misses)
