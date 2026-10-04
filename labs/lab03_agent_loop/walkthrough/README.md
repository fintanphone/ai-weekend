# Walkthrough — building the loop one turn at a time

**Saturday 13:45 · first 35 minutes of Lab 3 · one screen, everyone watching**

A real task on a (fake) Raspberry Pi, worked up from a single exchange to a
complete agent loop. Same style as Lab 2's walkthrough: straight-line code, one
idea per line, meant to be stepped through in a debugger.

> **The task:** *"Log on to the Pi, go to my home directory, find all the .tmp
> files and delete the largest one if there is one."*

| File | What it adds |
|---|---|
| `pi_tools.py` | The three tool functions. Read once, then step over |
| `setup_sandbox.py` | Creates the fake Pi home directory. Run first |
| `step1_one_turn.py` | **One** exchange, in full, then stops — deliberately stuck |
| `step2_by_hand.py` | All three turns, written out longhand and repetitively |
| `step3_the_loop.py` | The same thing as a while-loop. ~15 lines |
| `step4_guardrails.py` | A human gate, plus a tempting shortcut to argue about |

## Why it's built this way

Step 2 is the important one, and it is *deliberately bad code* — three
nearly-identical blocks. By the third one the room should be slightly annoyed.
That annoyance is the point: the loop in step 3 isn't a clever trick you have to
accept on faith, it's the obvious tidy-up of something they just watched
themselves do by hand.

Don't skip to step 3. The whole design depends on earning it.

## Nothing real gets deleted

Everything runs against `fake_pi_home/`, a local folder of dummy files. Reset it
any time:

```bash
python setup_sandbox.py
```

If you have a real Pi and want to use it, set `MODE = "ssh"` in `pi_tools.py`.
Deletion is then refused unless you *also* set `ALLOW_REAL_DELETES = True` —
two switches rather than one, on purpose.

## Setup

```bash
python setup_sandbox.py      # create the fake Pi
python pi_tools.py           # check the tools work on their own
```

Then the same Eclipse setup as Lab 2's walkthrough — PyDev, breakpoint in the
left margin, **Debug As → Python Run**, and **F6 to step over**. Never F5 on
`requests.post`.

The programs also pause between sections and print as they go, so plain
`python step1_one_turn.py` works fine without a debugger. Set `PAUSE = False`
to run straight through.

## What to say, file by file

### Before anything — the two things the task wording hides

Put the task on screen and ask the room to list the steps. They'll say four:
log on, cd, list, delete. Then:

> "Two of those four will never happen. The model cannot log on — *our* code
> opens the connection, with credentials it never sees. And it cannot `cd`,
> because there's no shell session to change directory in. Every tool call is
> separate. So 'home directory' stops being a step and becomes a parameter."

Four human steps collapse to two tool calls. That gap between how a person
describes a task and how an agent must perform it is worth five minutes on its
own.

### step1_one_turn.py

**Section 6** — `finish_reason` comes back as `tool_calls`. That single string is
the loop's exit condition, two files before there's a loop.

**Section 7** — we run the tool. Point at `pi_tools.DISPATCH`:

> "That dictionary is the only door. The model emitted the characters
> `list_files`. Nothing it can say will add an entry here."

**The ending is the point.** The file stops holding a result the model has never
seen:

> "We know what files are there. The model doesn't — the connection closed, and
> nothing persists. If we want it to pick the largest, we have to send the whole
> conversation again with this result stuck on the end."

### step2_by_hand.py

Step through all three turns. Keep two numbers visible as you go: the length of
`messages`, and the running token total.

After turn 2, stop on what just happened:

> "It compared five numbers and picked the biggest. There's no `find_largest`
> tool — it just did the arithmetic. Fine at five. At five thousand it would be
> unreliable, and that's where you'd give it a tool instead."

At turn 3, `finish_reason` is `stop`:

> "No tool asked for. That's the only 'done' signal that exists."

Then the tally — 3 model calls, 2 tools, ~1,560 tokens sent for maybe 500 tokens
of real information:

