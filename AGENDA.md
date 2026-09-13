# The Agenda

Two days, roughly 10:00–17:30 each. Times are deliberately generous. Everything
takes twice as long with an audience, and the conversations that break out
mid-lab are usually more valuable than finishing on schedule.

**Read `facilitator/FACILITATOR.md` before Saturday.** It has the cut-list for when you run
behind, and you will run behind.

---

# Saturday — Mechanics

## 09:30 · Coffee and setup check (30 min)

Run `python check_setup.py` on all three laptops. Fix anything red now.

If someone ignored `SETUP.md`, this is when you find out. Have a USB stick with
the wheels cached, or pair them with someone whose machine works.

## 10:00 · Session 0 — How a model actually gets used (45 min, whiteboard)

**No code. No laptops open.** This is the session that makes everything else land.

Draw these five things, in order:

1. **The API is stateless.** Every call sends the entire conversation. There is
   no session on the server. This surprises almost everyone and explains 80% of
   the cost and latency behaviour they'll see all weekend.
2. **The context window is a budget**, not a memory. Everything competes for it:
   system prompt, history, retrieved documents, tool definitions, tool results.
3. **Tool use is a contract.** The model does not execute anything. It emits a
   structured request — a name and a JSON object — and *your* code decides
   whether to run it. Say this twice. It's the single most misunderstood point
   in the whole field.
4. **The loop.** Call model → model asks for a tool → you run it → you send the
   result back → repeat until the model stops asking. Draw it as an actual
   circle on the board.
5. **Where the risk lives.** The model chooses; your code executes. Every
   security question for the rest of the weekend reduces to: what did you let it
   choose from, and what did you let that choose do?

> **Friend 1's moment:** ask him to explain why the stateless call means cost
> grows quadratically with conversation length. He'll know. Let him teach it.
>
> **Friend 2's moment:** ask what he'd want in front of this in production.
> He'll say rate limiting, retries, timeouts, cost caps, observability. He's
> right, and none of the tutorials mention any of it.

## 10:45 · Lab 1 — Your GPU, measured (60 min)

`labs/lab01_local_serving/`

Run three model sizes on the host's card. Measure time-to-first-token,
tokens/sec, and VRAM. Then deliberately overload it and watch it spill to
system RAM and collapse.

**The point:** inference is a capacity planning problem, not magic. And by the
end of the lab everyone has seen a 3B model produce confidently malformed JSON,
which sets up every design decision that follows.

## 11:45 · Break (15 min)

## 12:00 · Lab 2 — Structured output (45 min)

`labs/lab02_structured_output/`

Get a model to return data your program can actually use. Compare prompt-based
JSON (fragile) against schema-enforced tool calling (reliable).

Then run the identical task on the GPU with `structured_local.py`, which adds
constrained decoding — Ollama compiles the schema into a sampling grammar, so
even a 3B model cannot emit malformed JSON. The script scores validity and field
accuracy in separate columns, and they come apart dramatically.

**The point:** this is the exact moment a chatbot becomes a software component.
And the sting in the tail: a grammar guarantees shape, never truth. A
well-formed wrong answer is worse than one that fails to parse.

## 12:45 · Lunch (60 min)

## 13:45 · Lab 3 — Build the agent loop by hand ★ (90 min)

`labs/lab03_agent_loop/`

The centrepiece. Roughly 80 lines of Python, no frameworks. Three tools, a
while-loop, and a print statement showing every step of the model's reasoning.

Do not let anyone `pip install` an agent framework today. The whole design of
the weekend rests on them seeing that there is nothing underneath.

**The point:** the demystification. When the loop runs and the model chains
three tool calls to answer a question, that's the moment.

**Extension if they're fast:** break it deliberately. Remove a tool description
and watch behaviour degrade. Add a tool that always errors and see how it
recovers. Set `max_turns` to 2 and watch it fail mid-task.

## 15:15 · Break (15 min)

## 15:30 · Lab 4 — RAG, and watching it fail (75 min)

`labs/lab04_rag/`

Sixty lines: chunk, embed, cosine similarity, stuff into context. Then ask it
three questions specifically designed to break it — a multi-hop question, a
negation, and an aggregation.

**The point:** more instructive than making RAG work. Retrieval is a search
problem wearing an AI costume, and most production RAG failures are search
failures. This lab inoculates them against six months of confusion.

## 16:45 · Whiteboard recap (30 min)

Rebuild the ladder on the board from memory, as a group. Ask them to place each
lab on it. Then ask: *what's missing?* Let them arrive at "the model doesn't
know about my stuff" and "how do I know if it's any good" on their own — those
are Sunday.

## 17:15 · Close

Dinner. Do not do more labs. Cognitive load is real and tomorrow is the better day.

---

# Sunday — Agentic

## 10:00 · Recap (15 min)

One question: *what surprised you yesterday?* Then straight into it.

## 10:15 · Lab 5 — Skills and progressive disclosure (60 min)

`labs/lab05_skills/`

Write a `SKILL.md`, then watch a model discover it, decide it's relevant, load
it, and follow it. The lab implements the disclosure mechanism from scratch in
about 50 lines, so it's obvious there's no magic — just a description in the
system prompt and a `read_skill` tool.

**The point:** context is the scarce resource, and skills are how you buy
capability without paying for it up front. Also: the thing they're building is
just a folder with a markdown file in it. That's genuinely the whole format.

## 11:15 · Break (15 min)

## 11:30 · Lab 6 — MCP (75 min)

`labs/lab06_mcp/`

Two halves. First, connect Claude Code to an existing MCP server and use it.
Then write your own — a real one, about 40 lines, that exposes a local SQLite
database as tools.

**The point:** tools stop being code you wrote into one app, and become a
capability any client can consume. Friend 2 will immediately see this as service
discovery for models, which is exactly right.

## 12:45 · Lunch (60 min)

## 13:45 · Lab 7 — Agentic coding on a real repo (75 min)

`labs/lab07_agentic_coding/`

Turn Claude Code loose on a small, deliberately messy codebase. Have it find a
bug, write tests, and refactor. Then have it do something it will get *wrong*,
and discuss why.

**The point:** the "whoa" moment for most people, and the most immediately
useful skill either of them will take away. Also the best possible argument for
Lab 8.

## 15:00 · Break (15 min)

## 15:15 · Lab 8 — Evals, guardrails, cost (60 min)

`labs/lab08_evals/`

Build a small eval harness over the Lab 3 agent. Twelve test cases, a scoring
function, a number. Change one thing about the prompt and watch the number move.

Then twenty minutes on the unsexy stuff: prompt injection, tool permissioning,
cost caps, timeouts, logging every model call.

**The point:** this is the module that separates people who demo from people who
ship. It is also, for both of them, the most employable hour of the weekend.
Don't cut it — cut Lab 4 instead.

## 16:15 · Project scoping (60 min)

`PORTFOLIO.md`

Not a build session. A scoping session. Each of them leaves with a written
four-week plan, a repo initialised, and a first commit.

Work through it properly: pick an archetype, narrow the domain until it's almost
embarrassingly small, define what "done" looks like, and write the README
*first* — before any code exists. Writing the README first is the single best
scope-control technique there is.

## 17:15 · Demos and close (30 min)

Each person gets five minutes to show what they built or plan to build. Then
agree a check-in date three weeks out. Say it out loud and put it in calendars.

Momentum after a workshop lasts about ten days without a commitment. With one,
it lasts long enough to finish something.
