#!/usr/bin/env python3
"""Lab 9 — Harness: an introduction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib import colors
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer

from pdfkit import (AMBER, CW, INK, PETROL, PETROL_LT, RULE, SLATE, WASH,
                    WASH_WARM, Diagram, P, Rule, S, arrow, callout, make_doc,
                    rbox, transcript, two_col, txt)

RED = colors.HexColor("#A9412F")
GREEN = colors.HexColor("#2F6B4F")


class FiveRings(Diagram):
    """The loop in the middle, five concerns wrapped round it."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "The loop is the small part", "Display-Bold", 9.4, INK)

        # the loop, dead centre
        cw_, ch = 130, 44
        cx, cy = w / 2, h / 2 - 14
        rbox(c, cx - cw_ / 2, cy - ch / 2, cw_, ch, fill=PETROL, stroke=PETROL)
        txt(c, cx, cy + 4, "the loop", "Display-Bold", 10, colors.white, "c")
        txt(c, cx, cy - 9, "20 lines, from Lab 3", "Body", 7,
            colors.HexColor("#BFD6D2"), "c")

        items = [
            ("Registry", "schema + function,\nin one place", -1, 1),
            ("Observability", "every call recorded", 0, 1),
            ("Budget", "a ceiling, checked\nbefore you spend", 1, 1),
            ("Reliability", "timeouts, retries,\na turn limit", -0.5, -1),
            ("Policy", "what may run\nwithout a human", 0.5, -1),
        ]
        bw, bh = 118, 40
        for label, sub, slot, row in items:
            x = cx + slot * (bw + 16) - bw / 2
            y = cy + row * 72 - bh / 2
            rbox(c, x, y, bw, bh, fill=WASH_WARM, stroke=AMBER, lw=1.1)
            txt(c, x + bw / 2, y + bh - 14, label, "Display-Bold", 8.6, AMBER, "c")
            for j, line in enumerate(sub.split("\n")):
                txt(c, x + bw / 2, y + bh - 25 - j * 9, line, "Body", 6.8,
                    SLATE, "c")
            ey = y if row > 0 else y + bh
            arrow(c, x + bw / 2, ey, cx + slot * 22, cy + row * (ch / 2 + 4),
                  AMBER, 0.9, dash=(2, 2))