> "The tool schemas went over the wire three times. So did the question.
> Nothing is remembered, so everything is resent."

Finally, scroll back through the three TURN blocks:

> "Those are the same code three times. And we still needed an `if` at the end
> in case it wanted a fourth turn — because we don't know in advance how many
> it'll take. You can't write this longhand in general."

### step3_the_loop.py

Put a breakpoint on the `for turn in range(...)` line and press **F8** to come
back to it each lap. Seeing the same line hit three times with different message
lists is the whole lesson in one gesture.

> "Nothing new happened in this file. No new API, no new tool, no new idea.
> The only change is that the repetition is written once."

Then the five steps, on the board:

```
1. call the model with the whole conversation
2. if it didn't ask for a tool, we're done
3. append its turn
4. run what it asked for, append the results
5. go round again
```

> "That is an agent. Everything you'll read about this year — planning, memory,
> reflection, multi-agent — is a variation on those five steps."

Worth naming explicitly: **the model never wrote a plan.** Nothing asked it to
list steps, and there's no branch anywhere saying "if the task mentions
deleting, call delete_file". It worked out what to do, in order, from two tool
descriptions and one sentence.

Try `MAX_TURNS = 1` and watch what a truncated agent does.

### step4_guardrails.py

Run it and **refuse** at the prompt. This is the bit people don't expect:

> "The refusal went back as an ordinary tool result. The model read 'REFUSED'
> and reported that it couldn't finish. It didn't crash, and it didn't find
> another way round — because there *is* no other way round."

Then run it the other way and compare:

```bash
python setup_sandbox.py && python step4_guardrails.py
python setup_sandbox.py && python step4_guardrails.py --fat-tool
```

| | Turns | Tokens sent |
|---|---|---|
| Two narrow tools | 3 | ~1,560 |
| One `run_command` | **2** | **~920** |

The fat tool is faster, cheaper, and less code. It will also ask to run
something like:

```
ls -S *.tmp | head -1 | xargs rm -v --
```

> "Faster, cheaper, fewer moving parts. And you've handed a language model
> unrestricted shell access to a machine, where the difference between
> `rm -- one.tmp` and `rm -rf ~` is a typo it'll make with total confidence."

Then the argument that matters: **the gate could not have been written for the
fat tool.** "Is this command destructive?" isn't answerable by inspecting a
string. With `delete_file` it's one line — `if name in NEEDS_APPROVAL`.

> Narrow tools are a permissioning mechanism, not a limitation.

### The trap nobody notices

`fake_pi_home/` contains `archive.tmp.bak` at 4 MB — **bigger than the largest
real `.tmp` file**. If the model globs `*tmp*` instead of `*.tmp`, it deletes
the wrong file and reports success, confidently, in good English.

Check which file actually went:

```bash
ls -la fake_pi_home/
```

That's the failure mode to be frightened of, and it's the reason Lab 8 exists.

## If something breaks

**HTTP 400 on the first call**
`llama-server` was started without `--jinja`, so it has no tool-calling
template. Add it and restart.

**`KeyError: 'tool_calls'`**
The model replied with prose instead of a tool call. Usually it's thinking mode
— check the two flags in the request body. On a small model it may just not be
capable of tool use; that's a real finding, and Lab 1's JSON test predicted it.

**The agent deletes `archive.tmp.bak`**
Its glob was wrong. Don't fix it quietly — this is the best teaching moment in
the lab.

**The loop never terminates**
It keeps asking for tools. `MAX_TURNS` catches it, which is exactly why it's
there. Usually the task is underspecified or a tool keeps erroring.

**`No files matching '*.tmp'`**
Run `python setup_sandbox.py` — a previous run deleted things.

## Then the real thing

Open `../agent.py`. Same five steps, a file workspace instead of a Pi, three
tools instead of two, and the Anthropic message format rather than the OpenAI
one — tool results go back as `tool_result` blocks in a user message instead of
`role: "tool"` messages. Same mechanism, different spelling. That difference is
exactly why `labs/common/local_backend.py` exists.
