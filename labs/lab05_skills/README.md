# Lab 5 — Skills and Progressive Disclosure

**60 minutes · pairs · do not cut this one**

## Goal

Understand what a skill actually is, by implementing the mechanism yourself in
about 50 lines.

The headline should be slightly deflating: **a skill is a folder with a markdown
file in it.** That's the whole format. The interesting part isn't the file, it's
*when* it gets loaded.

## The idea worth having

Context is the scarce resource. Everything competes for it — system prompt,
history, tool schemas, retrieved documents, tool results — and it's paid for on
every single API call, because the API is stateless.

So you can't just put all your organisation's procedures in the system prompt.
Twenty skills at 2,000 tokens each is 40,000 tokens on every request, whether
they're relevant or not.

Progressive disclosure solves it in three levels:

| Level | What's loaded | When |
|---|---|---|
| 1 | Name + one-line description (~50 tokens) | Always |
| 2 | Full `SKILL.md` body | Only when the model decides it's relevant |
| 3 | Scripts, references, templates in the folder | Only when the instructions call for them |

The model is doing the routing. You are not writing an if-statement.

## Steps

### 1. Read a skill

```bash
cat skills/csv-profiler/SKILL.md
```

Note the shape: YAML frontmatter with `name` and `description`, then a markdown
body of instructions. That's the format, and it's an
[open standard](https://agentskills.io) — not Claude-specific.

Read the `description` carefully. **It is the only thing the model sees at
level 1**, so it's doing all the routing work. A vague description means the
skill never fires. This is the single most common mistake people make writing
skills.

### 2. See the contrast

Run the same task twice.

```bash
python skill_runner.py --no-skills "Profile the shipments.csv file for me."
```

You get a reasonable profile. Perfectly fine. Completely non-standard — a
different shape every time you ask.

```bash
python skill_runner.py "Profile the shipments.csv file for me."
```

Now watch the trace. The model sees a one-line description, decides it's
relevant, calls `read_skill`, gets the full procedure, and follows it exactly —
right down to the `[high]`/`[medium]`/`[low]` severity prefixes and the rule that
identifiers must never be summed.

Nobody told it to use the skill. The description did the work.

### 3. Watch the accounting

```bash
python skill_runner.py --show-context "Profile the shipments.csv file for me."
```

See how few characters go up front versus how many the bodies contain. Then
notice the `[+N chars into context]` when the skill actually loads.

Now imagine twenty skills instead of two.

### 4. Check it doesn't over-fire

```bash
python skill_runner.py "What's in the workspace? Just list the files."
```

It should **not** load either skill. If a skill fires when it shouldn't, the
description is too broad. That's a real failure mode and worth seeing.

```bash
python skill_runner.py "Write release notes for a version that fixed the
                        shipment export timeout and changed the reorder
                        threshold from 50 to 30 units."
```

Different skill, correctly selected. Check it obeys the house style — including
the banned-words list and the rule about **Changed** versus **What's new**.

### 5. Write your own — 20 minutes

Each person writes a skill for something they actually do. A code review
checklist, a bug report format, a commit message convention, a way of
structuring a status update.

```bash
mkdir -p skills/my-skill
$EDITOR skills/my-skill/SKILL.md
```

Rules, learned the hard way:

- **The description is a routing decision.** Write it as "use this when…" and
  name the triggering nouns. "Formats things nicely" will never fire.
- **Be prescriptive in the body.** Skills that say "consider using a table" get
  ignored. Skills that say "output a markdown table with exactly these columns"
  get followed.
- **Include the negative rules.** "Never speculate about business meaning" is
  doing real work in the csv-profiler skill.
- **Test it fires, and test it doesn't over-fire.** Both matter.

Then swap skills with your partner and run each other's. Someone else's skill
failing to trigger on your phrasing is the fastest way to learn what a good
description looks like.

## Expected output

With skills on, output is rigidly consistent across runs. Without, it's fine but
different every time.

**That consistency is the product.** It's what makes a skill deployable to a
team, and it's why skills are more interesting than a clever prompt.

## Discussion (10 min)

1. When is this better than fine-tuning? (Almost always, for procedure. Cheaper,
   instant to change, auditable, version-controllable, and reversible.)
2. When is it better than just a longer system prompt? (When you have more than
   two or three, and when different tasks need different ones.)
3. Friend 2: how would you distribute these across a team of 30? Where do they
   live, who reviews changes, how do you roll one back? (This is a real product
   gap, and it's a portfolio project.)
4. A skill is instructions that a model will follow. What happens if someone
   commits a malicious one? What's your review process?

## If it breaks

**Skill never loads** — the description is too vague, or doesn't share vocabulary
with how you phrased the task. Rewrite it as "Use when the user asks about X, Y,
or Z" and try again.

**Frontmatter not parsing** — needs `---` on its own line at the very start of
the file, no blank line before it.

**`ERROR: not found`** — the data lives in Lab 3's workspace. Run
`python ../lab03_agent_loop/make_workspace.py` first.

## Takeaway

> Skills are how you buy capability without paying context for it up front.
> The description does the routing; the body does the work.
