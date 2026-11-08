"""Build the Lab 7 introduction PDF.

Matches the visual language of Agentic-AI-Weekend-Guide.pdf: petrol + amber,
Poppins for display, Caladea for body, DejaVu Mono for code.
"""

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

# ---------------------------------------------------------------- palette
INK = colors.HexColor("#16211F")
PETROL = colors.HexColor("#14504C")
PETROL_LT = colors.HexColor("#2C7A73")
AMBER = colors.HexColor("#B85C1E")
AMBER_LT = colors.HexColor("#E8B98A")
SLATE = colors.HexColor("#6E7B78")
RULE = colors.HexColor("#D5DCD9")
WASH = colors.HexColor("#EDF2F0")
WASH_WARM = colors.HexColor("#FAF3EC")
RED = colors.HexColor("#A9412F")
GREEN = colors.HexColor("#2F6B4F")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 22 * mm, 20 * mm, 20 * mm, 20 * mm
CW = PAGE_W - ML - MR

GF = "/usr/share/fonts/truetype/google-fonts"
CX = "/usr/share/fonts/truetype/crosextra"
DJ = "/usr/share/fonts/truetype/dejavu"

for name, path in [
    ("Display", f"{GF}/Poppins-Medium.ttf"),
    ("Display-Bold", f"{GF}/Poppins-Bold.ttf"),
    ("Display-Light", f"{GF}/Poppins-Light.ttf"),
    ("Body", f"{CX}/Caladea-Regular.ttf"),
    ("Body-Bold", f"{CX}/Caladea-Bold.ttf"),
    ("Body-Italic", f"{CX}/Caladea-Italic.ttf"),
    ("Body-BoldItalic", f"{CX}/Caladea-BoldItalic.ttf"),
    ("Mono", f"{DJ}/DejaVuSansMono.ttf"),
    ("Mono-Bold", f"{DJ}/DejaVuSansMono-Bold.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, path))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                              italic="Body-Italic", boldItalic="Body-BoldItalic")

S = {
    "h1": ParagraphStyle("h1", fontName="Display-Bold", fontSize=22, leading=26,
                         textColor=INK, spaceAfter=2),
    "h2": ParagraphStyle("h2", fontName="Display", fontSize=13, leading=17,
                         textColor=PETROL, spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="Display", fontSize=10, leading=14,
                         textColor=AMBER, spaceBefore=9, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Body", fontSize=10.2, leading=15.4,
                           textColor=INK, spaceAfter=7),
    "tight": ParagraphStyle("tight", fontName="Body", fontSize=10, leading=14.2,
                            textColor=INK, spaceAfter=3),
    "lead": ParagraphStyle("lead", fontName="Body-Italic", fontSize=11.6,
                           leading=17, textColor=PETROL, spaceAfter=10),
    "caption": ParagraphStyle("caption", fontName="Display-Light", fontSize=8.2,
                              leading=11.5, textColor=SLATE, alignment=TA_CENTER,
                              spaceBefore=3),
    "mono": ParagraphStyle("mono", fontName="Mono", fontSize=8.2, leading=12.2,
                           textColor=PETROL),
    "box_head": ParagraphStyle("box_head", fontName="Display-Bold", fontSize=8.6,
                               leading=12, textColor=AMBER),
    "box_body": ParagraphStyle("box_body", fontName="Body", fontSize=9.6,
                               leading=13.6, textColor=INK),
}


# ---------------------------------------------------------------- helpers
def txt(c, x, y, s, font="Display", size=8.5, color=INK, align="l"):
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "c":
        c.drawCentredString(x, y, s)
    elif align == "r":
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)
    c.restoreState()


def rbox(c, x, y, w, h, fill=None, stroke=None, r=4, lw=0.9, dash=None):
    c.saveState()
    if dash:
        c.setDash(dash)
    c.setLineWidth(lw)
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
    elif fill:
        c.setStrokeColor(fill)
    c.roundRect(x, y, w, h, r, stroke=1, fill=1 if fill else 0)
    c.restoreState()


def arrow(c, x1, y1, x2, y2, color=SLATE, lw=1.1, head=4.5, dash=None):
    import math
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(lw)
    if dash:
        c.setDash(dash)
    ang = math.atan2(y2 - y1, x2 - x1)
    bx = x2 - head * math.cos(ang) * 0.9
    by = y2 - head * math.sin(ang) * 0.9
    c.line(x1, y1, bx, by)
    c.setDash()
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head * math.cos(ang - 0.42), y2 - head * math.sin(ang - 0.42))
    p.lineTo(x2 - head * math.cos(ang + 0.42), y2 - head * math.sin(ang + 0.42))
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


