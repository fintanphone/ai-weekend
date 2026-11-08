#!/usr/bin/env python3
"""Lab 5 — Skills: an introduction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib import colors
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer

from pdfkit import (AMBER, CW, INK, PETROL, PETROL_LT, RULE, SLATE, WASH,
                    WASH_WARM, Diagram, P, Rule, S, arrow, callout, make_doc,
                    rbox, spiral, transcript, two_col, txt)


# ------------------------------------------------------------------ diagrams
class Disclosure(Diagram):
    """Three levels, each wider, only the first always loaded."""

    def paint(self, c, w, h):
        levels = [
            ("Level 1", "Name and one-line description", "~50 tokens",
             "always in context, for every skill you own", 0.40, PETROL),
            ("Level 2", "The whole SKILL.md body", "~1,500 tokens",
             "loads only when the model judges it relevant", 0.70, PETROL_LT),
            ("Level 3", "Scripts, templates, reference files", "as needed",
             "loads only if those instructions ask for it", 1.0, AMBER),
        ]
        bh, gap = 48, 26
        top = h - 16
        txt(c, 0, h - 6, "What is loaded, and when", "Display-Bold", 9.4, INK)

        for i, (lvl, what, cost, when, frac, col) in enumerate(levels):
            y = top - (i + 1) * (bh + gap)
            bw = (w - 104) * frac
            rbox(c, 0, y, bw, bh, fill=WASH_WARM if i == 2 else WASH,
                 stroke=col, lw=1.2)
            txt(c, 12, y + bh - 18, lvl, "Display-Bold", 9, col)
            txt(c, 56, y + bh - 18, what, "Display", 9, INK)
            txt(c, 12, y + 12, when, "Body-Italic", 7.6, SLATE)
            txt(c, bw + 10, y + bh / 2 - 3.5, cost, "Mono", 7.6, col)
            if i < 2:
                arrow(c, 26, y - 4, 26, y - gap + 5, SLATE, 1.0)
                txt(c, 34, y - gap + 4,
                    "only if the description matches the task",
                    "Body-Italic", 7.2, SLATE)


class ContextCost(Diagram):
    """Twenty procedures: in the system prompt vs on demand."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "Twenty procedures, on every single request",
            "Display-Bold", 9.4, INK)

        bar_w = w - 150
        bh = 26

        def bar(y, label, filled, note, col, lw=0.9):
            txt(c, 0, y + bh / 2 - 3, label, "Display", 8.4, INK)
            rbox(c, 128, y, bar_w, bh, fill=None, stroke=RULE, lw=0.7)
            c.setFillColor(col)
            c.rect(128, y, bar_w * filled, bh, stroke=0, fill=1)
            c.setStrokeColor(RULE)
            c.setLineWidth(0.7)
            c.rect(128, y, bar_w, bh, stroke=1, fill=0)
            # label inside the fill when there is room, otherwise just after it
            if filled > 0.30:
                txt(c, 134, y + bh / 2 - 3, note, "Display-Bold", 7.6, colors.white)
            else:
                txt(c, 128 + bar_w * filled + 8, y + bh / 2 - 3, note,
                    "Display-Bold", 7.6, col)

        bar(h - 56, "In the system prompt", 1.0,
            "40,000 tokens, relevant or not", colors.HexColor("#A9412F"))
        bar(h - 104, "As skills", 0.055,
            "1,000 tokens of descriptions", PETROL)
        bar(h - 142, "   plus the one that fires", 0.135,
            "+1,500 when it is needed", AMBER)




def motif(c):
    spiral(c)


