#!/usr/bin/env python3
"""Lab 1 — measure what your GPU actually does.

Works against llama.cpp (llama-server) or Ollama, whichever is listening.

    python bench.py                          # benchmark what's loaded
    python bench.py --label "27B IQ3_M"      # tag the run
    python bench.py --json-test              # JSON reliability test
    python bench.py --compare                # table of saved runs
    python bench.py --models qwen3:8b,llama3.2:3b    # Ollama only

llama-server holds ONE model at a time, so on that backend you benchmark
what's currently loaded, restart with a different model or quant, and run
again. Results accumulate in bench_results.json; --compare tabulates them.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from local_backend import connect  # noqa: E402

load_dotenv()

RESULTS = Path(__file__).parent / "bench_results.json"

PROMPT = ("Explain what a database index is and when adding one makes things "
          "worse. Around 200 words.")

JSON_TASK = """Extract the details from this support ticket as JSON.

Ticket: "Hi, this is Dervla Nolan from Aurora Freight. Our API integration
started returning 502s at about 14:30 yesterday. It's blocking our overnight
customs filing, so it's pretty urgent. Ref is AF-7741."

Return ONLY a JSON object with keys: customer_name, company, issue_summary,
severity (one of: low, medium, high, critical), reference_id.
No markdown, no explanation, no code fences."""

REQUIRED = {"customer_name", "company", "issue_summary", "severity", "reference_id"}


def save(record: dict, key: str) -> None:
    history = []
    if RESULTS.exists():
        try:
            history = json.loads(RESULTS.read_text())
        except json.JSONDecodeError:
            pass
    history = [h for h in history if not (h.get("label") == record["label"]
                                          and h.get("kind") == key)]
    history.append(record)
    RESULTS.write_text(json.dumps(history, indent=2))


def benchmark(be, label: str, warm: bool = True) -> None:
    print(f"\n  backend   {be.kind} at {be.base}")
    print(f"  model     {be.model_name}")
    print(f"  label     {label}\n")
    print(f"  {'':<4}{'TTFT (s)':>12} {'tok/s':>10} {'tokens':>9} {'total (s)':>11}")
    print("  " + "-" * 48)

    if warm:
        try:
            be.stream_tokens("hi", max_tokens=1)   # load weights into VRAM
        except Exception:  # noqa: BLE001
            pass

    r = be.stream_tokens(PROMPT, max_tokens=300)
    print(f"  {'':<4}{r['ttft_s']:>12.2f} {r['tokens_per_s']:>10.1f} "
          f"{r['tokens']:>9} {r['total_s']:>11.2f}")

    save({"label": label, "kind": "speed", "model": be.model_name,
          "backend": be.kind, "ttft_s": round(r["ttft_s"], 3),
          "tokens_per_s": round(r["tokens_per_s"], 1), "tokens": r["tokens"],
          "when": datetime.now().isoformat(timespec="seconds")}, "speed")

    print("\n  Watch `nvidia-smi -l 1` in a second terminal while this runs.")
    print(f"  Saved to {RESULTS.name}.\n")


def json_reliability(be, label: str, trials: int) -> None:
    print(f"\n  JSON reliability — {trials} trials, no schema constraint")
    print(f"  model: {be.model_name}\n")

    valid = complete = 0
    for _ in range(trials):
        try:
            out = be.chat([{"role": "user", "content": JSON_TASK}], max_tokens=400)
        except Exception:  # noqa: BLE001
            continue
        parsed = be.json_from(out)
        if isinstance(parsed, dict):
            valid += 1
            if REQUIRED.issubset(parsed.keys()):
                complete += 1

    print(f"  parseable JSON   {valid}/{trials}")
    print(f"  all keys present {complete}/{trials}")

    save({"label": label, "kind": "json", "model": be.model_name,
          "backend": be.kind, "valid": valid, "complete": complete,
          "trials": trials,
          "when": datetime.now().isoformat(timespec="seconds")}, "json")

    print("""
  Discussion: which failures would your code catch, and which would silently
  poison a downstream system? The second kind is worse and far more common.

  Note this test deliberately uses NO schema constraint, so you see the
  model's unaided behaviour. Lab 2 turns the constraint on.
""")


def compare() -> None:
    if not RESULTS.exists():
        print("\nNo saved runs yet.\n")
        return
    history = json.loads(RESULTS.read_text())

    speed = [h for h in history if h.get("kind") == "speed"]
    if speed:
        print(f"\n  {'label':<26} {'TTFT (s)':>10} {'tok/s':>9} {'backend':>10}")
        print("  " + "-" * 58)
        for h in speed:
            print(f"  {h['label'][:26]:<26} {h['ttft_s']:>10.2f} "
                  f"{h['tokens_per_s']:>9.1f} {h['backend']:>10}")

    js = [h for h in history if h.get("kind") == "json"]
    if js:
        print(f"\n  {'label':<26} {'valid JSON':>12} {'all keys':>10}")
        print("  " + "-" * 50)
        for h in js:
            print(f"  {h['label'][:26]:<26} {h['valid']}/{h['trials']:<10} "
                  f"{h['complete']}/{h['trials']}")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", help="name this run, e.g. '27B IQ3_M'")
    ap.add_argument("--json-test", action="store_true")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--models", help="Ollama only: comma-separated list to loop over")
    args = ap.parse_args()

    if args.compare:
        compare()
        sys.exit(0)

    try:
        backend = connect()
    except ConnectionError as exc:
        print(f"\n\033[91m{exc}\033[0m\n")
        sys.exit(1)

    targets = [None]
    if args.models:
        if backend.kind != "ollama":
            print("\n  --models only works on Ollama. llama-server holds one model;")
            print("  restart it with a different GGUF and run again.\n")
            sys.exit(1)
        targets = [m.strip() for m in args.models.split(",")]

    for model in targets:
        if model:
            backend.use_model(model)
        name = args.label or backend.model_name
        if args.json_test:
            json_reliability(backend, name, args.trials)
        else:
            benchmark(backend, name)
