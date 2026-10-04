# Walkthrough — three small programs before the real lab

**Saturday 12:00 · first 20 minutes of Lab 2 · one screen, everyone watching**

Three deliberately simple programs, meant to be stepped through line by line in
a debugger before anyone opens `structured_local.py`.

| File | What it shows |
|---|---|
| `step1_prompt.py` | Ask for JSON in the prompt, then try to parse it |
| `step2_schema.py` | Send a schema so malformed output is impossible |
| `step3_tools.py` | Describe a function and let the model request a call |

Each is around 200 lines, but more than half of that is comments and `print`
statements. The actual logic is roughly thirty lines per file.

Same ticket in all three. Same three fields out. Only the *contract* changes.

## Why these exist

The real lab files run three methods across nine tickets and score them. That's
the right shape for measuring, and the wrong shape for a first look — there's a
loop, a scoring function, and a backend adapter in the way.

These three have none of that. No functions of our own, no loops, no classes.
Every line does exactly one thing and creates exactly one variable, so the
Variables pane tells the whole story.

**Read them in order.** Each one changes a single thing from the one before.

## Setting up Eclipse

You need **PyDev**. Help → Eclipse Marketplace → search "PyDev" → Install.

Then:

1. **File → New → Project → PyDev → PyDev Project.** Point it at the repo
   folder, pick your Python 3 interpreter.
2. If Eclipse hasn't seen your interpreter: **Window → Preferences → PyDev →
   Interpreters → Python Interpreter → Browse for python/pypy exe.** If you made
   a virtualenv, choose `.venv/bin/python` so `requests` is on the path.
3. Open `step1_prompt.py`.
4. **Double-click in the left margin** beside the first real line of code
   (`ticket_text = ...`). A blue dot appears — that's a breakpoint.
5. **Right-click the file → Debug As → Python Run.**

The debugger stops at your breakpoint. Now the keys:

| Key | Does | Use it |
|---|---|---|
| **F6** | Step Over — run this line, stop at the next | Almost always |
| F5 | Step Into — go *inside* a function call | Rarely. See warning |
| F7 | Step Return — finish this function, come back | If you F5 by mistake |
| F8 | Resume — run to the next breakpoint | To skip ahead |

> **Do not press F5 on the `requests.post` line.** You'll end up inside the HTTP
> library, several frames deep, and it is a long way back. Press F6. If you do
> it by accident, F7 gets you out.

The programs also print as they go and pause between sections, so they work
perfectly well outside a debugger too — just `python step1_prompt.py`. Set
`PAUSE = False` at the top to run straight through.

## What to point at, in each file

### step1_prompt.py

**Section 2** — after `prompt` is assigned, click it in the Variables pane.

> "That string is everything the model gets. It has no other input. It can't see
> our code, our files, or our intentions."

**Section 3** — step through the dict building.

> "We're not calling a Python function here. We're describing an HTTP request.
> Every one of these keys travels over the network as text."

**Section 5** — the layer-by-layer unpacking.

> "I could have got the text in one line. Four things would have happened at
> once and you'd have seen none of them. This is the shape of every reply
> you'll ever get back."

**Section 3** also has the two lines that switch the model's thinking mode off.
Don't skip past them — see *The thinking-mode trap* below, because you will
almost certainly meet it.

**Section 6** — the payoff, and it has three possible endings. The program
diagnoses which one you got, so whatever happens you have something to teach:

