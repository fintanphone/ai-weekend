#!/usr/bin/env python3
"""Lab 4b — the same RAG pipeline, generated on your own GPU.

Here is the thing worth noticing before you run anything: HALF OF THIS LAB WAS
ALREADY LOCAL. `rag.py` embeds with sentence-transformers, which runs on your
CPU and never touches a network. The only part that left the building was the
last step - generation.

So "making RAG local" means swapping one function. Everything about chunking,
embedding and retrieval is unchanged, and the retrieved chunks are identical to
the ones `rag.py` gets. That is useful: it isolates the generator. If the answer
changes, the generator is the only thing that changed.

    python rag_local.py "how many days annual leave do I get?"
    python rag_local.py --no-context "..."   # the control: no retrieval at all
    python rag_local.py --k-sweep            # what does more context cost?
    python rag_local.py --grounding          # does it admit what it cannot know?
    python rag_local.py --failures           # the three structural failures
    python rag_local.py --show-chunks "..."  # full text of what was retrieved

Works against llama.cpp (llama-server) or Ollama, whichever is listening.
"""

import argparse
import re
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from local_backend import connect  # noqa: E402

load_dotenv()

CORPUS = Path(__file__).parent / "corpus"
_encoder = None


def encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        print("Loading embedding model (first run downloads ~90MB)...")
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


# --------------------------------------------------------------------------
# 1. CHUNK   2. EMBED   3. RETRIEVE
#     — byte for byte the same as rag.py. Nothing here changes.
# --------------------------------------------------------------------------

def chunk_corpus() -> list[dict]:
    chunks = []
    for path in sorted(CORPUS.glob("*.md")):
        text = path.read_text()
        for para in re.split(r"\n\s*\n", text):
            para = para.strip()
            if len(para) < 40:
                continue
            chunks.append({"source": path.name, "text": para})
    return chunks


def build_index(chunks: list[dict]) -> np.ndarray:
    vectors = encoder().encode([c["text"] for c in chunks], normalize_embeddings=True)
    return np.asarray(vectors)


def retrieve(query: str, chunks: list[dict], index: np.ndarray, k: int = 3) -> list[dict]:
    qvec = encoder().encode([query], normalize_embeddings=True)[0]
    scores = index @ qvec
    top = np.argsort(scores)[::-1][:k]
    return [{**chunks[i], "score": float(scores[i])} for i in top]


# --------------------------------------------------------------------------
# 4. GENERATE   — the ONLY function that differs from rag.py
# --------------------------------------------------------------------------

PROMPT = """Answer the question using only the context below. If the context
does not contain enough information to answer, say so explicitly rather than
guessing.

Context:
{context}

Question: {question}"""

# Used by --no-context. Same question, nothing retrieved, no grounding
# instruction. This is what the model believes on its own.
BARE_PROMPT = """{question}"""


def build_context(retrieved: list[dict]) -> str:
    return "\n\n---\n\n".join(f"[{c['source']}]\n{c['text']}" for c in retrieved)


def answer(be, question: str, retrieved: list[dict] | None) -> dict:
    """Returns the reply plus what it cost. retrieved=None means no context."""

    if retrieved is None:
        prompt = BARE_PROMPT.format(question=question)
    else:
        prompt = PROMPT.format(context=build_context(retrieved), question=question)

    start = time.perf_counter()
    out = be.chat([{"role": "user", "content": prompt}], max_tokens=600, temperature=0.0)
    seconds = time.perf_counter() - start

    usage = out.get("usage") or {}
    sent = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    got = usage.get("completion_tokens") or usage.get("output_tokens") or 0

    return {"text": (out.get("text") or "").strip(), "seconds": seconds,
            "tokens_in": sent, "tokens_out": got, "prompt_chars": len(prompt)}


# --------------------------------------------------------------------------
# printing helpers
# --------------------------------------------------------------------------

def show_retrieved(retrieved, full=False):
    print("\033[90mretrieved:\033[0m")
    for c in retrieved:
        preview = c["text"][:76].replace("\n", " ")
        print(f"\033[90m  {c['score']:.3f}  {c['source']:<24} {preview}...\033[0m")
        if full:
            for line in c["text"].splitlines():
                print(f"\033[90m         {line}\033[0m")
            print()


def show_answer(result):
    print()
    for line in result["text"].splitlines():
        print(f"\033[94m{line}\033[0m")
    print()
    print(f"\033[90m  {result['tokens_in']} tokens in, {result['tokens_out']} out, "
          f"{result['seconds']:.1f}s\033[0m")


# --------------------------------------------------------------------------
# the normal path, with a timing breakdown
# --------------------------------------------------------------------------

