# The lab introductions

All five introduction PDFs in one place, so you can send them out without
digging through lab folders.

| PDF | Lab | Send it before |
|---|---|---|
| `Skills-Intro.pdf` | 5 — Skills | Sunday morning |
| `MCP-Intro.pdf` | 6 — MCP | Sunday morning |
| `Agentic-Coding-Intro.pdf` | 7 — Agentic coding | Sunday afternoon |
| `Evals-Intro.pdf` | 8 — Evals | Sunday afternoon |
| `Harness-Intro.pdf` | 9 — Harness | the harness session |

Each is five or six pages and takes about ten minutes. They cover what the
thing is, two worked examples, and where it goes wrong — so the definition
arrives before the session rather than eating the first ten minutes of it.

A copy of each also sits in its own lab folder, where someone working on that
lab will look for it. The two are kept in step automatically: the build
scripts write here first and copy across.

## Sending them out

The whole set is a reasonable thing to send a few days ahead. If you'd rather
not send five PDFs at once, the two that do most work are
**Agentic-Coding-Intro** (the one people are most curious about) and
**Evals-Intro** (the one they'd never pick up on their own).

Labs 1 to 4 have no PDF. Local inference, structured output, the agent loop
and retrieval are better met at the keyboard than on paper — and Lab 4 has
`what-the-model-sees.html` instead, which is a page to project rather than
something to read beforehand.

## Changing them

Don't edit the PDFs. They're generated — the source is in
`../pdf_build_scripts/`, one script per PDF plus a shared design module.
Change the wording there and rerun; both copies update together.