class Diagram(Flowable):
    def __init__(self, height, width=None):
        super().__init__()
        self.height = height
        self.width = width or CW

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        self.paint(self.canv, self.width, self.height)


class Rule(Flowable):
    def __init__(self, space=6, color=RULE, lw=0.8):
        super().__init__()
        self.width, self.color, self.lw = CW, color, lw
        self.height = lw + space

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.lw)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


def callout(title, body, fill=WASH_WARM, stroke=AMBER):
    head = S["box_head"].clone("h")
    head.textColor = stroke
    inner = Table([[Paragraph(title.upper(), head)],
                   [Paragraph(body, S["box_body"])]], colWidths=[CW - 24])
    inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 0)]))
    outer = Table([[inner]], colWidths=[CW])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, stroke),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return outer


def transcript(rows):
    """rows: list of (speaker, text). speaker in {you, agent, tool, result}"""
    data, style = [], [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 10), ("RIGHTPADDING", (0, 0), (0, -1), 8),
        ("LEFTPADDING", (1, 0), (1, -1), 0), ("RIGHTPADDING", (1, 0), (1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    look = {
        "you":   ("YOU",   PETROL, "Body-Bold", WASH),
        "agent": ("AGENT", AMBER,  "Body",      None),
        "tool":  ("RUNS",  SLATE,  "Mono",      None),
        "out":   ("OUTPUT", SLATE, "Mono",      None),
    }
    for i, (who, text) in enumerate(rows):
        label, col, face, bg = look[who]
        lab = ParagraphStyle(f"l{i}", fontName="Display-Bold", fontSize=6.8,
                             leading=10, textColor=col)
        bodystyle = ParagraphStyle(
            f"b{i}", fontName=face,
            fontSize=8.0 if face == "Mono" else 9.5,
            leading=11.8 if face == "Mono" else 13.4,
            textColor=SLATE if face == "Mono" else INK)
        data.append([Paragraph(label, lab), Paragraph(text, bodystyle)])
        if bg:
            style.append(("BACKGROUND", (0, i), (-1, i), bg))
        if i < len(rows) - 1:
            style.append(("LINEBELOW", (0, i), (-1, i), 0.4, RULE))
    t = Table(data, colWidths=[46, CW - 46])
    t.setStyle(TableStyle(style))
    outer = Table([[t]], colWidths=[CW])
    outer.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return outer


# ---------------------------------------------------------------- diagrams
class ThreeModes(Diagram):
    """The definition, in one picture: only the third one closes."""

    def paint(self, c, w, h):
        bw, bh = 86, 26
        lane_h = (h - 14) / 3

        def lane(idx, title, boxes, closes, note):
            top = h - 12 - idx * lane_h          # baseline of the lane title
            by = top - 36                        # bottom edge of the boxes
            txt(c, 0, top, title, "Display-Bold", 9.2, AMBER if closes else INK)

            for i, (label, sub) in enumerate(boxes):
                x = 112 + i * (bw + 34)
                rbox(c, x, by, bw, bh, fill=WASH_WARM if closes else WASH,
                     stroke=AMBER if closes else PETROL_LT,
                     lw=1.3 if closes else 0.9)
                txt(c, x + bw / 2, by + bh / 2 + 1.5, label, "Display", 8.2,
                    AMBER if closes else PETROL, "c")
                txt(c, x + bw / 2, by + bh / 2 - 7.5, sub, "Body", 6.8, SLATE, "c")
                if i:
                    arrow(c, x - 30, by + bh / 2, x - 5, by + bh / 2,
                          AMBER if closes else PETROL_LT)

            if closes:
                x0 = 112 + (len(boxes) - 1) * (bw + 34) + bw / 2
                x1 = 112 + bw / 2
                c.saveState()
                c.setStrokeColor(AMBER)
                c.setLineWidth(1.3)
                p = c.beginPath()
                p.moveTo(x0, by - 3)
                p.lineTo(x0, by - 14)
                p.lineTo(x1, by - 14)
                c.drawPath(p)
                c.restoreState()
                arrow(c, x1 + 5, by - 14, x1, by - 4, AMBER, 1.3)
                txt(c, (x0 + x1) / 2, by - 25, "and round again, without you",
                    "Display-Bold", 7, AMBER, "c")
                for j, ln in enumerate(note.split("\n")):
                    txt(c, 0, by - 5 - j * 10, ln, "Body-Italic", 7.4, SLATE)
            else:
                ex = 112 + (len(boxes) - 1) * (bw + 34) + bw
                arrow(c, ex + 3, by + bh / 2, ex + 26, by + bh / 2, SLATE)
                rbox(c, ex + 29, by + 2, 54, bh - 4, fill=PETROL, stroke=PETROL)
                txt(c, ex + 56, by + bh / 2 - 3.5, "YOU", "Display-Bold", 8.6,
                    colors.white, "c")
                txt(c, 0, by - 11, note, "Body-Italic", 7.4, SLATE)

        lane(0, "Autocomplete", [("you type", "in the editor"),
                                 ("it suggests", "the next lines")],
             False, "stops at a suggestion.")
        lane(1, "Chat", [("you ask", "in a side panel"),
                         ("it answers", "with a snippet")],
             False, "stops at an answer. You are still the hands.")
        lane(2, "Agentic", [("it reads", "files you did not name"),
                            ("it acts", "edits, runs tests")],
             True, "it observes what happened,\nthen decides what next.")


class VerifySpectrum(Diagram):
    """What it can check for itself, and what only you can check."""

    def paint(self, c, w, h):
        txt(c, 0, h - 11, "Can the agent tell whether it got this right?",
            "Display-Bold", 9.4, INK)

        left_w = (w - 16) / 2
        items_l = ["a test that passes or fails",
                   "code that compiles, or doesn't",
                   "a linter's complaint",
                   "a crash and its stack trace",
                   "output that matches a fixture"]
        items_r = ["whether the rule it inferred is the rule you meant",
                   "whether the refactor preserved behaviour you never tested",
                   "whether the thing it deleted was load-bearing",
                   "whether the bug it did not find is worse",
                   "whether any of this was a good idea"]

        bh = 15
        top = h - 34

        rbox(c, 0, top - len(items_l) * bh - 20, left_w,
             len(items_l) * bh + 14, fill=WASH, stroke=GREEN, lw=1.1)
        txt(c, 11, top - 12, "YES - IT CLOSES THE LOOP ITSELF",
            "Display-Bold", 7.4, GREEN)
        for i, s in enumerate(items_l):
            txt(c, 11, top - 28 - i * bh, s, "Body", 8.4, INK)

        rx = left_w + 16
        rbox(c, rx, top - len(items_r) * bh - 20, left_w,
             len(items_r) * bh + 14, fill=WASH_WARM, stroke=RED, lw=1.1)
        txt(c, rx + 11, top - 12, "NO - ONLY YOU CAN", "Display-Bold", 7.4, RED)
        for i, s in enumerate(items_r):
            txt(c, rx + 11, top - 28 - i * bh, s, "Body", 8.4, INK)

        txt(c, 0, 2,
            "Everything on the left is why it works. Everything on the right is "
            "why you read the diff.",
            "Body-Italic", 8.2, AMBER)


# ---------------------------------------------------------------- pages
def cover(c, doc):
    c.saveState()
    c.setFillColor(PETROL)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # motif: a loop closing
    import math
    cx, cy, r = PAGE_W / 2 + 30, 300, 86
    c.setStrokeColor(colors.HexColor("#22665F"))
    c.setLineWidth(1.4)
    for i in range(3):
        rr = r - i * 26
        p = c.beginPath()
        steps = 60
        for s in range(steps + 1):
            a = math.radians(-40 + 310 * s / steps)
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            p.moveTo(x, y) if s == 0 else p.lineTo(x, y)
        c.drawPath(p)
    c.setStrokeColor(colors.HexColor("#B85C1E"))
    c.setLineWidth(2.4)
    p = c.beginPath()
    for s in range(61):
        a = math.radians(-40 + 310 * s / 60)
        x, y = cx + (r - 52) * math.cos(a), cy + (r - 52) * math.sin(a)
        p.moveTo(x, y) if s == 0 else p.lineTo(x, y)
    c.drawPath(p)

    c.setFillColor(colors.HexColor("#8FBDB8"))
    c.setFont("Mono", 9)
    c.drawString(ML, PAGE_H - 28 * mm, "LAB 7  ·  AN INTRODUCTION")

    c.setFillColor(colors.white)
    c.setFont("Display-Bold", 38)
    c.drawString(ML, PAGE_H - 52 * mm, "Agentic")
    c.drawString(ML, PAGE_H - 65 * mm, "Coding")

    c.setStrokeColor(colors.HexColor("#B85C1E"))
    c.setLineWidth(3)
    c.line(ML, PAGE_H - 74 * mm, ML + 58, PAGE_H - 74 * mm)

    c.setFillColor(colors.HexColor("#BFD6D2"))
    c.setFont("Body-Italic", 13)
    c.drawString(ML, PAGE_H - 86 * mm, "What it is, what it is good at, and where")
    c.drawString(ML, PAGE_H - 93 * mm, "it will confidently mislead you.")

    c.setStrokeColor(colors.HexColor("#1E6560"))
    c.setLineWidth(1)
    c.line(ML, 40 * mm, PAGE_W - MR, 40 * mm)
    c.setFillColor(colors.HexColor("#7FA9A4"))
    c.setFont("Display-Bold", 7)
    c.drawString(ML, 32 * mm, "FOR")
    c.setFillColor(colors.white)
    c.setFont("Body", 9.5)
    c.drawString(ML + 70, 31 * mm, "Anyone who has not watched one of these run before.")
    c.setFillColor(colors.HexColor("#7FA9A4"))
    c.setFont("Display-Bold", 7)
    c.drawString(ML, 25 * mm, "READ IT")
    c.setFillColor(colors.white)
    c.setFont("Body", 9.5)
    c.drawString(ML + 70, 24 * mm, "Before Sunday afternoon. Ten minutes.")
    c.restoreState()


def content_page(c, doc):
    c.saveState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(ML, PAGE_H - MT + 6 * mm, PAGE_W - MR, PAGE_H - MT + 6 * mm)
    c.setFont("Display-Light", 7.4)
    c.setFillColor(SLATE)
    c.drawString(ML, PAGE_H - MT + 8.5 * mm, "AGENTIC CODING  ·  AN INTRODUCTION")
    c.restoreState()


def content_page_end(c, doc):
    c.saveState()
    c.setFont("Mono", 8)
    c.setFillColor(SLATE)
    c.drawRightString(PAGE_W - MR, MB - 9 * mm, str(doc.page))
    c.restoreState()


def _not_table():
    rows = [
        ("Not a smarter autocomplete.",
         "Autocomplete predicts the next few characters you were going to type "
         "anyway. An agent decides which files to open."),
        ("Not a robot that replaces you.",
         "It cannot tell whether the change was a good idea, only whether the "
         "tests went green. Those are very different questions."),
        ("Not reliable because it sounds reliable.",
         "Fluency and correctness are unrelated. The most dangerous output is "
         "the confident, well-structured, subtly wrong one."),
    ]
    data = [[Paragraph(f"<font face='Display-Bold' size='9.4' color='#B85C1E'>"
                       f"{t}</font>", S["tight"]),
             Paragraph(b, S["tight"])] for t, b in rows]
    tb = Table(data, colWidths=[168, CW - 168])
    tb.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, RULE)]))
    return tb


