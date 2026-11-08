#!/usr/bin/env python3
"""Lab 8 — Evals: an introduction."""

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


class MeasureLoop(Diagram):
    """Baseline, change one thing, re-measure."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "Change one thing. Re-measure. Keep the number.",
            "Display-Bold", 9.4, INK)

        bw, bh, vw = 100, 40, 84
        gap = (w - 3 * bw - vw) / 3
        y = h - 76

        boxes = [("Your cases", "40 tasks, each with\nwhat a good answer needs"),
                 ("The system", "one version of it"),
                 ("Scoring", "substring first,\njudge only if you must")]
        for i, (t, sub) in enumerate(boxes):
            x = i * (bw + gap)
            fill = PETROL if i == 1 else WASH
            tc = colors.white if i == 1 else PETROL
            rbox(c, x, y, bw, bh, fill=fill, stroke=PETROL if i == 1 else PETROL_LT)
            txt(c, x + bw / 2, y + bh - 14, t, "Display", 9, tc, "c")
            for j, line in enumerate(sub.split("\n")):
                txt(c, x + bw / 2, y + bh - 26 - j * 9, line, "Body", 6.6,
                    colors.HexColor("#BFD6D2") if i == 1 else SLATE, "c")
            if i:
                arrow(c, x - gap + 4, y + bh / 2, x - 5, y + bh / 2, PETROL_LT)

        vx = 3 * (bw + gap)
        arrow(c, vx - gap + 4, y + bh / 2, vx - 5, y + bh / 2, AMBER)
        rbox(c, vx, y - 4, vw, bh + 8, fill=AMBER, stroke=AMBER)
        txt(c, vx + vw / 2, y + bh / 2 - 3, "31 / 40", "Display-Bold", 15,
            colors.white, "c")
        txt(c, vx + vw / 2, y - 17, "a number", "Body-Italic", 7.6, AMBER, "c")

        c.saveState()
        c.setStrokeColor(AMBER)
        c.setLineWidth(1.0)
        c.setDash(3, 2)
        p = c.beginPath()
        p.moveTo(vx + vw / 2, y - 26)
        p.lineTo(vx + vw / 2, y - 44)
        p.lineTo(bw + gap + bw / 2, y - 44)
        c.drawPath(p)
        c.restoreState()
        arrow(c, bw + gap + bw / 2 + 4, y - 44, bw + gap + bw / 2, y - 6, AMBER)
        txt(c, 2 * (bw + gap) + 4, y - 41, "change exactly one thing",
            "Body-Italic", 7.6, AMBER)


class ScoringLadder(Diagram):
    """Prefer the cheap check. Reach for a judge last."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "Reach for these in order", "Display-Bold", 9.4, INK)

        rows = [
            ("1", "Exact or substring match", GREEN,
             "Free, instant, never drifts, needs no model. Use it wherever the "
             "answer contains a checkable fact."),
            ("2", "A rule you write", PETROL,
             "A few lines of Python: is it valid JSON, is the total right, is "
             "the citation real. Still free, still deterministic."),
            ("3", "A model as judge", AMBER,
             "Necessary for prose. Also biased toward long answers, "
             "inconsistent between runs, and a cost per case."),
        ]
        y = h - 36
        for num, title, col, body in rows:
            rbox(c, 0, y - 42, w, 40, fill=WASH if col != AMBER else WASH_WARM,
                 stroke=col, lw=1.0)
            c.setFillColor(col)
            c.circle(22, y - 22, 11, stroke=0, fill=1)
            txt(c, 22, y - 25, num, "Display-Bold", 9.5, colors.white, "c")
            txt(c, 42, y - 15, title, "Display-Bold", 9, col)
            txt(c, 42, y - 31, body[:72], "Body", 7.8, INK)
            if len(body) > 72:
                txt(c, 42, y - 40, body[72:], "Body", 7.8, INK)
            y -= 54