# ------------------------------------------------------------------ content
def build(out_path):
    doc, st = make_doc(
        out_path, "Skills - An Introduction",
        {"eyebrow": "LAB 5  ·  AN INTRODUCTION",
         "title": ["Skills"],
         "sub": ["A folder with a markdown file in it.",
                 "The interesting part is when it gets read."],
         "facts": [("FOR", "Anyone who has not written one."),
                   ("READ IT", "Before Sunday morning. Ten minutes.")],
         "motif": motif},
        "SKILLS  ·  AN INTRODUCTION")

    st += [
        P("What it actually is", "h1"), Rule(8), Spacer(1, 4),
        P("A skill is a folder containing a file called SKILL.md. That file has "
          "a name, a one-line description, and then instructions written in "
          "plain English. That is the entire format.", "lead"),
        P("The deflation is deliberate, because the format is not the idea. The "
          "idea is <b>when</b> the instructions get read."),
        P("Everything a model is told costs tokens, and because the API is "
          "stateless you pay for all of it again on every single request. So "
          "the obvious approach - put all your procedures in the system prompt - "
          "stops working almost immediately. Twenty procedures at two thousand "
          "tokens each is forty thousand tokens on every call, whether the "
          "request has anything to do with them or not."),
        Spacer(1, 6),
        KeepTogether([ContextCost(158),
                      Paragraph("Same twenty procedures either way. The saving "
                                "is not the point by itself - the point is that "
                                "it lets you have twenty at all.",
                                S["caption"])]),
        Spacer(1, 12),
        P("Skills solve that with <b>progressive disclosure</b>. Only the name "
          "and the one-line description are always present. The model reads "
          "those, decides whether a skill is relevant to what it has been "
          "asked, and loads the rest only if it is."),
        Spacer(1, 4),
        KeepTogether([Disclosure(250),
                      Paragraph("The model does the routing. You are not "
                                "writing an if-statement.", S["caption"])]),
        PageBreak(),

        P("The consequence nobody expects", "h2"),
        P("Because level one is all the model sees when it decides, <b>the "
          "description line is the most important line in the file</b>. It is "
          "doing all the routing work, and it is the part people write last and "
          "least carefully."),
        Spacer(1, 2),
        callout("The failure you will have, the first time",
                "A vague description never fires. The skill sits there, "
                "perfectly written, and is never read - and because nothing "
                "errors, you conclude that skills do not work. Write the "
                "description as \"Use this when the user asks about X, Y or "
                "Z\", and name the nouns that should trigger it."),
        Spacer(1, 14),

        P("Example 1 - Five people, five formats", "h1"), Rule(8), Spacer(1, 4),
        P("The problem skills were built for, and the one most teams have "
          "without noticing.", "lead"),
        P("Your team writes incident reports. There is a template for them in "
          "Confluence. Nobody opens it. So five engineers write five different "
          "shapes of report, the severity field means something different to "
          "each of them, and the monthly review is an exercise in archaeology."),
        P("This is not a knowledge problem. Everyone knows how an incident "
          "report should look. It is a <i>consistency</i> problem, and asking "
          "people to try harder has never once fixed one."),
        Spacer(1, 4),
        transcript([
            ("you", "Write up last night's outage. Logs are in the thread."),
            ("agent", "I have an incident-report skill available - loading it."),
            ("tool", "reads skills/incident-report/SKILL.md"),
            ("agent", "Writes the report in the house format: timeline in UTC "
                      "with one line per event, impact stated in customers "
                      "affected rather than services affected, severity from the "
                      "fixed four-value scale, contributing factors separated "
                      "from root cause, and actions with named owners."),
        ]),
        Spacer(1, 10),
        P("The same shape, every time, from everyone. That consistency is the "
          "product - it is what makes the monthly review possible, and it is "
          "what you could never get by sending round a template."),
        Spacer(1, 4),
        callout("Why this beats a better prompt",
                "You could paste the template into a prompt each time. The "
                "difference is that a skill is a file in a repository: it gets "
                "reviewed, versioned, improved, and rolled back. When the "
                "format changes, it changes in one place for everyone.",
                fill=WASH, stroke=PETROL),
        PageBreak(),

        P("Example 2 - The rules that are expensive to re-explain", "h1"),
        Rule(8), Spacer(1, 4),
        P("Domain knowledge that lives in one person's head, written down once.",
          "lead"),
        P("Every field has rules that are obvious to the people who have been "
          "burned by them and invisible to everyone else. A data team knows "
          "that an identifier column must never be summed, even when it is "
          "numeric. A finance team knows which of two date fields is the one "
          "that matters for a cut-off. A clinical team knows which codes are "
          "never reported without a denominator."),
        P("These are the rules you explain to every new starter, in person, "
          "twice. A skill is where they go instead."),
        Spacer(1, 4),
        transcript([
            ("you", "Profile this CSV for me."),
            ("agent", "Loading the csv-profiler skill."),
            ("tool", "reads skills/csv-profiler/SKILL.md"),
            ("agent", "Shape, then a column table with an inferred type for "
                      "each. Note that order_ref is numeric but is an "
                      "identifier, so it is typed as such and excluded from the "
                      "summary statistics. Two quality flags: a 7% null rate in "
                      "region, and inconsistent capitalisation in channel."),
        ]),
        Spacer(1, 10),
        P("The useful detail is the one in the middle. Nothing in the data says "
          "<i>order_ref</i> is an identifier - it is a column of integers. The "
          "skill said so, because somebody who had once averaged a column of "
          "order numbers wrote it down."),
        Spacer(1, 6),
        P("What a skill is good for", "h2"),
        Spacer(1, 2),
        two_col([
            ("Procedure", "A sequence that must be followed the same way every "
                          "time. Reviews, reports, handovers, checklists."),
            ("House format", "An output shape your team has agreed on and keeps "
                             "failing to apply consistently."),
            ("Hard-won rules", "The gotchas that are obvious only to people who "
                               "have already been caught by them."),
            ("Tool conventions", "How your organisation uses a thing, as "
                                 "distinct from how the thing works."),
        ], left_w=136),
        PageBreak(),

        P("Where it goes wrong", "h1"), Rule(8), Spacer(1, 4),
        P("Three failures, in the order you will meet them.", "lead"),
        Spacer(1, 2),
        two_col([
            ("It never fires.",
             "The description was too vague, or used different words from the "
             "ones people actually type. The skill is invisible and nothing "
             "tells you. Test the trigger, not just the content: ask three "
             "differently-worded questions and check it loads."),
            ("It fires when it should not.",
             "The description was too broad, so a csv-profiler skill loads when "
             "someone asks to list the files in a folder. Wasted tokens and a "
             "confused answer. Test this too - ask something adjacent and check "
             "it stays quiet."),
            ("It is ignored once loaded.",
             "Instructions that suggest get ignored; instructions that specify "
             "get followed. \"Consider using a table\" is decoration. \"Output "
             "a markdown table with exactly these five columns\" is a "
             "procedure."),
        ], left_w=168, label_color="#A9412F"),
        Spacer(1, 14),
        callout("The one that is not a usability problem",
                "A skill is a set of instructions that a model will follow, "
                "stored in a file. If someone can commit a file to your "
                "repository, they can change what your agents do - and a skill "
                "that fetches content from an external URL can have its "
                "instructions changed by someone outside your organisation "
                "entirely. Review skills the way you review code, because that "
                "is what they are."),
        Spacer(1, 14),

        P("What to take into the lab", "h2"),
        Spacer(1, 4),
        callout("One",
                "A skill is a folder with a markdown file in it. The format is "
                "not the idea; <b>when it gets read</b> is the idea.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 7),
        callout("Two",
                "The description does the routing and the body does the work. "
                "Most first skills fail at the description."),
        Spacer(1, 7),
        callout("Three",
                "The product is consistency. A model that writes a good report "
                "is useful; one that writes the <i>same</i> report every time is "
                "something you can give to a team.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 16),
        P("<font face='Body-Italic' color='#6E7B78'>In the lab you will write a "
          "skill, watch a model discover and load it, and then swap with your "
          "partner - because the fastest way to learn what a good description "
          "looks like is to watch yours fail to fire on somebody else's "
          "phrasing.</font>", "tight"),
    ]

    doc.build(st)
    print("Built", out_path)


if __name__ == "__main__":
    from pdfkit import publish
    publish(build, "Skills-Intro.pdf", "lab05_skills")
