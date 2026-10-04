#!/usr/bin/env python3
# =============================================================================
#  STEP 4 of 4  —  THE HUMAN GATE, AND A TEMPTING SHORTCUT
# =============================================================================
#
#  Step 3's loop works. It also deleted a file without asking anybody.
#
#  This file adds two things:
#
#    1. A human approval gate in front of anything destructive - and, more
#       interestingly, what happens when the human says no.
#
#    2. A switch to run the same task with ONE powerful tool instead of two
#       narrow ones, so you can compare the turn counts yourself.
#
#  Run it twice:
#
#      python step4_guardrails.py              # two narrow tools
#      python step4_guardrails.py --fat-tool   # one shell tool
#
#  Then compare the turn counts, and have the argument.
#
#  Run setup_sandbox.py before each run.
#
# =============================================================================

import json
import sys

import requests

import pi_tools

# --- scaffolding, not part of the lesson ------------------------------------

PAUSE = True
SERVER = "http://localhost:8080"
MAX_TURNS = 8

USE_FAT_TOOL = "--fat-tool" in sys.argv

# Tools we will not run without a human saying yes. Note this is a list WE
# keep, in our own code. The model has no say in what goes on it.
NEEDS_APPROVAL = ["delete_file", "run_command"]


def pause(note):
    print()
    print("    " + "-" * 66)
    if PAUSE:
        input("    >>> " + note + "   (press Enter to continue) ")
    else:
        print("    >>> " + note)
    print("    " + "-" * 66)
    print()


# =============================================================================
#  THE GATE
# =============================================================================
#  Three lines of logic. The interesting part is the `else`.

def ask_the_human(name, arguments):
    """Returns True to allow, False to refuse."""

    print()
    print("   " + "!" * 60)
    print("   THE AGENT WANTS TO RUN SOMETHING DESTRUCTIVE")
    print()
    print("      tool      : " + name)
    print("      arguments : " + json.dumps(arguments))
    print("   " + "!" * 60)
    print()

    answer = input("   Allow this? [y/N] ").strip().lower()
    return answer == "y"


# =============================================================================
#  SETUP
# =============================================================================

task = ("Log on to the Pi, go to my home directory, find all the .tmp files "
        "and delete the largest one if there is one.")

system_prompt = ("You are a careful assistant with access to a Raspberry Pi. "
                 "Use the tools rather than guessing. When the task is done, "
                 "say so in one sentence and stop calling tools.")

messages = []
messages.append({"role": "system", "content": system_prompt})
messages.append({"role": "user", "content": task})

tools = []
if USE_FAT_TOOL:
    tools.append(pi_tools.RUN_COMMAND_SCHEMA)
else:
    tools.append(pi_tools.LIST_FILES_SCHEMA)
    tools.append(pi_tools.DELETE_FILE_SCHEMA)

tokens_sent_total = 0
tools_run_total = 0
refusals = 0

print("TASK")
print("   " + task)
print()
print("TOOLS AVAILABLE TO THE MODEL")
for t in tools:
    print("   " + t["function"]["name"])
print()

if USE_FAT_TOOL:
    print("   \033[93mYou are running with ONE shell tool. Watch the turn count,")
    print("   and watch what it asks to run.\033[0m")
else:
    print("   Two narrow tools. Each one does exactly one thing.")

pause("Same loop as step 3, with a gate added at step 4 of the five.")


# =============================================================================
#  THE LOOP   —   identical to step 3 except for the marked block
# =============================================================================

final_answer = "(the loop ended without an answer)"

