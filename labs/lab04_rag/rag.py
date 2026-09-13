#!/usr/bin/env python3
"""Lab 4 — RAG in about a hundred lines, then watching it fail.

    python rag.py "how many days annual leave do I get?"
    python rag.py --show-chunks "..."     # see what was actually retrieved
    python rag.py --failures              # run the three questions designed to break it

There is no vector database here on purpose. A vector DB is an index and a
network hop. The actual retrieval is four lines of numpy, and hiding that
behind a service makes RAG seem more sophisticated than it is.
"""

import argparse
import os
import re
from pathlib import Path

import anthropic
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
CORPUS = Path(__file__).parent / "corpus"

client = anthropic.Anthropic()
_encoder = None


def encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        print("Loading embedding model (first run downloads ~90MB)...")
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


# --------------------------------------------------------------------------
# 1. CHUNK — split documents into retrievable pieces
# --------------------------------------------------------------------------

def chunk_corpus() -> list[dict]:
    """Split on paragraph boundaries. Crude, and that's part of the lesson:
    chunking strategy determines what can ever be retrieved together."""
    chunks = []
    for path in sorted(CORPUS.glob("*.md")):
        text = path.read_text()
        for para in re.split(r"\n\s*\n", text):
            para = para.strip()
            if len(para) < 40:  # skip headers and stubs
                continue
            chunks.append({"source": path.name, "text": para})
    return chunks


# --------------------------------------------------------------------------
# 2. EMBED and 3. RETRIEVE — this is the entire "vector database"
# --------------------------------------------------------------------------

def build_index(chunks: list[dict]) -> np.ndarray:
    vectors = encoder().encode([c["text"] for c in chunks], normalize_embeddings=True)
    return np.asarray(vectors)


def retrieve(query: str, chunks: list[dict], index: np.ndarray, k: int = 3) -> list[dict]:
    qvec = encoder().encode([query], normalize_embeddings=True)[0]
    scores = index @ qvec                      # cosine similarity, vectors are normalised
    top = np.argsort(scores)[::-1][:k]
    return [{**chunks[i], "score": float(scores[i])} for i in top]


# --------------------------------------------------------------------------
# 4. GENERATE — stuff the retrieved text into the prompt
# --------------------------------------------------------------------------

PROMPT = """Answer the question using only the context below. If the context
does not contain enough information to answer, say so explicitly rather than
guessing.

Context:
{context}

Question: {question}"""


def answer(question: str, retrieved: list[dict]) -> str:
    context = "\n\n---\n\n".join(f"[{c['source']}]\n{c['text']}" for c in retrieved)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": PROMPT.format(context=context, question=question)}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


# --------------------------------------------------------------------------

FAILURE_QUESTIONS = [
    (
        "multi-hop",
        "What notice period does a Warehouse Supervisor have to give?",
        "Requires grades doc (Supervisor = Senior Associate) AND probation doc "
        "(below manager grade = one month). Neither chunk contains both facts, "
        "so neither scores highly on the combined question.",
    ),
    (
        "negation",
        "Which roles cannot work remotely?",
        "The answer lives in an exclusion clause. Embeddings are poor at "
        "negation — 'can work remotely' and 'cannot work remotely' sit very "
        "close together in vector space.",
    ),
    (
        "aggregation",
        "How many separate policies mention a monetary limit, and what are they?",
        "Requires reading every document. Top-k retrieval by definition cannot "
        "answer questions about the whole corpus. k=3 will never see all five.",
    ),
]


def run_failures(chunks, index, show_chunks: bool) -> None:
    print("\n" + "=" * 72)
    print("THE THREE QUESTIONS RAG IS BAD AT")
    print("=" * 72)

    for kind, question, why in FAILURE_QUESTIONS:
        print(f"\n\033[1m[{kind}]\033[0m {question}")
        retrieved = retrieve(question, chunks, index, k=3)

        print("\n\033[90mretrieved:\033[0m")
        for c in retrieved:
            preview = c["text"][:80].replace("\n", " ")
            print(f"\033[90m  {c['score']:.3f}  {c['source']:<24} {preview}...\033[0m")
            if show_chunks:
                print(f"\033[90m         {c['text']}\033[0m")

        print(f"\n\033[94m{answer(question, retrieved)}\033[0m")
        print(f"\n\033[93mwhy this is hard: {why}\033[0m")
        print("-" * 72)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("-k", type=int, default=3, help="chunks to retrieve")
    ap.add_argument("--show-chunks", action="store_true")
    ap.add_argument("--failures", action="store_true")
    args = ap.parse_args()

    chunks = chunk_corpus()
    index = build_index(chunks)
    print(f"Indexed {len(chunks)} chunks from {len(list(CORPUS.glob('*.md')))} documents.")

    if args.failures:
        run_failures(chunks, index, args.show_chunks)
    else:
        q = args.question or "how many days annual leave do I get?"
        print(f"\n\033[1mQ:\033[0m {q}\n")
        retrieved = retrieve(q, chunks, index, args.k)
        for c in retrieved:
            preview = c["text"][:80].replace("\n", " ")
            print(f"\033[90m  {c['score']:.3f}  {c['source']:<24} {preview}...\033[0m")
            if args.show_chunks:
                print(f"\033[90m         {c['text']}\n\033[0m")
        print(f"\n\033[94m{answer(q, retrieved)}\033[0m\n")