| Outcome | What to say |
|---|---|
| Clean JSON, parses fine | "Resist being pleased. What *made* it work? Nothing did." |
| JSON with a preamble or ```fences | "The model was *helpful*, and the helpfulness broke our program." |
| Empty, `finish_reason: length` | The thinking-mode trap. See below. |

**On a 27B model the first outcome is the likely one**, and that's fine — the
lesson is not "it always fails", it's "nothing guarantees it". Push on that:

> "It complied because it felt like it. That's a probability, not a guarantee.
> And a probability passes all your testing and then fails at 3am, differently
> each time."

Run it four or five times so they see for themselves whether it's stable.

### step2_schema.py

**Section 3** is the whole point of this file. Step through it slowly and watch
`schema` assemble in the Variables pane, field by field.

Stop on the `enum` line:

> "This doesn't say 'please pick one of these'. It says these are the only
> values that exist. There is no way for the model to say 'Urgent' or 'HIGH'."

**Section 4** — put step 1 and step 2 side by side.

> "One extra key. That's the entire difference between the two programs."

**Section 7** — there's no `try`/`except` here. Ask them why not, and let
someone work it out.

> "The server turned our schema into a grammar. As the model picks each word,
> anything that would break the schema is removed from its options *before* it
> chooses. It isn't being obedient. It can't do anything else."

Then the sentence the whole lab exists for:

> **A grammar guarantees shape. It guarantees nothing about truth.**

If you have time, edit the ticket so the customer mentions a second company. The
output stays perfectly formed. It may well be wrong.

### step3_tools.py

**Section 3** — we describe a function and hand over no code at all.

> "There is no `record_ticket` function in this file. Search it. The model gets
> a name, a sentence, and an argument shape. That's all it will ever get."

**Section 6** — the reveal. `message['content']` is empty.

> "In the last two programs the answer was right here. Now it's empty. The model
> didn't write us a reply — it made a request."

**Section 7** — note the arguments come back as a *string*, needing one more
parse. Small detail, trips people up constantly.

**Section 9** — stop here and make it land. This is the most important moment in
the first day.

> "Look at that if-statement. The model asked us to call `record_ticket`. We
> checked the name, and *we* decided to act on it. If it had asked for
> `delete_all_tickets`, that if-statement is the only thing standing between the
> request and the deed."

Then the bridge:

> "Now imagine we actually did the thing, sent the result back, and asked what
> to do next. And again, until it stopped asking. That's tomorrow afternoon.
> That's what 'agent' means — and you've now seen every moving part."

## The thinking-mode trap

Worth reading before you run anything, because it produces a baffling result
and it is not a bug in the lab.

Qwen 3.6 and models like it are **hybrid reasoning** models. Left to themselves
they write out a long internal monologue before answering — hundreds of tokens
of "let me consider this carefully" — and only then produce the answer. On
llama.cpp that monologue arrives in a **separate `reasoning_content` field**,
and `content` stays empty until the thinking is done.

So if the monologue runs past `max_tokens`, you get back:

```
"finish_reason": "length"
"content": ""
"reasoning_content": "Thinking Process: 1. Analyze the request... Result:\n{"
```

Cut off at the exact moment it was about to answer. `content` is empty, the
parse fails, and nothing about the error tells you why.

The three programs switch thinking off with two lines in the request body:

```python
request_body["chat_template_kwargs"] = {"enable_thinking": False}
request_body["reasoning_budget"] = 0
```

Different builds want different spellings, so they send both. **This is worth
showing rather than hiding**, for two reasons. It's a real thing you have to
know to get reliable output from this model family at all — and it is the same
failure mode, in miniature, that the Lab 1 and Lab 2 adapters had to handle.

Step 1 prints `reasoning_content` if it comes back non-empty. If you see
anything there, the flags didn't take on your server — raise `max_tokens` to
2000 and the model will finish thinking and then answer, slowly.

You can also set `--reasoning-budget 0` on `llama-server` itself and skip the
per-request flags entirely.

## Before you start

Make sure the model server is running and reachable:

```bash
curl http://localhost:8080/health
```

If your server is on another port, change `SERVER` at the top of each file.

## If something breaks

**`ConnectionError` / `Failed to establish a new connection`**
The server isn't running, or it's on a different port. Check `SERVER`.

**`ModuleNotFoundError: No module named 'requests'`**
Eclipse is using a different interpreter than your virtualenv. Window →
Preferences → PyDev → Interpreters, and point it at `.venv/bin/python`.

**Step 2 returns HTTP 400**
Your llama.cpp build wants a different `response_format` shape. The program
prints the alternative to try — swap it in and rerun. This is a real quirk, not
a mistake in the lab; see the briefing for why builds differ.

**Step 3 returns HTTP 400, or `KeyError: 'tool_calls'`**
The server was started without `--jinja`, or the model has no tool template.
Steps 1 and 2 still work. Add `--jinja` and restart.

**The debugger won't stop at my breakpoint**
You ran it with "Run As" instead of "Debug As". Right-click → Debug As →
Python Run.

## Then the real thing

Once all three make sense, open `../structured_local.py`. It does the same three
methods across nine tickets and counts how often each gets the answer *right* —
which turns out to be a very different question from whether it parses.
