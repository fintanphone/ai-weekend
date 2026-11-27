#!/usr/bin/env python3
"""The opening housekeeping slide.

    python build_housekeeping.py

One landscape A4 page, played absolutely straight. The entire joke is that the
register never slips: it is the slide a conference centre would show four
hundred delegates, shown to three people in a house. Resist the urge to add a
wink anywhere — no exclamation marks, no emoji, no "(not really)". The moment
it admits it is joking it stops being funny.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

from pdfkit import AMBER, INK, PETROL, PETROL_LT, RULE, SLATE, WASH, rbox, txt

OUT = "Housekeeping.pdf"
PW, PH = landscape(A4)
M = 18 * mm
CW = PW - 2 * M


# ------------------------------------------------------------------ icons
# Deliberately plain. Clip-art would be funnier for about one second and then
# would just look like a joke slide.

def _setup(c, col, lw=1.6):
    c.saveState()
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(lw)
    c.setLineCap(1)
    c.setLineJoin(1)


def icon_exit(c, x, y, s, col):
    _setup(c, col)
    c.rect(x, y, s * 0.55, s, stroke=1, fill=0)                 # doorway
    c.line(x + s * 0.72, y + s * 0.5, x + s * 1.15, y + s * 0.5)  # arrow shaft
    c.line(x + s * 1.0, y + s * 0.64, x + s * 1.15, y + s * 0.5)
    c.line(x + s * 1.0, y + s * 0.36, x + s * 1.15, y + s * 0.5)
    c.restoreState()


def icon_cup(c, x, y, s, col):
    _setup(c, col)
    p = c.beginPath()
    p.moveTo(x, y + s * 0.72)
    p.lineTo(x + s * 0.08, y + s * 0.08)
    p.lineTo(x + s * 0.72, y + s * 0.08)
    p.lineTo(x + s * 0.80, y + s * 0.72)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.arc(x + s * 0.72, y + s * 0.30, x + s * 1.06, y + s * 0.62, -90, 180)
    for i in range(2):                                           # steam
        sx = x + s * (0.28 + i * 0.26)
        c.line(sx, y + s * 0.86, sx, y + s * 1.04)
    c.restoreState()


def icon_door(c, x, y, s, col):
    _setup(c, col)
    c.rect(x + s * 0.12, y, s * 0.66, s, stroke=1, fill=0)
    c.circle(x + s * 0.66, y + s * 0.46, s * 0.055, stroke=1, fill=1)
    c.restoreState()


def icon_norant(c, x, y, s, col):
    _setup(c, col)
    c.roundRect(x, y + s * 0.26, s * 1.0, s * 0.68, s * 0.14, stroke=1, fill=0)
    p = c.beginPath()                                            # bubble tail
    p.moveTo(x + s * 0.24, y + s * 0.28)
    p.lineTo(x + s * 0.22, y + s * 0.02)
    p.lineTo(x + s * 0.46, y + s * 0.26)
    c.drawPath(p, stroke=1, fill=0)
    c.setLineWidth(2.0)                                          # the bar sinister
    c.line(x - s * 0.06, y + s * 0.20, x + s * 1.04, y + s * 1.00)
    c.restoreState()


def icon_phone(c, x, y, s, col):
    _setup(c, col)
    c.roundRect(x + s * 0.22, y, s * 0.56, s, s * 0.10, stroke=1, fill=0)
    c.line(x + s * 0.40, y + s * 0.90, x + s * 0.60, y + s * 0.90)
    c.circle(x + s * 0.50, y + s * 0.12, s * 0.05, stroke=1, fill=1)
    c.restoreState()


def icon_wifi(c, x, y, s, col):
    _setup(c, col)
    cx, cy = x + s * 0.5, y + s * 0.12
    for r in (s * 0.26, s * 0.48, s * 0.70):
        c.arc(cx - r, cy - r, cx + r, cy + r, 35, 110)
    c.circle(cx, cy, s * 0.055, stroke=0, fill=1)
    c.restoreState()


# ------------------------------------------------------------------ copy
ITEMS = [
    (icon_exit, "Fire exits",
     ["The front door and the back door. In the event of an",
      "alarm, leave by whichever is nearer and assemble on",
      "the lawn. Delegates are asked not to congregate by",
      "the bins."]),
    (icon_cup, "Refreshments",
     ["Tea and coffee are provided free of charge in the",
      "canteen. The canteen is the kitchen. Dietary",
      "requirements should have been notified at the point",
      "of booking. There was no booking."]),
    (icon_door, "Facilities",
     ["The bathroom is the middle door in the corridor.",
      "The other two doors are not the bathroom and we",
      "would ask that you satisfy yourself on this point",
      "before the session begins."]),
    (icon_norant, "No ranting",
     ["Strong opinions are warmly encouraged. Sustained",
      "ranting is not. For the purposes of this session a rant",
      "is any opinion still being expressed three minutes",
      "after everybody has agreed with it."]),
    (icon_phone, "Mobile devices",
     ["Please set all devices to silent. The venue has a",
      "capacity of three and we will establish whose it is",
      "almost immediately."]),
    (icon_wifi, "Connectivity",
     ["The wireless password is on the router. It has always",
      "been on the router. It was on the router the last time",
      "you asked."]),
]

SMALL_PRINT = (
    "This venue is on one floor and has no lift  ·  Lanyards are not provided; "
    "delegates should introduce themselves as required  ·  This session is not "
    "being recorded  ·  Feedback will be gathered informally, in the kitchen"
)


def build(path):
    c = pdfcanvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Housekeeping")
    c.setFillColor(colors.white)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    # ---------------------------------------------------------- header
    top = PH - M
    txt(c, M, top - 24, "Housekeeping", "Display-Bold", 30, INK)
    txt(c, PW - M, top - 22, "AGENTIC AI WEEKEND", "Display-Bold", 9, PETROL, "r")
    txt(c, PW - M, top - 34, "Delegate Information  ·  Rev. 1.0", "Body-Italic",
        8.4, SLATE, "r")
    txt(c, M, top - 42,
        "Please take a moment to familiarise yourself with the following before "
        "we begin.", "Body-Italic", 11, PETROL)

    c.setStrokeColor(RULE)
    c.setLineWidth(0.9)
    c.line(M, top - 54, PW - M, top - 54)

    # ---------------------------------------------------------- the grid
    gap = 22
    colw = (CW - gap * 2) / 3
    rowh = 170
    gtop = top - 72

    for i, (icon, head, body) in enumerate(ITEMS):
        col, row = i % 3, i // 3
        x = M + col * (colw + gap)
        y = gtop - row * (rowh + 18) - rowh

        rbox(c, x, y, colw, rowh, fill=WASH, stroke=RULE, r=4)
        icon(c, x + 20, y + rowh - 48, 34, PETROL)
        txt(c, x + 20, y + rowh - 78, head, "Display-Bold", 14, INK)

        yy = y + rowh - 100
        for line in body:
            txt(c, x + 20, yy, line, "Body", 9.8, SLATE)
            yy -= 13.4

    # ---------------------------------------------------------- footer
    fy = gtop - 2 * (rowh + 18) + 18 - 24
    c.setStrokeColor(RULE)
    c.line(M, fy, PW - M, fy)
    txt(c, M, fy - 15, SMALL_PRINT, "Body-Italic", 8.4, SLATE)
    txt(c, PW - M, fy - 29, "Thank you for your co-operation.", "Body-Bold",
        8.8, PETROL, "r")

    c.showPage()
    c.save()


if __name__ == "__main__":
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    target = repo / "pdfs" / OUT
    target.parent.mkdir(exist_ok=True)
    build(str(target))
    print(f"built {target}  ({target.stat().st_size / 1024:.0f} KB)")
