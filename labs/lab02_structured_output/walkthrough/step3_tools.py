#!/usr/bin/env python3
# =============================================================================
#  STEP 3 of 3  —  THE MODEL ASKS US TO CALL A FUNCTION
# =============================================================================
#
#  Same ticket again. Same three fields. But this time we do not ask for data
#  at all - we describe a FUNCTION, and let the model ask us to call it.
#
#  That sounds like a pointless detour for an extraction job, and for this job
#  it slightly is. Stay with it anyway, because this is the mechanism that
#  tomorrow's agent is built out of. Everything in Lab 3 is this, in a loop.
#
#  Step through with F6. The new material is in Section 3 (describing a
#  function) and Section 6 (the answer arrives somewhere different).
#
# =============================================================================

import json
import requests

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
#  SECTION 1  —  The same ticket, for the third and last time
# =============================================================================

ticket_text = (
    "Hi, this is Dervla Nolan from Aurora Freight. Our API integration "
    "started returning 502s at about 14:30 yesterday. It's blocking our "
    "overnight customs filing so it's pretty urgent."
)

prompt = "Parse this support ticket:\n\n" + ticket_text

print("THE PROMPT (same as step 2)")
print()
print(prompt)

pause("Identical so far. The change is what we send alongside it.")


# =============================================================================
#  SECTION 2  —  The same schema as step 2
# =============================================================================
#  Nothing new here - we are reusing step 2's work. Skim it and move on.

field_customer_name = {"type": "string", "description": "The person who wrote in"}
field_company = {"type": "string", "description": "The organisation they belong to"}
field_severity = {
    "type": "string",
    "enum": ["low", "medium", "high", "critical"],
    "description": "How bad the actual impact is",
}

all_fields = {}
all_fields["customer_name"] = field_customer_name
all_fields["company"] = field_company
all_fields["severity"] = field_severity

schema = {}
schema["type"] = "object"
schema["properties"] = all_fields
schema["required"] = ["customer_name", "company", "severity"]

print("THE SCHEMA (unchanged from step 2)")
print()
print(json.dumps(schema, indent=2))

pause("Now we wrap it up as a function instead of a response format.")


# =============================================================================
#  SECTION 3  —  Describe a function   *** THIS IS THE NEW IDEA ***
# =============================================================================
#  We are about to tell the model: "there is a function called record_ticket.
#  Here is what it does, and here are the arguments it takes."
#
#  We are NOT giving it any code. There is no record_ticket function anywhere
#  in this file. The model never sees an implementation and never runs one.

function_description = {}
function_description["name"] = "record_ticket"
function_description["description"] = "Record a parsed support ticket in the tracking system."
function_description["parameters"] = schema        # the schema becomes the arguments

tool = {}
tool["type"] = "function"
tool["function"] = function_description

tools_list = []
tools_list.append(tool)

print("THE TOOL DEFINITION")
print()
print(json.dumps(tools_list, indent=2))

pause("Read the 'description' line again. That sentence is doing real work.")


# =============================================================================
#  SECTION 4  —  Build the request
# =============================================================================

user_message = {}
user_message["role"] = "user"
user_message["content"] = prompt

messages_list = []
messages_list.append(user_message)

request_body = {}
request_body["model"] = "local-model"
request_body["messages"] = messages_list
request_body["temperature"] = 0.0
request_body["max_tokens"] = 300
request_body["tools"] = tools_list          # <-- instead of response_format

print("THE REQUEST BODY")
print()
print(json.dumps(request_body, indent=2))

pause("Step 2 sent 'response_format'. This sends 'tools'. That is the change.")


# =============================================================================
#  SECTION 5  —  Send it
# =============================================================================

url = SERVER + "/v1/chat/completions"

print("Sending to " + url + " ...")

response = requests.post(url, json=request_body, timeout=120)

print("HTTP status code:", response.status_code)

if response.status_code == 400:
    print()
    print("A 400 here usually means the server was started without --jinja,")
    print("or this model has no tool template. Steps 1 and 2 still work.")

pause("Now the interesting part - where did the answer go?")


# =============================================================================
#  SECTION 6  —  The answer is NOT where it was before
# =============================================================================

response_json = response.json()

print("THE WHOLE REPLY")
print()
print(json.dumps(response_json, indent=2))
print()

choices_list = response_json["choices"]
first_choice = choices_list[0]
message_object = first_choice["message"]

# In steps 1 and 2 we read message["content"] here. Look what is in it now:

content_field = message_object.get("content")

print("message['content'] is:", repr(content_field))
print()
print("Empty, or nearly. The model did not write us a reply.")

pause("So where is the answer? In a different field entirely.")


# =============================================================================
#  SECTION 7  —  Dig out the tool call
# =============================================================================

tool_calls_list = message_object["tool_calls"]     # a list - it can ask for several
first_tool_call = tool_calls_list[0]

print("THE TOOL CALL THE MODEL MADE")
print()
print(json.dumps(first_tool_call, indent=2))
print()

called_function = first_tool_call["function"]
function_name = called_function["name"]
arguments_text = called_function["arguments"]

print("It wants us to call :", function_name)
print("With arguments      :", repr(arguments_text))
print()
print("Note the quotes. The arguments arrive as a STRING, not a dictionary.")

pause("One more parse to go.")


# =============================================================================
#  SECTION 8  —  Parse the arguments
# =============================================================================

arguments = json.loads(arguments_text)

print("AFTER json.loads():")
print()
print("   customer_name :", arguments["customer_name"])
print("   company       :", arguments["company"])
print("   severity      :", arguments["severity"])

pause("Same three values as step 2. Delivered a completely different way.")


# =============================================================================
#  SECTION 9  —  The bit that matters for tomorrow
# =============================================================================
#  The model asked us to call record_ticket. So... do we?
#
#  That is entirely our decision. Nothing has happened yet. Nothing will
#  happen unless we write the code to make it happen. Watch:

print("The model has REQUESTED that record_ticket be called.")
print()
print("Nothing has run. There is no record_ticket function in this file.")
print("If we want something to happen, we have to do it ourselves:")
print()

if function_name == "record_ticket":
    print("   >>> pretending to save to the database:")
    print("       INSERT INTO tickets VALUES (")
    print("           '" + arguments["customer_name"] + "',")
    print("           '" + arguments["company"] + "',")
    print("           '" + arguments["severity"] + "')")
else:
    print("   >>> unknown function requested, refusing:", function_name)

pause("Read that if-statement again. It is the most important line all weekend.")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  Three ways to get the same three fields:
#
#    Step 1  ask in the prompt      -> usually works, fails unpredictably
#    Step 2  send a schema          -> cannot produce malformed output
#    Step 3  describe a function    -> the model REQUESTS an action
#
#  For pulling fields out of a ticket, step 2 is the sensible choice and step
#  3 is overkill. So why did we do it?
#
#  Because of that if-statement in Section 9.
#
#  The model did not read our database. It did not write to it. It could not,
#  no matter what the ticket said. It emitted a name and some arguments, and
#  OUR code decided what to do about it.
#
#  Now imagine that instead of pretending to save a row, we really did the
#  thing - and then sent the result back to the model, and asked it what to do
#  next. And again. And again, until it stopped asking.
#
#  That loop is tomorrow. That loop is what "agent" means. And you have now
#  seen every moving part of it.
#
#      The model chooses. Your code executes.
#
# =============================================================================

print()
print("Finished all three steps.")
print()
print("Now open structured_local.py - the real version. It does all three of")
print("these across several tickets and counts how often each one gets the")
print("answer RIGHT, which turns out to be a very different question.")
print()
