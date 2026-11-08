# Lab 9 — From a Loop to a Harness

**90 minutes · pairs · can be bolted onto Sunday or open a third day**

Lab 3's loop was twenty lines and it worked. This lab asks the next question:
what do you have to add before you would let it run while you are asleep?

The answer is a **harness** — and the point of the lab is as much *when* you
need one as *what* it is.

> Prerequisite: Lab 3. This lab takes that exact loop and breaks it four times
> in front of you before fixing anything.

## Files

| File | What it is |
|---|---|
| `setup_sandbox.py` | Creates the fake datasets. Run first |
| `tools.py` | Two unrelated tool groups — ops, and reporting |
| `step1_what_breaks.py` | Lab 3's loop, failing four realistic ways |
| `harness.py` | **The thing itself.** ~180 lines, read it properly |
| `step2_harnessed.py` | The same task, through the harness |
| `step3_reuse_it.py` | A different job entirely, zero loop code |

Everything runs against your local model and a sandbox folder. Nothing real is
touched.

**Send [`Harness-Intro.pdf`](Harness-Intro.pdf) ahead of the session.** A short introduction for anyone new to the topic: the five concerns around the loop, and when you genuinely do not need them.

## What a harness actually is

A harness is the code around the loop. Not the loop — the loop is twenty lines
and you already wrote it. The harness is the five things you bolt on before the
loop can be trusted:

| | Concern | What it answers |
|---|---|---|
| 1 | **Registry** | Where do tools come from, and who keeps the schema and the function in step? |
| 2 | **Observability** | What happened, in what order, and what did it cost? |
| 3 | **Budget** | What stops it spending more than you meant? |
| 4 | **Reliability** | What happens when the third call fails? |
| 5 | **Policy** | What may run without asking a human? |

**None of those are AI problems.** Audit logs, spend caps, retries with
backoff, and authorisation are the same five problems any service that calls a
remote API has had for thirty years. That is why a cloud background transfers
into this field almost intact, and it is the single most useful thing to notice
in the whole lab.

## Steps

### 1. Earn it — `step1_what_breaks.py`

```bash
python setup_sandbox.py
python step1_what_breaks.py
```

Lab 3's loop, unchanged, run four times under conditions you will actually
meet. No harness anywhere in the file. Each run fails in a different way:

**You cannot see what it did.** It answers. Which tools did it call? What
arguments? What came back? What did it cost? You cannot answer any of it — the
information existed for a few milliseconds and was discarded.

**Nothing stops it spending.** A badly-worded task meets a loop with no
ceiling. Watch the running token total accelerate — it grows faster than
linearly, because every turn resends the whole conversation. A turn limit is
not a budget.

**One blip destroys the run.** A transient tool failure propagates out of the
loop and kills the process. Everything the agent had learned is gone, unlogged
and unretried, and you pay for all of it again.

**It acts without being asked.** `restart_service` is in the tool list and
nothing distinguishes it from `check_disk`. Lab 3 fixed this with
`if name == "delete_file"`, which works for exactly one tool.

> Run this before reading `harness.py`. The whole design depends on wanting the
> solution before you see it.

### 2. Read the harness — `harness.py`

About 180 lines. Read it top to bottom; there is nothing clever in it, and
that's the point. Five small classes:

- **`Registry`** — schema and implementation in one place, so the model can
  never be offered a tool with no function behind it
- **`Policy`** — authorisation as *data* (`allow` / `ask` / `deny` by rule),
  not an if-statement buried in a loop
- **`Budget`** — a token ceiling checked **before** each call. Checking after
  gives you a receipt; checking before gives you a cap
- **`Run`** — the result object: answer, why it stopped, turns, tokens, and
  the full event list
- **`Harness`** — the loop, with the other four wrapped round it

### 3. Same task, harnessed — `step2_harnessed.py`

```bash
python step2_harnessed.py
```