def run_one(be, chunks, index, question, k, show_chunks, no_context):
    print(f"\n\033[1mQ:\033[0m {question}\n")

    if no_context:
        print("\033[93m  NO RETRIEVAL. The model gets the bare question and "
              "nothing else.\033[0m\n")
        result = answer(be, question, None)
        show_answer(result)
        print("""
\033[93mRead that answer again, carefully.\033[0m
It is fluent, it is confident, and it is about a company that does not exist.
Any number in it was invented. Nothing in the prompt could have contradicted
it, because the prompt contained nothing.

Now run the same question without --no-context and compare.
""")
        return

    t0 = time.perf_counter()
    retrieved = retrieve(question, chunks, index, k)
    retrieval_seconds = time.perf_counter() - t0

    show_retrieved(retrieved, show_chunks)
    result = answer(be, question, retrieved)
    show_answer(result)

    # Where did the time actually go? On a local model this is lopsided, and
    # the shape of it surprises people.
    total = retrieval_seconds + result["seconds"]
    r_pct = 100 * retrieval_seconds / total if total else 0
    g_pct = 100 * result["seconds"] / total if total else 0
    print()
    print("\033[90m  time breakdown\033[0m")
    print(f"\033[90m    embed + retrieve  {retrieval_seconds:6.3f}s  {r_pct:4.1f}%\033[0m")
    print(f"\033[90m    generate          {result['seconds']:6.3f}s  {g_pct:4.1f}%\033[0m")
    print()
    print("\033[90m  Retrieval is the part everyone worries about optimising.\033[0m")
    print("\033[90m  Look at which row is bigger.\033[0m")
    print()


# --------------------------------------------------------------------------
# --k-sweep : what does more context actually buy?
# --------------------------------------------------------------------------

def run_k_sweep(be, chunks, index, question, show_chunks):
    print("\n" + "=" * 72)
    print("WHAT DOES MORE CONTEXT COST, AND DOES IT HELP?")
    print("=" * 72)
    print(f"\n\033[1mQ:\033[0m {question}\n")
    print(f"  (the corpus has {len(chunks)} chunks in total)\n")

    print(f"  {'k':>3} {'chars sent':>11} {'tokens in':>10} {'seconds':>9}   first line of the answer")
    print("  " + "-" * 94)

    for k in (1, 3, 5, 10):
        if k > len(chunks):
            continue
        retrieved = retrieve(question, chunks, index, k)
        result = answer(be, question, retrieved)
        first = result["text"].splitlines()[0] if result["text"] else "(empty)"
        print(f"  {k:>3} {result['prompt_chars']:>11} {result['tokens_in']:>10} "
              f"{result['seconds']:>8.1f}s   {first[:50]}")

    print("""
\033[93mThings to look at:\033[0m
  - tokens in grows roughly linearly with k, and so does the time
  - the answer usually stops improving well before k=10
  - at k=10 you are sending half the corpus. At that point, ask yourself why
    you are doing retrieval at all rather than just sending everything

Raising k is the first thing everyone tries when RAG gives a bad answer. It
treats a precision problem by paying for recall, and it is why so many RAG
systems are slow and expensive without being more accurate.
""")


# --------------------------------------------------------------------------
# --grounding : will it admit what it cannot know?
# --------------------------------------------------------------------------

# Questions the corpus genuinely cannot answer. The prompt tells the model to
# say so. Does it?
GROUNDING_QUESTIONS = [
    ("What is the sick pay policy?",
     "nothing in the corpus mentions sick pay at all"),
    ("How much is the annual bonus worth?",
     "the grades doc mentions bonus ELIGIBILITY but never an amount - so "
     "retrieval returns a relevant-looking chunk that does not answer the "
     "question. This is the hard one"),
    ("Who is the CEO of Aurora Freight?",
     "never mentioned anywhere"),
    ("How many days of paternity leave are there?",
     "the leave policy covers annual leave only"),
]

# A crude check for refusal language. Crude on purpose - read the answers
# yourself rather than trusting this column.
REFUSAL_HINTS = ["does not", "doesn't", "do not contain", "not contain",
                 "no information", "not specified", "not mentioned",
                 "not stated", "cannot determine", "can't determine",
                 "not provided", "unable to", "not enough information",
                 "does not say", "doesn't say", "no mention", "not include"]


def looks_like_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in REFUSAL_HINTS)


