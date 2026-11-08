#!/usr/bin/env python3
"""Lab 6 — MCP: an introduction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib import colors
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer

from pdfkit import (AMBER, CW, INK, PETROL, PETROL_LT, RULE, SLATE, WASH,
                    WASH_WARM, Diagram, P, Rule, S, arrow, callout, make_doc,
                    rbox, transcript, two_col, txt)

RED = colors.HexColor("#A9412F")


class Before(Diagram):
    """Three apps, three copies of the same integration."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "Without a protocol", "Display-Bold", 9.4, INK)

        bw, bh = 116, 30
        apps = [("Your agent", "Lab 3's loop"),
                ("A colleague's", "different repo"),
                ("Your editor", "someone else's app")]
        x0 = (w - (3 * bw + 2 * 22)) / 2
        y = h - 54

        for i, (name, sub) in enumerate(apps):
            x = x0 + i * (bw + 22)
            rbox(c, x, y, bw, bh, fill=colors.white, stroke=PETROL)
            txt(c, x + bw / 2, y + bh / 2 + 1.5, name, "Display", 8.6, PETROL, "c")
            txt(c, x + bw / 2, y + bh / 2 - 8, sub, "Body", 6.8, SLATE, "c")

            # each one carries its own copy of the integration
            iy = y - 42
            rbox(c, x, iy, bw, 26, fill=WASH_WARM, stroke=RED, dash=(2, 2))
            txt(c, x + bw / 2, iy + 9, "its own copy", "Display", 7.6, RED, "c")
            arrow(c, x + bw / 2, y - 3, x + bw / 2, iy + 29, RED, 1.0, dash=(2, 2))
            arrow(c, x + bw / 2, iy - 3, w / 2, iy - 26, SLATE, 0.9)

        rbox(c, (w - 150) / 2, h - 152, 150, 26, fill=PETROL, stroke=PETROL)
        txt(c, w / 2, h - 143, "your ticketing system", "Display-Bold", 8.4,
            colors.white, "c")

        txt(c, 0, 4, "Three integrations to write, three to keep in step, "
                     "three to fix when the API changes.",
            "Body-Italic", 8, RED)


class After(Diagram):
    """One server, any client."""

    def paint(self, c, w, h):
        txt(c, 0, h - 10, "With one", "Display-Bold", 9.4, INK)

        bw, bh = 116, 30
        apps = ["Your agent", "A colleague's", "Your editor"]
        x0 = (w - (3 * bw + 2 * 22)) / 2
        y = h - 54

        for i, name in enumerate(apps):
            x = x0 + i * (bw + 22)
            rbox(c, x, y, bw, bh, fill=colors.white, stroke=PETROL)
            txt(c, x + bw / 2, y + bh / 2 - 3, name, "Display", 8.6, PETROL, "c")
            arrow(c, x + bw / 2, y - 3, w / 2 + (i - 1) * 30, y - 34, PETROL_LT)

        band_y = h - 112
        rbox(c, 0, band_y, w, 28, fill=PETROL, stroke=PETROL)
        txt(c, w / 2, band_y + 9.5, "MCP     ·     one protocol, standard transport",
            "Display-Bold", 9.2, colors.white, "c")

        sy = band_y - 54
        rbox(c, (w - 170) / 2, sy, 170, 30, fill=WASH_WARM, stroke=AMBER, lw=1.3)
        txt(c, w / 2, sy + 16, "one server you write", "Display-Bold", 8.6, AMBER, "c")
        txt(c, w / 2, sy + 6, "your ticketing system", "Body", 7, SLATE, "c")
        arrow(c, w / 2, band_y - 3, w / 2, sy + 33, AMBER)




def motif(c):
    """Three clients converging on one band."""
    import math
    cx, cy = 300, 300
    c.setStrokeColor(colors.HexColor("#22665F"))
    c.setLineWidth(1.4)
    for dx in (-80, 0, 80):
        c.line(cx + dx, cy + 70, cx + dx * 0.25, cy + 8)
    for dx in (-80, 0, 80):
        c.line(cx + dx * 0.25, cy - 8, cx + dx, cy - 70)
    c.setStrokeColor(colors.HexColor("#B85C1E"))
    c.setLineWidth(2.6)
    c.line(cx - 110, cy, cx + 110, cy)


