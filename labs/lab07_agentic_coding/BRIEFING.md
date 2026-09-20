# Lab 7 — Agentic Coding

**Briefing for the facilitator.** Sunday 13:45 · 75 minutes · pairs or one
shared screen.

*The answer key for the planted bugs is in `facilitator/LAB07-ANSWERS.md`,
which is deliberately kept out of the shared repo. Don't read it out.*

---

## Open with

> "This is the lab where the thing you learned on Saturday becomes something
> you'll use on Monday. It's also the one where I want you most sceptical,
> because it's very good at looking more competent than it is."

## The scenario

`sample_repo/` is a freight billing calculator. Eighty lines, no tests, written
in a hurry two years ago by someone who has since left. The README states the
business rules clearly.

**The README and the code disagree.** That's the whole exercise.

This is deliberately the most realistic artefact of the weekend. Nobody's first
week in a new job involves a clean codebase with full test coverage. It involves
this: undocumented decisions, a departed author, and finance saying some
invoices "look a bit off" without being able to say which.

## The challenges

**One: reading is easy, proving is hard.** The agent will produce a confident
list of problems within thirty seconds. Some will be real. Distinguishing the
two is the actual skill.

**Two: some bugs are invisible from the code alone.** At least one of the
planted problems only appears when you look at the *data* the code runs on. An
agent reading source sees a reasonable-looking default. It's only wrong given a
particular input that happens to exist in the CSV. Ask the room afterwards what
would have made the agent find it — the answer is telling it to *run* the code
on real inputs rather than reason about it.

**Three: broad changes look identical to narrow ones in a diff.** A refactor
comes back clean, well-structured, and plausible. Whether behaviour is actually
unchanged is a completely separate question, and the diff won't tell you.

## What we want them to practise

Five steps. Put them on the board.

```
Read  →  Propose  →  PROVE  →  Fix  →  Verify
```

**Step three is the one people skip**, and it's the one that makes the
difference.

> "'The model asserted a bug exists' and 'there is a red test on my screen' are
> completely different claims. Ask for the failing test *before* the fix. Every
> single time."

The rest of the discipline:

- **Work on a branch, commit before you start.** `git checkout .` must always
  be free. Agent work is cheap to redo and expensive to half-review.
- **Small scoped tasks beat large vague ones.** "Fix the discount boundary" not
  "clean up the billing code".
- **Read the diff. All of it.** If it's too big to read, the task was too big.
- **Give it the ability to run things.** An agent that can execute tests is
  dramatically more useful than one that can only read.

## Running the room

**Ten minutes reading, privately, with no agent.** Each person writes down what
they think is wrong before anyone runs anything.

This matters for two reasons. It gives them a baseline to compare against — and
it stops the session going passive, which is the failure mode of every "watch
the AI do something impressive" demo.

Then let it explore, and compare its list against theirs. The interesting
question isn't which is longer. It's **what's in one and not the other, and
why.**

Then push it somewhere it struggles: a broad refactor, multi-currency support, a
thread-safety review. Watch the output get progressively less trustworthy while
remaining equally confident in tone. That gap between confidence and reliability
is the thing to notice.

Finish with `git checkout .` and make that reflex explicit.

**Ask Friend 1:** *this is the fastest way to get productive in an unfamiliar
codebase — which is exactly your first month in a new job. Try it tonight on a
real open-source repo you've never seen.* Genuinely useful advice for someone
about to start interviewing.

**Ask Friend 2:** *what review process would you need before this touches
production code?* Who's accountable for a bug an agent introduced? What does the
audit trail look like?

## The punchline

> Excellent at reading. Good at narrow changes. Dangerous at broad ones.
> **The skill is knowing which one you just asked for.**

And the bridge to Lab 8, which comes immediately after:

> "Everything we just did was judged by eye. We read a diff and decided it
> looked right. That doesn't scale past about fifty lines, and it doesn't work
> at all when you're not the one reading. That's the next hour."

## If you're short on time

Do the bug-hunting and the failing test. Cut the refactor exercise — though it's
the best demonstration of the danger, it's also the part they'll explore on
their own without any encouragement from you.

If you're catastrophically behind on Sunday, this is the lab to cut entirely.
Agentic coding is the one topic both of them will absolutely pursue unprompted.
