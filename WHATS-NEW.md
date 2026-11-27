# What changed since the last build

Everything below is already in this copy. The open questions at the bottom are
the only things still waiting on you.

---

## New

**`labs/lab03b_tools_and_actions/`** — a second agentic lab. Same loop as Lab 3,
but one tool has a side effect: it sends an email. Covers the human in the loop,
a cross-customer data leak and the three rungs of fixing it (nothing → a rule in
the prompt → a rule in the code). Runs on SQLite with no install, or on
PostgreSQL via `DATABASE_URL`. 45 minutes, unscheduled in the agenda.

**`droplet/`** — `bootstrap.sh`, `add_user.sh` and a walkthrough README for
standing up the shared box. Creates accounts from `keys/*.pub`, hardens SSH,
sets up a PostgreSQL database per person, builds a shared venv with CPU-only
torch, and installs Node and Claude Code. Safe to re-run.

**`labs_audio/`** — the nine narration recordings, one per lab, plus the scripts
they were read from in `scripts/`. Lab 2's was re-cut to fix a sentence the
speech engine rushed at 4:12.

**Three new PDFs** in `pdfs/`:
- `Lab1-Context-KV-Weights.pdf` — weights vs KV cache vs context length, drawn
  to scale on a 16 GiB card. Show it before Lab 1's terminal work.
- `Closing-Hosted-or-Local.pdf` — the weekend's closing slide, built on the
  measured inversion between hosted and local.
- `Housekeeping.pdf` (and `.html`) — the deadpan opening slide.

## Changed

**Models.** `.env.example` now defaults to `WORKSHOP_MODEL=claude-haiku-5-5`,
because Lab 2's central finding only appears on Haiku — Sonnet scores 100% on
both methods and leaves nothing to discuss. `JUDGE_MODEL` moved to
`claude-sonnet-5` so the judge is never the same model as the thing it grades.
The in-code fallbacks in all eight scripts were changed to match, so a missing
`.env` no longer silently switches model.

**Lab 1** — new `kv_math.py` pulls the hidden GGUF metadata and does the KV
arithmetic, including hybrid attention models. `bench.py` takes `--base`. The
README gained an Ollama vs llama-server comparison and a table of which commands
run where.

**Lab 2** — `tickets.py` gained four tier-2 tickets (brand-as-verb, product
brand, employer-is-brand, common-noun company) and three schema variants
(`lax`, `honest`, `strict`). `structured.py` gained `--schema`, `--model`,
`--raw` and retry-with-backoff, after rate limiting wiped out a whole method
mid-run.

**Lab 8** — the judge's tokens are now counted, and both models appear in the
header and in every result row.

**`labs/common/local_backend.py`** — Ollama is detected properly (it also serves
`/v1/models`, which used to make it look like llama-server), an explicit
`LOCAL_API_BASE` is never silently fallen back on, and there is optional bearer
auth via `LOCAL_API_KEY`.

**`SETUP.md`** — `python -m pip` throughout, a warning that a venv is per
terminal, and current links.

---

## Still open

**The walkthrough programs hardcode `localhost:8080`.** All seven of them, in
Labs 2 and 3, and neither walkthrough README mentions it. If the model is on
another machine they all fail with connection refused. Three ways out, and you
haven't picked one yet:

1. run the walkthroughs on the GPU box, where `localhost` is correct
2. `sed` the address once as a setup step, documented in the README
3. make the line `SERVER = os.environ.get("LOCAL_API_BASE", "http://localhost:8080")`

**The closing slide's local numbers are from the six-ticket era.** The hosted
column is the current ten tier-2 tickets; the local column is `70/72` from when
there were six. The inversion held on both, but re-run
`python structured_local.py --tier 2 --misses --label "27B IQ3_M"` before
presenting them as a matched pair. The figures live in `MEASURED` at the top of
`pdf_build_scripts/build_closing_slide.py` — edit that block and rebuild.

**`walkthrough/README.md` in Lab 2 still frames step 1 as expected to fail.**
On a current model it succeeds. The lab README and BRIEFING were corrected; this
one wasn't.

---

## Note on `facilitator/`

It holds the Lab 7 answer key and the cut-list, and it is gitignored. The
droplet scripts now exclude it when copying the repo into each person's home, so
it will not leak even if it is sitting in `/root`. If you share this repo any
other way, delete that folder first.
