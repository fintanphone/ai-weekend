#!/usr/bin/env python3
# =============================================================================
#  STEP 2 of 3  —  THE SAME TASK, THROUGH A HARNESS
# =============================================================================
#
#  Identical task to problem 1. Identical tools. Identical model. The only
#  difference is what is wrapped round the loop.
#
#  Read harness.py before or after this file - it is about 180 lines and
#  there is nothing clever in it. This file is just the caller.
#
#      python step2_harnessed.py
#      python step2_harnessed.py --deny        # policy refuses destructive tools
#      python step2_harnessed.py --broke       # tiny budget, watch it stop
#      python step2_harnessed.py --trace       # print the full event log
#
# =============================================================================

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from local_backend import connect  # noqa: E402

import tools  # noqa: E402
from harness import Budget, Harness, Policy, Registry  # noqa: E402

LOG = Path(__file__).parent / "runs.jsonl"

SYSTEM = ("You are an on-call engineer's assistant with access to a server. "
          "Use the tools rather than guessing. When the task is done, say so "
          "and stop calling tools.")

TASK = ("The ingest service is failing. Work out why and tell me what to do "
        "about it.")


def ask_operator(name, arguments):
    """Called when the policy says 'ask'. Returning False is a normal outcome,
    not an error - the harness feeds the refusal back as a tool result."""
    print()
    print(f"    \033[93m? {name}({json.dumps(arguments)})\033[0m")
    answer = input("      allow? [y/N] ").strip().lower()
    return answer == "y"


def live(event):
    """Printed as it happens. In production this would go to your log pipeline
    instead - same events, different sink."""
    kind = event["kind"]
    turn = event.get("turn", 0)
    if kind == "model_reply":
        said = event.get("said", "")
        wants = event.get("wants") or []
        print(f"    turn {turn}  model  "
              f"{event['tokens_in']:>5} in / {event['tokens_out']:>4} out   "
              f"{'wants ' + ','.join(wants) if wants else 'done'}")
        if said:
            print(f"             \033[90m{said[:80]}\033[0m")
    elif kind == "policy" and event["verdict"] != "allow":
        print(f"    turn {turn}  \033[93mpolicy {event['verdict']} on "
              f"{event['tool']}\033[0m")
    elif kind == "tool_ok":
        print(f"    turn {turn}  ran    {event['tool']}  "
              f"\033[90m{event['seconds']}s, {event['chars']} chars\033[0m")
    elif kind == "tool_error":
        print(f"    turn {turn}  \033[91mfailed {event['tool']} "
              f"(attempt {event['attempt']}): {event['error']}\033[0m")
    elif kind == "model_retry":
        print(f"    turn {turn}  \033[91mmodel retry {event['attempt']}, "
              f"waiting {event['waiting']}s\033[0m")
    elif kind == "budget_stop":
        print(f"    \033[91mbudget stop: estimated {event['estimate']} more "
              f"tokens, only {event['remaining']} left\033[0m")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--deny", action="store_true",
                    help="policy refuses destructive tools outright")
    ap.add_argument("--broke", action="store_true",
                    help="set a budget too small to finish")
    ap.add_argument("--trace", action="store_true",
                    help="print the whole event log at the end")
    ap.add_argument("--flaky", action="store_true",
                    help="make tools fail 45%% of the time, to watch retries")
    args = ap.parse_args()

    if args.flaky:
        tools.FLAKE_RATE = 0.45

    try:
        backend = connect()
    except ConnectionError as exc:
        print(f"\n\033[91m{exc}\033[0m\n")
        sys.exit(1)

    LOG.unlink(missing_ok=True)

    harness = Harness(
        backend=backend,
        registry=Registry(tools.OPS_TOOLS),
        system=SYSTEM,
        policy=Policy(mode="deny-destructive" if args.deny else "ask"),
        budget=Budget(max_tokens=900 if args.broke else 50_000),
        max_turns=10,
        retries=2,
        log_path=LOG,
        approve=ask_operator,
        on_event=live,
    )

    print()
    print(f"  backend   {backend.kind} at {backend.base}")
    print(f"  tools     {', '.join(harness.registry.names())}")
    print(f"  policy    {harness.policy.mode}")
    print(f"  budget    {harness.budget.max_tokens:,} tokens")
    print(f"  log       {LOG.name}")
    print()
    print(f"  task: {TASK}")
    print()

    run = harness.run(TASK)

    print()
    print("  ANSWER")
    for line in (run.answer or "(none)").splitlines():
        print("    " + line)

    print()
    print("  " + run.summary())
    print(f"  run id {run.run_id}, {len(run.events)} events recorded")

    if args.trace:
        print()
        print("  FULL TRACE")
        for e in run.events:
            print("    " + json.dumps(e))

    print(f"""
  Compare that with problem 1 in step 1. The task, the tools and the model
  were identical; only the wrapper changed. Now you can answer every question
  you could not answer before:

      which tools, in what order    -> the trace
      what arguments                -> the trace
      what each one returned        -> {LOG.name}
      what it cost                  -> {run.tokens_in + run.tokens_out} tokens
      why it stopped                -> {run.stopped_because!r}

  And one you did not think to ask: it is all in {LOG.name} as JSON lines, so
  the next question - "how often does this task need the log tool?" - is a
  grep, not an investigation.

  \033[93mTry these:\033[0m
      --deny     policy refuses destructive tools; watch the agent cope
      --broke    a budget too small to finish; watch it stop cleanly
      --flaky    tools fail 45% of the time; watch retries work
      --trace    the full structured event log

  Next:  python step3_reuse_it.py
""")
