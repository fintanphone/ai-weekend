# The Agentic AI Weekend

A two-day, hands-on workshop for three people. No slides beyond a whiteboard, no
frameworks until you've built the thing by hand.

## The one idea

Everything in this workshop is a variation on a single sentence:

> **An agent is a while-loop around a model that can call functions.**

Skills, RAG, MCP, memory, multi-agent orchestration — all of it is plumbing
bolted onto that loop. If you leave the weekend genuinely believing that
sentence, and having written the loop yourself, the entire field stops looking
like magic and starts looking like software.

## Who this is for

| | Background | What they get out of it |
|---|---|---|
| **Host** | Runs the labs, owns the GPU | A repeatable workshop you can run again |
| **Friend 1** | MSc in AI, light on practice | Theory grounded in running code, plus a portfolio project scoped and started |
| **Friend 2** | Cloud/infra background | A working mental model, plus an AI-platform-engineering angle for the job market |

They are complementary. **Pair them at one machine for most labs** and let each
be the expert for half the day. Friend 1 explains why the attention mechanism
means context is expensive; Friend 2 explains why you'd never run that in
production without a circuit breaker. Both are right.

## The ladder

Each lab is visibly one small step up from the last. Don't skip rungs — the
whole design depends on the steps feeling small.

```
prompt
  └── structured output          (model becomes a software component)
        └── tool call            (model can affect the world)
              └── loop           (← this is an agent)
                    └── skills   (context loaded on demand)
                          └── MCP        (tools as a protocol)
                                └── real agentic work
                                      └── evals & guardrails
```

## Repo layout

```
.
├── README.md          you are here
├── SETUP.md           send this to both friends a week ahead
├── AGENDA.md          the timed two-day plan
├── PORTFOLIO.md       project tracks for both friends
├── check_setup.py     run this first, on all three machines
├── requirements.txt
├── .env.example
└── labs/
    ├── common/                shared local-backend adapter
    ├── lab01_local_serving/    your GPU, measured
    ├── lab02_structured_output/  JSON, and why it matters (API + local)
    ├── lab03_agent_loop/       ★ the centrepiece — build it by hand
    ├── lab04_rag/              retrieval, and watching it fail
    ├── lab05_skills/           progressive disclosure, implemented from scratch
    ├── lab06_mcp/              use a server, then write one
    ├── lab07_agentic_coding/   turn an agent loose on a real repo
    └── lab08_evals/            the thing that separates demo from system
```

Every lab folder has its own `README.md` with: **goal → steps → expected output
→ if it breaks**. Working solutions live on the `solutions` branch.

### The facilitator folder

If you're the host, you'll also have a `facilitator/` directory containing the
prep checklist, the cut-list for when you run behind, and the answer key for the
Lab 7 planted bugs.

**It is gitignored on purpose.** Those exercises are worth much less if the
answers are one click away in the shared repo. Keep your local copy; it won't
travel when you clone this somewhere else, so don't delete the original.

## Quick start

```bash
git clone <your-repo-url> ai-agents-weekend
cd ai-agents-weekend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then paste your API key into .env
python check_setup.py
```

If `check_setup.py` prints all green, you're ready. If it doesn't, fix it
**before** the weekend starts. Two hours lost to CUDA drivers on Saturday
morning kills the whole event.

## A note on models

The labs deliberately use **two different kinds of model**:

- **Local models on the GPU** (Lab 1, and comparisons throughout) — for
  understanding inference economics, VRAM, quantisation, and throughput.
- **A frontier API model** (Labs 2–8) — for the agentic work.

Labs 1 and 2b auto-detect your local backend — llama.cpp (`llama-server`) or
Ollama, whichever is listening. See `labs/common/local_backend.py`, and run it
directly to see what it finds.

This split is intentional and worth explaining out loud on Saturday morning.
Small local models in the 8B range are genuinely unreliable at multi-step tool
calling. If you build the agent labs on them you will spend the weekend
debugging malformed JSON instead of learning agentic patterns. Lab 1 makes that
failure mode visible on purpose, and then we move on.
