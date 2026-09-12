#!/usr/bin/env python3
"""Lab 1 — measure what your GPU actually does.

    python bench.py                    # benchmark all configured models
    python bench.py --model qwen3:8b   # just one
    python bench.py --json-test        # the JSON reliability test

Reports time-to-first-token, generation throughput, and total latency.
"""

import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

MODELS = [
    os.environ.get("LOCAL_MODEL_SMALL", "llama3.2:3b"),
    os.environ.get("LOCAL_MODEL_MID", "qwen3:8b"),
    os.environ.get("LOCAL_MODEL_LARGE", "qwen3:14b"),
]

PROMPT = (
    "Explain what a database index is and when adding one makes things worse. "
    "Around 200 words."
)


def stream_generate(model: str, prompt: str, num_predict: int = 300) -> dict:
    """Call Ollama's streaming endpoint and time the response by hand."""
    start = time.perf_counter()
    first_token_at = None
    token_count = 0
    text_parts = []

    resp = requests.post(
        f"{HOST}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {"num_predict": num_predict, "temperature": 0.3},
        },
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()

    for line in resp.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        piece = chunk.get("response", "")
        if piece:
            if first_token_at is None:
                first_token_at = time.perf_counter()
            token_count += 1
            text_parts.append(piece)
        if chunk.get("done"):
            break

    end = time.perf_counter()
    ttft = (first_token_at - start) if first_token_at else float("nan")
    gen_time = (end - first_token_at) if first_token_at else float("nan")

    return {
        "model": model,
        "ttft_s": ttft,
        "total_s": end - start,
        "tokens": token_count,
        "tokens_per_s": token_count / gen_time if gen_time and gen_time > 0 else 0.0,
        "text": "".join(text_parts),
    }


def benchmark(models: list[str]) -> None:
    print(f"\nHost: {HOST}")
    print(f"Prompt: {PROMPT[:60]}...\n")
    print(f"{'model':<20} {'TTFT (s)':>10} {'tok/s':>10} {'tokens':>8} {'total (s)':>11}")
    print("-" * 63)

    for model in models:
        try:
            # Warm-up call: loads weights into VRAM. Never benchmark a cold model.
            stream_generate(model, "hi", num_predict=1)
            r = stream_generate(model, PROMPT)
            print(
                f"{r['model']:<20} {r['ttft_s']:>10.2f} {r['tokens_per_s']:>10.1f} "
                f"{r['tokens']:>8} {r['total_s']:>11.2f}"
            )
        except requests.HTTPError as exc:
            print(f"{model:<20}  ERROR — {exc.response.status_code}. Pulled it? `ollama pull {model}`")
        except requests.ConnectionError:
            print(f"{model:<20}  ERROR — can't reach {HOST}. Is `ollama serve` running?")

    print("\nWatch `nvidia-smi -l 1` in a second terminal while this runs.\n")


JSON_TASK = """Extract the details from this support ticket as JSON.

Ticket: "Hi, this is Dervla Nolan from Aurora Freight. Our API integration
started returning 502s at about 14:30 yesterday. It's blocking our overnight
customs filing, so it's pretty urgent. Ref is AF-7741."

Return ONLY a JSON object with keys: customer_name, company, issue_summary,
severity (one of: low, medium, high, critical), reference_id.
No markdown, no explanation, no code fences."""


def json_reliability(models: list[str], trials: int = 5) -> None:
    """The important half of this lab.

    Ask each model for strict JSON, several times, and count how often it
    actually complies. Small models fail here, confidently and silently.
    """
    print(f"\nJSON reliability — {trials} trials per model\n")
    print(f"{'model':<20} {'valid JSON':>12} {'all keys':>10}")
    print("-" * 44)

    required = {"customer_name", "company", "issue_summary", "severity", "reference_id"}

    for model in models:
        valid, complete = 0, 0
        for _ in range(trials):
            try:
                out = stream_generate(model, JSON_TASK, num_predict=400)["text"]
            except Exception:  # noqa: BLE001
                continue
            try:
                parsed = json.loads(out.strip().strip("`").removeprefix("json").strip())
                valid += 1
                if required.issubset(parsed.keys()):
                    complete += 1
            except (json.JSONDecodeError, AttributeError):
                pass
        print(f"{model:<20} {valid}/{trials:<11} {complete}/{trials}")

    print(
        "\nDiscussion: what does a 3B model do wrong here? Is it wrong in a way\n"
        "your code could detect, or wrong in a way that would quietly poison a\n"
        "downstream system? That difference is the whole argument for Lab 2.\n"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="benchmark a single model")
    ap.add_argument("--json-test", action="store_true", help="run the JSON reliability test")
    ap.add_argument("--trials", type=int, default=5)
    args = ap.parse_args()

    targets = [args.model] if args.model else MODELS

    if args.json_test:
        json_reliability(targets, args.trials)
    else:
        benchmark(targets)
