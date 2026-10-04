# Lab 2 — Structured Output

**Briefing for the facilitator.** Saturday 12:00 · 45 minutes · pairs.

*Deliverable from the front of the room in about eight minutes, before anyone
opens a laptop.*

---

## Open with

> "Everything we've done so far, you could have done in a chat window. This is
> the lab where the model stops being something you talk to and becomes
> something you can call from a program. Every single thing we do tomorrow
> depends on the next forty-five minutes."

Lab 2 looks like the smallest lab of the weekend and it's actually the hinge.
The agent loop in Lab 3 is built entirely on the mechanism they're about to see,
and won't make sense without it.

## The scenario

Aurora Freight is a logistics company. Support tickets arrive as free text —
emails, chat messages, someone typing in a hurry from a warehouse floor. They
need to land in a ticketing system as structured records: who wrote in, which
company, what's wrong, how bad it is, and the reference number if there is one.

Nobody wants to read these by hand. A model can read them. The question is
whether what comes back is something a database will accept.

Make it concrete — read one aloud:

> *"URGENT URGENT our entire production database is unreachable, every customer
> is down, we are losing money by the minute. Priya Raghavan, Meridian Health.
> This is ticket MH-0031 I think."*

Then ask the room: what are the five fields, and what's the severity? They'll
get it instantly. That's the point — **the task is trivially easy for a human,
and the difficulty is entirely in making it reliable at machine scale.**

## The three challenges, in order

Draw these as three rungs on the board. Each is a different problem and people
routinely conflate them.

**One: can you get JSON at all?** Ask a model for JSON and most of the time you
get JSON. Sometimes a code fence around it. Sometimes a helpful preamble:
"Sure! Here's the extracted data:". Sometimes a trailing "Hope that helps!".
Occasionally a key renamed because the model thought of a better name, or a
severity of `"URGENT"` when your enum has four values and that isn't one.

Here's the part that matters: **those failures are different every run.** It's
not a bug you fix once. It's a probability, and it will bite you at exactly the
volume where you've stopped watching.

**Two: can you get the *right* JSON?** A perfectly-formed record naming the
wrong person is worse than no record, because nothing downstream will flag it.
Your parser is happy. Your database is happy. Your support manager is looking at
a ticket assigned to someone who doesn't work there.

**Three: can you tell which one you just failed?** This is the one people never
think about, and it's where the lab lands.

## What the code has to do

Four things. Say them before they read the file, or people skim looking for
clever bits and miss the structure.

**Extract five fields from unstructured text** — name, company, summary,
severity from a fixed set of four, and a reference that may or may not exist.
The nullable field matters more than it looks; "absent" is a real answer and the
model has to be able to express it.

**Try it two ways and compare.** Method A asks for JSON in the prompt and parses
what comes back. Method B declares the same five fields as a *schema* and forces
the model to fill it in — and the API validates the arguments before your code
ever sees them. This isn't a better prompt. It's a different contract.

**Score shape and truth separately.** Two columns. *Valid* means it parses, has
all the keys, and the severity is inside the enum. *Fields right* means the
values are actually correct. The whole lab is watching these two diverge.

**Run it enough times to see the variance.** One run tells you nothing. Several
tickets times several trials tells you whether you're looking at a capability or
a coin flip.

Point them at one specific line when they read the code — the bit in method A
that strips code fences. Ask: *why does that line exist?* It's defensive
cleanup, written because the code is fighting the model instead of constraining
it. Every codebase that goes the prompt-based route accumulates lines like it.
**That line is the smell.**

## Why there are two tiers of tickets

Say this before they run anything, or the first result is confusing.

**Tier 1 is clean** — one sender, one company, an explicit reference. A good
model scores 100% and that is *expected*. Those tickets exist so the lab opens
with something that works.

**Tier 2 is where the teaching is.** Six tickets, each with one trap:

- Three companies named, and the writer's isn't the most prominent one
- A colleague mentioned by name before the signature
- A customer insisting "NOT URGENT, don't page anyone" while describing an
  entire warehouse reduced to pen and paper
- An invoice number and an error code both shaped like ticket references
- A closed ticket's reference quoted in the thread below the new problem
- An account manager raising something on a client's behalf

None of these are unfair. The extraction rules are stated explicitly and given
to the model. **A careful human gets all six right.** It's the model that finds
them hard.

## Running the room

**Start in `walkthrough/`, on one screen, with a debugger open.** Three small
programs — one per method — designed to be stepped through line by line. No
loops, no functions of our own, one idea per line, so the Variables pane carries
the explanation. Budget twenty minutes for all three.

`walkthrough/README.md` has the Eclipse setup, which keys to press, and what to
say at each stopping point. The short version: F6 steps over, and never press F5
on the `requests.post` line or you'll end up inside the HTTP library.

**Read the "thinking-mode trap" section of that README before the day.** On a
hybrid reasoning model like Qwen 3.6, an unconstrained call will happily spend
its entire token budget on an internal monologue and hand you back an empty
`content` field — a baffling result that looks like a broken lab. The programs
switch thinking off and explain why, but you want to have met it before you
meet it in front of an audience.

Also expect step 1 to **succeed** on a 27B model. That's fine and the program
handles it: the framing becomes "it worked — now what *made* it work?" Answer:
nothing did. A probability is not a guarantee, and it will pass every test you
write before failing at 3am.

Do this even if — especially if — your audience is new to reading Python. The
three real lab files have a loop, a scoring function and a backend adapter in
the way. That's the right shape for measuring and the wrong shape for a first
look.

Then fifteen minutes reading `structured.py` together before anything executes.
Coming from the walkthrough it reads as the same three ideas wearing a loop.

Then the local run on the GPU, which adds a third method the API can't
demonstrate: **constrained decoding**, where the server compiles the schema into
a sampling grammar and masks the logits, so tokens that would break the schema
are literally unavailable. A small model *physically cannot* emit malformed
JSON.

**Ask Friend 1:** *why do the schema field descriptions change output quality at
all?* They're just text in a context window — they aren't executed. What is the
model actually doing with them?

**Ask Friend 2:** *where does this validation belong in a real system?* At the
model boundary, the API boundary, or both? What do you do with a record that
validates but smells wrong?

## The punchline

Save this for after they've seen the numbers:

> "Method B will hold at or near 100% valid, all the way through tier 2. It
> cannot produce malformed JSON — the schema won't let it. Now look at the
> second column."

Then:

> **A grammar guarantees shape. It guarantees nothing about truth.**

And the operational version, which is the sentence they should leave with:

> A malformed response is an outage — you find out in minutes. A well-formed
> wrong one is a data quality incident you discover three months later, and by
> then it's in every report you've sent.

That's the bridge to Lab 8. You cannot test your way out of the second kind with
a parser. You need evals.

## If you're short on time

Run tier 2 only and skip tier 1 — a capable model makes tier 1 uninformative
anyway. Keep the code-reading segment; cut the "break it on purpose"
experiments, which they can do at home.
