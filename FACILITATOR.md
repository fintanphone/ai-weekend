# Facilitator Notes

For the host. Read this the weekend *before*.

---

## Prep checklist

### Three weeks out
- [ ] Send `SETUP.md` to both friends, ask for confirmation `check_setup.py` passes
- [ ] Pick the dates, book them properly

### One week out
- [ ] **Run every lab yourself, start to finish, timed.** Non-negotiable. You
      will find at least three things broken, and you'll discover which labs
      overrun
- [ ] Cut a third of the content based on what you learned. Everything takes
      twice as long with an audience
- [ ] `ollama pull` all four models
- [ ] Pre-cache pip wheels: `pip download -r requirements.txt -d ./wheels`
- [ ] Chase whoever hasn't confirmed their setup. There's always one

### The day before
- [ ] Push a `solutions` branch with working code for every lab
- [ ] Test the API key has credit on it
- [ ] Check the GPU machine's screen is visible to three people, or set up
      screen sharing
- [ ] Charge everything, find the power strips
- [ ] Buy more coffee than you think you need

### The morning of
- [ ] `ollama serve` running
- [ ] Whiteboard and working markers
- [ ] Repo pulled fresh on all machines

---

## The cut-list

You will run behind. Cut in this order:

1. **Lab 4 (RAG)** — cut to a 15-minute demo you drive yourself. Show the three
   failure questions, skip the build. It's the most self-contained lab and the
   easiest to learn later.
2. **Lab 1 extensions** — do the two-model comparison, skip the overload test.
3. **Lab 6 second half** — connect to an existing MCP server, skip writing one.
4. **Lab 7 refactor exercise** — do the bug-finding only.

**Never cut:** Lab 3 (the loop), Lab 5 (skills), Lab 8 (evals), or the Sunday
scoping session. Lab 3 is the entire premise. Lab 8 is the most employable hour.
The scoping session is why Friend 1 came.

If you're catastrophically behind on Sunday, cut Lab 7 entirely — agentic coding
is the one thing they will absolutely explore on their own afterwards without
any encouragement from you.

---

## Running it well

**Pair them at one machine** for Labs 1–5. Two people at one keyboard argue
productively; two people at two keyboards go silent and google separately.
Swap who types every 20 minutes.

**Let them be experts.** Friend 1 knows the theory — hand him the "why does this
work" questions. Friend 2 knows systems — hand him "what breaks in production".
Both of them are job-hunting and confidence is part of what you're building here.

**When something breaks, debug it in front of them.** Don't fix it quietly on
your own machine. Watching someone competent read a stack trace calmly is
genuinely instructional, and it's the most honest thing you can show them about
what this work is actually like.

**Resist the framework question.** Someone will ask about LangChain or similar
within the first hour. The answer is: "Sunday afternoon, and by then you'll be
able to tell whether it's buying you anything." Frameworks introduced after the
hand-rolled loop feel like conveniences. Introduced before, they feel like magic,
and the whole point is to remove the magic.

**Watch the energy after lunch.** If Saturday's 13:45 slot is flagging, do ten
minutes on the whiteboard before opening laptops.

---

## Questions you should expect

**"Isn't this just a chatbot with extra steps?"**
Yes, structurally. The extra steps are the entire field. A chatbot that can
query your database, write a file, and check its own work is a different
category of thing to one that can't.

**"Why not just fine-tune?"**
Different tool for a different problem. Fine-tuning changes behaviour and style;
it's a poor way to add knowledge and a terrible way to add capability. Tools and
retrieval handle knowledge and capability. Friend 1 may push back on this from
his coursework — good, have the argument, it's a genuinely interesting one.

**"How do I stop it doing something dangerous?"**
Lab 8. But the short answer, which you should give immediately: you control the
tool list. The model can only choose from what you gave it. Everything else is
defence in depth.

**"Can it run entirely locally?"**
Yes, and Lab 1 shows what you give up. For simple single-tool tasks, an 8B model
is fine. For five-step chains, it isn't, and the failure mode is silent and
confident. That gap is closing fast, but it's real today.

**"What about [this week's news]?"**
Be honest if you don't know. Modelling "I'd have to check" is more useful to
them than bluffing, particularly in a field where half of what anyone confidently
asserts is three months out of date.

---

## After the weekend

- Push everything, including the solutions branch, and give them both access
- Send a one-page follow-up: what you covered, what you cut, links to go deeper
- **Put the three-week check-in in your own calendar** and be the one who chases
  it. Both of them are job-hunting; the accountability is the most valuable thing
  you can offer after the weekend itself
