#!/usr/bin/env python3
# =============================================================================
#  STEP 3 of 3  —  THE PART THAT MAKES IT INFRASTRUCTURE
# =============================================================================
#
#  Steps 1 and 2 were an on-call task on a server. This file is a completely
#  different job - reading datasets and writing a report - with completely
#  different tools.
#
#  Count the lines of loop code below. There are none. Not one message list,
#  not one tool_calls check, not one json.loads. The harness did not need to
#  know anything about this task existing.
#
#  THAT is the difference between a script and infrastructure: a script
#  solves your problem, infrastructure solves the next one too.
#
#      python setup_sandbox.py      # first
#      python step3_reuse_it.py
#      python step3_reuse_it.py --unattended    # nobody to ask
#
# =============================================================================

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from local_backend import connect  # noqa: E402

import tools  # noqa: E402
from harness import Budget, Harness, Policy, Registry  # noqa: E402

LOG = Path(__file__).parent / "runs.jsonl"
UNATTENDED = "--unattended" in sys.argv

SYSTEM = ("You are a data analyst with access to a small set of CSV datasets. "
          "Use the tools rather than guessing at numbers. When the task is "
          "done, say so and stop calling tools.")

TASK = ("Look at what datasets are available, read the sales one, and write "
        "me a short summary report as summary.md covering the total revenue "
        "and which region did best.")


def ask_operator(name, arguments):
    preview = json.dumps(arguments)
    if len(preview) > 90:
        preview = preview[:90] + " ...]"
    print()
    print(f"    \033[93m? {name}({preview})\033[0m")
    return input("      allow? [y/N] ").strip().lower() == "y"


def live(event):
    kind, turn = event["kind"], event.get("turn", 0)
    if kind == "model_reply":
        wants = event.get("wants") or []
        print(f"    turn {turn}  model  {event['tokens_in']:>5} in   "
              f"{'wants ' + ','.join(wants) if wants else 'done'}")
    elif kind == "policy" and event["verdict"] != "allow":
        print(f"    turn {turn}  \033[93mpolicy {event['verdict']} on "
              f"{event['tool']}\033[0m")
    elif kind == "tool_ok":
        print(f"    turn {turn}  ran    {event['tool']}  "
              f"\033[90m{event['chars']} chars\033[0m")


if __name__ == "__main__":
    try:
        backend = connect()
    except ConnectionError as exc:
        print(f"\n\033[91m{exc}\033[0m\n")
        sys.exit(1)

    if not (Path(__file__).parent / "sandbox").exists():
        print("\n  No sandbox. Run: python setup_sandbox.py\n")
        sys.exit(1)

    # ---------------------------------------------------------------------
    #  THE WHOLE OF THE NEW CODE. A different registry, a different system
    #  prompt, a different policy. No loop.
    # ---------------------------------------------------------------------

    harness = Harness(
        backend=backend,
        registry=Registry(tools.REPORT_TOOLS),        # <- different tools
        system=SYSTEM,                                 # <- different prompt
        policy=Policy(
            # Unattended: writing a file is fine, but nothing else destructive.
            mode="deny-destructive" if UNATTENDED else "ask",
            always_allow=["write_report"] if UNATTENDED else [],
        ),
        budget=Budget(max_tokens=40_000),
        max_turns=10,
        log_path=LOG,
        approve=(lambda n, a: True) if UNATTENDED else ask_operator,
        on_event=live,
    )

    run = harness.run(TASK)

    # ---------------------------------------------------------------------

    print()
    print("  ANSWER")
    for line in (run.answer or "(none)").splitlines():
        print("    " + line)
    print()
    print("  " + run.summary())

    report = Path(__file__).parent / "sandbox" / "summary.md"
    if report.exists():
        print()
        print(f"  It wrote {report.name}:")
        print("  " + "-" * 60)
        for line in report.read_text().splitlines()[:12]:
            print("    " + line)
        print("  " + "-" * 60)

    print("""
  \033[93mNow go back and read this file.\033[0m

  Count the lines that deal with the loop. Message lists, tool_calls checks,
  json.loads on the arguments, appending results in the right order, the
  turn limit, the retries, the token accounting, the audit log.

  There are none. You wrote a registry, a system prompt and a policy. The
  harness had never heard of datasets or reports and did not need to.

  That is the test for whether you have built infrastructure or just
  refactored a script: can someone solve a problem you never thought about,
  without opening your file?

  \033[93mTry:\033[0m  python step3_reuse_it.py --unattended
  Same task with nobody to ask. The policy changes, nothing else does.
""")
