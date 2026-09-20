# Lab 5 — Skills

**Briefing for the facilitator.** Sunday 10:15 · 60 minutes · pairs.

*Do not cut this one.*

---

## Open with

Deliberately deflate it first — the deflation is the lesson.

> "A skill is a folder with a markdown file in it. That's the whole format.
> There's no compilation, no registration, no framework. The interesting part
> isn't the file — it's *when* it gets loaded."

## The scenario

Your organisation has procedures. How you profile a data file. How you write
release notes. What a code review must cover. How an incident report is
structured.

You want a model to follow them — exactly, every time, the same way.

The obvious approach is to put them in the system prompt. Try that with twenty
procedures at two thousand tokens each and you're paying forty thousand tokens
on *every single request*, relevant or not. Remember Session 0: the API is
stateless, so you pay again every time.

That's the problem. Skills are the answer.

## The core idea: progressive disclosure

Draw three bands, each wider than the last.

| Level | What's loaded | When |
|---|---|---|
| 1 | Name + one-line description (~50 tokens) | Always, for every skill you have |
| 2 | The full `SKILL.md` body | Only when the model judges it relevant |
| 3 | Bundled scripts, templates, references | Only if those instructions call for them |

Then the sentence that matters:

> "The model is doing the routing. You are not writing an if-statement."

That's a genuinely different way to think about capability, and it's why this
lab is worth an hour rather than ten minutes.

## The consequence nobody expects

Because level 1 is all the model sees when deciding, **the description line is
the most important line in the file.**

> "Vague descriptions never fire. That's the single most common mistake people
> make writing their first skill, and it's invisible — the skill just silently
> never gets used, and you conclude skills don't work."

Write descriptions as *"Use this when the user asks about X, Y or Z"* and name
the triggering nouns.

## What the code has to do

The lab implements the whole mechanism from scratch in about fifty lines,
specifically so there's nowhere for magic to hide.

**Read only the frontmatter at startup.** Walk a directory, parse the YAML
header out of each `SKILL.md`, keep the name and description. Ignore the body
entirely — that's level 1.

**Put the descriptions in the system prompt.** A list of names and one-liners,
plus an instruction to load one before starting work if it's relevant.

**Offer a `read_skill` tool.** That's level 2. The model calls it, gets the full
body back as a tool result, and continues with the instructions now in context.

**Account for the tokens.** Print how many characters went up front versus how
many the bodies contain. The saving is the product.

That's it. Four small pieces. When people realise the "skills system" is a
description in a prompt plus a file-reading tool, the concept stops being
intimidating and becomes something they'll actually use.

## Running the room

**Run the same task twice.** Once with skills off: you get a reasonable
CSV profile, perfectly fine, completely non-standard. Once with skills on: the
model discovers the skill from one line of description, loads it, and follows
the procedure exactly — down to the `[high]`/`[medium]`/`[low]` severity
prefixes and the rule that identifiers must never be summed.

**Nobody told it to use the skill.** The description did the work.

Then check it doesn't *over*-fire: ask it to just list the files. Neither skill
should load. A skill that triggers when it shouldn't is a real failure mode and
worth seeing.

**Then they each write one.** Twenty minutes, for something they actually do — a
code review checklist, a commit message convention, a status update format.
Then **swap and run each other's.** Watching your own description fail to
trigger on someone else's phrasing is the fastest possible way to learn what a
good one looks like.

**Ask Friend 1:** *when is this better than fine-tuning?* Almost always, for
procedure — cheaper, instant to change, auditable, version-controlled,
reversible. He may push back from his coursework. Have the argument; it's a good
one.

**Ask Friend 2:** *how would you distribute these to a team of thirty?* Where do
they live, who reviews changes, how do you roll one back, how do you know which
version fired? Almost none of this is solved in the ecosystem — **which makes it
a portfolio project.** Point him at `PORTFOLIO.md`.

And one for the room: *a skill is instructions a model will follow. What happens
if someone commits a malicious one?* What's your review process?

## The punchline

> Skills are how you buy capability without paying context for it up front.
> **The description does the routing; the body does the work.**

And the thing that makes them worth deploying:

> The output with skills on is *rigidly consistent* across runs. Without, it's
> fine but different every time. That consistency is the product — it's what
> makes a skill something you can hand to a team.

## If you're short on time

Keep the two-run contrast and the token accounting; they're five minutes
together and carry the whole idea. Cut the write-your-own segment to ten minutes
and have them finish it at home — but do have them start it in the room, because
the first description is the one that teaches.
