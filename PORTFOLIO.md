# Portfolio Tracks

Used in the Sunday 16:15 scoping session. Both friends are entering the job
market, so both get a track. Work through this document with them open on
screen; it's designed to be filled in, not read.

---

# Friend 1 — MSc in AI, deciding on direction

## The honest market picture

A Masters plus a notebook that fine-tunes a model on a public dataset is now the
baseline. Hundreds of graduates have exactly that, and hiring managers have
stopped reading them. What almost nobody has is **a shipped agentic system with
a real evaluation harness attached**.

That gap is the opportunity. He should aim squarely at it.

## Since he's still deciding on a role — start here

Being undecided is an argument *for* a specific project, not against one. The
eval-harness archetype below is the one that reads well to all three of the
roles he's weighing, so it doesn't force a choice he isn't ready to make:

| Role he might target | How the eval project reads to them |
|---|---|
| ML / research engineer | Rigorous methodology, measurement, ablations |
| AI application engineer | He shipped a working system, not a notebook |
| Data scientist | He designed the measurement, not just the model |

Build that first. The four weeks will also tell him which parts he enjoyed,
which is better career information than any amount of deliberating.

## The four archetypes

### 1. The eval harness project ★ recommended

Build a modest agent for one narrow domain. Then build 50–80 test cases with a
scoring rubric, and demonstrate measured improvement across versions.

The agent is the easy half and everyone has one. **The eval harness is the
differentiator.** "I took it from 41% to 78%, and here's which change bought
each increment" is an interview-winning sentence, and he can defend it under
questioning because he actually did the methodology.

His academic training is a genuine advantage here. Most people writing about
agents cannot design a valid experiment. He can.

**Scope guardrail:** the agent should do one thing. Not "a research assistant" —
"answers questions about the Irish Residential Tenancies Act with citations".

### 2. An MCP server for a niche domain

Pick something with no server yet, expose it properly, publish it.

Small surface area, genuinely new territory, and a hiring engineer can read it in
ten minutes and judge competence. Demonstrates API design, protocol
understanding, and documentation ability all at once. Considerably more
impressive than its line count suggests.

**Scope guardrail:** 4–6 tools maximum. Excellent docs beat more features.

### 3. Local model agentic benchmarking

Your GPU makes this one possible and almost nobody has done it well.

Which open-weight models can actually sustain multi-step tool use? At what
quantisation does tool-calling reliability fall off a cliff? What's the real
cost-per-completed-task versus an API, once you count the failures and retries?

Produces charts, a writeup, and a reproducible harness. Sits exactly on the seam
between his theory and practical engineering, which is precisely the seam he
needs to demonstrate he can cross.

**Scope guardrail:** three models, two quantisations, one task suite. That's it.

### 4. A vertical agent in a domain he can speak to

Legal, clinical, finance, logistics, agriculture — whatever he has genuine
adjacency to, through family, previous work, or his thesis.

Generic "AI assistant" projects are invisible. Domain specificity is what makes
a recruiter stop scrolling, because it signals he can talk to users and
understands that the hard part is the domain, not the model.

**Scope guardrail:** one workflow, one user type, one clearly stated failure mode.

## One more avenue worth raising

His thesis almost certainly contains something reusable. Rebuilding an academic
result as a working agentic system demonstrates both halves at once, and he
already has the domain knowledge loaded. Ask him what his thesis was on before
he picks anything from the list above.

## The packaging matters as much as the code

Tell him plainly: **the deliverable is not a repo.** A bare GitHub link does not
get read. The bundle that does get read is:

- [ ] Repo with a genuinely good README — problem, approach, results, in that order
- [ ] An architecture diagram. Hand-drawn and photographed is fine
- [ ] Eval numbers in a table, with the methodology stated
- [ ] A written post explaining **something he got wrong and then fixed**
- [ ] A two-minute screen recording of it working
- [ ] Clean commit history that shows the thing evolving

The "what I got wrong" post is worth more than the code. It is the clearest
available signal of engineering judgement, and it's the thing interviewers
quote back at candidates.

## Four-week plan template

| Week | Goal | Definition of done |
|---|---|---|
| 1 | Narrowest possible working version | It runs end-to-end and produces a wrong answer |
| 2 | Eval harness + baseline number | You have a number you don't like |
| 3 | Three improvements, measured individually | You know which one mattered |
| 4 | Packaging: README, diagram, writeup, video | A stranger can understand it in 5 minutes |

Note that week 1's definition of done is a *wrong* answer. Getting the pipeline
running end-to-end before it's any good is the whole trick.

---

# Friend 2 — Cloud background, out of work a year

Don't leave him with a smaller version of Friend 1's project. He has a different
and arguably stronger hand to play.

## The angle

**AI platform and infrastructure engineering** is in real demand, and there are
far fewer people who can do it than people who can call an API. His cloud
background transfers almost directly, and the year out of work matters much less
in a field this new — nobody has five years of agent-ops experience, because it
hasn't existed for five years.

The pitch is: *"I'm a cloud engineer who understands how to run these things in
production."* That's a much rarer and more hireable claim than "I'm learning AI."

## Project archetypes

**1. An agent deployment reference architecture.** Take the Lab 3 agent and put
it into production properly: containerised, autoscaled, with rate limiting,
retries with backoff, cost caps, structured logging of every model call, and a
dashboard. Terraform it. This is a portfolio piece almost nobody builds, and
every company hiring in this space needs it.

**2. LLM cost and observability tooling.** A middleware layer that logs every
call, attributes spend per feature and per user, alerts on anomalies, and shows
where the tokens actually went. Cost control is a live, unsolved, expensive
problem. Speaks fluently to his existing FinOps instincts.

**3. Self-hosted inference economics.** Extends Lab 1 into a real study: at what
request volume does running your own GPU beat per-token API pricing? Model the
whole thing — hardware amortisation, utilisation, ops burden, the lot. Produces
a genuinely useful writeup that a CTO would read, and it is exactly the kind of
question he'd be asked in an interview.

**4. Agent security and sandboxing.** Prompt injection, tool permissioning,
egress control, running untrusted agent output safely. Growing fast, badly
served, and adjacent to security work that pays well.

## Same packaging rules

Repo, README, diagram, writeup, video. Plus one thing specific to him: **a
public cost model** — a spreadsheet or calculator others can use. Those get
shared, and shared artifacts are how a job-seeker becomes visible.

---

# For both, in the session itself

Work through these four questions on paper, out loud, one person at a time
while the other two challenge the answers:

1. **What's the narrowest useful version?** Then halve it. Then halve it again.
2. **How will you know it's working?** If there's no number, go back to 1.
3. **Who is the imagined reader of the README?** Name an actual job posting.
4. **What will you have committed by this time next week?**

Then: initialise the repo, write the README before any code, make the first
commit. Both of them leave with a live repo, not an intention.

## The check-in

Agree a date three weeks out and put it in calendars before anyone goes home.

Post-workshop momentum lasts about ten days on its own. With a date in the diary
and two people expecting a demo, it lasts long enough to finish something.
