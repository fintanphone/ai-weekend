# Lab 4 — RAG, and Watching It Fail

**75 minutes · pairs · first on the cut-list, see `FACILITATOR.md`**

## Goal

Build retrieval-augmented generation from scratch, then break it on purpose.

The breaking is the point. Making RAG work on a friendly question takes ten
minutes and teaches you almost nothing. Understanding the three question shapes
it reliably fails on will save either of them six months of confusion.

## The uncomfortable idea

> RAG is a search problem wearing an AI costume.

Most production RAG failures are search failures: bad chunking, bad ranking, a
question the index shape can't answer. People respond by changing the model,
which does nothing, because the model never saw the right text in the first place.

There is **no vector database in this lab**, deliberately. A vector DB is an
index and a network hop. The actual retrieval here is four lines of numpy, and
hiding that behind a service makes RAG look more sophisticated than it is.

## Steps

### 1. Look at the corpus

```bash
ls corpus/
cat corpus/handbook_grades.md corpus/handbook_probation.md
```

Five short policy documents for a fictional freight company. Read them — you'll
need to know what's in them to judge whether the answers are right.

### 2. Read `rag.py`

Four functions, four stages, in order: **chunk → embed → retrieve → generate.**

The whole "vector database" is these two lines:

```python
scores = index @ qvec          # cosine similarity
top = np.argsort(scores)[::-1][:k]
```

That's it. Everything else in the RAG tooling ecosystem is operational
convenience around those two lines.

### 3. Make it work

```bash
python rag.py "how many days annual leave do I get?"
python rag.py "can I claim for a hotel dinner?" --show-chunks
python rag.py "what happens if I submit an expense late?"
```

These work well. Note the retrieval scores — the right chunk sits clearly at the
top. Enjoy it briefly.

### 4. Now break it

```bash
python rag.py --failures --show-chunks
```

Three questions, three different failure modes:

**Multi-hop** — *"What notice period does a Warehouse Supervisor have to give?"*
The answer needs two facts from two documents: Supervisor is Senior Associate
grade (grades doc), and below-manager grade means one month (probation doc).
Neither chunk contains both. Neither scores highly against the combined
question. The system retrieves plausible-looking text and answers wrongly, or
hedges.

**Negation** — *"Which roles cannot work remotely?"*
The answer is in an exclusion clause. Embeddings are notoriously poor at
negation: "can work remotely" and "cannot work remotely" are near-neighbours in
vector space, because they're about the same *topic*.

**Aggregation** — *"How many policies mention a monetary limit?"*
Top-k retrieval structurally cannot answer questions about the whole corpus.
With `k=3` it will never see all five documents. Raising `k` doesn't fix the
class of problem, it just moves the threshold.

### 5. Try to fix them

Twenty minutes, in pairs. Attempt each:

- Raise `k` to 10. What improves? What gets worse? (Watch the token count.)
- Change the chunking to whole documents instead of paragraphs. Which questions
  get better, which get worse?
- Add the question *"what grade is a Warehouse Supervisor?"* as a first
  retrieval, then use its answer to make a second query. **You have just
  reinvented agentic RAG** — retrieval as a tool inside a loop, rather than a
  fixed pipeline step. Say this out loud; it's the connection back to Lab 3.

## Expected output

The friendly questions answer correctly with high similarity scores. The three
failure questions produce answers that are plausible, well-written, and wrong or
incomplete — which is precisely why this failure mode is dangerous.

## Discussion (15 min)

1. A user asks the multi-hop question and gets a confident wrong answer. How
   would you ever find out? What would the monitoring even look like?
2. Which of the three failures could be fixed by a better model, and which are
   structural?
3. When would you not use RAG at all? (Small corpus that fits in context; data
   that belongs in a SQL query; questions that need computation not retrieval.)
4. Friend 1: what's actually being lost when a paragraph becomes a 384-dimension
   vector? Have him explain why negation survives so poorly.

## If it breaks

**Slow first run** — it's downloading the embedding model. Once only.

**`No module named sentence_transformers`** — `pip install -r requirements.txt`.

**Torch/CUDA warnings on the laptops** — harmless. The embedding model runs fine
on CPU at this scale.

**Everything retrieves with score ~0.99** — you're probably embedding the query
into the index by mistake. Check `build_index` and `retrieve` use separate calls.

## Takeaway

> Retrieval decides what the model *can* know. The model only decides how well
> it says it. Debug the retrieval first, every time.
