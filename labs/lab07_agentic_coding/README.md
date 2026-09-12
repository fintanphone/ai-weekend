# Lab 7 — Agentic Coding on a Real Repo

**75 minutes · pairs, or one screen shared**

## Goal

Turn an agent loose on a small, deliberately messy codebase and watch what it's
genuinely good at, then find where it's confidently wrong.

This is the most immediately useful skill either of them will take away, and the
best argument for Lab 8 that exists.

## The repo

`sample_repo/` is a freight billing calculator. About 80 lines, no tests, one
departed author, and a README that states the business rules clearly.

**The README and the code disagree.** That's the whole exercise. There are
several planted bugs of different kinds, and part of the point is that some are
much easier for an agent to find than others.

## Steps

### 1. Look at it yourself first — 10 minutes, no agent

Read `README.md`, `rates.py`, and `invoices.py`. Each person writes down what
they think is wrong, privately, before anyone runs anything.

This matters. It gives you a baseline to compare the agent against, and it stops
the session becoming passive.

### 2. Let it explore

```bash
cd sample_repo
claude
```

```
> Read the README and the code. Where do they disagree?
```

Watch how it works: it reads files, builds a picture, cross-references. Don't
interrupt. Compare its list against yours.

### 3. Make it prove things

Finding a bug by reading is a claim. Make it produce evidence.

```
> Write a test that fails because of the bulk discount bug, then show me it failing.
```

The distinction between "the model asserted a bug exists" and "there is a red
test on my screen" is the entire difference between agentic coding being useful
and being a liability. **Insist on the second, always.**

### 4. Fix and verify

```
> Fix it and show me the test passing. Don't change anything else.
```

Then:

```
> Now write tests covering the other rules in the README, and tell me which fail.
```

### 5. Push it somewhere it will struggle

Try these and watch it get progressively less reliable:

```
> Refactor this so the rules are data-driven and configurable per customer.
> Add multi-currency support with historical exchange rates.
> Is this code thread-safe? What would break under concurrency?
```

The refactor will look clean and plausible. **Check whether the behaviour is
actually identical.** This is where people get burned — the diff reads well, the
tests they didn't write don't exist, and a subtle behaviour change ships.

### 6. Undo it

```bash
git checkout .
```

Non-negotiable habit. Work on a branch, commit before you let an agent loose,
and be willing to throw the whole thing away. Agent work is cheap to redo and
expensive to half-review.

---

## Facilitator answer key

**Don't read this section out.** Use it to steer if they stall, and to check
what the agent missed.

| # | Bug | Difficulty for an agent |
|---|---|---|
| 1 | `apply_bulk_discount` uses `qty > 100`; README says 100 **or more**. CN-002 and CN-008 are exactly 100 and get no discount | Easy — usually found immediately |
| 2 | `zone_surcharge` silently returns 0% for an unknown zone. CN-007 has zone `atlantic`, which isn't in the dict, so it's undercharged with no error | Medium — needs it to look at the *data*, not just the code |
| 3 | `build_invoice` has a mutable default argument `lines=[]`. Call it twice and the second invoice contains the first one's lines | Medium — a classic, usually spotted, but its *impact* is often understated |
| 4 | Handling fee is added before the fuel levy is applied, so the levy is charged on handling. README says the levy applies to the total "including surcharge" — not handling | Hard — requires careful reading of the README's ordering |
| 5 | `float` used for currency throughout; `invoice_total` accumulates rounding error | Hard — often mentioned as a general concern rather than demonstrated |

Bug 2 is the most instructive one. An agent reading only the code sees a
reasonable-looking default. It only becomes a bug when you look at
`consignments.csv` and notice a zone that isn't in the dictionary. **Ask them:
what would have made the agent find it?** (Answer: telling it to run the code on
the real data, not just read it.)

---

## Discussion (15 min)

1. Which bugs did the agent find that you didn't? Which did you find that it
   didn't? What's the pattern?
2. It's a much better *reader* than writer at this scale. Why might that be, and
   what does it imply about how to use it?
3. What review process would you need before letting this near production code?
   Who's accountable for a bug an agent introduced?
4. Friend 1: this is the fastest possible way to get productive in an unfamiliar
   codebase. That's directly relevant to your first month in a new job — try it
   on a real open-source repo tonight.

## Good habits, worth stating explicitly

- **Always on a branch, always committed first.** `git checkout .` should be free.
- **Ask for a failing test before a fix.** Every time.
- **Small scoped tasks beat large vague ones.** "Fix the discount boundary" not
  "clean up the billing code".
- **Read the diff.** All of it. If it's too big to read, the task was too big.
- **Give it the ability to run things.** An agent that can execute tests is
  dramatically more useful than one that can only read.

## Takeaway

> Agentic coding is excellent at reading, good at narrow changes, and dangerous
> at broad ones. The skill is knowing which one you just asked for.
