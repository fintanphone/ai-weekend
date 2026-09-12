#!/usr/bin/env python3
"""Lab 2b — the same task, on your own GPU.

structured.py compares two ways of getting structured data out of an API model.
This runs the same three tickets against LOCAL models, and adds a third method
that the cloud version does not have:

  A. Ask nicely in the prompt, then parse.        (fragile everywhere)
  B. Constrained decoding: Ollama's `format`.     (the grammar forbids bad JSON)
  C. Tool calling, if the model supports it.      (mirrors structured.py)

Method B is the interesting one. Ollama compiles your JSON Schema into a grammar
and masks the sampler at every step, so tokens that would break the schema are
simply not available. A 3B model physically cannot emit malformed JSON.

That is NOT the same as being right, which is the whole point of this file:
we score validity and field accuracy separately, and watch them come apart.

    python structured_local.py                    # all configured models
    python structured_local.py --model qwen3:8b   # just one
    python structured_local.py --trials 10        # sharper contrast
    python structured_local.py --show             # print the actual JSON
"""

import argparse
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

MODELS = [
    os.environ.get("LOCAL_MODEL_SMALL", "llama3.2:3b"),
    os.environ.get("LOCAL_MODEL_MID", "qwen3:8b"),
    os.environ.get("LOCAL_MODEL_LARGE", "qwen3:14b"),
]

SEVERITIES = ["low", "medium", "high", "critical"]

# --------------------------------------------------------------------------
# Same three tickets as structured.py, so the two files are comparable.
# `expect` is what a careful human would extract.
# --------------------------------------------------------------------------

TICKETS = [
    {
        "text": """Hi, this is Dervla Nolan from Aurora Freight. Our API integration
        started returning 502s at about 14:30 yesterday. It's blocking our overnight
        customs filing so it's pretty urgent. Ref AF-7741.""",
        "expect": {
            "surname": "nolan",
            "company": "aurora freight",
            "reference_id": "af-7741",
            "severity": ["high", "critical"],
        },
    },
    {
        "text": """morning - dashboard colours look a bit off on the new release? not a
        big deal, just flagging. tom @ Kestrel Analytics""",
        "expect": {
            "surname": "tom",
            "company": "kestrel analytics",
            "reference_id": None,          # the customer gave none
            "severity": ["low"],
        },
    },
    {
        "text": """URGENT URGENT our entire production database is unreachable, every
        customer is down, we are losing money by the minute. Priya Raghavan,
        Meridian Health. This is ticket MH-0031 I think.""",
        "expect": {
            "surname": "raghavan",
            "company": "meridian health",
            "reference_id": "mh-0031",
            "severity": ["critical"],
        },
    },
]

SCHEMA = {
    "type": "object",
    "properties": {
        "customer_name": {"type": "string", "description": "Full name of the person who wrote in"},
        "company": {"type": "string"},
        "issue_summary": {"type": "string", "description": "One sentence, factual, no speculation"},
        "severity": {
            "type": "string",
            "enum": SEVERITIES,
            "description": "critical means production is down for all users",
        },
        "reference_id": {
            "type": ["string", "null"],
            "description": "Ticket reference if the customer gave one, otherwise null",
        },
    },
    "required": ["customer_name", "company", "issue_summary", "severity", "reference_id"],
}

REQUIRED = set(SCHEMA["required"])


