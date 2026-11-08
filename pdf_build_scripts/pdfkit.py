"""Shared design system for the lab introduction PDFs.

Petrol + amber, Poppins for display, Caladea for body, DejaVu Mono for code -
the same language as Agentic-AI-Weekend-Guide.pdf and the Lab 7 intro.

Each lab's PDF imports this, defines its own diagrams, and calls make_doc().
"""

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




# ---------------------------------------------------------------- pages
def make_cover(spec):
    """Returns an onPage handler for the cover, driven by a spec dict:
    eyebrow, title (1-2 lines), sub (1-2 lines), facts [(label, value), ...]"""

    def cover(c, doc):
        import math
        c.saveState()
        c.setFillColor(PETROL)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

        spec["motif"](c)

        c.setFillColor(colors.HexColor("#8FBDB8"))
        c.setFont("Mono", 9)
        c.drawString(ML, PAGE_H - 28 * mm, spec["eyebrow"])

        c.setFillColor(colors.white)
        c.setFont("Display-Bold", spec.get("title_size", 38))
        y = PAGE_H - 52 * mm
        for line in spec["title"]:
            c.drawString(ML, y, line)
            y -= 13 * mm

        c.setStrokeColor(colors.HexColor("#B85C1E"))
        c.setLineWidth(3)
        c.line(ML, y + 4 * mm, ML + 58, y + 4 * mm)

        c.setFillColor(colors.HexColor("#BFD6D2"))
        c.setFont("Body-Italic", 13)
        y -= 8 * mm
        for line in spec["sub"]:
            c.drawString(ML, y, line)
            y -= 7 * mm

        c.setStrokeColor(colors.HexColor("#1E6560"))
        c.setLineWidth(1)
        c.line(ML, 40 * mm, PAGE_W - MR, 40 * mm)
        fy = 32 * mm
        for label, value in spec["facts"]:
            c.setFillColor(colors.HexColor("#7FA9A4"))
            c.setFont("Display-Bold", 7)
            c.drawString(ML, fy, label)
            c.setFillColor(colors.white)
            c.setFont("Body", 9.5)
            c.drawString(ML + 70, fy - 1, value)
            fy -= 7 * mm
        c.restoreState()

    return cover


def content_page(c, doc):
    c.saveState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(ML, PAGE_H - MT + 6 * mm, PAGE_W - MR, PAGE_H - MT + 6 * mm)
    c.setFont("Display-Light", 7.4)
    c.setFillColor(SLATE)
    c.drawString(ML, PAGE_H - MT + 8.5 * mm, RUNNING["head"])
    c.restoreState()


def content_page_end(c, doc):
    c.saveState()
    c.setFont("Mono", 8)
    c.setFillColor(SLATE)
    c.drawRightString(PAGE_W - MR, MB - 9 * mm, str(doc.page))
    c.restoreState()


RUNNING = {"head": ""}


def make_doc(out_path, title, cover_spec, running_head):
    """Returns (doc, story_prefix). Append flowables, then doc.build(story)."""
    RUNNING["head"] = running_head
    doc = BaseDocTemplate(out_path, pagesize=A4, leftMargin=ML, rightMargin=MR,
                          topMargin=MT, bottomMargin=MB, title=title,
                          author="The Agentic AI Weekend")
    frame = Frame(ML, MB, CW, PAGE_H - MT - MB, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=make_cover(cover_spec)),
        PageTemplate(id="content", frames=[frame], onPage=content_page,
                     onPageEnd=content_page_end),
    ])
    return doc, [NextPageTemplate("content"), PageBreak()]


def P(text, style="body"):
    return Paragraph(text, S[style])


def two_col(rows, left_w=150, label_color="#14504C"):
    """A label/description table, used for habit lists and comparisons."""
    data = [[Paragraph(f"<font face='Display-Bold' size='9.4' "
                       f"color='{label_color}'>{t}</font>", S["tight"]),
             Paragraph(b, S["tight"])] for t, b in rows]
    tb = Table(data, colWidths=[left_w, CW - left_w])
    tb.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, RULE)]))
    return tb


def spiral(c, cx=None, cy=300, r=86, turns=3):
    """Default cover motif: concentric arcs with one picked out in amber."""
    import math
    cx = cx if cx is not None else PAGE_W / 2 + 30
    c.setStrokeColor(colors.HexColor("#22665F"))
    c.setLineWidth(1.4)
    for i in range(turns):
        rr = r - i * 26
        p = c.beginPath()
        for s in range(61):
            a = math.radians(-40 + 310 * s / 60)
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


def publish(build_fn, filename, lab_folder):
    """Build once into pdfs/, then copy into the lab folder.

    Two copies on purpose: pdfs/ is the set you send to participants, and the
    lab folder is where someone working on that lab will look. This keeps them
    in step so a rebuild never leaves a stale one behind.
    """
    import shutil
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    collected = repo / "pdfs" / filename
    collected.parent.mkdir(exist_ok=True)

    build_fn(str(collected))

    beside_lab = repo / "labs" / lab_folder / filename
    if beside_lab.parent.exists():
        shutil.copy2(collected, beside_lab)
        print("  also copied to labs/" + lab_folder + "/")
    else:
        print("  (no labs/" + lab_folder + "/ - left only in pdfs/)")
