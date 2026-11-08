#!/usr/bin/env python3
# =============================================================================
#  STEP 1 of 3  —  WHAT BREAKS WHEN YOU SHIP LAB 3's LOOP
# =============================================================================
#
#  Lab 3's loop was twenty lines and it worked. So why would anyone need
#  anything more?
#
#  Because it worked on a Saturday afternoon, on one task, with someone
#  watching, on a machine where nothing mattered. This file runs that same
#  loop four more times, under four conditions you will actually meet, and
#  lets it fail in front of you.
#
#  No harness in this file. On purpose. The point is to earn one.
#
#      python step1_what_breaks.py
#      python step1_what_breaks.py --only 3     # just one of them
#
# =============================================================================

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from local_backend import connect  # noqa: E402

import tools  # noqa: E402

SYSTEM = ("You are an on-call engineer's assistant with access to a server. "
          "Use the tools rather than guessing. When the task is done, say so "
          "and stop calling tools.")


# =============================================================================
#  THE NAKED LOOP — Lab 3, reproduced, with nothing added
# =============================================================================

def naked_loop(be, task, tool_list, max_turns=12, dispatch_wrapper=None):
    """Exactly the shape you wrote on Saturday. No logging, no budget, no
    policy, no retries. Returns the final answer, or raises."""

    schemas = [t["schema"] for t in tool_list]
    by_name = {t["name"]: t["func"] for t in tool_list}

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]

    for _ in range(max_turns):
        reply = be.chat(messages, tools=schemas, temperature=0.0, max_tokens=800)

        calls = reply.get("tool_calls") or []
        if not calls:
            return reply.get("text", "").strip()

        messages.append({"role": "assistant",
                         "content": reply.get("text") or None,
                         "tool_calls": calls})

        for call in calls:
            name = call["function"]["name"]
            raw = call["function"]["arguments"]
            args = json.loads(raw) if isinstance(raw, str) else raw
            runner = dispatch_wrapper or (lambda n, a: by_name[n](**a))
            output = runner(name, args)
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": output})

    return "(hit the turn limit)"


def banner(n, title, question):
    print()
    print("=" * 72)
    print(f"  PROBLEM {n}  —  {title}")
    print("=" * 72)
    print(f"  {question}")
    print()


# =============================================================================
#  PROBLEM 1 — it gave you an answer and you cannot check it
# =============================================================================

def problem_1(be):
    banner(1, "You cannot see what it did",
           "It answers. Is the answer right? How would you know?")

    task = ("The ingest service is failing. Work out why and tell me what to do "
            "about it.")
    print(f"  task: {task}\n")

    answer = naked_loop(be, task, tools.OPS_TOOLS)

    print("  ANSWER")
    for line in answer.splitlines():
        print("    " + line)

    print("""
  That is the entire output. Now answer these:

      Which tools did it call, in what order?
      What arguments did it pass?
      Did it read the log, or guess from the disk figures?
      What did /var actually come back as?
      How many tokens did that cost?

  You cannot answer any of them. The information existed for a few
  milliseconds inside the loop and was discarded.

  In a workshop that is mildly annoying. At 3am, with a wrong answer and a
  colleague asking "are you sure?", it is the whole problem.
""")


# =============================================================================
#  PROBLEM 2 — it runs away and you pay for it
# =============================================================================

def problem_2(be):
    banner(2, "Nothing stops it spending",
           "A badly-specified task meets a loop with no ceiling.")

    task = ("Check the disk usage on every mount point you can find, then check "
            "them all again to confirm, and keep confirming until you are "
            "completely certain nothing has changed.")
    print(f"  task: {task}\n")
    print("  (a silly instruction, but a plausible accident - watch it go)\n")

    spent = {"in": 0, "out": 0, "calls": 0}
    schemas = [t["schema"] for t in tools.OPS_TOOLS]
    by_name = {t["name"]: t["func"] for t in tools.OPS_TOOLS}
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]

    for turn in range(1, 13):
        reply = be.chat(messages, tools=schemas, temperature=0.0, max_tokens=800)
        usage = reply.get("usage") or {}
        spent["in"] += usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        spent["out"] += usage.get("completion_tokens") or usage.get("output_tokens") or 0

        calls = reply.get("tool_calls") or []
        print(f"    turn {turn:>2}  {len(calls)} tool call(s)   "
              f"running total: {spent['in'] + spent['out']:>6} tokens")

        if not calls:
            print("\n  It stopped on its own this time.")
            break

        messages.append({"role": "assistant", "content": reply.get("text") or None,
                         "tool_calls": calls})
        for call in calls:
            name = call["function"]["name"]
            raw = call["function"]["arguments"]
            args = json.loads(raw) if isinstance(raw, str) else raw
            spent["calls"] += 1
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": by_name[name](**args)})
    else:
        print("\n  It did not stop. The range() ran out - that is the only")
        print("  thing that saved you, and it is a magic number in a for-loop.")

    print(f"""
  {spent['in'] + spent['out']} tokens, {spent['calls']} tool calls.

  On your GPU that was free and slow. On an API it was neither. And notice
  there was no ceiling anywhere - the loop would happily have run until the
  turn count ran out, every time, for every user, all night.

  A turn limit is not a budget. Ten turns of a 200k-token context is a very
  different bill from ten turns of a short one.
""")