def chat(model: str, messages: list, **extra) -> dict:
    resp = requests.post(
        f"{HOST}/api/chat",
        json={"model": model, "messages": messages, "stream": False,
              "options": {"temperature": 0.2}, **extra},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------------------------------
# A. Prompt-based
# --------------------------------------------------------------------------

PROMPT_A = """Extract the details from this support ticket as JSON.

Return ONLY a JSON object with keys: customer_name, company, issue_summary,
severity (one of: low, medium, high, critical), reference_id (or null).
No markdown, no code fences, no explanation.

Ticket:
{ticket}"""


def method_a(model: str, ticket: str):
    out = chat(model, [{"role": "user", "content": PROMPT_A.format(ticket=ticket)}])
    text = out["message"]["content"].strip()

    # The same defensive cleanup as the cloud version. Still a smell.
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------
# B. Constrained decoding — the schema becomes a grammar
# --------------------------------------------------------------------------

def method_b(model: str, ticket: str):
    out = chat(
        model,
        [{"role": "user", "content": f"Parse this support ticket:\n\n{ticket}"}],
        format=SCHEMA,      # <- Ollama compiles this into a sampling grammar
    )
    try:
        return json.loads(out["message"]["content"])
    except (json.JSONDecodeError, KeyError):
        return None


# --------------------------------------------------------------------------
# C. Tool calling — mirrors structured.py exactly. Not all models support it.
# --------------------------------------------------------------------------

TOOL = {
    "type": "function",
    "function": {
        "name": "record_ticket",
        "description": "Record a parsed support ticket in the tracking system.",
        "parameters": SCHEMA,
    },
}


class NotSupported(Exception):
    pass


def method_c(model: str, ticket: str):
    try:
        out = chat(
            model,
            [{"role": "user", "content": f"Parse this support ticket:\n\n{ticket}"}],
            tools=[TOOL],
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            raise NotSupported(model) from exc
        raise

    calls = out.get("message", {}).get("tool_calls") or []
    if not calls:
        return None
    args = calls[0]["function"]["arguments"]
    return json.loads(args) if isinstance(args, str) else args


# --------------------------------------------------------------------------
# Scoring — validity and accuracy are deliberately kept apart
# --------------------------------------------------------------------------

def is_valid(obj) -> bool:
    """Would this survive contact with a downstream system?"""
    if not isinstance(obj, dict):
        return False
    if not REQUIRED.issubset(obj.keys()):
        return False
    return obj.get("severity") in SEVERITIES


def norm_ref(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    return None if s in ("", "none", "null", "n/a", "na", "unknown") else s


def accuracy(obj, expect) -> tuple[int, int, list[str]]:
    """Returns (fields correct, fields checked, list of what went wrong)."""
    if not isinstance(obj, dict):
        return 0, 4, ["unparseable"]

    wrong = []
    score = 0

    name = str(obj.get("customer_name", "")).lower()
    if expect["surname"] in name:
        score += 1
    else:
        wrong.append(f"name={obj.get('customer_name')!r}")

    company = str(obj.get("company", "")).lower()
    if expect["company"] in company or company in expect["company"]:
        score += 1
    else:
        wrong.append(f"company={obj.get('company')!r}")

    if norm_ref(obj.get("reference_id")) == expect["reference_id"]:
        score += 1
    else:
        wrong.append(f"ref={obj.get('reference_id')!r}")

    if obj.get("severity") in expect["severity"]:
        score += 1
    else:
        wrong.append(f"severity={obj.get('severity')!r}")

    return score, 4, wrong


# --------------------------------------------------------------------------

METHODS = [
    ("A  prompt", method_a),
    ("B  format", method_b),
    ("C  tools ", method_c),
]


def run(models: list[str], trials: int, show: bool) -> None:
    print(f"\nHost: {HOST}   Trials per ticket: {trials}")
    print("\nvalid  = parseable, all keys present, severity in enum")
    print("fields = of the 4 checkable fields, how many were actually right\n")

    for model in models:
        print(f"\033[1m{model}\033[0m")
        print(f"  {'method':<12} {'valid':>12} {'fields right':>16}   notes")
        print("  " + "-" * 62)

        for label, fn in METHODS:
            valid = 0
            got = 0
            possible = 0
            attempts = 0
            problems = []
            unsupported = False

            for ticket in TICKETS:
                for _ in range(trials):
                    attempts += 1
                    try:
                        result = fn(model, ticket["text"])
                    except NotSupported:
                        unsupported = True
                        break
                    except requests.ConnectionError:
                        print(f"  {label:<12}   cannot reach {HOST} — is ollama running?")
                        return
                    except Exception as exc:  # noqa: BLE001
                        problems.append(type(exc).__name__)
                        continue

                    if is_valid(result):
                        valid += 1
                    s, total, wrong = accuracy(result, ticket["expect"])
                    got += s
                    possible += total
                    problems.extend(wrong)

                    if show:
                        print(f"    \033[90m{json.dumps(result)}\033[0m")

                if unsupported:
                    break

            if unsupported:
                print(f"  {label:<12} {'—':>12} {'—':>16}   model has no tool support")
                continue

            vpct = 100 * valid / attempts if attempts else 0
            apct = 100 * got / possible if possible else 0
            note = ""
            if problems:
                common = max(set(problems), key=problems.count)
                note = f"most common miss: {common}"
            print(f"  {label:<12} {valid}/{attempts} ({vpct:>3.0f}%)".ljust(29)
                  + f"{got}/{possible} ({apct:>3.0f}%)".rjust(16)
                  + f"   {note}")
        print()

    print("""\033[93mThe question to sit with:\033[0m
Method B should be at or near 100% valid for every model, including the 3B one,
because the grammar makes malformed JSON unreachable. Now look at the second
column. Constrained decoding guarantees SHAPE. It guarantees nothing about
TRUTH — and a confidently wrong, perfectly-shaped record is harder to catch
than one that fails to parse.

Compare these numbers against `python structured.py` on the API model before
you decide what you would actually deploy.\n""")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="run a single model")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--show", action="store_true", help="print every parsed object")
    args = ap.parse_args()

    run([args.model] if args.model else MODELS, args.trials, args.show)
