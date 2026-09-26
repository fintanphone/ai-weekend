#!/usr/bin/env python3
# =============================================================================
#  STEP 1 of 3  —  ASKING FOR JSON IN THE PROMPT
# =============================================================================
#
#  This is the simplest possible version of "Method A" from Lab 2.
#
#  Run it in a debugger and step through with F6 (Step Over).
#  Watch the Variables pane on the left: every line below creates exactly one
#  new variable, so you can see the request being built piece by piece.
#
#  WARNING: do not press F5 (Step Into) on the requests.post line. You will
#  end up inside the HTTP library and it is a long way back. F6 only.
#
#  What we are doing: taking a messy support ticket written by a human, and
#  asking the model to hand it back as data our program can use.
#
# =============================================================================

import json
import requests

# --- scaffolding, not part of the lesson ------------------------------------
# This just stops the script between sections so you can read the output.
# If you are stepping in a debugger you can set PAUSE = False.

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
#  SECTION 1  —  The raw material
# =============================================================================
#  A support ticket, exactly as a customer typed it. Messy, human, no structure.

ticket_text = (
    "Hi, this is Dervla Nolan from Aurora Freight. Our API integration "
    "started returning 502s at about 14:30 yesterday. It's blocking our "
    "overnight customs filing so it's pretty urgent."
)

print("THE TICKET AS THE CUSTOMER WROTE IT")
print()
print(ticket_text)

pause("That is the input. It is just a string. Now we wrap instructions round it.")


# =============================================================================
#  SECTION 2  —  Build the instruction
# =============================================================================
#  We want three specific fields back, and we want them as JSON.
#  So we write that down in English and glue the ticket on the end.

instruction = (
    "Extract the details from this support ticket.\n"
    "\n"
    "Return ONLY a JSON object with these three keys:\n"
    "  customer_name  - the person who wrote in\n"
    "  company        - the organisation they belong to\n"
    "  severity       - one of: low, medium, high, critical\n"
    "\n"
    "No explanation. No code fences. Just the JSON.\n"
)

prompt = instruction + "\nTicket:\n" + ticket_text

print("THE FULL TEXT WE ARE ABOUT TO SEND TO THE MODEL")
print()
print(prompt)

pause("This whole string is the input. The model sees nothing else.")


# =============================================================================
#  SECTION 3  —  Build the request
# =============================================================================
#  The model lives behind an HTTP API, so we have to describe our request as
#  a dictionary. We will build it one key at a time so you can watch it grow.

# A conversation is a list of messages. Ours has exactly one message in it.
user_message = {}
user_message["role"] = "user"
user_message["content"] = prompt

messages_list = []
messages_list.append(user_message)

# Now the request body itself.
request_body = {}
request_body["model"] = "local-model"      # llama.cpp ignores this, but the API wants it
request_body["messages"] = messages_list
request_body["temperature"] = 0.0          # 0.0 = as predictable as possible
request_body["max_tokens"] = 300

print("THE REQUEST BODY, AS JSON")
print()
print(json.dumps(request_body, indent=2))

pause("That dictionary is literally what travels over the network.")


# =============================================================================
#  SECTION 4  —  Send it
# =============================================================================
#  F6 over this next line. It takes a second or two - the model is thinking.

url = SERVER + "/v1/chat/completions"

print("Sending to " + url + " ...")

response = requests.post(url, json=request_body, timeout=120)

print("HTTP status code:", response.status_code)     # 200 means it worked

pause("We have a response object. Now we dig the answer out of it.")


# =============================================================================
#  SECTION 5  —  Unpack the response, one layer at a time
# =============================================================================
#  The reply is a nested structure. You could get the text in one long line,
#  but then four things happen at once and you cannot see any of them.
#  So we do it one layer per line. Watch the Variables pane.

response_json = response.json()

print("THE WHOLE REPLY")
print()
print(json.dumps(response_json, indent=2))
print()

choices_list = response_json["choices"]      # a list of possible answers
first_choice = choices_list[0]               # we only asked for one
message_object = first_choice["message"]     # the assistant's message
reply_text = message_object["content"]       # the actual words

print("JUST THE TEXT THE MODEL PRODUCED")
print()
print(repr(reply_text))                      # repr() shows hidden characters

pause("Look closely. Is that clean JSON, or is there something round it?")


# =============================================================================
#  SECTION 6  —  Try to turn the text into data
# =============================================================================
#  This is the moment of truth. json.loads() turns a string into a dictionary,
#  but ONLY if the string is valid JSON. Anything else and it raises an error.

print("Attempting json.loads() ...")
print()

parsed = None

try:
    parsed = json.loads(reply_text)
    print("SUCCESS - we now have real data:")
    print()
    print("   customer_name :", parsed["customer_name"])
    print("   company       :", parsed["company"])
    print("   severity      :", parsed["severity"])

except json.JSONDecodeError as error:
    print("FAILED - that string was not valid JSON.")
    print()
    print("   Python said:", error)
    print()
    print("   This is the whole problem with Method A. The model was helpful")
    print("   in a way that broke our program.")

pause("Run this file a few more times. Do you always get the same result?")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  We asked politely for JSON and we probably got JSON.
#
#  But nothing FORCED it. The model could have added "Here you go:" in front.
#  It could have wrapped the answer in ```json fences. It could have invented
#  a fourth key, or used "Urgent" when we said the only options were low,
#  medium, high and critical.
#
#  And the failures are different every run - which is far worse than a bug
#  that happens every time, because it will pass all your testing and then
#  fail in production at 3am.
#
#  Step 2 shows what to do about it.
#
# =============================================================================

print()
print("Finished. Next:  python step2_schema.py")
print()