def run_grounding(be, chunks, index, show_chunks):
    print("\n" + "=" * 72)
    print("WILL IT ADMIT WHAT IT CANNOT KNOW?")
    print("=" * 72)
    print("""
Every question below is unanswerable from this corpus. The prompt explicitly
says "if the context does not contain enough information to answer, say so
explicitly rather than guessing".

Retrieval will still return three chunks for each one, because retrieval always
returns three chunks. They will look relevant. They will not contain the answer.
""")

    honest = 0

    for question, why in GROUNDING_QUESTIONS:
        print("-" * 72)
        print(f"\n\033[1mQ:\033[0m {question}")
        print(f"\033[90m   ({why})\033[0m\n")

        retrieved = retrieve(question, chunks, index, k=3)
        show_retrieved(retrieved, show_chunks)
        result = answer(be, question, retrieved)
        show_answer(result)

        refused = looks_like_refusal(result["text"])
        honest += refused
        verdict = ("\033[92mSAID IT DIDN'T KNOW\033[0m" if refused
                   else "\033[91mANSWERED ANYWAY\033[0m")
        print(f"\n  verdict: {verdict}")
        print()

    print("=" * 72)
    print(f"  admitted ignorance on {honest} of {len(GROUNDING_QUESTIONS)}")
    print("=" * 72)
    print("""
\033[93mThe verdict column is a keyword match, not a judge. Read the answers.\033[0m

This is the single most important property of a RAG system and almost nobody
measures it. A system that answers 95% of questions well and invents the other
5% without flagging them is worse than useless, because you cannot tell which
5%.

Smaller and more heavily quantised models are measurably worse at this. The
instruction to refuse is right there in the prompt; following it reliably is a
capability, not a given.

This is the same failure as Lab 2's second column and Lab 8's refusal-honesty
case, wearing a third costume.
""")


# --------------------------------------------------------------------------
# --failures : the three structural failures, same as rag.py
# --------------------------------------------------------------------------

FAILURE_QUESTIONS = [
    ("multi-hop",
     "What notice period does a Warehouse Supervisor have to give?",
     "Needs grades doc (Supervisor = Senior Associate) AND probation doc "
     "(below manager grade = one month). No chunk contains both facts, so "
     "neither scores highly on the combined question. Caused at CHUNKING."),
    ("negation",
     "Which roles cannot work remotely?",
     "The answer is an exclusion clause. Embeddings encode subject matter, "
     "not polarity - 'can work remotely' and 'cannot work remotely' sit "
     "almost on top of each other. Caused at EMBEDDING."),
    ("aggregation",
     "How many separate policies mention a monetary limit, and what are they?",
     "Needs every document. Top-k cannot answer a question about the whole "
     "corpus; k=3 never sees all five. Caused at RETRIEVAL."),
]


def run_failures(be, chunks, index, show_chunks):
    print("\n" + "=" * 72)
    print("THE THREE QUESTIONS RAG IS BAD AT")
    print("=" * 72)

    for kind, question, why in FAILURE_QUESTIONS:
        print(f"\n\033[1m[{kind}]\033[0m {question}\n")
        retrieved = retrieve(question, chunks, index, k=3)
        show_retrieved(retrieved, show_chunks)
        result = answer(be, question, retrieved)
        show_answer(result)
        print(f"\n\033[93mwhy this is hard: {why}\033[0m")
        print("-" * 72)

    print("""
None of these improve with a better generator, because the generator was never
the problem - the right text never reached the prompt. Swap the model, run it
again, and watch the answers stay wrong.

That is the whole argument of this lab:
  \033[93mretrieval decides what the model CAN know. Debug retrieval first.\033[0m
""")


# --------------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("-k", type=int, default=3, help="chunks to retrieve")
    ap.add_argument("--show-chunks", action="store_true", help="full text of each chunk")
    ap.add_argument("--no-context", action="store_true", help="the control: no retrieval")
    ap.add_argument("--k-sweep", action="store_true", help="k=1,3,5,10 side by side")
    ap.add_argument("--grounding", action="store_true", help="unanswerable questions")
    ap.add_argument("--failures", action="store_true", help="the three structural failures")
    args = ap.parse_args()

    try:
        backend = connect()
    except ConnectionError as exc:
        print(f"\n\033[91m{exc}\033[0m\n")
        sys.exit(1)

    chunks = chunk_corpus()
    index = build_index(chunks)

    print()
    print(f"  backend   {backend.kind} at {backend.base}")
    print(f"  model     {backend.model_name}")
    print(f"  embedding all-MiniLM-L6-v2, on this CPU  "
          f"\033[90m(already local before we changed anything)\033[0m")
    print(f"  indexed   {len(chunks)} chunks from "
          f"{len(list(CORPUS.glob('*.md')))} documents")

    question = args.question or "how many days annual leave do I get?"

    if args.failures:
        run_failures(backend, chunks, index, args.show_chunks)
    elif args.grounding:
        run_grounding(backend, chunks, index, args.show_chunks)
    elif args.k_sweep:
        run_k_sweep(backend, chunks, index, question, args.show_chunks)
    else:
        run_one(backend, chunks, index, question, args.k,
                args.show_chunks, args.no_context)
