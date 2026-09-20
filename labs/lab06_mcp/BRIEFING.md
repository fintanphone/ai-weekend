# Lab 6 — MCP

**Briefing for the facilitator.** Sunday 11:30 · 75 minutes · pairs.

---

## Open with

> "On Saturday you wrote three tools. They worked inside that one script and
> nowhere else. If you wanted the same three tools in a different app, you'd
> copy the code. This is the lab where that stops being true."

## The scenario

You've got a database. Or an internal API, or a ticketing system, or a build
pipeline — something with real information in it that a model could usefully
reach.

You could write tools for it inside every application that needs them. Or you
could expose it once, over a protocol, and let any client consume it.

That's MCP. A server offers capabilities; any client can use them — Claude Code,
a desktop client, your own agent from Lab 3, or someone else's.

**Friend 2 will recognise this within thirty seconds** as service discovery and
a capability registry for models. He's exactly right. Let him say it out loud
rather than saying it for him — the analogy will help Friend 1 more coming from
him than from the specification.

## The core idea

Draw it: clients across the top, one protocol band in the middle, servers along
the bottom.

> "Neither side knows anything about the other. The client doesn't know your
> server is SQLite. Your server doesn't know or care which client is asking."

Three primitives exist — tools, resources, prompts — but tools are roughly
ninety per cent of what anyone uses. Don't over-explain the other two.

## The design conversation that matters most

This is the part to protect if time runs short.

The server in this lab exposes a SQLite database through **four narrow tools**:
list shipments by status, get one shipment's detail, stock by warehouse, search
inventory.

Ask the room: *why not just expose one `run_sql` tool that takes arbitrary SQL?*

It would be far more flexible. It would be dramatically less code. And it's a
genuinely bad idea — because it hands the model the database's full authority,
including `DROP TABLE`, including every row of every table regardless of what
the question needed.

> **Narrow tools are a permissioning mechanism, not a limitation.**

That reframes the whole lab. You're not writing tools because the model needs
help. You're writing them because the tool list *is* the capability grant — the
exact point from Session 0, now at protocol scale.

## What the code has to do

**Declare tools from function signatures.** The decorator turns the Python
signature into a JSON Schema and the docstring into the description. Point out
what that means: **this is Lab 2 and Lab 3 wearing a protocol.** Same contract,
standard transport.

**Make the docstring good.** It isn't documentation — it's the interface. The
model reads it to decide whether the tool is relevant and what to put in the
arguments. This is the same lesson as the skill description in Lab 5, and it's
worth naming the repetition.

**Return text, not objects.** Results go back into the context window as
strings. Format them so they're readable — the model is the consumer.

**Expose narrow operations.** Four tools with clear names beat one general one,
for the reason above.

## Running the room

**First half: consume something you didn't write.** Add the filesystem server,
ask a client about some documents, watch it call tools nobody in the room
authored. Note the permission prompt before each call — then ask whether a
human clicking "allow" is a sufficient security boundary when there are two
hundred calls in a session.

**Second half: write one.** Sixty lines, then register it and ask business
questions:

- *"Which shipments are delayed, and is there a pattern in why?"*
- *"We need 100 units of anything strapping-related. Can we fulfil that?"*

That second question needs a search, a check of quantities across warehouses,
and reasoning about the result. Three tool calls, sequenced by the model. Same
moment as Lab 3, now over a protocol.

**Then the experiment worth doing:** add a tool with a deliberately vague
docstring — `"""Gets data."""` — and watch the model fail to use it correctly.
Nothing makes the "docstring is the interface" point land like seeing it break.

**Ask Friend 1:** *what happens if a server returns text containing
instructions?* It's Lab 3's prompt injection, now at protocol scale, and with
someone else's code in the middle. Who is trusting whom?

**Ask Friend 2:** *how would you run this for a company?* Auth, secrets
management, audit logging, multi-tenancy, rate limits, versioning. Almost none
of it is solved in the ecosystem yet. **That gap is a portfolio project** —
point him at `PORTFOLIO.md` before the session ends.

## The punchline

> A tool is a contract. MCP is that contract with a standard transport, so it
> stops belonging to one application.

## If you're short on time

Do the first half only — connect an existing server and use it. Writing your own
is the better half, but consuming one demonstrates the idea, and the server code
reads well on your own afterwards.