# ---------------------------------------------------------------- build
def build(out_path):
    doc = BaseDocTemplate(out_path, pagesize=A4, leftMargin=ML, rightMargin=MR,
                          topMargin=MT, bottomMargin=MB,
                          title="Agentic Coding - An Introduction",
                          author="The Agentic AI Weekend")
    frame = Frame(ML, MB, CW, PAGE_H - MT - MB, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=cover),
        PageTemplate(id="content", frames=[frame], onPage=content_page,
                     onPageEnd=content_page_end),
    ])

    st = [NextPageTemplate("content"), PageBreak()]
    P = lambda t, s="body": Paragraph(t, S[s])  # noqa: E731

    # ---------------------------------------------------- what it is
    st += [
        P("What it actually is", "h1"), Rule(8), Spacer(1, 4),
        P("An agent is a loop: a model that can call functions, running until it "
          "stops asking for them. Agentic coding is that loop with three "
          "particular functions wired in - read a file, write a file, run a "
          "command.", "lead"),
        P("That is the whole definition. Everything surprising about it follows "
          "from one consequence of those three functions: <b>the loop closes.</b> "
          "The agent can run the thing it just wrote, read what happened, and "
          "decide what to do about it. Nothing else in the tooling you have used "
          "before can do that."),
        P("The difference is easiest to see against the two things people have "
          "already met."),
        Spacer(1, 6),
        KeepTogether([ThreeModes(250),
                      Paragraph("Autocomplete and chat both terminate at you. "
                                "The third one does not need you on every lap.",
                                S["caption"])]),
        Spacer(1, 12),
        callout("The distinction that matters",
                "Autocomplete and chat make <b>you</b> faster at writing code. An "
                "agent does work while you are not watching, and comes back with "
                "a result. Those are different products with different risks, and "
                "conflating them is why people are either disappointed or "
                "alarmed."),
        Spacer(1, 14),
        P("Three things it is not", "h2"),
        P("Most of the confusion comes from picturing one of the following, "
          "all of which are wrong.", "tight"),
        Spacer(1, 6),
        _not_table(),
        PageBreak(),
    ]

    # ---------------------------------------------------- example 1
    st += [
        P("Example 1 - A bug nobody could find", "h1"), Rule(8), Spacer(1, 4),
        P("This is the repository you will work on during the lab, so you can "
          "check every word of it on Sunday.", "lead"),
        P("<b>The situation.</b> A small billing calculator for a freight "
          "company. Eighty lines of Python, written in a hurry two years ago by "
          "someone who has since left. No tests. A README that states the "
          "business rules clearly. Finance have reported that some invoices "
          "\"look a bit off\" but nobody has narrowed it down."),
        P("Everyone has worked somewhere with a file like this. The reason it "
          "never gets fixed is not that it is hard - it is that finding the "
          "problem means holding the README and the code in your head at the "
          "same time and checking them against each other, line by line, for an "
          "hour, on a Tuesday, when four other things are on fire."),
        P("<b>What happens.</b> One instruction, then four exchanges:"),
        Spacer(1, 4),
        transcript([
            ("you", "Read the README and the code. Where do they disagree?"),
            ("tool", "reads README.md, rates.py, invoices.py, consignments.csv"),
            ("agent", "Four discrepancies. The clearest: the README says the bulk "
                      "discount applies to orders of 100 units <i>or more</i>, but "
                      "<font face='Mono' size='8'>apply_bulk_discount</font> tests "
                      "<font face='Mono' size='8'>qty &gt; 100</font>. Two "
                      "consignments in the sample data are exactly 100 and are "
                      "being overcharged."),
            ("you", "Don't fix it yet. Write a test that fails because of that, "
                    "and show me it failing."),
            ("tool", "writes test_rates.py, runs pytest"),
            ("out", "FAILED test_bulk_discount_at_exactly_100 - assert 1230.00 == "
                    "1131.60"),
            ("you", "Now fix it. Change nothing else."),
            ("tool", "edits rates.py line 17, runs pytest"),
            ("out", "1 passed"),
        ]),
        Spacer(1, 10),
        P("Four minutes, not an hour. But the interesting part is not the speed."),
        Spacer(1, 2),
        callout("One down",
                "That is one of several things wrong with this repository, and it "
                "is shown here deliberately so you can see the shape of the work. "
                "The others are still there, and at least one of them cannot be "
                "found by reading the code at all. Do not assume you have seen "
                "the exercise.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 6),
    ]

    # ---------------------------------------------------- why that shape
    st += [
        P("Why that exchange was shaped like that", "h2"),
        P("Notice what was <i>not</i> said. Nobody asked it to fix anything in "
          "the first message. The instruction was \"where do they disagree\", and "
          "the second instruction was explicitly <b>don't fix it yet</b>."),
        P("That is the discipline the whole lab is built around, and it comes "
          "down to one sentence:"),
        Spacer(1, 2),
        callout("Insist on this, every single time",
                "\"The model says there is a bug\" and \"there is a red test on my "
                "screen\" are completely different claims. Ask for the failing "
                "test <b>before</b> the fix. A fix without a failing test is a "
                "guess that you have agreed to ship.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 10),
        P("The failing test does three jobs at once. It proves the bug is real "
          "rather than plausible. It proves the agent understood which bug it was "
          "talking about. And when the fix lands, it proves the fix worked - "
          "without you reading a single line of the change."),
        P("That last point is what makes this scale. You are not reviewing code; "
          "you are reviewing <i>evidence</i>."),
        Spacer(1, 6),
        P("Example 2 - The first day on an unfamiliar codebase", "h1"),
        Rule(8), Spacer(1, 4),
        P("The use case that converts sceptics, because there is nothing to "
          "review and nothing to break.", "lead"),
        P("You have joined a team, or inherited a service, or been asked to fix "
          "something urgent in a repository you have never opened. Thirty "
          "thousand lines. The person who wrote it is on holiday. The "
          "documentation is a README from 2023 and a Confluence page that "
          "contradicts it."),
        P("Normally this costs you two days of reading before you can make a "
          "one-line change with any confidence. Instead:"),
        Spacer(1, 4),
        KeepTogether([transcript([
            ("you", "I've never seen this repo. What does it do, what are the "
                    "main moving parts, and where would I start if I needed to "
                    "change how pricing works?"),
            ("tool", "reads 40+ files, follows imports, greps for call sites"),
            ("agent", "It is an order pipeline with three entry points. Pricing is "
                      "calculated in two places that do not agree - "
                      "<font face='Mono' size='8'>pricing/engine.py</font> for the "
                      "web path and an older copy inside "
                      "<font face='Mono' size='8'>batch/nightly.py</font>. The web "
                      "one is the live path; the batch one is used for "
                      "reconciliation and has drifted. Start in engine.py, but "
                      "expect reconciliation to break."),
            ("you", "How do I run the tests?"),
            ("tool", "reads Makefile, CI config, tries make test"),
            ("out", "214 passed, 3 skipped in 48s"),
        ])]),
        Spacer(1, 10),
        P("Nothing was changed. Nothing could have been changed - you only asked "
          "it to read. The risk of this use case is approximately zero, and it "
          "compresses the most tedious two days in software engineering into a "
          "ten-minute conversation."),
        P("For anyone about to start a new job, this is the single most valuable "
          "thing in this document."),
        PageBreak(),
    ]

    # ---------------------------------------------------- where it fails
    st += [
        P("Where it goes wrong", "h1"), Rule(8), Spacer(1, 4),
        P("An introduction that only showed you the good parts would be an "
          "advert. Here is the failure mode that actually costs people money.",
          "lead"),
        P("<b>It is excellent at reading, good at narrow changes, and dangerous "
          "at broad ones.</b> Ask for a wide refactor and you will get back "
          "something clean, well-structured, plausible, and subtly different in "
          "behaviour. The diff will look fine. It will read like something a "
          "competent colleague wrote. And the thing it quietly changed is the "
          "thing you had no test for."),
        P("The reason is not that the model is careless. It is that the loop can "
          "only close around things that produce a signal."),
        Spacer(1, 6),
        VerifySpectrum(158),
        Spacer(1, 12),
        P("There is a second failure worth naming, because you will meet it in "
          "the lab. Some bugs are invisible from the code alone - they only "
          "appear when you look at the <i>data</i> the code runs on. An agent "
          "reading source sees a reasonable-looking default and moves on. Telling "
          "it to <b>run</b> the code on real inputs rather than reason about it "
          "is often the difference between finding the bug and confidently "
          "reporting that there isn't one."),
        Spacer(1, 4),
        P("The working discipline", "h2"),
        P("Four habits. None of them are optional, and all of them take seconds.",
          "tight"),
        Spacer(1, 4),
    ]

    habits = [
        ("Commit before you start.",
         "Work on a branch. <font face='Mono' size='8'>git checkout .</font> must "
         "always be free. Agent work is cheap to redo and expensive to "
         "half-review."),
        ("Ask for the failing test first.",
         "Every time. No exceptions. Evidence, not assertions."),
        ("Keep the task narrow.",
         "\"Fix the discount boundary\" - not \"clean up the billing code\". A "
         "task you can describe in one clause produces a diff you can read."),
        ("Read the whole diff.",
         "If it is too big to read, the task was too big. Go back and split it."),
    ]
    rows = [[Paragraph(f"<font face='Display-Bold' size='9.4' color='#14504C'>"
                       f"{t}</font>", S["tight"]),
             Paragraph(b, S["tight"])] for t, b in habits]
    tb = Table(rows, colWidths=[150, CW - 150])
    tb.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, RULE)]))
    st += [tb, PageBreak()]

    # ---------------------------------------------------- try it
    st += [
        P("Try it before Sunday", "h1"), Rule(8), Spacer(1, 4),
        P("Ten minutes, on a repository you already know, with no risk at all.",
          "lead"),
        P("Pick any project of your own - or clone something off GitHub you have "
          "never read. Then ask it only to <i>read</i>:"),
        Spacer(1, 4),
        callout("The four questions",
                "What does this project do, and who is it for?<br/>"
                "What are the main moving parts and how do they fit together?<br/>"
                "Where is the messiest part, and why?<br/>"
                "If I wanted to add X, where would I start?",
                fill=WASH, stroke=PETROL),
        Spacer(1, 10),
        P("On a repository you know well, you will be able to grade the answers "
          "immediately - which is the point. You will find out where it is sharp "
          "and where it is confidently vague, on material where you are the "
          "expert. That calibration is worth more than any amount of reading "
          "about it, including this document."),
        P("Then, if you want the full experience, give it write access on a "
          "branch and ask for one small, specific change. Read the diff. Throw it "
          "away. Do it again with a better-worded instruction."),
        Spacer(1, 8),
        P("What you should take into the lab", "h2"),
        P("Three sentences:", "tight"),
        Spacer(1, 6),
        callout("One",
                "An agent is a loop around a model that can read files, write "
                "files and run commands. The loop closing is the whole difference.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 7),
        callout("Two",
                "It is excellent at reading, good at narrow changes, and dangerous "
                "at broad ones. The skill is knowing which one you just asked for."),
        Spacer(1, 7),
        callout("Three",
                "Ask for the failing test before the fix. You are reviewing "
                "evidence, not code.",
                fill=WASH, stroke=PETROL),
        Spacer(1, 16),
        P("<font face='Body-Italic' color='#6E7B78'>Aurora Freight is fictional. "
          "The billing repository, its README and the bug described in Example 1 "
          "are real and are in the lab folder - you can check every claim in this "
          "document on Sunday morning.</font>", "tight"),
    ]

    doc.build(st)
    print("Built", out_path)


if __name__ == "__main__":
    from pdfkit import publish
    publish(build, "Agentic-Coding-Intro.pdf", "lab07_agentic_coding")