def motif(c):
    """A number getting better."""
    import math
    base_x, base_y = 230, 240
    vals = [0.32, 0.46, 0.55, 0.78, 0.84]
    bw, gap = 26, 14
    c.setStrokeColor(colors.HexColor("#22665F"))
    c.setLineWidth(1.4)
    for i, v in enumerate(vals):
        x = base_x + i * (bw + gap)
        hgt = 130 * v
        if i == len(vals) - 1:
            c.setFillColor(colors.HexColor("#B85C1E"))
            c.rect(x, base_y, bw, hgt, stroke=0, fill=1)
        else:
            c.rect(x, base_y, bw, hgt, stroke=1, fill=0)
    c.line(base_x - 14, base_y, base_x + 5 * (bw + gap), base_y)


def build(out_path):
    doc, st = make_doc(
        out_path, "Evals - An Introduction",
        {"eyebrow": "LAB 8  ·  AN INTRODUCTION",
         "title": ["Evals"],
         "sub": ["How you find out whether the change you just",
                 "made actually made anything better."],
         "facts": [("FOR", "Anyone who has improved a prompt by feel."),
                   ("READ IT", "Before Sunday afternoon. Ten minutes.")],
         "motif": motif},
        "EVALS  ·  AN INTRODUCTION")

    st += [
        P("What it actually is", "h1"), Rule(8), Spacer(1, 4),
        P("A set of test cases, a way of scoring the answers, and a number. "
          "You change one thing, run it again, and watch the number move.",
          "lead"),
        P("That is the whole mechanism, and the reason it needs explaining is "
          "not that it is complicated. It is that almost nobody does it, and "
          "the alternative feels fine right up until it doesn't."),
        P("<b>The alternative is tuning by vibes.</b> You change a prompt. You "
          "try it once. It reads better. You ship it. You have no idea whether "
          "you fixed one case and broke two others, because you only looked at "
          "one case, and it was the one you were already thinking about."),
        Spacer(1, 6),
        KeepTogether([MeasureLoop(176),
                      Paragraph("Forty cases is a realistic start. The common "
                                "mistake is assuming you need hundreds, which "
                                "is why most people never begin.",
                                S["caption"])]),
        Spacer(1, 12),
        callout("Why this is the unglamorous half of the field",
                "Building something that works once is a demo, and demos are "
                "easy now. Knowing that it still works after a change - and "
                "being able to prove it to someone else - is the part that "
                "separates a prototype from a system, and almost nobody has "
                "it."),
        Spacer(1, 14),

        P("Example 1 - Making something measurably better", "h1"),
        Rule(8), Spacer(1, 4),
        P("The ordinary case: you have something that half works.", "lead"),
        P("Support tickets arrive and a model routes them to the right team. "
          "It is roughly right, and \"roughly\" is doing a lot of work in that "
          "sentence - nobody can say how roughly, because nobody has counted."),
        P("So you count. Forty real tickets, each with the team it should have "
          "gone to. One afternoon of work, mostly copy and paste. Then:"),
        Spacer(1, 4),
        two_col([
            ("Baseline",
             "<b>23 / 40.</b> Worse than anyone guessed. Three people had "
             "described it as \"pretty good\"."),
            ("+ team descriptions",
             "<b>29 / 40.</b> Telling it what each team actually owns, in one "
             "sentence each. The biggest single win, and the cheapest."),
            ("+ five examples",
             "<b>31 / 40.</b> A small gain for a large number of tokens on "
             "every request. Worth knowing before you pay for it forever."),
            ("+ an \"unclear\" option",
             "<b>36 / 40.</b> Letting it decline to route. Most of the "
             "remaining errors were tickets that genuinely could have gone to "
             "two teams."),
        ], left_w=150),
        Spacer(1, 12),
        P("Four numbers, and each one changed exactly one thing. That last "
          "row is the interesting one: the fix was not a better prompt, it was "
          "noticing that some tickets are genuinely ambiguous and the system "
          "had no way to say so. <b>You cannot find that by reading outputs. "
          "You find it by looking at which cases keep failing.</b>"),
        Spacer(1, 4),
        callout("The sentence this buys you",
                "\"I took it from 58% to 90%, and here is which change bought "
                "each increment.\" That is a different conversation from \"I "
                "improved the prompt\", in a standup, in a review, and "
                "especially in an interview.",
                fill=WASH, stroke=PETROL),
        PageBreak(),

        P("Example 2 - The day the model changes", "h1"), Rule(8), Spacer(1, 4),
        P("The case people do not see coming, and it is now routine.", "lead"),
        P("Your system has been running happily for eight months. Then one of "
          "these happens, and at least one of them will:"),
        Spacer(1, 2),
        two_col([
            ("A new version ships.", "Better on every published benchmark. "
                                     "Also different, in ways no benchmark "
                                     "measured, on your particular task."),
            ("Costs come under review.", "Someone asks whether the cheaper "
                                         "model would do. A perfectly "
                                         "reasonable question that you "
                                         "currently cannot answer."),
            ("A version is retired.", "You are moving whether you like it or "
                                      "not, on somebody else's timetable."),
        ], left_w=160),
        Spacer(1, 12),
        P("Without an eval suite, each of these is a gamble dressed up as a "
          "decision. You swap the model, click around for ten minutes, and "
          "ship. Any regression is discovered by customers, weeks later, in a "
          "form that does not obviously point back at the change."),
        P("With one, it is twenty minutes and a table:"),
        Spacer(1, 4),
        transcript([
            ("you", "python eval.py --compare"),
            ("out", "current    36/40   (90%)   412k tokens   $1.84"),
            ("out", "new        38/40   (95%)   401k tokens   $1.79"),
            ("out", "cheaper    31/40   (78%)   398k tokens   $0.31"),
            ("agent", "Regressions on the cheaper model are concentrated in "
                      "the ambiguous-ticket cases - it routes confidently "
                      "where the current one declines."),
        ]),
        Spacer(1, 10),
        P("Now the decision is a decision. The new version is a free upgrade. "
          "The cheaper one saves 83% of the bill and loses the exact behaviour "
          "you worked hardest to get - which might still be the right trade "
          "for a low-stakes queue, and you can now make that call deliberately "
          "rather than by accident."),
        PageBreak(),

        P("How to score without fooling yourself", "h1"), Rule(8), Spacer(1, 4),
        P("Most of the craft is here, and the rule is simple: use the cheapest "
          "check that can tell the difference.", "lead"),
        Spacer(1, 4),
        KeepTogether([ScoringLadder(180)]),
        Spacer(1, 12),
        callout("If you use a judge, check the judge",
                "Grade ten cases yourself and compare. A judge you have never "
                "audited is not a measurement - it is a second opinion from "
                "something with the same blind spots as the thing it is "
                "grading."),
        Spacer(1, 14),

        P("The case most suites are missing", "h2"),
        P("Every suite tests things the system should get right. Very few test "
          "what happens when the answer <b>is not available</b> - the question "
          "whose data does not exist, the ticket with a false premise, the "
          "field that is genuinely absent from the document."),
        P("A system that answers 95% of questions well and invents the other "
          "5% without flagging them is worse than one that answers 80% and "
          "says so, because with the first one you cannot tell which answers "
          "to trust. Put three unanswerable cases in your suite from the start."),
        Spacer(1, 14),

        P("What to take into the lab", "h2"),
        Spacer(1, 4),
        callout("One",
                "Cases, a scoring function, and a number. Forty cases is a "
                "real eval suite; the belief that you need hundreds is why "
                "most people have none.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 7),
        callout("Two",
                "Change one thing at a time, or the number tells you nothing "
                "about which change did what."),
        Spacer(1, 7),
        callout("Three",
                "Test what happens when the answer is not available. That is "
                "the failure that destroys trust, and it never appears in "
                "happy-path testing.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 16),
        P("<font face='Body-Italic' color='#6E7B78'>In the lab you will build a "
          "twelve-case suite against the agent from Saturday, run three "
          "variants of its prompt, and watch the number move. Then you will "
          "add three cases of your own and find out whether you can predict "
          "which ones it fails - being wrong about that is the most useful "
          "thing that can happen in the hour.</font>", "tight"),
    ]

    doc.build(st)
    print("Built", out_path)


if __name__ == "__main__":
    from pdfkit import publish
    publish(build, "Evals-Intro.pdf", "lab08_evals")
