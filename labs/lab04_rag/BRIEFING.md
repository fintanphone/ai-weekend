# Lab 4 — Retrieval

**Briefing for the facilitator.** Saturday 15:30 · 75 minutes · pairs.

*First on the cut-list if you're behind. See `facilitator/FACILITATOR.md`.*

---

## Open with

> "Everyone's first instinct after Lab 3 is 'great, now let me point it at my
> own documents.' This is that lab. We'll build it in sixty lines — and then
> we're going to spend most of the time deliberately breaking it, because the
> breaking is what's actually useful."

## The scenario

A fictional freight company has five short policy documents — leave, expenses,
remote working, probation, grades. Staff ask questions. The documents have the
answers. Connect the two.

This is the single most common thing people build with a model, and it's the
thing they most reliably get wrong.

## The uncomfortable idea, stated early

> **RAG is a search problem wearing an AI costume.**

Most production RAG failures are *search* failures: bad chunking, bad ranking,
or a question the index shape simply cannot answer. People respond by swapping
the model, which does nothing at all, because the model never saw the right text
in the first place.

Say this at the start and then let the lab prove it.

## Why there's no vector database

Worth being explicit, because they'll have read about Pinecone and friends:

> "There's no vector database in this lab, on purpose. A vector DB is an index
> and a network hop. The actual retrieval here is four lines of numpy. Hiding
> those four lines behind a service makes this look more sophisticated than it
> is — and makes failures much harder to reason about."

Show them the two lines that *are* the whole thing:

```python
scores = index @ qvec          # cosine similarity
top = np.argsort(scores)[::-1][:k]
```

Everything else in the RAG tooling ecosystem is operational convenience around
those two lines.

## The four stages

Draw them: **chunk → embed → retrieve → generate.**

Then circle the third one.

> "Stage three decides what the model *can* know. Stage four only decides how
> well it says it. When an answer is wrong, almost everyone debugs stage four."

## The three questions it cannot answer

This is the core of the lab. Each failure is structural, not a tuning problem.

**Multi-hop.** *"What notice period does a Warehouse Supervisor have to give?"*
The answer needs two facts from two documents — Supervisor is Senior Associate
grade, and below-manager grade means one month. Neither chunk contains both.
Neither scores highly against the combined question. The system retrieves
plausible-looking text and answers confidently wrong.

**Negation.** *"Which roles cannot work remotely?"* The answer is in an
exclusion clause. Embeddings are poor at negation — "can work remotely" and
"cannot work remotely" are near-neighbours in vector space, because they're
about the same *topic*.

**Aggregation.** *"How many policies mention a monetary limit?"* Top-k retrieval
structurally cannot answer a question about the whole corpus. With k=3 it will
never see all five documents. Raising k doesn't fix the class of problem — it
moves the threshold.

## What the code has to do

**Chunk on paragraph boundaries.** Crude, and that's part of the lesson:
chunking strategy determines what can *ever* be retrieved together. If the two
facts a question needs land in different chunks, no amount of model quality
recovers it.

**Embed and normalise.** Then similarity is a dot product, which is why the
retrieval is two lines.

**Show the scores.** Every result prints its similarity. People need to see that
a wrong answer often came from a chunk that scored *well* — the retrieval was
confident and still unhelpful.

**Stuff the top-k into the prompt with sources.** And instruct the model to say
when the context is insufficient. Then watch how often it doesn't.

## Running the room

Have them read the five policy documents first. They need to know what's in
there to judge whether an answer is right — otherwise they're grading output
they can't evaluate.

Start with friendly questions so it works. Enjoy it briefly. Then run the three
failures with `--show-chunks` so they can see exactly what the model was handed.

**The fix that matters:** have them answer *"what grade is a Warehouse
Supervisor?"* first, then use that answer to make a second query.

> "You've just reinvented agentic RAG. Retrieval as a tool inside yesterday's
> loop, rather than a fixed pipeline step. That's the whole difference, and
> you got there by hitting the wall yourself."

Say that out loud — it's the connection back to Lab 3 and forward to Lab 6.

**Ask Friend 1:** *what's actually lost when a paragraph becomes a
384-dimension vector?* Why does negation survive so badly? He has the background
for this and it's a better answer than "embeddings are bad at negation".

**Ask Friend 2:** *a user asks the multi-hop question and gets a confident wrong
answer. How would you ever find out?* What does monitoring even look like when
the failure is semantic and the system reports success?

## The punchline

> Retrieval decides what the model **can** know. Debug the retrieval first,
> every time.

## If you're short on time

This is the designated cut. Reduce it to a fifteen-minute demo you drive
yourself: show the three failure questions and the retrieved chunks, skip the
build entirely. It's the most self-contained topic of the weekend and the
easiest to pick up later from the README.
