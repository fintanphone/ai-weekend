#!/usr/bin/env python3
"""Lab 8 — an eval harness for the Lab 3 agent.

Twelve cases, a scoring function, and a number. Change one thing about the
agent, rerun, watch the number move. That's the entire discipline.

    python eval.py                       # run the suite
    python eval.py --variant terse       # a different system prompt
    python eval.py --case reorder-breach # one case, verbose
    python eval.py --compare             # run all variants, tabulate
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent / "lab03_agent_loop"))
from agent import DISPATCH, TOOLS  # noqa: E402

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
CASES = json.loads((Path(__file__).parent / "cases.json").read_text())
client = anthropic.Anthropic()

# --------------------------------------------------------------------------
# The thing under test. Variants let you change one factor and re-measure.
# --------------------------------------------------------------------------

VARIANTS = {
    "baseline": (
        "You are an assistant with access to a file workspace. "
        "Answer the user's question."
    ),
    "careful": (
        "You are a careful assistant with access to a small file workspace.\n\n"
        "Work step by step. Use tools rather than guessing — if you need to know "
        "what files exist, list them; if you need arithmetic, calculate it. "
        "When you have enough information, give a direct answer and stop calling "
        "tools."
    ),
    "grounded": (
        "You are a careful assistant with access to a small file workspace.\n\n"
        "Work step by step. Use tools rather than guessing. Never do arithmetic "
        "in your head — always use the calculate tool.\n\n"
        "If the workspace does not contain the information needed to answer, say "
        "so plainly. Do not estimate, extrapolate, or infer figures that are not "
        "present. It is always better to say you don't know."
    ),
}


def run_case(task: str, system: str, max_turns: int = 10) -> dict:
    """Quiet version of the Lab 3 loop, instrumented."""
    messages = [{"role": "user", "content": task}]
    turns = 0
    in_tokens = out_tokens = 0
    start = time.perf_counter()

    for turns in range(1, max_turns + 1):
        resp = client.messages.create(
            model=MODEL, max_tokens=2000, system=system, tools=TOOLS, messages=messages
        )
        in_tokens += resp.usage.input_tokens
        out_tokens += resp.usage.output_tokens

        if resp.stop_reason != "tool_use":
            answer = "".join(b.text for b in resp.content if b.type == "text")
            return {
                "answer": answer,
                "turns": turns,
                "in_tokens": in_tokens,
                "out_tokens": out_tokens,
                "seconds": time.perf_counter() - start,
            }

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            fn = DISPATCH.get(block.name)
            out = fn(**block.input) if fn else f"ERROR: unknown tool {block.name}"
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        messages.append({"role": "user", "content": results})

    return {
        "answer": "[hit turn limit]",
        "turns": turns,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "seconds": time.perf_counter() - start,
    }


# --------------------------------------------------------------------------
# Scoring — deterministic first, judge only where it's unavoidable
# --------------------------------------------------------------------------

def score_contains(answer: str, case: dict) -> tuple[bool, str]:
    needles = case.get("must_contain")
    if not needles:
        return True, ""
    lowered = answer.lower()
    hits = [n for n in needles if n.lower() in lowered]
    if case.get("match") == "any":
        return bool(hits), "" if hits else f"none of {needles}"
    missing = [n for n in needles if n not in hits]
    return not missing, "" if not missing else f"missing {missing}"


JUDGE_PROMPT = """You are grading one answer against a rubric. Be strict.

Rubric: {rubric}

Answer to grade:
{answer}

Reply with exactly one word: PASS or FAIL."""


def score_judge(answer: str, case: dict) -> tuple[bool, str]:
    rubric = case.get("judge")
    if not rubric:
        return True, ""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=10,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(rubric=rubric, answer=answer),
            }
        ],
    )
    verdict = "".join(b.text for b in resp.content if b.type == "text").strip().upper()
    return verdict.startswith("PASS"), "" if verdict.startswith("PASS") else "judge: FAIL"


def score(answer: str, case: dict) -> tuple[bool, str]:
    ok, why = score_contains(answer, case)
    if not ok:
        return False, why
    return score_judge(answer, case)


# --------------------------------------------------------------------------

def run_suite(variant: str, cases: list, verbose: bool = False) -> dict:
    system = VARIANTS[variant]
    passes = 0
    totals = {"in": 0, "out": 0, "turns": 0, "seconds": 0.0}

    print(f"\n\033[1mvariant: {variant}\033[0m   model: {MODEL}   cases: {len(cases)}\n")
    print(f"{'case':<20} {'result':<8} {'turns':>6} {'tok in':>8} {'tok out':>8}  why")
    print("-" * 78)

    for case in cases:
        r = run_case(case["task"], system)
        ok, why = score(r["answer"], case)
        passes += ok

        totals["in"] += r["in_tokens"]
        totals["out"] += r["out_tokens"]
        totals["turns"] += r["turns"]
        totals["seconds"] += r["seconds"]

        mark = "\033[92mPASS\033[0m" if ok else "\033[91mFAIL\033[0m"
        print(
            f"{case['id']:<20} {mark:<17} {r['turns']:>6} {r['in_tokens']:>8} "
            f"{r['out_tokens']:>8}  {why}"
        )
        if verbose or not ok:
            print(f"\033[90m    {r['answer'][:400]}\033[0m")

    pct = 100 * passes / len(cases)
    print("-" * 78)
    print(
        f"\033[1m{passes}/{len(cases)} ({pct:.0f}%)\033[0m   "
        f"{totals['in']:,} in / {totals['out']:,} out tokens   "
        f"{totals['turns']} turns   {totals['seconds']:.0f}s"
    )
    print(
        "\n\033[90mCost: multiply the token counts by your model's per-token rate\n"
        "(https://www.anthropic.com/pricing). Do this now — knowing the cost per\n"
        "eval run is what stops the suite quietly becoming unaffordable.\033[0m"
    )
    return {"variant": variant, "passes": passes, "total": len(cases), **totals}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="careful", choices=list(VARIANTS))
    ap.add_argument("--case", help="run a single case id, verbose")
    ap.add_argument("--compare", action="store_true", help="run every variant")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    cases = [c for c in CASES if c["id"] == args.case] if args.case else CASES
    if not cases:
        raise SystemExit(f"No case with id {args.case!r}")

    if args.compare:
        rows = [run_suite(v, cases) for v in VARIANTS]
        print("\n\033[1m=== comparison ===\033[0m")
        print(f"{'variant':<12} {'score':>10} {'tokens':>12}")
        for r in rows:
            pct = 100 * r["passes"] / r["total"]
            print(f"{r['variant']:<12} {r['passes']}/{r['total']} ({pct:>3.0f}%) "
                  f"{r['in'] + r['out']:>12,}")
    else:
        run_suite(args.variant, cases, args.verbose or bool(args.case))
