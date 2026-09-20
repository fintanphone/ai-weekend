# Facilitator Briefings

One per session. Each is a script for the person standing at the front of the
room — what to say, what to draw, which questions to hand to whom, and what to
cut when you're running behind.

These are **not** the same as the lab READMEs. A README is written for the
person at the keyboard: goal, steps, expected output, troubleshooting. A
briefing is written for the person explaining it, and is meant to be delivered
before anyone opens a laptop.

| Session | Briefing | When | Length |
|---|---|---|---|
| Foundations | [`lab00_foundations/BRIEFING.md`](lab00_foundations/BRIEFING.md) | Sat 10:00 | 45 min |
| Local inference | [`lab01_local_serving/BRIEFING.md`](lab01_local_serving/BRIEFING.md) | Sat 10:45 | 60 min |
| Structured output | [`lab02_structured_output/BRIEFING.md`](lab02_structured_output/BRIEFING.md) | Sat 12:00 | 45 min |
| The agent loop ★ | [`lab03_agent_loop/BRIEFING.md`](lab03_agent_loop/BRIEFING.md) | Sat 13:45 | 90 min |
| Retrieval | [`lab04_rag/BRIEFING.md`](lab04_rag/BRIEFING.md) | Sat 15:30 | 75 min |
| Skills | [`lab05_skills/BRIEFING.md`](lab05_skills/BRIEFING.md) | Sun 10:15 | 60 min |
| MCP | [`lab06_mcp/BRIEFING.md`](lab06_mcp/BRIEFING.md) | Sun 11:30 | 75 min |
| Agentic coding | [`lab07_agentic_coding/BRIEFING.md`](lab07_agentic_coding/BRIEFING.md) | Sun 13:45 | 75 min |
| Evals & guardrails ★ | [`lab08_evals/BRIEFING.md`](lab08_evals/BRIEFING.md) | Sun 15:15 | 60 min |

★ = protect these two. Everything else is negotiable.

## How each briefing is laid out

The same shape every time, so you can find what you need mid-session:

- **Open with** — the actual framing sentence. Say it more or less verbatim
- **The scenario** — the concrete problem, in terms a non-specialist gets
- **The challenges** — what makes it hard, usually three things people conflate
- **What the code has to do** — the structure, before they read the file
- **Running the room** — the mechanics, plus a question for each friend
- **The punchline** — the line to leave on the board
- **If you're short on time** — what to cut, and what never to cut

## Reading order for prep

If you read nothing else the week before, read the Foundations briefing and
Lab 3. Those two carry the weekend: the first establishes the vocabulary and the
second proves it.

Lab 8 is the one people skip in planning and regret skipping on the day. Both of
your friends are entering the job market, and it's the hour with the clearest
line to employability.

## The running threads

Four ideas recur across sessions. Naming them out loud each time they come back
is most of what makes two days feel like one argument rather than nine
disconnected topics.

**The model chooses, your code executes.** Introduced in Foundations, proved in
Lab 3, applied to permissioning in Lab 6, and the basis of every guardrail in
Lab 8.

**Valid is not correct.** Lab 2's two columns, Lab 4's confident wrong answers,
Lab 7's plausible diff, and the case in Lab 8 that asks for data that doesn't
exist. Same failure, four costumes.

**Context is the scarce resource.** The budget bar in Foundations, the KV cache
in Lab 1, progressive disclosure in Lab 5, and the cost arithmetic in Lab 8.

**The description is the interface.** Tool descriptions in Lab 3, schema field
descriptions in Lab 2, skill descriptions in Lab 5, docstrings in Lab 6. Prose
that a model reads to make a decision is load-bearing code.