def build(out_path):
    doc, st = make_doc(
        out_path, "MCP - An Introduction",
        {"eyebrow": "LAB 6  ·  AN INTRODUCTION",
         "title": ["Model Context", "Protocol"],
         "title_size": 33,
         "sub": ["Tools stop belonging to one application.",
                 "Write the integration once; any client can use it."],
         "facts": [("FOR", "Anyone who has written an integration twice."),
                   ("READ IT", "Before Sunday morning. Ten minutes.")],
         "motif": motif},
        "MCP  ·  AN INTRODUCTION")

    st += [
        P("What it actually is", "h1"), Rule(8), Spacer(1, 4),
        P("A standard way for a program that uses a model to discover and call "
          "tools that live somewhere else. A server offers capabilities; any "
          "client can consume them.", "lead"),
        P("The reason it exists is easiest to see by describing the problem it "
          "removes. When you give an agent a tool, you write that tool into the "
          "agent. It works in that script and nowhere else. Want the same tool "
          "in a second application? Copy the code. A third? Copy it again."),
        P("Everyone who has worked in infrastructure recognises this "
          "immediately. It is the problem that produced shared libraries, then "
          "internal APIs, then service discovery. The answer has always been "
          "the same: expose the capability once, behind an agreed interface, "
          "and let the callers find it."),
        Spacer(1, 6),
        KeepTogether([Before(170)]),
        Spacer(1, 14),
        KeepTogether([After(178),
                      Paragraph("Write it once. Every client that speaks the "
                                "protocol gets it, including ones that do not "
                                "exist yet.", S["caption"])]),
        Spacer(1, 10),
        callout("The part that surprises people",
                "The client does not know your server is a Python script "
                "talking to Postgres, and your server does not know or care "
                "which client is asking. Neither side was written with the "
                "other in mind. That is the whole point of a protocol, and it "
                "is why a tool you write today works in a client released next "
                "year."),
        Spacer(1, 14),

        P("Example 1 - Exposing something of your own", "h1"),
        Rule(8), Spacer(1, 4),
        P("The case where you write the server.", "lead"),
        P("Your company has a deployment system. It knows which version is in "
          "which environment, who released it, and what the rollback target "
          "is. Four people have written their own scripts to query it. Two of "
          "those scripts are broken and nobody has noticed."),
        P("Instead, one person writes a small MCP server with four narrow "
          "tools: <font face='Mono' size='8'>current_version</font>, "
          "<font face='Mono' size='8'>deploy_history</font>, "
          "<font face='Mono' size='8'>who_released</font>, "
          "<font face='Mono' size='8'>rollback_target</font>. Perhaps sixty "
          "lines. Then:"),
        Spacer(1, 4),
        transcript([
            ("you", "What's in production right now, and who put it there?"),
            ("tool", "current_version(env=\"production\")"),
            ("out", "4.18.2, deployed 2026-11-06 14:21 UTC"),
            ("tool", "who_released(version=\"4.18.2\")"),
            ("out", "released by m.okafor, PR #3312"),
            ("agent", "Production is on 4.18.2, released by Maryam Okafor "
                      "yesterday afternoon from PR 3312. The previous version "
                      "was 4.18.1 if you need a rollback target."),
        ]),
        Spacer(1, 10),
        P("The useful part is not that one question got answered. It is that "
          "the same four tools now work in everyone's client, the team stopped "
          "maintaining four scripts, and the access rules live in one place "
          "where they can be reviewed."),
        Spacer(1, 6),
        P("Example 2 - Consuming somebody else's", "h1"),
        Rule(8), Spacer(1, 4),
        P("The case where the work is already done.", "lead"),
        P("You want your agent to read from a Postgres database, or search the "
          "web, or look at files on your machine. You could write those tools. "
          "Somebody already has, and theirs handles the connection pooling and "
          "the pagination and the error cases that yours would get wrong for "
          "the first month."),
        P("Adding one is a single command, and from that moment the tools "
          "simply exist in your client. You did not write a schema, a dispatch "
          "function or a loop."),
        Spacer(1, 4),
        callout("What to notice the first time",
                "Your client will ask your permission before each call. Watch "
                "that prompt carefully, because it is the main security "
                "boundary in practice - and ask yourself honestly whether you "
                "would still be reading it on the two hundredth call of a long "
                "session.",
                fill=WASH, stroke=PETROL),
        PageBreak(),

        P("The design decision that matters most", "h1"), Rule(8), Spacer(1, 4),
        P("You will be tempted by one powerful tool. Resist it.", "lead"),
        P("The deployment server above has four narrow tools. The obvious "
          "alternative is one general one - "
          "<font face='Mono' size='8'>run_query(sql)</font> - which is less "
          "code, more flexible, and handles questions you have not thought of "
          "yet."),
        P("It is also a genuinely bad idea, and the reason is worth stating "
          "precisely. The tool list is not a convenience for the model. "
          "<b>The tool list is the capability grant.</b> Four narrow tools "
          "give the model four things it can do. One SQL tool gives it "
          "everything the database connection can do, including every row of "
          "every table and every statement that is not a SELECT."),
        Spacer(1, 4),
        two_col([
            ("Four narrow tools",
             "The model can ask four questions. You can audit which. You can "
             "require approval for one of them and not the others. A prompt "
             "injection in the data can, at worst, make it ask a question it "
             "was already allowed to ask."),
            ("One run_query tool",
             "The model can do anything the credential can do. You cannot "
             "meaningfully approve a call without reading and understanding "
             "the SQL. \"Is this statement destructive?\" is not a question "
             "you can answer by inspecting a string."),
        ], left_w=150, label_color="#A9412F"),
        Spacer(1, 12),
        callout("The sentence to remember",
                "Narrow tools are a <b>permissioning mechanism</b>, not a "
                "limitation. Every tool you decline to write is a thing the "
                "model cannot be talked into doing."),
        Spacer(1, 14),

        P("Where else it goes wrong", "h2"),
        Spacer(1, 2),
        two_col([
            ("The docstring is the interface.",
             "Not documentation - interface. The model reads it to decide "
             "whether your tool is relevant and what to put in the arguments. "
             "A tool described as \"Gets data\" will be used wrongly or not at "
             "all, and nothing will error."),
            ("Server output enters your context.",
             "Whatever a server returns is read by the model as part of the "
             "conversation. A server that returns text containing instructions "
             "is prompt injection with an extra hop - and if it is somebody "
             "else's server, it is somebody else's code deciding what your "
             "agent reads."),
            ("Third-party servers are dependencies.",
             "Installing one is running someone's code with your credentials "
             "and your data. Read it, pin it, and apply whatever standard you "
             "would apply to any other dependency."),
        ], left_w=178, label_color="#A9412F"),
        PageBreak(),

        P("What to take into the lab", "h2"),
        Spacer(1, 4),
        callout("One",
                "A tool is a contract: a name, a description, an argument "
                "shape. MCP is that contract with a standard transport, so it "
                "stops belonging to one application.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 7),
        callout("Two",
                "Narrow tools are a permissioning mechanism, not a limitation. "
                "You will want to write run_query. Do not write run_query."),
        Spacer(1, 7),
        callout("Three",
                "The docstring is the interface. Write it for the model, "
                "because the model is the only thing that reads it.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 16),
        P("In the lab you will connect to a server somebody else wrote, then "
          "write your own exposing a small database - about sixty lines - and "
          "register it. The experiment worth doing at the end is writing a "
          "tool with a deliberately vague docstring and watching the model "
          "fail to use it. Nothing makes the point faster."),
        Spacer(1, 10),
        P("<font face='Body-Italic' color='#6E7B78'>The specification lives at "
          "modelcontextprotocol.io. It is readable in an afternoon, which is "
          "unusual for a specification and says something good about how much "
          "of this is genuinely new.</font>", "tight"),
    ]

    doc.build(st)
    print("Built", out_path)


if __name__ == "__main__":
    from pdfkit import publish
    publish(build, "MCP-Intro.pdf", "lab06_mcp")