# =============================================================================
#  PROBLEM 3 — one blip and the whole run is gone
# =============================================================================

def problem_3(be):
    banner(3, "A transient failure destroys everything",
           "The network hiccups on turn four. What happens to turns one to three?")

    tools.FLAKE_RATE = 0.45          # make failures likely, for the demo
    task = "Why is the ingest service failing? Check the disk and the log."
    print(f"  task: {task}")
    print(f"  (tools are failing {int(tools.FLAKE_RATE * 100)}% of the time)\n")

    try:
        answer = naked_loop(be, task, tools.OPS_TOOLS)
        print("  It got through. Run it again - it will not always.")
        print("    " + answer.splitlines()[0][:70])
    except tools.ToolFailure as exc:
        print(f"  \033[91mToolFailure: {exc}\033[0m")
        print("""
  The exception propagated out of the loop and killed the process.

  Everything the agent had learned - the disk figures, the log lines, the
  conclusion it was two tokens away from writing - is gone. Not saved
  anywhere. Not retried. Not logged.

  The failure was transient. A single retry would almost certainly have
  worked. Instead you lost the whole run, and you will pay for all of it
  again when you start over.
""")
    finally:
        tools.FLAKE_RATE = 0.0


# =============================================================================
#  PROBLEM 4 — it does something destructive and nobody was asked
# =============================================================================

def problem_4(be):
    banner(4, "It acts, and nobody authorised it",
           "restart_service is in the tool list. Nothing is guarding it.")

    task = ("The ingest service is stuck and has been failing for an hour. "
            "Diagnose it and fix it.")
    print(f"  task: {task}\n")

    did = []

    def watching(name, args):
        did.append(name)
        marker = "  \033[91m<-- destructive\033[0m" if name == "restart_service" else ""
        print(f"    ran {name}({json.dumps(args)}){marker}")
        return {t["name"]: t["func"] for t in tools.OPS_TOOLS}[name](**args)

    answer = naked_loop(be, task, tools.OPS_TOOLS, dispatch_wrapper=watching)

    print()
    print("  ANSWER")
    for line in answer.splitlines()[:4]:
        print("    " + line)

    if "restart_service" in did:
        print("""
  It restarted a production service. You were not asked. Nothing in the loop
  distinguished restart_service from check_disk - they are both just names in
  a dispatch dict.

  In Lab 3 we fixed this with:

      if name == "delete_file":
          ...ask the human...

  That works for exactly one tool. Add a second destructive tool and you add
  a second if-statement. Add a second task with different tools and you copy
  the whole loop. That is not a guard rail, it is a sticking plaster.
""")
    else:
        print("""
  It did not restart anything this time - it read the log and reported back.
  Run it again, or make the task more urgent, and it will.

  That it MIGHT is the problem. Nothing in the loop prevents it. You are
  relying on the model's judgement for an irreversible action, which is
  exactly the thing you are not supposed to do.
""")


# =============================================================================

PROBLEMS = {1: problem_1, 2: problem_2, 3: problem_3, 4: problem_4}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, choices=[1, 2, 3, 4])
    args = ap.parse_args()

    try:
        backend = connect()
    except ConnectionError as exc:
        print(f"\n\033[91m{exc}\033[0m\n")
        sys.exit(1)

    print()
    print(f"  backend  {backend.kind} at {backend.base}")
    print(f"  model    {backend.model_name}")
    print()
    print("  Running Lab 3's loop, unchanged, under four realistic conditions.")

    for n in ([args.only] if args.only else [1, 2, 3, 4]):
        PROBLEMS[n](backend)
        time.sleep(0.2)

    print("=" * 72)
    print("""
  Four problems, and not one of them is about AI:

      1. no audit trail            2. no spend control
      3. no fault tolerance        4. no authorisation

  Those are the same four problems as any service that calls a remote API.
  Your cloud background already has answers to all of them.

  A HARNESS is what you call the code that solves them once, so you never
  write them into a loop again.

  Next:  python step2_harnessed.py
""")
