#!/usr/bin/env python3
# =============================================================================
#  STEP 1 of 4  —  ONE TURN, BY HAND
# =============================================================================
#
#  The task:
#      "Log on to the Pi, go to my home directory, find all the .tmp files
#       and delete the largest one if there is one."
#
#  A human would do that in four steps at a terminal. We are going to find out
#  what it looks like when a model does it - and the first surprise is that it
#  is NOT four steps.
#
#  This file does exactly ONE turn and then stops. No loop. We want to see a
#  single complete exchange with nothing hidden.
#
#  Step through with F6 (Step Over).
#  Do not press F5 on the requests.post line - you'll land inside the HTTP
#  library. F7 gets you out if you do.
#
#  Run setup_sandbox.py first.
#
# =============================================================================

import json
import requests

import pi_tools          # our three tool functions. Read that file, then F6 past it.

# --- scaffolding, not part of the lesson ------------------------------------

PAUSE = True
SERVER = "http://localhost:8080"


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
#  SECTION 1  —  What the user asked for
# =============================================================================

task = ("Log on to the Pi, go to my home directory, find all the .tmp files "
        "and delete the largest one if there is one.")

print("THE TASK")
print()
print("   " + task)

pause("Four instructions, the way a person would say them. Hold that thought.")


# =============================================================================
#  SECTION 2  —  Two things the model will never do
# =============================================================================
#  Worth saying before we go any further, because the task wording is
#  misleading.
#
#  "Log on"  -  not a model action. OUR code opens the connection, with
#               credentials the model never sees. Look in pi_tools.py: PI_HOST
#               is in there, and it is never sent to the model.
#
#  "cd ~"    -  not a model action either. There is no shell session to change
#               directory IN. Every tool call is separate and independent, so
#               "home directory" is a PARAMETER, not a step.
#
#  So four human steps become two tool calls: list, then delete.

print("WHAT THE MODEL CAN ACTUALLY DO")
print()
print("   Two tools, and nothing else:")
print()
print("     list_files(directory, pattern)   -> names and sizes")
print("     delete_file(path)                -> deletes ONE file")
print()
print("   It cannot log in. It cannot cd. It cannot run a shell.")

pause("Open pi_tools.py and look at the two schemas near the bottom.")


# =============================================================================
#  SECTION 3  —  Build the message list
# =============================================================================
#  This list is the entire conversation. Right now it has one item in it.
#  By the end of step 2 it will have five. Watch it grow - that IS the agent.

system_prompt = ("You are a careful assistant with access to a Raspberry Pi. "
                 "Use the tools rather than guessing. When the task is done, "
                 "say so in one sentence and stop calling tools.")

system_message = {}
system_message["role"] = "system"
system_message["content"] = system_prompt

user_message = {}
user_message["role"] = "user"
user_message["content"] = task

messages = []
messages.append(system_message)
messages.append(user_message)

print("THE MESSAGE LIST  (" + str(len(messages)) + " items)")
print()
print(json.dumps(messages, indent=2))

pause("Two items. Remember that number.")


# =============================================================================
#  SECTION 4  —  Build the request
# =============================================================================

tools = []
tools.append(pi_tools.LIST_FILES_SCHEMA)
tools.append(pi_tools.DELETE_FILE_SCHEMA)

request_body = {}
request_body["model"] = "local-model"
request_body["messages"] = messages
request_body["tools"] = tools
request_body["temperature"] = 0.0
request_body["max_tokens"] = 800

# Thinking mode off - see lab 2's walkthrough for why this matters.
request_body["chat_template_kwargs"] = {"enable_thinking": False}
request_body["reasoning_budget"] = 0

print("WHAT WE ARE SENDING")
print()
print("   messages :", len(request_body["messages"]), "items")
print("   tools    :", len(request_body["tools"]), "schemas")
print()
print("   The tool schemas are", len(json.dumps(tools)), "characters.")
print("   They go over the wire on EVERY call. Remember that too.")

pause("Now send it. F6, not F5.")


# =============================================================================
#  SECTION 5  —  Send it
# =============================================================================

url = SERVER + "/v1/chat/completions"

print("Sending to " + url + " ...")

response = requests.post(url, json=request_body, timeout=180)

print("HTTP status:", response.status_code)

if response.status_code == 400:
    print()
    print("A 400 here almost always means llama-server was started without")
    print("--jinja, so it has no tool-calling template. Add it and restart.")
    raise SystemExit(1)

pause("Unpack it.")


# =============================================================================
#  SECTION 6  —  What came back
# =============================================================================

response_json = response.json()

choices_list = response_json["choices"]
first_choice = choices_list[0]
message_object = first_choice["message"]
finish_reason = first_choice["finish_reason"]

print("finish_reason :", repr(finish_reason))
print()

# This is the exit condition for the loop we have not written yet.
#   "tool_calls"  -> the model wants something run. Keep going.
#   "stop"        -> the model has finished. Stop.

if finish_reason == "tool_calls":
    print("   -> the model wants a tool run. The conversation is NOT over.")
else:
    print("   -> the model thinks it is done. (Unexpected this early.)")

print()
print("Anything in 'content'?", repr(message_object.get("content")))
print()
print("THE TOOL CALL")
print()
print(json.dumps(message_object["tool_calls"], indent=2))

pause("It asked for list_files. Look at the pattern it chose.")


# =============================================================================
#  SECTION 7  —  Run the tool   *** our decision, not the model's ***
# =============================================================================

tool_calls = message_object["tool_calls"]
first_call = tool_calls[0]

call_id = first_call["id"]                       # we must quote this back
called_function = first_call["function"]
function_name = called_function["name"]
arguments_text = called_function["arguments"]    # a STRING, not a dict
arguments = json.loads(arguments_text)

print("   name      :", function_name)
print("   arguments :", arguments)
print()

# The dispatch table. Nothing the model emitted can add an entry to this.
tool_function = pi_tools.DISPATCH.get(function_name)

if tool_function is None:
    tool_output = "ERROR: no such tool: " + function_name
else:
    tool_output = tool_function(**arguments)

print("WHAT THE TOOL RETURNED")
print()
for line in tool_output.splitlines():
    print("   " + line)

pause("The model has not seen any of that yet. It is just sitting in a variable.")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  One turn. One tool call. We ran it. And now we are stuck.
#
#  The model asked what files were there. We found out. But the model does not
#  know what we found out, because the API is stateless - our reply went out,
#  its answer came back, and the connection closed. Nothing persists.
#
#  If we want it to pick the largest file, we have to send the conversation
#  AGAIN, with this result added to the end.
#
#  That is step 2. And once you have done it twice by hand, you will see why
#  step 3 is a while-loop.
#
# =============================================================================

print()
print("Finished one turn. We now hold a result the model has never seen.")
print()
print("Next:  python step2_by_hand.py")
print()
