# Lab 2 — Structured Output

**Briefing for the facilitator.** Saturday 12:00 · 45 minutes · pairs.

*Deliverable from the front of the room in about eight minutes, before anyone
opens a laptop.*

---

## Read this first: do not promise that method A will fail

This lab was originally built on the premise that prompt-based JSON extraction
fails to parse and schema enforcement rescues it. **That premise is no longer
true, and we have measured it.** On `claude-haiku-5-5` — the cheapest model
available — method A returned clean parseable JSON in **90 out of 90 responses**
and the defensive code-fence stripper never fired once.

If you open by promising they'll watch method A fall over, you will be standing
in front of two 100% columns with nothing to say.

**Promise this instead:**

> "You're going to run two methods against ten deliberately nasty tickets. In
> 240 extractions you'll find exactly one wrong answer — and it will be in the
> method you'd least expect, for a reason that is entirely our fault rather than
> the model's."

That lands, it's true, and it sets up the actual lesson.

## Open with

> "Everything we've done so far, you could have done in a chat window. This is
> the lab where the model stops being something you talk to and becomes
> something you can call from a program. Everything we do tomorrow depends on
> the next forty-five minutes."

Lab 2 looks like the smallest lab of the weekend and it's the hinge. The agent
loop in Lab 3 is built entirely on this mechanism.

## The scenario

Aurora Freight is a logistics company. Support tickets arrive as free text —
emails, chat messages, someone typing in a hurry from a warehouse floor. They
need to land in a ticketing system as structured records: who wrote in, which
company, what's wrong, how bad it is, and the reference number if there is one.

Read one aloud:

> *"URGENT URGENT our entire production database is unreachable, every customer
> is down, we are losing money by the minute. Priya Raghavan, Meridian Health.
> This is ticket MH-0031 I think."*

Ask the room: what are the five fields, and what's the severity? They'll get it
instantly. That's the point — **the task is trivially easy for a human, and the
difficulty is entirely in making it reliable at machine scale.**

## The three challenges, in order

Draw these as three rungs. People routinely conflate them, and the first one has
changed.

**One: can you get JSON at all?** This used to be the hard part — code fences,
preambles, "Hope that helps!", a renamed key, an invented enum value. **On
current models, it is solved.** Say so plainly, and say what replaced it: method
B's argument is no longer a pass rate, it's a *guarantee* of shape plus three
lines of repair code you never write.

**Two: can you get the *right* JSON?** A perfectly-formed record naming the
wrong person is worse than no record, because nothing downstream flags it. Your
parser is happy. Your database is happy. Your support manager is looking at a
ticket assigned to someone who doesn't work there.

**Three: can you tell which one you just failed?** The one people never think
about, and where the lab lands.

## What the code has to do

Four things. Say them before they read the file, or people skim for clever bits
and miss the structure.

**Extract five fields from unstructured text** — name, company, summary,
severity from a fixed set of four, and a reference that may or may not exist.
**The nullable field is the whole lab.** Hold that thought.

**Try it two ways and compare.** Method A asks for JSON in the prompt. Method B
declares the same fields as a schema and forces the model to fill it, with the
API validating arguments before your code sees them. Not a better prompt — a
different contract.

**Score shape and truth separately.** *Valid* means it parses, has all the keys,
and severity is inside the enum. *Fields right* means the values are correct.
The lab is watching these diverge.

**Run it enough times to see variance.** Several tickets times several trials
tells you whether you're looking at a capability or a coin flip.

When they read the code, point at the code-fence stripper in method A and ask
*why does that line exist?* Then tell them it **never fires** on a current
model. A dead defensive branch that somebody is still maintaining is a more
interesting artefact than a live one, and it's an honest way to show them how
fast this field moves.

## Why there are two tiers

Say this before they run anything, or the first result is confusing.

**Tier 1 is clean** — one sender, one company, an explicit reference. Any good
model scores 100% and that is *expected*.

**Tier 2 is ten tickets**, each with one trap: three companies with the writer's
not most prominent; a colleague named before the signature; a customer insisting
"NOT URGENT" while describing a warehouse on pen and paper; an invoice number
and error code shaped like references; a closed ticket's reference quoted below;
an account manager writing on a client's behalf; "tried to **Google** the
problem"; "my **Dell** monitor"; a writer whose employer *is* the famous brand;
and "the **orange** warning light" from **Orange** Facilities Management.

**Six of those ten are company-attribution traps, and all six pass, on both
models, every trial.** Zero company errors in 240 extractions. Tell them that
*after* they've run it, not before — the surprise is the content. They are
regression guards now, and "the thing we were worried about turns out to be
solved" is a legitimate and useful finding.

## The centre of the lab: three schemas, one field

This is the segment to protect. Everything above is setup.

Tier 2 produces exactly one reproducible failure, on `t9-relayed`, on **method
B**. Run the three variants live, in this order:

```bash
python structured.py --tier 2 --misses --schema lax
python structured.py --tier 2 --misses --schema honest
python structured.py --tier 2 --misses --schema strict
```

