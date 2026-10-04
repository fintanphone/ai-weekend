#!/usr/bin/env python3
# =============================================================================
#  STEP 2 of 4  —  THE WHOLE TASK, BY HAND
# =============================================================================
#
#  Step 1 did one turn and got stuck holding a result the model had never seen.
#  This file finishes the job - by writing out every turn longhand.
#
#  THIS CODE IS DELIBERATELY REPETITIVE. Three nearly-identical blocks. That is
#  the entire point of the file. By turn three you should be slightly annoyed,
#  and that annoyance is the thing step 3 fixes.
#
#  Step through with F6. Watch two numbers the whole way:
#     - how many items are in `messages`
#     - how many tokens we have sent in total
#
#  Run setup_sandbox.py first (again, if step 1 deleted something).
#
# =============================================================================

import json
import requests

import pi_tools

# --- scaffolding, not part of the lesson ------------------------------------

PAUSE = True
SERVER = "http://localhost:8080"

tokens_sent_total = 0          # we'll add these up as we go


def pause(note):
    print()
    print("    " + "-" * 66)
    if PAUSE:
        input("    >>> " + note + "   (press Enter to continue) ")
    else:
        print("    >>> " + note)
    print("    " + "-" * 66)
    print()


def ask_model(messages, tools):
    """One request to the model. This is exactly the code you stepped through
    in step 1, sections 4 to 6, wrapped up. F6 over it - you've seen inside."""

    global tokens_sent_total

    body = {
        "model": "local-model",
        "messages": messages,
        "tools": tools,
        "temperature": 0.0,
        "max_tokens": 800,
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_budget": 0,
    }

    reply = requests.post(SERVER + "/v1/chat/completions", json=body, timeout=180)
    reply.raise_for_status()
    data = reply.json()

    used = data.get("usage", {}).get("prompt_tokens", 0)
    tokens_sent_total = tokens_sent_total + used

    choice = data["choices"][0]
    return choice["message"], choice["finish_reason"], used


def run_one_tool(tool_call):
    """Execute one tool the model asked for, and build the result message."""

    call_id = tool_call["id"]
    name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    print("   -> " + name + "(" + json.dumps(arguments) + ")")

    function = pi_tools.DISPATCH.get(name)
    if function is None:
        output = "ERROR: no such tool: " + name
    else:
        output = function(**arguments)

    for line in output.splitlines():
        print("   <- " + line)

    # In the OpenAI message format a tool result is its own message, with the
    # role "tool", quoting back the id we were given.
    result_message = {}
    result_message["role"] = "tool"
    result_message["tool_call_id"] = call_id
    result_message["content"] = output

    return result_message


# =============================================================================
#  SETUP  —  the same starting point as step 1
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

print("STARTING POINT")
print("   messages:", len(messages), "items     tokens sent so far:", tokens_sent_total)

pause("Now turn 1, written out longhand.")


# =============================================================================
#  TURN 1
# =============================================================================

print("=" * 72)
print("TURN 1")
print("=" * 72)
print()

reply_1, finish_1 = ask_model(messages, tools)[:2]

print("finish_reason:", repr(finish_1))
if reply_1.get("content"):
    print()
    print("   model says: " + reply_1["content"].strip())
print()

# Append the model's own turn. If we skip this, the next call has no idea it
# ever asked for anything.
messages.append(reply_1)

# Run what it asked for, and append the result.
for tool_call in reply_1["tool_calls"]:
    messages.append(run_one_tool(tool_call))

print()
print("   messages:", len(messages), "items     tokens sent so far:", tokens_sent_total)

pause("The model now knows what files exist. Turn 2 is the same code again.")


# =============================================================================
#  TURN 2   —   note how little of this is new
# =============================================================================

print("=" * 72)
print("TURN 2")
print("=" * 72)
print()

reply_2, finish_2 = ask_model(messages, tools)[:2]

print("finish_reason:", repr(finish_2))
if reply_2.get("content"):
    print()
    print("   model says: " + reply_2["content"].strip())
print()

messages.append(reply_2)

if finish_2 == "tool_calls":
    for tool_call in reply_2["tool_calls"]:
        messages.append(run_one_tool(tool_call))

print()
print("   messages:", len(messages), "items     tokens sent so far:", tokens_sent_total)

pause("It compared the sizes itself. No tool for that - it just did the maths.")


# =============================================================================
#  TURN 3   —   identical code for the third time
# =============================================================================

print("=" * 72)
print("TURN 3")
print("=" * 72)
print()

reply_3, finish_3 = ask_model(messages, tools)[:2]

print("finish_reason:", repr(finish_3))
print()

if finish_3 == "tool_calls":
    print("   It wants ANOTHER tool. We would need a turn 4. And maybe a 5.")
    messages.append(reply_3)
    for tool_call in reply_3["tool_calls"]:
        messages.append(run_one_tool(tool_call))
else:
    print("   THE ANSWER:")
    print()
    for line in reply_3["content"].strip().splitlines():
        print("   " + line)

print()
print("   messages:", len(messages), "items     tokens sent so far:", tokens_sent_total)

pause("finish_reason is 'stop'. No tool asked for. That is how we know to stop.")


# =============================================================================
#  THE TALLY
# =============================================================================

print("=" * 72)
print("THE TALLY")
print("=" * 72)
print()
print("   model calls       : 3")
print("   tools actually run: 2")
print("   results fed back  : 2")
print()
print("   The rule: model calls = tool calls + 1.")
print("   The extra one is the model writing its answer.")
print()
print("   total tokens SENT :", tokens_sent_total)
print()
print("   The task contained maybe 500 tokens of real information. We sent")
print("   " + str(tokens_sent_total) + ". The two tool schemas went over the wire three times.")
print("   So did the original question. Nothing is remembered between calls,")
print("   so everything is resent, every time.")

pause("Now look back at the three TURN blocks in this file.")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  Read turns 1, 2 and 3 again. They are the same code:
#
#      reply = ask_model(messages, tools)
#      if the model asked for nothing:  we are done
#      append its turn to messages
#      run what it asked for
#      append the results to messages
#      go round again
#
#  We wrote that three times because we did not know in advance how many turns
#  the task would take. And we still don't - turn 3 had an "if" in case it
#  wanted a fourth.
#
#  You cannot write this out longhand in general. You have to let it repeat
#  until the model stops asking.
#
#  Which is a while-loop. That's step 3, and it is fifteen lines.
#
# =============================================================================

print()
print("Next:  python step3_the_loop.py")
print()
