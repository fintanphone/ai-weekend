#!/usr/bin/env python3
# =============================================================================
#  STEP 3 of 4  —  THE SAME THING, AS A LOOP
# =============================================================================
#
#  Step 2 wrote out three nearly-identical turns and ended with an "if" in case
#  a fourth was needed. This file replaces all of that with a while-loop.
#
#  Nothing new happens here. No new idea, no new API, no new tool. The only
#  change is that the repetition is written once instead of three times.
#
#  THAT IS THE WHOLE LESSON OF LAB 3. An agent is a while-loop around a model
#  that can call functions. You have now built one by hand and watched it
#  collapse into fifteen lines.
#
#  Step through with F6. Go round the loop more than once - put a breakpoint on
#  the `for turn in range(...)` line and press F8 to come back to it each time.
#
#  Run setup_sandbox.py first.
#
# =============================================================================

import json
import requests

import pi_tools

# --- scaffolding, not part of the lesson ------------------------------------

PAUSE = True
SERVER = "http://localhost:8080"
MAX_TURNS = 8               # the circuit breaker. See the note at the bottom.


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
tools.append(pi_tools.LIST_FILES_SCHEMA)
tools.append(pi_tools.DELETE_FILE_SCHEMA)

tokens_sent_total = 0
tools_run_total = 0

print("TASK")
print("   " + task)
print()

pause("Here comes the loop. Put a breakpoint on the 'for turn' line.")


# =============================================================================
#  THE LOOP   *** this is the whole of lab 3 ***
# =============================================================================

final_answer = "(the loop ended without an answer)"

for turn in range(1, MAX_TURNS + 1):

    print("=" * 72)
    print("TURN", turn)
    print("=" * 72)

    # ---- 1. ask the model, sending the ENTIRE conversation every time ------

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

    # ---- 2. did it ask for a tool? if not, we are finished -----------------

    if finish_reason != "tool_calls":
        final_answer = reply.get("content") or "(no answer given)"
        print()
        print("   finish_reason is", repr(finish_reason), "- no tool wanted - the loop ends.")
        break

    # ---- 3. append the model's own turn -----------------------------------
    #  Miss this and the next request has no idea it ever asked for anything.

    messages.append(reply)

    # ---- 4. run every tool it asked for, append every result ---------------
    #  EVERY requested call must get a result back, even a failed one, or the
    #  next request is rejected. This is the most common bug people hit.

    for tool_call in reply["tool_calls"]:

        name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        print("   -> " + name + "(" + json.dumps(arguments) + ")")

        function = pi_tools.DISPATCH.get(name)
        if function is None:
            output = "ERROR: no such tool: " + name
        else:
            output = function(**arguments)

        tools_run_total = tools_run_total + 1

        for line in output.splitlines()[:6]:
            print("   <- " + line)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": output,
        })

    # ---- 5. round we go again ---------------------------------------------

    print()
    print("   messages:", len(messages), "items     tokens sent:", tokens_sent_total)
    print()

else:
    print()
    print("   Hit the turn limit of", MAX_TURNS, "without finishing.")


# =============================================================================
#  DONE
# =============================================================================

print()
print("=" * 72)
print("ANSWER")
print("=" * 72)
print()
for line in final_answer.strip().splitlines():
    print("   " + line)
print()
print("   turns taken   :", turn)
print("   tools run     :", tools_run_total)
print("   tokens sent   :", tokens_sent_total)
print("   final messages:", len(messages))

pause("Scroll up. Count the lines in the loop. It is about fifteen.")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  Five steps, repeated until the model stops asking:
#
#      1. call the model with the whole conversation
#      2. if it did not ask for a tool, we are done
#      3. append its turn
#      4. run what it asked for, append the results
#      5. go round again
#
#  That is an agent. Everything else you will read about this year - planning,
#  memory, reflection, multi-agent, whatever the vocabulary is next month - is
#  a variation on those five steps.
#
#  THE TURN LIMIT is not decoration. Without it, a model that keeps asking for
#  tools loops forever, and every lap costs money and does real things to real
#  machines. It is the only circuit breaker in the whole design. Try setting
#  MAX_TURNS to 1 and watch what a truncated agent does.
#
#  WORTH NOTICING: the model never once wrote a plan. We did not ask it to
#  list steps, and there is no branch in this file that says "if the task
#  mentions deleting, call delete_file". It worked out what to do, in order,
#  from two tool descriptions and a sentence.
#
#  Step 4 adds the one thing this loop is missing before you'd let it near a
#  real machine.
#
# =============================================================================

print()
print("Next:  python step4_guardrails.py")
print()
