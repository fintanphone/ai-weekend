#!/usr/bin/env python3
"""Lab 2b — the same task, on your own GPU.

Three ways to get structured data out of a local model:

  A. Ask nicely in the prompt, then parse.       (fragile everywhere)
  B. Constrained decoding via a JSON Schema.     (the grammar forbids bad JSON)
  C. Tool calling, if the model supports it.     (mirrors structured.py)

Method B is the interesting one: the server compiles your schema into a
sampling grammar and masks the logits, so tokens that would break the schema
are simply unavailable. A small model *physically cannot* emit malformed JSON.

That is not the same as being right. Validity and field accuracy are scored
separately, and on tier-2 tickets they come apart badly.

    python structured_local.py --label "27B IQ3_M"
    python structured_local.py --tier 2 --trials 5     # just the hard ones
    python structured_local.py --show                  # every parsed object
    python structured_local.py --misses                # only what went wrong
    python structured_local.py --compare               # table of saved runs

llama-server holds one model at a time, so results append to results.json.
Run, restart the server with another model or quant, run again, --compare.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from local_backend import NotSupported, connect, normalise_tool_args  # noqa: E402

import tickets as T  # noqa: E402

load_dotenv()
RESULTS = Path(__file__).parent / "results.json"

TOOL = [{
    "type": "function",
    "function": {
        "name": "record_ticket",
        "description": "Record a parsed support ticket in the tracking system.",
        "parameters": T.SCHEMA,
    },
}]


def method_a(be, text: str):
    out = be.chat([{"role": "user",
                    "content": T.PROMPT_A.format(rules=T.RULES, ticket=text)}])
    return be.json_from(out)


def method_b(be, text: str):
    out = be.chat([{"role": "user",
                    "content": f"{T.RULES}\n\nParse this support ticket:\n\n{text}"}],
                  schema=T.SCHEMA)
    return be.json_from(out)


def method_c(be, text: str):
    out = be.chat([{"role": "user",
                    "content": f"{T.RULES}\n\nParse this support ticket:\n\n{text}"}],
                  tools=TOOL)
    calls = out.get("tool_calls") or []
    return normalise_tool_args(calls[0]) if calls else None


METHODS = [("A  prompt", method_a), ("B  schema", method_b), ("C  tools ", method_c)]


def run(trials: int, show: bool, misses: bool, label: str | None, tier: str) -> None:
    try:
        be = connect()
    except ConnectionError as exc:
        print(f"\n\033[91m{exc}\033[0m\n")
        return

    cases = T.select(tier)
    style = be.probe_schema_support()
    tag = label or be.model_name

    print(f"\n  backend        {be.kind} at {be.base}")
    print(f"  model          {be.model_name}")
    print(f"  schema support {style or 'NONE — method B will be skipped'}")
    print(f"  tickets        {len(cases)}  (tier {tier})   trials {trials}")
    print(f"  label          {tag}\n")
    print("  valid  = parseable, all keys present, severity inside the enum")
    print("  fields = of 4 checkable fields, how many were actually right\n")

    header = f"  {'method':<12} {'valid':>12} {'fields right':>14}"
    tiers = sorted({t["tier"] for t in cases})
    for ti in tiers:
        header += f" {'tier ' + str(ti):>9}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    record = {"label": tag, "backend": be.kind, "model": be.model_name,
              "schema_style": style, "trials": trials, "tier": tier,
              "when": datetime.now().isoformat(timespec="seconds"), "methods": {}}
    all_misses = []

    for name, fn in METHODS:
        valid = attempts = got = possible = 0
        per_tier = {ti: [0, 0] for ti in tiers}
        unsupported = None

        for case in cases:
            for _ in range(trials):
                attempts += 1
                try:
                    result = fn(be, case["text"])
                except NotSupported as exc:
                    unsupported = str(exc)[:50]
                    break
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
                if show:
                    print(f"    \033[90m{case['id']}: {json.dumps(result)}\033[0m")
            if unsupported:
                break

        if unsupported:
            print(f"  {name:<12} {'—':>12} {'—':>14}   unsupported: {unsupported}")
            record["methods"][name.strip()] = None
            continue

        vpct = 100 * valid / attempts if attempts else 0
        apct = 100 * got / possible if possible else 0
        row = f"  {name:<12} {valid}/{attempts} ({vpct:>3.0f}%)".ljust(28)
        row += f"{got}/{possible} ({apct:>3.0f}%)".rjust(14)
        tier_pcts = {}
        for ti in tiers:
            g, p = per_tier[ti]
            pct = 100 * g / p if p else 0
            tier_pcts[ti] = round(pct, 1)
            row += f" {pct:>8.0f}%"
        print(row)
        record["methods"][name.strip()] = {"valid_pct": round(vpct, 1),
                                           "accuracy_pct": round(apct, 1),
                                           "by_tier": tier_pcts}

    save(record)

    if misses and all_misses:
        print("\n  \033[93mwhat went wrong\033[0m")
        seen = {}
        for method, cid, what in all_misses:
            seen.setdefault((method, cid), []).append(what)

        # Tier 2 first — that's where the interesting failures are.
        def order(item):
            (method, cid), _ = item
            case = next(c for c in cases if c["id"] == cid)
            return (-case["tier"], method, cid)

        rows = sorted(seen.items(), key=order)
        shown = rows[:12]
        for (method, cid), whats in shown:
            case = next(c for c in cases if c["id"] == cid)
            common = max(set(whats), key=whats.count)
            print(f"    {method}  {cid:<20} {common}")
            if case["traps"] != "none":
                print(f"      \033[90m{case['traps']}\033[0m")
        if len(rows) > len(shown):
            print(f"    \033[90m... and {len(rows) - len(shown)} more "
                  f"(use --tier 2 to focus)\033[0m")

    print(f"\n  saved to {RESULTS.name}\n")
    print("""\033[93mWhat to look for:\033[0m
Tier 1 should be close to 100% everywhere — those tickets are clean, and a
capable model handles them without effort. The teaching happens in the tier 2
column, where each ticket sets one specific trap: a company that isn't the
writer's, a colleague named before the signature, a customer downplaying an
outage, an invoice number shaped like a reference, a closed ticket quoted in
a thread, and a request relayed on someone's behalf.

Watch the two scoring columns. Method B should stay at 100% valid throughout,
because the grammar cannot produce malformed JSON. Its tier 2 accuracy will
not. That gap is the point: constrained decoding guarantees SHAPE, never
TRUTH, and a well-formed wrong record is far harder to catch than one that
fails to parse.

Run with --misses to see exactly which trap caught it.\n""")


def save(record: dict) -> None:
    history = []
    if RESULTS.exists():
        try:
            history = json.loads(RESULTS.read_text())
        except json.JSONDecodeError:
            pass
    key = (record["label"], record["tier"])
    history = [h for h in history if (h.get("label"), h.get("tier")) != key]
    history.append(record)
    RESULTS.write_text(json.dumps(history, indent=2))


def compare() -> None:
    if not RESULTS.exists():
        print("\nNo saved runs yet.\n")
        return
    history = json.loads(RESULTS.read_text())
    if not history:
        print("\nNo saved runs yet.\n")
        return

    print(f"\n  {'label':<24} {'tier':>5} {'A prompt':>16} {'B schema':>16} {'C tools':>16}")
    print("  " + "-" * 80)
    for h in history:
        cells = []
        for key in ("A  prompt", "B  schema", "C  tools"):
            m = h["methods"].get(key)
            cells.append("—" if not m
                         else f"{m['valid_pct']:.0f}% / {m['accuracy_pct']:.0f}%")
        print(f"  {h['label'][:24]:<24} {str(h.get('tier','?')):>5} "
              + " ".join(f"{c:>16}" for c in cells))
    print("\n  each cell is  valid% / fields-right%")
    print("  a model that holds 100% valid while accuracy drops is the whole lesson\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--tier", default="all", choices=["1", "2", "all"])
    ap.add_argument("--label", help="name this run, e.g. '27B IQ3_M'")
    ap.add_argument("--show", action="store_true", help="print every parsed object")
    ap.add_argument("--misses", action="store_true", help="show which traps caught it")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()

    if args.compare:
        compare()
    else:
        run(args.trials, args.show, args.misses, args.label, args.tier)