class NotAiProblems(Diagram):
    """Each concern has a name you already know."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "You have solved all five before, under other names",
            "Display-Bold", 9.4, INK)

        pairs = [
            ("Registry", "a service catalogue"),
            ("Observability", "audit logging"),
            ("Budget", "quotas and rate limits"),
            ("Reliability", "retries with backoff"),
            ("Policy", "authorisation"),
        ]
        rh = 24
        top = h - 34
        lw_ = (w - 40) / 2
        for i, (a, b) in enumerate(pairs):
            y = top - (i + 1) * rh
            rbox(c, 0, y, lw_, rh - 4, fill=WASH_WARM, stroke=AMBER, r=3, lw=0.9)
            txt(c, 11, y + 6, a, "Display-Bold", 8.4, AMBER)
            arrow(c, lw_ + 6, y + (rh - 4) / 2, lw_ + 32, y + (rh - 4) / 2, SLATE, 0.9)
            rbox(c, lw_ + 38, y, lw_, rh - 4, fill=WASH, stroke=PETROL_LT, r=3, lw=0.9)
            txt(c, lw_ + 49, y + 6, b, "Display", 8.4, PETROL)

        txt(c, 0, 4, "Nothing in the right-hand column is new, and nothing in "
                     "it is about AI.", "Body-Italic", 8.2, AMBER)


def motif(c):
    """A small core with rings around it."""
    import math
    cx, cy = 300, 300
    c.setStrokeColor(colors.HexColor("#22665F"))
    c.setLineWidth(1.3)
    for r in (46, 68, 90, 112):
        c.circle(cx, cy, r, stroke=1, fill=0)
    c.setFillColor(colors.HexColor("#B85C1E"))
    c.circle(cx, cy, 22, stroke=0, fill=1)


def build(out_path):
    doc, st = make_doc(
        out_path, "Harness - An Introduction",
        {"eyebrow": "LAB 9  ·  AN INTRODUCTION",
         "title": ["The Harness"],
         "sub": ["Everything you have to wrap round a working loop",
                 "before you would let it run while you are asleep."],
         "facts": [("FOR", "Anyone who has shipped a script that ran twice."),
                   ("READ IT", "Before the session. Ten minutes.")],
         "motif": motif},
        "THE HARNESS  ·  AN INTRODUCTION")

    st += [
        P("What it actually is", "h1"), Rule(8), Spacer(1, 4),
        P("A harness is the code around the loop. Not the loop - the loop is "
          "twenty lines and you have already written it. The harness is the "
          "five things you bolt on before the loop can be trusted.", "lead"),
        P("The agent loop from Lab 3 works. That is not in question. It worked "
          "on a Saturday afternoon, on one task, with someone watching, on a "
          "machine where nothing mattered and the inference was free."),
        P("Change any one of those conditions and it stops being enough - not "
          "because it stops working, but because when it does go wrong you "
          "have no way to find out what happened, no way to stop it, and no "
          "record of what it did."),
        Spacer(1, 6),
        KeepTogether([FiveRings(248)]),
        Spacer(1, 10),
        callout("The observation this lab is built on",
                "Read those five again. An audit trail. A spend cap. Retries. "
                "Authorisation. A catalogue of what can be called. <b>Not one "
                "of them is an AI problem.</b> They are the same five problems "
                "as any service that calls a remote API, and they have had "
                "the same answers for thirty years."),
        PageBreak(),

        P("Which means you already know this", "h2"),
        P("If you have run anything in production, you have built all five "
          "before. The vocabulary is different and the libraries are new; the "
          "problems are not."),
        Spacer(1, 6),
        KeepTogether([NotAiProblems(170)]),
        Spacer(1, 14),
        P("This is worth saying plainly because the opposite impression is "
          "everywhere. Agentic systems are presented as a new discipline "
          "requiring new instincts. The loop is new. The engineering around "
          "it is almost entirely familiar, and the people who are good at it "
          "are the people who were already good at running services."),
        Spacer(1, 10),

        P("Example 1 - The job that runs at three in the morning", "h1"),
        Rule(8), Spacer(1, 4),
        P("The case where every single one of the five earns its place.",
          "lead"),
        P("An agent processes a queue overnight: for each item it reads some "
          "records, works something out, and writes a result. Nobody is "
          "watching. It handles perhaps four hundred items between midnight "
          "and six."),
        P("Run Lab 3's loop against that and here is the night you get:"),
        Spacer(1, 4),
        two_col([
            ("00:14", "Item 7 triggers a long chain of tool calls. Nothing "
                      "caps it. It runs twenty turns, each resending the whole "
                      "conversation, and the cost of that single item exceeds "
                      "the other 399 combined."),
            ("02:40", "A transient network error on one tool call raises out of "
                      "the loop. The process dies. Items 150 to 400 are never "
                      "attempted, and nothing says so."),
            ("08:30", "You find out. The queue is backed up, the output is "
                      "partial, and there is no log of what was processed, "
                      "what was skipped, or what anything cost."),
        ], left_w=70, label_color="#A9412F"),
        Spacer(1, 12),
        P("None of those is an exotic failure. They are Tuesday. With a "
          "harness, the same night produces: item 7 stopped at its turn limit "
          "and marked for review, the network error retried twice and "
          "succeeded, and a JSONL file with one line per event that answers "
          "every question before you have to ask it."),
        PageBreak(),

        P("Example 2 - The second person to run it", "h1"), Rule(8), Spacer(1, 4),
        P("The case that catches teams, because it does not look like a "
          "technical problem.", "lead"),
        P("You built an agent that helps with on-call: it reads logs, checks "
          "disk, and can restart a service. You know which of those three is "
          "dangerous, so you are careful. It is useful enough that a colleague "
          "asks for it."),
        P("They do not know. Why would they? It is a tool that answers "
          "questions about servers, and nothing in it distinguishes "
          "<font face='Mono' size='8'>read_log</font> from "
          "<font face='Mono' size='8'>restart_service</font> - both are just "
          "names in a dispatch dictionary."),
        Spacer(1, 4),
        transcript([
            ("you", "The ingest service has been failing for an hour. "
                    "Diagnose it and fix it."),
            ("agent", "Disk is full and ingest is wedged. Restarting it."),
            ("tool", "restart_service(name=\"ingest\")"),
            ("out", "Service ingest restarted. 2 in-flight requests dropped."),
            ("agent", "Restarted ingest. Root cause is /var at 98% full - it "
                      "will fail again unless you free space."),
        ]),
        Spacer(1, 10),
        P("It diagnosed correctly and then restarted a production service "
          "because the word \"fix\" was in the request. Nobody authorised "
          "that. The agent was not wrong, exactly - it did what it was asked - "
          "but no human was ever given the chance to say no."),
        Spacer(1, 4),
        callout("Why an if-statement is not the answer",
                "The obvious patch is <font face='Mono' size='8'>if name == "
                "\"restart_service\": ask()</font>. That works for one tool. "
                "Add a second dangerous tool and you add a second branch; add "
                "a second task with different tools and you copy the whole "
                "loop. A <b>policy</b> - a rule, held as data - can be "
                "printed, tested, reviewed in a pull request, and loaded "
                "differently in staging and production."),
        PageBreak(),

        P("When you do not need one", "h1"), Rule(8), Spacer(1, 4),
        P("The judgement this document exists to give you, and it points the "
          "other way more often than you would expect.", "lead"),
        P("<b>You do not need a harness for a script you run once, watching, "
          "on free inference, where the worst outcome is a wrong answer you "
          "spot immediately.</b> Lab 3's twenty lines are genuinely the right "
          "amount of code for that. Wrapping them in five abstractions would "
          "be ceremony, and you would be maintaining infrastructure for a "
          "problem you do not have."),
        P("Write the twenty-line loop first. Every time. It is the fastest way "
          "to find out what tools the job actually needs, and you cannot "
          "design a registry for tools you have not discovered yet."),
        Spacer(1, 6),
        P("Then reach for a harness the moment any one of these becomes true:",
          "tight"),
        Spacer(1, 4),
        two_col([
            ("It runs unattended.", "Nobody is there to notice it looping, or "
                                    "to say no."),
            ("It runs more than once.", "The second task is where a script "
                                        "becomes a pattern. A pattern with no "
                                        "registry is copy-paste."),
            ("Someone else runs it.", "They will not know which tools are "
                                      "dangerous, and nothing in your code "
                                      "tells them."),
            ("It costs real money.", "A cap you set in advance is a different "
                                     "object from a bill you read afterwards."),
            ("It can do something you'd regret.", "Irreversible, external, or "
                                                  "expensive. Any one of the "
                                                  "three needs a policy, not a "
                                                  "comment."),
            ("You have to explain it.", "To a colleague, an auditor, or "
                                        "yourself next Tuesday. Without a "
                                        "trace, you cannot."),
        ], left_w=172),
        Spacer(1, 14),
        callout("The two ways people get the timing wrong",
                "<b>Too early:</b> elaborate infrastructure built around a "
                "problem nobody has understood yet, abstracting tools that "
                "turned out to be the wrong tools.<br/><br/>"
                "<b>Too late:</b> after the 3am incident, which is the "
                "expensive way to discover you needed a spend cap. The second "
                "is more common and more costly, but the first wastes more "
                "weeks."),
        PageBreak(),

        P("What to take into the session", "h2"),
        Spacer(1, 4),
        callout("One",
                "A harness is the code around the loop: a registry, "
                "observability, a budget, reliability, and a policy. The loop "
                "itself stays twenty lines.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 7),
        callout("Two",
                "None of the five is an AI problem. You have built all of them "
                "before, under different names, for ordinary services."),
        Spacer(1, 7),
        callout("Three",
                "Write the loop first, every time. Reach for a harness at the "
                "second task, or the first unattended run, whichever comes "
                "first.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 16),
        P("The session itself runs backwards from most: you spend the first "
          "half-hour watching Lab 3's loop fail four times under realistic "
          "conditions, and only then read the thing that fixes it. The test "
          "at the end is not whether the code is tidy. It is whether somebody "
          "can solve a problem you never thought about without opening your "
          "file."),
        Spacer(1, 10),
        P("<font face='Body-Italic' color='#6E7B78'>The harness in the lab is "
          "about 180 lines and deliberately small enough to read in ten "
          "minutes. What it leaves out - persistence, concurrency, circuit "
          "breakers, cost attribution, a real policy engine - is the shape of "
          "a genuinely good portfolio project, and very few people have built "
          "one.</font>", "tight"),
    ]

    doc.build(st)
    print("Built", out_path)


if __name__ == "__main__":
    from pdfkit import publish
    publish(build, "Harness-Intro.pdf", "lab09_harness")
