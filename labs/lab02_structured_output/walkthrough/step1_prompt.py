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
request_body["max_tokens"] = 800

# --- turn the model's "thinking mode" off -----------------------------------
# Qwen 3.6 and models like it are HYBRID REASONING models. Left alone they
# write out a long internal monologue before answering - hundreds of tokens of
# "let me consider this carefully" - and only then produce the answer.
#
# That is useful for hard problems. For pulling three fields out of a ticket it
# is a waste of time and money, and if the monologue runs past max_tokens you
# get back nothing at all. These two lines switch it off. Different servers
# want different spellings, so we send both.

request_body["chat_template_kwargs"] = {"enable_thinking": False}
request_body["reasoning_budget"] = 0

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

# Why the model stopped. "stop" = it finished naturally. "length" = it hit our
# max_tokens cap and was cut off mid-sentence. Always worth checking.
finish_reason = first_choice.get("finish_reason")

print("Why the model stopped :", finish_reason)
print()

# Some servers put the model's internal monologue in its own field. If thinking
# was switched off this will be empty - but if it is NOT empty, that tells you
# the flags in section 3 did not take effect on this server.
thinking = message_object.get("reasoning_content")

if thinking:
    print("The model also produced", len(thinking), "characters of private")
    print("thinking, in a separate 'reasoning_content' field. Here is the start:")
    print()
    print("   " + repr(thinking[:160]) + " ...")
    print()
    print("That is its scratchpad, not its answer. It is NOT in 'content'.")
    print()

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

except json.JSONDecodeError as error:
    print("FAILED - that string was not valid JSON.")
    print()
    print("   Python said:", error)
    print()

    # There are three different ways this goes wrong, and they need three
    # different fixes. Work out which one we just hit.

    if finish_reason == "length":
        print("   DIAGNOSIS: truncation.")
        print("   finish_reason is 'length', so the model was cut off before it")
        print("   finished. Either max_tokens is too small, or thinking mode is")
        print("   still on and the monologue ate the whole budget.")
        print("   FIX: raise max_tokens, and check the two flags in section 3.")

    elif reply_text.strip() == "":
        print("   DIAGNOSIS: empty reply.")
        print("   The 'content' field came back blank. If 'reasoning_content'")
        print("   above was full, the model spent its whole turn thinking.")
        print("   FIX: the two flags in section 3 did not take on this server.")

    elif "{" in reply_text:
        print("   DIAGNOSIS: the JSON is in there, with something wrapped round it.")
        print("   A preamble like 'Here you go:', or ```json fences, or a cheery")
        print("   sign-off at the end. The model was HELPFUL, and the")
        print("   helpfulness broke our program.")
        print("   FIX: there isn't a good one. You can write string-trimming code")
        print("   and play whack-a-mole forever. Step 2 does something better.")

    else:
        print("   DIAGNOSIS: no JSON at all. The model answered in prose,")
        print("   or refused, or misunderstood the instruction entirely.")

else:
    print("SUCCESS - we now have real data:")
    print()
    print("   customer_name :", parsed["customer_name"])
    print("   company       :", parsed["company"])
    print("   severity      :", parsed["severity"])
    print()
    print("   It worked. Now ask the harder question: what MADE it work?")
    print("   Nothing did. We asked nicely and the model happened to oblige.")
    print("   Nothing in this program would have stopped it adding a preamble,")
    print("   or inventing a fourth key, or answering 'Urgent' instead of 'high'.")

pause("Run this file four or five times. Do you get the same thing every time?")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  We asked politely for JSON. On a big model, we probably got JSON.
#
#  If it worked, resist the urge to be pleased. Ask what MADE it work. Nothing
#  did. Nothing in this program could have stopped the model adding "Here you
#  go:" in front, or wrapping the answer in ```json fences, or inventing a
#  fourth key, or answering "Urgent" when the only options we gave it were
#  low, medium, high and critical.
#
#  It complied because it felt like it. That is not a guarantee, it is a
#  probability - and a probability will pass all your testing and then fail in
#  production at 3am, differently each time.
#
#  There is also a second failure we met in section 6: the model thinking at
#  such length that it never reaches the answer. We switched that off in
#  section 3, but notice what that means. We had to know about a quirk of this
#  particular family of models to get a reliable answer out of it at all.
#
#  Step 2 removes both problems at once, and does not rely on the model
#  feeling cooperative.
#
# =============================================================================

print()
print("Finished. Next:  python step2_schema.py")
print()
