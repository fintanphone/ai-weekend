# Session 0 — Foundations

**Briefing for the facilitator.** Saturday 10:00 · 45 minutes · whiteboard only.

*This is the one session with no code at all. Read this the night before and
deliver it from the board.*

---

## Open with

> "We're not opening laptops for the next forty-five minutes. There are five
> things that, once you've got them, make everything else this weekend obvious
> instead of magical. If we skip these you'll spend two days copying commands
> and learning nothing."

That's the whole pitch. Resist any pull toward demos here. The session works
*because* nothing is running — there's nothing to debug, nothing scrolling past,
and no laptop screen to hide behind.

## The scenario

Both of your friends have used a chat window. Neither has used a model as a
*component* — something a program calls, whose output goes somewhere other than
a human's eyes.

Everything this weekend lives in the gap between those two things. This session
is about drawing the gap.

## The five ideas, in order

Draw each one. Don't just say it — the picture is what they remember on Sunday.

### 1. The API is stateless

Draw three boxes, left to right: Turn 1, Turn 2, Turn 3. In turn one, one
message. In turn two, two messages. In turn three, three.

> "There is no session living on a server somewhere. There's no memory. Every
> single call sends the *entire* conversation back again, from the start."

This surprises nearly everyone, and it explains most of the cost and latency
behaviour they'll meet over the two days.

### 2. The context window is a budget, not a memory

Draw one long bar. Fill it in segments as you name them: system prompt, tool
definitions, conversation history, retrieved documents, tool results, headroom.

> "Everything competes for the same finite space. And because of idea one,
> you pay for all of it again on every single request."

### 3. Tool use is a contract

Two boxes with a gap between them. Model on the left, your code on the right.
Write **"JSON only"** in the gap.

> "The model does not execute anything. Ever. It emits a structured request — a
> name and a JSON object — and *your* code decides whether to run it."

Say this twice. It is the most misunderstood idea in the field, and everything
in Lab 3, Lab 6 and Lab 8 is a consequence of it.

### 4. The loop

Draw an actual circle. Call the model → it asks for a tool → you run it → you
send the result back → repeat until it stops asking.

> "That circle is what people mean when they say 'agent'. That's it. That's the
> whole thing."

**Leave this one on the board all weekend.** You will point at it repeatedly.

### 5. The risk lives in the split

Back to the two boxes from idea three.

> "The model chooses. Your code executes. Every security question for the rest
> of the weekend reduces to two things: what did you let it choose from, and
> what can those choices do?"

## Hand the explaining over

This is the moment to establish the pattern for the whole weekend — they teach
half of it.

**Ask Friend 1:** *why does the stateless call mean cost grows with the square
of conversation length?* He has the background for this. Let him work it out at
the board. It's the first time the Masters visibly pays off in a practical room,
and that matters more than the answer does.

**Ask Friend 2:** *what would you want sitting in front of this in production?*
He'll say rate limiting, retries with backoff, timeouts, a cost ceiling,
structured logging. He's right about all of it, none of it appears in any
tutorial, and it's the seed of his whole track in `PORTFOLIO.md`.

## The punchline

> **An agent is a while-loop around a model that can call functions.**

Write it on the board. Underline it. Tell them that if they leave on Sunday
genuinely believing that sentence, the weekend worked.

## Running the room

Forty-five minutes is generous for five ideas — that's deliberate. The value is
in the arguments that break out, not the coverage.

If someone reaches for a laptop, ask them to wait. If someone asks about
frameworks, the answer is "Sunday afternoon, and by then you'll be able to judge
whether it's buying you anything."

## If you're short on time

Ideas 3 and 4 are non-negotiable — the contract and the loop. Ideas 1 and 2
compress into three minutes. Idea 5 can wait for Lab 3, where they meet it
concretely anyway.