Identical task, tools and model to problem 1. Only the wrapper changed. Now
every question you couldn't answer has an answer, and it's all in
`runs.jsonl` as JSON lines — so "how often does this task need the log tool?"
is a grep, not an investigation.

Four flags, each demonstrating one concern:

```bash
python step2_harnessed.py --deny     # policy refuses destructive tools
python step2_harnessed.py --broke    # a budget too small to finish
python step2_harnessed.py --flaky    # tools fail 45% of the time
python step2_harnessed.py --trace    # the full structured event log
```

`--flaky` is the satisfying one: the run that died in step 1 now completes,
because a retry was all it ever needed.

`--deny` is the instructive one. The agent is refused, told so as an ordinary
tool result, and **reports that it could not finish** rather than crashing or
finding a way round. There is no way round — the registry is the only door.

### 4. Prove it's infrastructure — `step3_reuse_it.py`

```bash
python step3_reuse_it.py
python step3_reuse_it.py --unattended
```

A completely different job — read datasets, write a report — with completely
different tools. Then go back and **count the lines of loop code in that
file.** There are none. No message list, no `tool_calls` check, no
`json.loads`, no turn limit, no retries.

You wrote a registry, a system prompt and a policy. The harness had never
heard of datasets and did not need to.

> That is the test for whether you have built infrastructure or just
> refactored a script: **can someone solve a problem you never thought about,
> without opening your file?**

## When do you actually need one?

The part worth arguing about, and the thing to take away.

**You don't.** Not for a script you run once, watching, on free inference,
where the worst outcome is a wrong answer you immediately spot. Lab 3's twenty
lines are genuinely the right amount of code for that, and wrapping them in
this would be ceremony.

**You do, the moment any one of these becomes true:**

- **It runs unattended.** Nobody is there to notice it looping, or to say no.
- **It runs more than once.** The second task is when a script becomes a
  pattern, and a pattern with no registry is copy-paste.
- **Somebody else runs it.** They will not know which tools are dangerous.
- **It costs real money.** A cap you set in advance is a different thing from
  a bill you read afterwards.
- **It can do something you would regret.** Irreversible, external, or
  expensive — any one of those needs a policy, not a comment.
- **You need to explain what it did.** To a colleague, an auditor, or yourself
  next Tuesday. Without a trace you cannot.

**The two ways people get this wrong.** Building the harness first, before
they know what tools the job needs — producing elaborate infrastructure around
a problem they haven't understood yet. Or building it after a 3am incident,
which is the expensive way to discover you needed a spend cap.

The honest heuristic: write the twenty-line loop first, every time. Reach for
a harness at the second task, or the first unattended run, whichever comes
first.

## If it breaks

**`No local model server found`**
Start `llama-server` (or `ollama serve`) and check `LOCAL_API_BASE` in `.env`.
Run `python ../common/local_backend.py` to see what's detectable.

**HTTP 400 on the first call**
`llama-server` was started without `--jinja`, so it has no tool-calling
template. Add it and restart.

**Problem 4 doesn't restart anything**
The model read the log and reported back instead. Run it again, or make the
task more urgent. That it *might* is the point — nothing in the loop prevents
it.

**`--flaky` run fails completely**
Possible with 45% failure and two retries. That's a real outcome: retries
reduce failure, they don't eliminate it. Run again.

**Budget stop fires immediately**
`--broke` sets 900 tokens on purpose. That's the demo.

## Where this goes next

The harness here is deliberately small enough to read in ten minutes. The
things it does **not** have are the shape of Friend 2's portfolio project in
`PORTFOLIO.md`:

- persistence and resumability — a run that survives a restart
- concurrency, and what happens when two runs share a tool
- per-tool rate limits and circuit breakers
- cost attribution per user, per feature, per task
- a real policy engine, loaded per environment rather than hardcoded
- the eval suite from Lab 8, running against every harness change in CI

Any two of those is a weekend. All of them is a portfolio piece that very few
people have built.
