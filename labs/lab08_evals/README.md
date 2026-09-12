# Lab 8 — Evals, Guardrails and Cost

**60 minutes · pairs · never cut this**

## Goal

This is the module that separates people who demo from people who ship. It is
also, for two people job-hunting, the most employable hour of the weekend.

Almost everyone can build an agent now. Very few can tell you whether theirs
works, and fewer still can prove it got better.

## Part 1 — Evals (35 min)

### The idea

Without an eval suite you are tuning by vibes. You change a prompt, it feels
better, you ship it, and you have no idea whether you fixed one thing and broke
two others. With one, you have a number, and the number moves.

The suite here is twelve cases against the Lab 3 agent. That's a realistic
starting size — you do not need hundreds.

### 1. Look at the cases

```bash
cat cases.json
```

Three kinds of scoring, in order of preference:

- **`must_contain`** — deterministic substring checks. Cheap, fast, no model
  needed. Use these wherever you possibly can.
- **`judge`** — an LLM grades against a rubric. Necessary when the answer is
  prose, but it costs money and it is itself fallible.
- **Both** — the substring check runs first as a cheap gate.

Read `refusal-honesty`. It asks for information that doesn't exist in the
workspace. **This is the single most important case in the suite**, because
inventing a plausible number is the failure mode that destroys trust in a system
and it will never show up in your happy-path testing.

### 2. Get a baseline

```bash
cd ../lab03_agent_loop && python make_workspace.py && cd ../lab08_evals
python eval.py --variant baseline
```

Note the score and the token totals. Look at the failures printed underneath.

### 3. Change one thing and re-measure

```bash
python eval.py --variant careful
python eval.py --variant grounded
```

Then all three side by side:

```bash
python eval.py --compare
```

Look at what changed. The `grounded` prompt adds one instruction about not
inventing figures — see what it buys, and what it costs in tokens.

**Say the sentence out loud:** *"I took it from X% to Y%, and here's which
change bought each increment."* That's an interview answer, and it's the exact
thing `PORTFOLIO.md` recommends Friend 1 build a project around.

### 4. Write your own cases — 15 min

Add three cases to `cases.json`:

- One the agent currently gets right (a regression guard)
- One you think it will fail
- One adversarial — a question with a false premise, or asking for something
  that doesn't exist

Run them. Were you right about which would fail? Being wrong about that is the
most useful thing that can happen here.

```bash
python eval.py --case your-new-case-id
```

### On judging with a model

Cheap, scalable, and it has real problems: it's biased toward longer answers,
inconsistent between runs, and expensive at volume. Use deterministic checks
wherever the answer has a checkable fact in it, and reserve the judge for prose.

If you must judge, **spot-check the judge against your own grading on 10 cases**
before trusting it.

## Part 2 — Guardrails and cost (25 min)

Whiteboard, not code. Work through each of these against the agent you built.

### Prompt injection

You already saw it in Lab 3: put an instruction inside `notes.md` and the model
may follow it. The model cannot distinguish your instructions from text it read.

- Untrusted content is **data**, not instruction, and only your code can enforce that
- The containment check in `tool_read_file` held even when the model was tricked.
  Security lives in the tool implementation, not in the prompt
- Ask: which of our tools would be dangerous if the model were fully
  adversary-controlled? Design for that case

### Tool permissioning

- The model can only choose from tools you gave it. **The tool list is your
  primary control surface**
- Narrow tools beat general ones. `list_shipments(status)` is safer than
  `run_sql(query)`, and Lab 6 has that argument in full
- Which actions need a human in the loop? Anything irreversible, anything that
  spends money, anything that touches a third party
- Read-only by default; write access as a deliberate exception

### Cost

Take the token totals from your eval run and work out the real number using
current rates at <https://www.anthropic.com/pricing>. Then:

- The API is stateless, so **every turn resends the whole history**. A 10-turn
  conversation is not 10 units of cost, it's closer to 55
- Where do the tokens actually go? Usually tool results, not the conversation
- Prompt caching on a stable system prompt is often the single largest saving
  available
- Route by difficulty. A cheaper model for classification and routing, an
  expensive one for the hard step
- **Set a hard spend cap before you need one.** Runaway loops are the classic
  way to discover this

### Observability

Friend 2 should lead this bit.

- Log every model call: prompt, response, tools called, tokens, latency, cost
- You cannot debug an agent from the final answer alone. You need the trace
- What are the alerting conditions? (Turn limit hit, tool error rate, cost per
  request, latency, eval score on a nightly run)
- Run the eval suite in CI against every prompt change. This is the practice
  almost nobody has yet and it's a genuine differentiator on a CV

## If it breaks

**`ImportError: cannot import name 'TOOLS'`** — run from inside
`labs/lab08_evals/`. The path insert is relative.

**Cases fail that shouldn't** — read the printed answer. It's usually formatting
(`10,140.30` vs `10140.3`) rather than a wrong answer. That's a real lesson
about brittle scoring, and it's why `match: "any"` exists on some cases.

**Judge disagrees with you** — good, and instructive. Which of you is right?
Tighten the rubric.

**Slow** — twelve cases across three variants is ~40 agent runs. Use
`--case <id>` while iterating.

## Takeaway

> If you can't measure it, you're not improving it — you're just changing it.

And the thing to say in an interview:

> "I built the agent. Then I built the eval suite. The second one is why I know
> the first one works."