| Variant | Method B | What broke |
|---|---|---|
| `lax` | 117/120 | `t9` → `None`, all three trials |
| `honest` | **120/120** | nothing |
| `strict` | 117/120 | `t9` → `'null'`, and `t4` → `'<UNKNOWN>'` |

**After `lax`, before revealing anything, ask the room why.** Method A gets `t9`
right every single time. Same model, same ticket, same rules. The only
difference is the schema. Let them work at it.

The answer: `reference_id` is the only nullable field, and its description ends
*"null if none"* after listing three things not to count. **The schema taught the
model that giving up was acceptable**, and on the one hard ticket it accepted the
invitation. Free text offers no such affordance.

Then `honest`: identical type, prose rewritten so the positive instruction comes
first and null is framed as the exception. 120/120.

Then `strict`, and this is the bit worth the whole session. Removing the null
makes it **worse**. `t9` fails again as the *string* `"null"` — it routed around
the constraint — and `t4`, which passed before, now returns `'<UNKNOWN>'`,
because nine of ten tickets have no reference and the schema now asserts
otherwise.

> **You cannot fix a prompt problem by tightening a type.** You make the schema
> lie about the world, and the model lies back politely to satisfy it.

Have them compare the two instructions directly:

```bash
python -c "import tickets as T; print(T.RULES)"
python -c "import tickets as T; print(T.schema('lax')['properties']['reference_id']['description'])"
```

700 characters against 148. The schema version lost the worked example and the
word "always". **Method B wasn't failing because it was schema-enforced. It was
failing because somebody compressed the instruction on the way into the schema**
— which is the most common mistake in writing tool definitions, and they have
just watched it cost three marks.

**Ask Friend 1:** *why do schema descriptions change output quality at all?*
They aren't executed. What is the model doing with them? He'll get there, and
step 3 is the proof.

## The local run, and the result that reframes everything

```bash
python structured_local.py --tier 2 --misses --label "27B IQ3_M"
```

| Model | Method A | Method B |
|---|---|---|
| Haiku 5.5, hosted | **100%** | 98% |
| Qwen3.6 27B, local | 97% | **100%** |

**The ranking inverts.** Free text wins on the frontier model; the schema wins
on the local 27B. Same tickets, same rules, opposite conclusion. The local
failures are both method A dropping a reference that *is* present.

Draw the conclusion explicitly, because it's the sentence the weekend keeps
returning to: **scaffolding helps whoever is struggling and slightly hinders
whoever isn't. Choose per workload, not per ideology.**

Note also that `--schema honest` changes *nothing* locally — byte-identical
numbers — because every local failure is in method A, which never sees the
schema. Good moment to ask who spotted that before you said it.

The local run also adds **constrained decoding**: the server compiles the schema
into a sampling grammar and masks the logits, so tokens that would break the
schema are literally unavailable. A small model *physically cannot* emit
malformed JSON.

## Running the room

**Start in `walkthrough/`, one screen, debugger open.** Three small programs,
one per method, stepped through line by line. Twenty minutes.
`walkthrough/README.md` has the Eclipse setup. Short version: F6 steps over,
never F5 on the `requests.post` line.

**Read the "thinking-mode trap" section of that README before the day.** On a
hybrid reasoning model, an unconstrained call will spend its whole token budget
on an internal monologue and hand back an empty `content` field — a baffling
result that looks like a broken lab. The programs switch thinking off and
explain why, but meet it in private first.

Expect walkthrough step 1 to **succeed** on a 27B. The framing becomes "it
worked — now what *made* it work?" Answer: nothing did. A probability is not a
guarantee.

Do the walkthrough even if — especially if — your audience is new to Python. The
three lab files have a loop, a scoring function and a backend adapter in the way.

**Use `--model`, not an export.** `python structured.py --model claude-haiku-5-5`
sets it for one run and prints it in the header. An export dies with the shell,
and "which model produced this number" is not a question you want live.

**If many calls fail with `APIConnectionError` on one method only**, that's rate
limiting, not the model. `METHODS` is the outer loop, so a limit that engages
partway through wipes out one whole method. The script retries and reports it;
space the runs out and re-run before trusting anything.

**Ask Friend 2:** *where does validation belong in a real system?* Model
boundary, API boundary, or both? And who owns the schema when the schema is also
the prompt?

## The punchline

Save this until after the three variants:

> "The only wrong field in 240 extractions came from the schema-enforced path —
> the safe one. And the schema caused it."

Then:

> **A schema guarantees the shape of an answer. Its accuracy is a property of
> how you wrote the schema.**

And the operational version, which is the sentence they should leave with:

> A malformed response is an outage — you find out in minutes. A well-formed
> wrong one is a data quality incident you discover three months later, and by
> then it's in every report you've sent.

That's the bridge to Lab 8. You cannot test your way out of the second kind with
a parser. You need evals.

## If you're short on time

Run tier 2 only and skip tier 1 — a capable model makes tier 1 uninformative.
Keep the code-reading segment. Keep `lax` and `honest`; they are the lab.

**Cut `strict` before you cut anything else, and cut the break-it experiments
first.** If you have to lose `strict`, say the one sentence out loud anyway:
tightening the type made it worse in two new ways.
