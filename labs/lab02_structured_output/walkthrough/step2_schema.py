#!/usr/bin/env python3
# =============================================================================
#  STEP 2 of 3  —  MAKING MALFORMED JSON IMPOSSIBLE
# =============================================================================
#
#  Step 1 asked the model nicely for JSON. This one does not ask.
#
#  Same model. Same ticket. Same server. One thing changes: we send a SCHEMA
#  describing the shape we want, and the server uses it to constrain what the
#  model is physically able to produce.
#
#  Step through with F6 again. The new material is Section 3, where we build
#  the schema one field at a time - watch it assemble in the Variables pane.
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
#  SECTION 1  —  The same ticket as before
# =============================================================================

ticket_text = (
    "Hi, this is Dervla Nolan from Aurora Freight. Our API integration "
    "started returning 502s at about 14:30 yesterday. It's blocking our "
    "overnight customs filing so it's pretty urgent."
)

print("THE TICKET (identical to step 1)")
print()
print(ticket_text)

pause("Nothing new yet. The change is in how we ask.")


# =============================================================================
#  SECTION 2  —  A much shorter instruction
# =============================================================================
#  Notice what is MISSING compared to step 1. We are not begging for JSON any
#  more. We are not listing the keys. We are not saying "no code fences".
#  The schema will do all of that, and it will do it properly.

prompt = "Parse this support ticket:\n\n" + ticket_text

print("THE PROMPT")
print()
print(prompt)

pause("Much shorter. So where did the field names go? Next section.")


# =============================================================================
#  SECTION 3  —  Build the schema   *** THIS IS THE NEW IDEA ***
# =============================================================================
#  A JSON Schema is just a dictionary that describes the shape of other data.
#  We build it in small pieces so you can see exactly what it is made of.

# --- first, describe each field on its own ---

field_customer_name = {}
field_customer_name["type"] = "string"
field_customer_name["description"] = "The person who wrote in"

field_company = {}
field_company["type"] = "string"
field_company["description"] = "The organisation they belong to"

field_severity = {}
field_severity["type"] = "string"
field_severity["enum"] = ["low", "medium", "high", "critical"]
field_severity["description"] = "How bad the actual impact is"

# The "enum" line above is the interesting one. It does not say "please choose
# from these". It says these are the ONLY values that exist. The model will not
# be able to emit anything else - not "Urgent", not "HIGH", not "very high".

# --- then collect them together ---

all_fields = {}
all_fields["customer_name"] = field_customer_name
all_fields["company"] = field_company
all_fields["severity"] = field_severity

# --- then wrap that into a complete schema ---

schema = {}
schema["type"] = "object"
schema["properties"] = all_fields
schema["required"] = ["customer_name", "company", "severity"]

print("THE SCHEMA WE JUST BUILT")
print()
print(json.dumps(schema, indent=2))

pause("That dictionary is a description of a shape. Now we attach it.")


# =============================================================================
#  SECTION 4  —  Build the request, with the schema attached
# =============================================================================

user_message = {}
user_message["role"] = "user"
user_message["content"] = prompt

messages_list = []
messages_list.append(user_message)

# The schema goes inside a "response_format" wrapper. The nesting looks fussy
# but it is just the shape the API expects.

schema_wrapper = {}
schema_wrapper["name"] = "ticket"
schema_wrapper["strict"] = True
schema_wrapper["schema"] = schema

response_format = {}
response_format["type"] = "json_schema"
response_format["json_schema"] = schema_wrapper

# Now the request body. Same as step 1, plus one extra key.

request_body = {}
request_body["model"] = "local-model"
request_body["messages"] = messages_list
request_body["temperature"] = 0.0
request_body["max_tokens"] = 300
request_body["response_format"] = response_format      # <-- the only difference

print("THE REQUEST BODY")
print()
print(json.dumps(request_body, indent=2))

pause("Compare this to step 1. One extra key. That is the whole change.")


# =============================================================================
#  SECTION 5  —  Send it
# =============================================================================

url = SERVER + "/v1/chat/completions"

print("Sending to " + url + " ...")

response = requests.post(url, json=request_body, timeout=120)

print("HTTP status code:", response.status_code)

if response.status_code == 400:
    print()
    print("A 400 here usually means this llama.cpp build wants a different")
    print("shape. Try replacing the response_format block in Section 4 with:")
    print()
    print('    response_format = {"type": "json_object", "schema": schema}')
    print()
    print("Then run it again. See BRIEFING.md for why builds differ.")

pause("Now unpack it exactly as before.")


# =============================================================================
#  SECTION 6  —  Unpack, one layer at a time
# =============================================================================

response_json = response.json()

choices_list = response_json["choices"]
first_choice = choices_list[0]
message_object = first_choice["message"]
reply_text = message_object["content"]

print("THE TEXT THE MODEL PRODUCED")
print()
print(repr(reply_text))

pause("Compare that with step 1. Any preamble? Any code fences?")


# =============================================================================
#  SECTION 7  —  Parse it
# =============================================================================

print("Attempting json.loads() ...")
print()

parsed = json.loads(reply_text)

print("SUCCESS - and this time it was never in doubt:")
print()
print("   customer_name :", parsed["customer_name"])
print("   company       :", parsed["company"])
print("   severity      :", parsed["severity"])

pause("Notice there is no try/except here. Why did we not need one?")


# =============================================================================
#  WHAT TO TAKE AWAY
# =============================================================================
#
#  The server turned our schema into a GRAMMAR. As the model picks each word,
#  any word that would break the schema is removed from the choices before it
#  chooses. It is not being obedient. It is physically unable to do otherwise.
#
#  That is why step 1 needed a try/except and this one does not.
#
#  BUT - and this is the sentence to remember from the whole lab:
#
#      A grammar guarantees SHAPE. It guarantees nothing about TRUTH.
#
#  Try this: edit the ticket in Section 1 so the customer signs off as someone
#  else entirely, or mentions a second company. The answer will still be
#  perfectly formed JSON. It may well be wrong.
#
#  A malformed answer is an outage - you find out in minutes.
#  A well-formed wrong answer is a data quality incident you discover in three
#  months, by which time it is in every report you have sent.
#
# =============================================================================

print()
print("Finished. Next:  python step3_tools.py")
print()
