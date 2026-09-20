# Lab 8 — Evals, Guardrails and Cost

**Briefing for the facilitator.** Sunday 15:15 · 60 minutes · pairs.

*Never cut this. If you're behind, cut Lab 4 or Lab 7 instead.*

---

## Open with

Be direct about why this hour matters, because it's the least glamorous material
of the weekend and the most valuable.

> "Almost everyone can build an agent now. You both could, as of yesterday
> afternoon. Very few people can tell you whether theirs works, and almost
> nobody can prove it got better. That gap is where the jobs are."

For two people job-hunting, this is the most employable hour of the weekend.
Say so.

## The scenario

You built the Lab 3 agent. You want to improve it. You change a prompt, try it
once, and it feels better.

Does it work better? You have no idea. You might have fixed one thing and broken
two others, and you'd never know — because you tested by vibes.

> "Without a suite, every change you make is a guess you can't evaluate. With
> one, you have a number, and the number moves."

## The core idea

Twelve cases against the Lab 3 agent, three variants of the system prompt, and
one number per run.

That's a realistic starting size. **Say that explicitly** — people assume evals
means hundreds of cases and a framework, and that assumption is why they never
start. Twelve cases in a JSON file is a real eval suite.

## Three kinds of scoring, in order of preference

**Deterministic substring checks.** Cheap, instant, never drift, no model
needed. Use these wherever the answer contains a checkable fact.

**A model as judge, against a rubric.** Necessary when the answer is prose.
Also biased toward longer answers, inconsistent between runs, and expensive at
volume. **Spot-check the judge against your own grading on ten cases before
trusting it** — that instruction is the difference between an eval suite and a
comfortable illusion.

**Both.** Cheap gate first, judge only what survives.

## The case that matters most

Point them at `refusal-honesty` specifically. It asks for information that does
not exist in the workspace.

> "Inventing a plausible number is the failure mode that destroys trust in a
> system. And it will *never* show up in happy-path testing, because nobody
> writes a happy-path test for a question their data can't answer."

This connects straight back to Lab 2's second column and Lab 4's confident wrong
answers. It's the same failure wearing a third costume, and by now they should
recognise it.

## What the code has to do

**Separate the thing under test from the harness.** Variants are just different
system prompts against the same agent, same tools, same cases. Change one factor
at a time or the number tells you nothing.

**Instrument everything.** Turns taken, input tokens, output tokens, wall-clock
seconds. You're not only measuring quality — you're measuring what quality cost.

**Print the failures, not just the score.** A score of 9/12 is useless without
knowing which three and why.

**Make the comparison one command.** If comparing variants is fiddly, nobody
does it, and the suite rots.

## The second half: guardrails and cost

Twenty minutes, whiteboard, no code. Work through each against the agent they
built.

**Prompt injection.** They already saw it in Lab 3 — an instruction inside
`notes.md`. Untrusted content is *data*, not instruction, and only your code can
enforce that distinction. The containment check held even when the model was
fooled, because security lived in the tool implementation.

**Tool permissioning.** The model can only choose from what you gave it. The
tool list is the primary control surface. Narrow beats general — that's Lab 6's
`run_sql` argument again. Which actions need a human in the loop? Anything
irreversible, anything that spends money, anything touching a third party.

**Cost.** Take the real token totals from their eval run and work out the actual
number. Then the thing that surprises people: because the API is stateless, a
ten-turn conversation isn't ten units of cost — it's closer to fifty-five.
Session 0's first idea, arriving with a price tag attached.

**Observability.** Friend 2 should lead this. Log every model call: prompt,
response, tools called, tokens, latency, cost. You cannot debug an agent from
its final answer — you need the trace. What are the alerting conditions? Turn
limit hit, tool error rate, cost per request, eval score on a nightly run.

## Running the room

Get the baseline number first, before any discussion. People engage differently
once there's a number on screen they don't like.

Then have them each add three cases: one the agent currently passes (a
regression guard), one they expect it to fail, and one adversarial — a question
with a false premise.

**Were they right about which would fail?** Being wrong about that is the most
useful thing that can happen in this hour.

## The punchline

> **If you can't measure it, you're not improving it — you're just changing it.**

And the sentence to hand them for interviews, said slowly:

> "I built the agent. Then I built the eval suite. The second one is why I know
> the first one works."

Then the practice almost nobody has yet: **run the suite in CI against every
prompt change.** That's a genuine differentiator on a CV in 2026, and it's the
direct bridge into the project scoping session that follows this hour.

## If you're short on time

Cut the model-as-judge discussion and run deterministic scoring only. Keep the
baseline → variant → compare cycle, keep `refusal-honesty`, and keep the cost
arithmetic. Those three are the hour.
