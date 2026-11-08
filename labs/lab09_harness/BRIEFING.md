# Lab 9 — From a Loop to a Harness

**Briefing for the facilitator.** 90 minutes · pairs.

*Sits after Lab 8. Works as a Sunday add-on or as the anchor of a third
morning. Requires Lab 3 — it takes that exact loop apart.*

---

## Send the PDF first

`Harness-Intro.pdf` is a short introduction covering the five concerns around the loop, and when you genuinely do not need them. Send it a few days ahead so the definition arrives before the session rather than during it - that buys you the first ten minutes back.

## Open with

Point at Lab 3's loop, still on the whiteboard from Saturday.

> "That worked. You wrote it, you understood every line, and it did the job.
> So here is the question this lab exists to answer: what would you have to add
> before you'd let it run at two in the morning while you were asleep?"

Then set the expectation that the answer is boring, because that *is* the
lesson:

> "Nothing we add today is clever, and almost none of it is about AI."

## The scenario

Two of them, deliberately unrelated. An on-call task on a server — why is the
ingest service failing — and then a data task, reading CSVs and writing a
report. The second exists purely to prove the harness isn't secretly built
around the first.

## The shape of the session

This lab inverts the usual order. **Do not show them the harness first.** The
first thirty minutes are spent making them want one.

`step1_what_breaks.py` runs Lab 3's loop, unchanged, four times, and lets it
fail four different ways. Each failure maps to one thing the harness adds. By
the fourth they should be slightly irritated, which is the same trick Lab 3's
walkthrough uses and it works for the same reason.

| Problem | What they see | What it earns |
|---|---|---|
| 1 | An answer, and no way to check it | Observability |
| 2 | Token total accelerating, nothing stopping it | A budget |
| 3 | One transient blip kills the whole run | Retries |
| 4 | It restarts a production service unasked | A policy |

Problem 2 is the one to linger on. The running total doesn't grow linearly —
it accelerates, because every turn resends the whole conversation. That's
Session 0's "the API is stateless" arriving with a bill attached, and seeing
the numbers climb lands it better than the whiteboard did.

> **Ask Friend 2 before you reveal anything:** "You've seen four failures.
> You've solved all four before, in a completely different context. What are
> they called?" He will say audit logging, rate limiting or quotas, retries
> with backoff, and authorisation. That is the entire harness, named by someone
> who has never built one. Let that land before you open `harness.py`.

## The reveal

`harness.py` is about 180 lines. Read the five classes together — `Registry`,
`Policy`, `Budget`, `Run`, `Harness` — and keep saying the quiet part:

> "This is not an AI library. This is the same thing you'd put in front of any
> remote API."

Two details worth stopping on.

**The budget is checked before the call, not after.** Checking afterwards tells
you what you already spent. That's a receipt. Checking before is a cap.

**Policy is data, not an if-statement.** Lab 3 had `if name == "delete_file"`
hardcoded in the loop. Ask the room what happens when you add a second
destructive tool, and then a second task. A policy you can print, diff in
review, and load per environment is a different kind of object.

## The two demonstrations that land

**`--flaky`** reruns the task with tools failing 45% of the time. The run that
died in step 1 now completes. Nothing was made smarter; a retry was all it ever
needed.

**`--deny`** refuses the destructive tool. Watch what the agent does: it gets
`REFUSED` back as an ordinary tool result, reports that it could not finish,
and stops.

> "It didn't crash, and it didn't find a way round. There is no way round. The
> registry is the only door into our code."

## The part that makes it infrastructure

`step3_reuse_it.py` is a different job with different tools. Have them read it
*after* running it, and count the lines of loop code.

There are none. No message list, no `tool_calls` check, no `json.loads`, no
turn limit.

> "That's the test. Not 'is my code tidy' — can someone solve a problem you
> never thought about, without opening your file?"

## The discussion that matters most — 15 minutes, laptops closed

The lab's real takeaway is a judgement call, not a class.

Ask: **when would you not bother with any of this?**

Push them until someone says it: for a script you run once, watching, on free
inference, Lab 3's twenty lines are the right amount of code. This would be
ceremony. Agree with them loudly — a facilitator who thinks more infrastructure
is always better has taught the wrong lesson.

Then draw the threshold. You need a harness the moment any one of these is
true: it runs unattended, it runs more than once, somebody else runs it, it
costs real money, it can do something you'd regret, or you need to explain
afterwards what it did.

Finish with the two failure modes, because both are common and they look
opposite:

> "People build the harness too early — elaborate infrastructure around a
> problem they haven't understood yet — or after a 3am incident, which is the
> expensive way to find out you needed a spend cap. Write the twenty-line loop
> first, every time. Reach for this at the second task, or the first unattended
> run."

## The punchline

> A loop solves your problem. A harness solves the next one too.

And for Friend 2 specifically, said directly to him:

> "You already knew four of the five things in that file. The gap between you
> and an AI platform engineer is smaller than it looks from the outside, and
> it's mostly vocabulary."

## If you're short on time

Cut `--trace` and `--broke`; keep `--flaky` and `--deny`, which are the two
that produce a visible behaviour change. Cut the harness code-read to the
`Policy` and `Budget` classes only.

**Do not cut `step1_what_breaks.py` or the closing discussion.** Without the
first, the harness is a solution to a problem nobody has; without the second,
they'll go home and over-engineer their next script.

## If this is opening a third day

It works well as a day-three opener because it reframes everything from the
first two days as "that was the prototype". Natural companions, in the order
I'd run them:

1. **This lab** — the loop becomes infrastructure
2. **Lab 8's eval suite, pointed at the harness** — now the two fit together:
   every change to the harness runs against the cases from Sunday
3. **Deployment** — containerise it, put it behind a queue, watch it from a
   dashboard. Friend 2 leads; this is his portfolio project starting in the room
4. **Project time** — they build, you float

That's a genuine third day with a spine, rather than three more topics.
