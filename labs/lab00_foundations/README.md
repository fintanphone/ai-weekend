# Session 0 — Foundations

**Saturday 10:00 · 45 minutes · whiteboard only · no laptops**

There's no code in this folder, and that's deliberate. This session is a
whiteboard conversation covering five ideas that make everything else in the
weekend obvious rather than magical:

1. The API is stateless — every call resends the whole conversation
2. The context window is a budget, not a memory
3. Tool use is a contract — the model requests, your code executes
4. The loop — call, tool, result, repeat — is what "agent" means
5. The risk lives in the split between choosing and executing

The facilitator script is in [`BRIEFING.md`](BRIEFING.md): what to draw, in what
order, and which questions to hand to whom.

## For participants

Nothing to install, nothing to run. Turn up with a coffee and no laptop open.

If you want to read ahead — genuinely optional — Anthropic's
[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
covers most of idea four and is the best short piece on when *not* to build an
agent.

## The one sentence

Everything over the two days is a variation on this:

> **An agent is a while-loop around a model that can call functions.**

If that feels obvious by Sunday evening, the weekend worked.