for turn in range(1, MAX_TURNS + 1):

    print("=" * 72)
    print("TURN", turn)
    print("=" * 72)

    body = {
        "model": "local-model",
        "messages": messages,
        "tools": tools,
        "temperature": 0.0,
        "max_tokens": 800,
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_budget": 0,
    }

    http_reply = requests.post(SERVER + "/v1/chat/completions", json=body, timeout=180)
    http_reply.raise_for_status()
    data = http_reply.json()

    tokens_sent_total = tokens_sent_total + data.get("usage", {}).get("prompt_tokens", 0)

    choice = data["choices"][0]
    reply = choice["message"]
    finish_reason = choice["finish_reason"]

    if reply.get("content"):
        print("   " + reply["content"].strip())

    if finish_reason != "tool_calls":
        final_answer = reply.get("content") or "(no answer given)"
        print()
        print("   no tool wanted - the loop ends.")
        break

    messages.append(reply)

    for tool_call in reply["tool_calls"]:

        name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        print("   -> " + name + "(" + json.dumps(arguments) + ")")

        # ================= THE ONLY NEW BLOCK IN THIS FILE =================

        if name in NEEDS_APPROVAL:
            allowed = ask_the_human(name, arguments)
        else:
            allowed = True

        if not allowed:
            # A refusal is just another tool result. We hand it back and let
            # the model deal with it. No exception, no crash, and the model
            # cannot go around us - this is the only path to the function.
            output = ("REFUSED by the human operator. The file was NOT deleted. "
                      "Do not try again; report that you could not complete "
                      "the task.")
            refusals = refusals + 1
            print("   <- " + output)

        else:
            function = pi_tools.DISPATCH.get(name)
            if function is None:
                output = "ERROR: no such tool: " + name
            else:
                output = function(**arguments)
            tools_run_total = tools_run_total + 1
            for line in output.splitlines()[:6]:
                print("   <- " + line)

        # ===================================================================

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": output,
        })

    print()
    print("   messages:", len(messages), "items     tokens sent:", tokens_sent_total)
    print()

else:
    print()
    print("   Hit the turn limit of", MAX_TURNS, "without finishing.")


# =============================================================================
#  THE TALLY
# =============================================================================

print()
print("=" * 72)
print("ANSWER")
print("=" * 72)
print()
for line in final_answer.strip().splitlines():
    print("   " + line)
print()
print("   mode          :", "ONE SHELL TOOL" if USE_FAT_TOOL else "two narrow tools")
print("   turns taken   :", turn)
print("   tools run     :", tools_run_total)
print("   refused       :", refusals)
print("   tokens sent   :", tokens_sent_total)

pause("Now run it the other way and compare these numbers.")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  TRY REFUSING. Run it again and answer N at the prompt. The model gets
#  "REFUSED" back as an ordinary tool result, and then has to deal with it -
#  it will normally report that it could not finish, and why. It does not
#  crash, and it does not find another way round, because there IS no other
#  way round. Our dispatch table is the only door.
#
#  THE FAT TOOL. Run with --fat-tool and compare. You will probably see the
#  whole task done in two turns instead of three, with something like:
#
#      run_command("cd ~ && ls -S *.tmp | head -1 | xargs rm -f")
#
#  Faster. Cheaper. Fewer moving parts. And you have just handed a language
#  model unrestricted shell access to a machine, where the difference between
#     rm -- one.tmp
#  and
#     rm -rf ~
#  is a typo it will make with complete confidence and no warning.
#
#  Ask the room: which version would you put on a machine that mattered?
#
#  Then notice what the narrow version bought you. The gate could never have
#  been written for the fat tool - "is this command destructive?" is not a
#  question you can answer by inspecting a string. With delete_file, it is one
#  line: `if name in NEEDS_APPROVAL`.
#
#      Narrow tools are a permissioning mechanism, not a limitation.
#
#  ONE MORE THING. Look at the glob the model chose. The sandbox contains
#  archive.tmp.bak, which is BIGGER than the largest real .tmp file. If the
#  model globbed '*tmp*' instead of '*.tmp' it would have deleted the wrong
#  file - and reported success, confidently, in good English.
#
#  That is the failure mode to be frightened of, and it is why lab 8 exists.
#
# =============================================================================

print()
print("Finished the walkthrough. Now open ../agent.py - the same loop, with a")
print("file workspace instead of a Pi, and three tools instead of two.")
print()
