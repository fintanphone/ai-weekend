"""Diagrams for Agentic-AI-Weekend-Guide.pdf.

Kept apart from build_guide.py so the content of the guide stays readable as
content. Each class is a Diagram with a fixed height; the height is reserved in
the flow, so if one overflows it collides with the caption underneath rather
than reflowing. Check the rendered pages after changing any of these.
"""

import math

from pdfkit import (
    AMBER, AMBER_LT, CW, GREEN, INK, PETROL, PETROL_LT, RED, RULE, SLATE,
    WASH, WASH_WARM, Diagram, arrow, colors, rbox, txt,
)

PALE = colors.HexColor("#C9D8D5")


# ------------------------------------------------------------------ orientation
class Ladder(Diagram):
    """The nine rungs, each one step up from the last."""

    RUNGS = [
        ("Prompt", "text in, text out"),
        ("Structured output", "now it's a function"),
        ("Tool call", "it can affect the world"),
        ("The loop", "this is an agent"),
        ("Skills", "context on demand"),
        ("MCP", "tools as a protocol"),
        ("Agentic work", "turned loose on a repo"),
        ("Evals & guardrails", "how you know it works"),
        ("Harness", "when it runs unattended"),
    ]
    HIGHLIGHT = 3  # "The loop"

    def __init__(self):
        super().__init__(height=330)

    def paint(self, c, w, h):
        bw, bh = 196, 30
        step_x = (w - bw) / (len(self.RUNGS) - 1)
        step_y = (h - bh - 14) / (len(self.RUNGS) - 1)
        for i, (name, sub) in enumerate(self.RUNGS):
            x = i * step_x
            y = i * step_y
            on = i == self.HIGHLIGHT
            rbox(c, x, y, bw, bh, fill=WASH_WARM if on else WASH,
                 stroke=AMBER if on else PETROL_LT, r=4, lw=1.1 if on else 0.8)
            txt(c, x + 10, y + bh - 13, name, "Display", 9.2,
                AMBER if on else PETROL)
            txt(c, x + 10, y + 7, sub, "Body", 7.4, SLATE)
            if i:
                px, py = (i - 1) * step_x, (i - 1) * step_y
                c.saveState()
                c.setStrokeColor(PALE)
                c.setDash(1.6, 2.2)
                c.setLineWidth(0.9)
                c.line(px + bw * 0.42, py + bh, px + bw * 0.42, y + bh / 2)
                c.line(px + bw * 0.42, y + bh / 2, x, y + bh / 2)
                c.restoreState()
        txt(c, 0, -11, "each rung is one small step up from the last",
            "Body-Italic", 7.6, SLATE)


# ------------------------------------------------------------------ 00
class StatelessTurns(Diagram):
    """Four turns, each resending everything before it."""

    def __init__(self):
        super().__init__(height=150)

    def paint(self, c, w, h):
        n = 4
        gap = 26
        bw = (w - gap * (n - 1)) / n
        bh = 96
        y = 18
        for t in range(n):
            x = t * (bw + gap)
            rbox(c, x, y, bw, bh, fill=None, stroke=RULE, r=3, lw=0.8)
            txt(c, x + bw / 2, y + bh + 10, f"Turn {t + 1}", "Display", 8.4,
                PETROL, "c")
            for m in range(t + 1):
                my = y + bh - 16 - m * 18
                newest = m == t
                rbox(c, x + 8, my, bw - 16, 14,
                     fill=AMBER_LT if newest else colors.HexColor("#E9EDEB"),
                     stroke=None, r=2)
                txt(c, x + bw / 2, my + 4, f"msg {m + 1}", "Body", 7,
                    AMBER if newest else SLATE, "c")
            txt(c, x + bw / 2, y - 11, f"{t + 1} messages sent", "Mono", 6.8,
                SLATE, "c")
            if t < n - 1:
                arrow(c, x + bw + 5, y + bh / 2, x + bw + gap - 5, y + bh / 2,
                      color=PALE, lw=1.0)


class ContextBudget(Diagram):
    """One bar, segmented by what competes for the window."""

    SEGMENTS = [
        ("System prompt", 0.11, PETROL),
        ("Tool schemas", 0.09, PETROL_LT),
        ("Conversation history", 0.24, colors.HexColor("#7FB3AD")),
        ("Retrieved documents", 0.21, AMBER_LT),
        ("Tool results", 0.20, AMBER),
        ("Headroom", 0.15, colors.HexColor("#E9EDEB")),
    ]

    def __init__(self):
        super().__init__(height=74)

    def paint(self, c, w, h):
        bh = 26
        y = h - bh - 2
        x = 0
        for _, frac, col in self.SEGMENTS:
            seg = w * frac
            c.setFillColor(col)
            c.rect(x, y, seg, bh, stroke=0, fill=1)
            x += seg
        # legend, two rows of three
        for i, (label, _, col) in enumerate(self.SEGMENTS):
            col_i, row_i = i % 3, i // 3
            lx = col_i * (w / 3)
            ly = y - 16 - row_i * 13
            c.setFillColor(col)
            c.rect(lx, ly, 7, 7, stroke=0, fill=1)
            txt(c, lx + 11, ly + 1, label, "Body", 7.4, INK)


# ------------------------------------------------------------------ 01
class VramBars(Diagram):
    """What fits on a 16 GB card, weights plus KV cache."""

    ROWS = [
        ("3B  ·  4-bit", 0.10, 0.045, "fast, unreliable at tool use", False),
        ("8B  ·  4-bit", 0.25, 0.075, "the workhorse", False),
        ("14B ·  4-bit", 0.44, 0.105, "pushes a 16 GB card", False),
        ("8B  ·  16-bit", 1.00, 0.0, "does not fit", True),
    ]

    def __init__(self):
        super().__init__(height=190)

    def paint(self, c, w, h):
        lab_w = 96
        track = w - lab_w - 120
        limit_x = lab_w + track
        bh = 20
        for i, (label, wt, kv, note, spill) in enumerate(self.ROWS):
            y = h - 26 - i * 42
            txt(c, lab_w - 10, y + 6, label, "Mono", 8, INK, "r")
            if spill:
                c.setFillColor(colors.HexColor("#9AA5A2"))
                c.rect(lab_w, y, track, bh, stroke=0, fill=1)
                rbox(c, limit_x, y, 34, bh, fill=RED, stroke=None, r=2)
                txt(c, limit_x + 17, y + 6, "spill", "Display-Bold", 7.6,
                    colors.white, "c")
                txt(c, limit_x + 42, y + 6, note, "Body-Italic", 7.6, RED)
            else:
                c.setFillColor(PETROL)
                c.rect(lab_w, y, track * wt, bh, stroke=0, fill=1)
                c.setFillColor(AMBER_LT)
                c.rect(lab_w + track * wt, y, track * kv, bh, stroke=0, fill=1)
                c.setStrokeColor(RULE)
                c.setLineWidth(0.6)
                c.line(lab_w, y - 8, lab_w + track, y - 8)
                txt(c, limit_x + 10, y + 6, note, "Body-Italic", 7.6, SLATE)
        # the 16 GB ceiling
        c.saveState()
        c.setStrokeColor(AMBER)
        c.setDash(2.5, 2.5)
        c.setLineWidth(1.2)
        c.line(limit_x, 14, limit_x, h - 8)
        c.restoreState()
        txt(c, limit_x + 2, h - 6, "16 GB", "Display-Bold", 8, AMBER)
        # key
        c.setFillColor(PETROL)
        c.rect(lab_w, 0, 8, 8, stroke=0, fill=1)
        txt(c, lab_w + 12, 1, "model weights", "Body", 7.6, INK)
        c.setFillColor(AMBER_LT)
        c.rect(lab_w + 108, 0, 8, 8, stroke=0, fill=1)
        txt(c, lab_w + 120, 1, "KV cache — grows with context", "Body", 7.6, INK)


# ------------------------------------------------------------------ 02
class TwoContracts(Diagram):
    """Method A and method B as two pipelines with their end states."""

    def __init__(self):
        super().__init__(height=235)

    def _row(self, c, w, y, label, heading, steps, end, end_col, warm):
        txt(c, 0, y + 74, label, "Display-Bold", 9, AMBER if warm else PETROL)
        txt(c, 22, y + 74, heading, "Display", 9.4, INK)
        # widths derive from the frame, so the row can never run past the margin
        endw, gap = 88, 30
        bw = (w - endw - gap * len(steps)) / len(steps)
        for i, (top, bottom) in enumerate(steps):
            x = i * (bw + gap)
            rbox(c, x, y, bw, 46, fill=WASH_WARM if warm else WASH,
                 stroke=AMBER_LT if warm else PETROL_LT, r=4, lw=0.9)
            txt(c, x + bw / 2, y + 28, top, "Display", 9, AMBER if warm else PETROL, "c")
            txt(c, x + bw / 2, y + 12, bottom, "Body-Italic", 7.6, SLATE, "c")
            arrow(c, x + bw + 6, y + 23, x + bw + gap - 6, y + 23,
                  color=AMBER if warm else PETROL, lw=1.2)
        ex = len(steps) * (bw + gap)
        rbox(c, ex, y, endw, 46, fill=end_col, stroke=None, r=4)
        txt(c, ex + endw / 2, y + 17, end, "Display-Bold", 13, colors.white, "c")

    def paint(self, c, w, h):
        self._row(c, w, h - 105, "A", "Ask for JSON in the prompt",
                  [("prompt", "“return JSON”"), ("free text", "hopefully JSON"),
                   ("json.loads", "fingers crossed")], "~85%", RED, True)
        c.saveState()
        c.setStrokeColor(PALE)
        c.setDash(2, 3)
        c.setLineWidth(0.8)
        c.line(0, h - 123, w, h - 123)
        c.restoreState()
        self._row(c, w, h - 211, "B", "Declare a schema, force the call",
                  [("prompt", "plus tool schema"), ("tool_use", "validated by API"),
                   ("dict", "guaranteed shape")], "~100%", PETROL, False)


# ------------------------------------------------------------------ 03
class LoopCircle(Diagram):
    """The loop drawn as an actual circle, with the decision on the right."""

    def __init__(self):
        super().__init__(height=310)

    def paint(self, c, w, h):
        # Geometry is derived, not hardcoded: the left-hand node must start at
        # x=0 and the decision box must clear the answer box on the right.
        nw, nh = 160, 44
        r = 94
        dw, dh = 120, 48
        aw, ah = 100, 44
        cx, cy = nw / 2 + r, h / 2
        c.saveState()
        c.setStrokeColor(PETROL_LT)
        c.setLineWidth(1.4)
        p = c.beginPath()
        for s in range(97):
            a = math.radians(360 * s / 96)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            p.moveTo(x, y) if s == 0 else p.lineTo(x, y)
        c.drawPath(p)
        c.restoreState()

        nodes = [
            (cx, cy + r, "Call the model", "with the full history", PETROL, colors.white),
            (cx, cy - r, "YOUR code runs it", "never the model", WASH, INK),
            (cx - r, cy, "Append the result", "as a new message", WASH, INK),
        ]
        for nx, ny, top, bottom, fill, fg in nodes:
            rbox(c, nx - nw / 2, ny - nh / 2, nw, nh, fill=fill,
                 stroke=PETROL if fill is WASH else None, r=5, lw=0.8)
            txt(c, nx, ny + 6, top, "Display", 9.6, fg, "c")
            txt(c, nx, ny - 10, bottom, "Body-Italic", 7.6,
                colors.HexColor("#A9C6C2") if fg is colors.white else SLATE, "c")

        # the decision, sitting on the circle's right
        dx, dy = cx + r - dw / 2, cy - dh / 2
        rbox(c, dx, dy, dw, dh, fill=WASH_WARM, stroke=AMBER, r=5, lw=1.2)
        txt(c, dx + dw / 2, dy + 28, "asked for a tool?", "Display-Bold", 9.6, AMBER, "c")
        txt(c, dx + dw / 2, dy + 12, "stop_reason", "Mono", 8, SLATE, "c")

        txt(c, dx - 16, dy - 26, "yes", "Display-Bold", 8.6, AMBER, "c")

        ax, ay = w - aw, cy - ah / 2
        arrow(c, dx + dw + 8, cy, ax - 8, cy, color=INK, lw=1.2)
        txt(c, (dx + dw + ax) / 2, cy + 7, "no", "Display-Bold", 8.6, INK, "c")
        rbox(c, ax, ay, aw, ah, fill=PETROL, stroke=None, r=5)
        txt(c, ax + aw / 2, ay + 25, "Answer", "Display-Bold", 11, colors.white, "c")
        txt(c, ax + aw / 2, ay + 10, "the loop exits", "Body-Italic", 7.8,
            colors.HexColor("#A9C6C2"), "c")


# ------------------------------------------------------------------ 04
class RagStages(Diagram):
    """Four stages, and the three question shapes that defeat stage three."""

    FAILURES = [
        ("Multi-hop", "The answer needs two facts\nfrom two documents. Neither\nchunk scores well alone."),
        ("Negation", "“can work remotely” and\n“cannot work remotely” sit\nright next to each other."),
        ("Aggregation", "Top-k structurally cannot\nanswer a question about\nthe whole corpus."),
    ]

    def __init__(self):
        super().__init__(height=250)

    def paint(self, c, w, h):
        stages = [("Chunk", "split the docs"), ("Embed", "text → vectors"),
                  ("Retrieve", "cosine similarity"), ("Generate", "stuff into prompt")]
        gap = 22
        bw = (w - gap * 3) / 4
        y = h - 58
        rx = None
        for i, (top, bottom) in enumerate(stages):
            x = i * (bw + gap)
            on = i == 2
            rbox(c, x, y, bw, 52, fill=WASH_WARM if on else WASH,
                 stroke=AMBER if on else PETROL_LT, r=4, lw=1.2 if on else 0.8)
            txt(c, x + bw / 2, y + 31, top, "Display", 10.4,
                AMBER if on else PETROL, "c")
            txt(c, x + bw / 2, y + 14, bottom, "Body-Italic", 7.8, SLATE, "c")
            if on:
                rx = x + bw / 2
            if i < 3:
                arrow(c, x + bw + 4, y + 26, x + bw + gap - 4, y + 26,
                      color=SLATE, lw=1.0)

        fy = h - 212
        fw = (w - 24 * 2) / 3
        for i, (title, body) in enumerate(self.FAILURES):
            x = i * (fw + 24)
            rbox(c, x, fy, fw, 118, fill=WASH_WARM, stroke=AMBER, r=4, lw=0.9)
            txt(c, x + 14, fy + 96, title, "Display-Bold", 9.6, AMBER)
            for j, line in enumerate(body.split("\n")):
                txt(c, x + 14, fy + 74 - j * 13, line, "Body", 8, INK)
            arrow(c, rx, y - 6, x + fw / 2, fy + 124, color=AMBER, lw=0.9,
                  dash=(2, 2.4))


# ------------------------------------------------------------------ 05
class ThreeLevels(Diagram):
    """Progressive disclosure: each band wider than the one above it."""

    LEVELS = [
        ("Level 1", "Name + description", "always in context, for every skill",
         "~50 tokens", 0.42, PETROL, WASH),
        ("Level 2", "The full SKILL.md body", "loads when the model judges it relevant",
         "~1,500 tokens", 0.62, PETROL_LT, WASH),
        ("Level 3", "Scripts, templates, references", "loads only if the instructions call for it",
         "as needed", 0.82, AMBER, WASH_WARM),
    ]

    def __init__(self):
        super().__init__(height=235)

    def paint(self, c, w, h):
        bh = 58
        for i, (lvl, title, sub, cost, frac, col, fill) in enumerate(self.LEVELS):
            y = h - bh - i * 84
            bw = w * frac
            rbox(c, 0, y, bw, bh, fill=fill, stroke=col, r=4, lw=1.2)
            txt(c, 14, y + 36, lvl, "Display-Bold", 9.2, col)
            txt(c, 66, y + 36, title, "Display", 10.4, INK)
            txt(c, 14, y + 15, sub, "Body-Italic", 7.8, SLATE)
            txt(c, bw + 14, y + bh / 2 - 3, cost, "Mono", 8, SLATE)
            if i < 2:
                arrow(c, 38, y - 6, 38, y - 24, color=SLATE, lw=0.9)
                txt(c, 46, y - 20, "only if the description matches the task",
                    "Body-Italic", 7.2, SLATE)


# ------------------------------------------------------------------ 06
class McpFabric(Diagram):
    """Clients above, one protocol band, servers below."""

    def __init__(self):
        super().__init__(height=270)

    def paint(self, c, w, h):
        clients = [("Claude Code", "terminal"), ("Claude Desktop", "chat"),
                   ("Your own agent", "Lab 3's loop")]
        servers = [("freight", "the one you write"), ("filesystem", "off the shelf"),
                   ("anything else", "the ecosystem")]
        gap = 26
        bw = (w - gap * 2 - 96) / 3
        off = 48

        cy = h - 52
        for i, (top, bottom) in enumerate(clients):
            x = off + i * (bw + gap)
            rbox(c, x, cy, bw, 46, fill=None, stroke=PETROL, r=4, lw=1.0)
            txt(c, x + bw / 2, cy + 27, top, "Display", 9.6, PETROL, "c")
            txt(c, x + bw / 2, cy + 12, bottom, "Body-Italic", 7.6, SLATE, "c")

        band_y = h - 150
        rbox(c, 0, band_y, w, 40, fill=PETROL, stroke=None, r=4)
        txt(c, w / 2 - 74, band_y + 15, "MCP", "Display-Bold", 11, colors.white)
        txt(c, w / 2 - 40, band_y + 15, "·", "Display", 11,
            colors.HexColor("#8FBDB8"))
        txt(c, w / 2 - 26, band_y + 15, "one protocol, standard transport",
            "Display", 11, colors.white)

        sy = h - 254
        for i, (top, bottom) in enumerate(servers):
            x = off + i * (bw + gap)
            rbox(c, x, sy, bw, 46, fill=WASH_WARM, stroke=AMBER, r=4, lw=1.0)
            txt(c, x + bw / 2, sy + 27, top, "Display", 9.6, AMBER, "c")
            txt(c, x + bw / 2, sy + 12, bottom, "Body-Italic", 7.6, SLATE, "c")
            arrow(c, w / 2 + (i - 1) * 90, band_y - 6, x + bw / 2, sy + 52,
                  color=AMBER, lw=1.0)

        for i in range(3):
            x = off + i * (bw + gap) + bw / 2
            arrow(c, x, cy - 6, w / 2 + (i - 1) * 90, band_y + 46,
                  color=PETROL_LT, lw=1.0)

        txt(c, 0, sy - 18, "Clients above, servers below. Neither knows anything "
            "about the other.", "Body-Italic", 7.8, SLATE)


# ------------------------------------------------------------------ 07
class CodingRhythm(Diagram):
    """Five steps, with step three picked out, over the review gate."""

    STEPS = [
        ("Read", "builds a picture of\nthe codebase"),
        ("Propose", "claims a bug\nexists"),
        ("Prove", "writes a FAILING\ntest first"),
        ("Fix", "narrow, scoped\nchange"),
        ("Verify", "test passes, you\nread the diff"),
    ]

    def __init__(self):
        super().__init__(height=190)

    def paint(self, c, w, h):
        gap = 14
        bw = (w - gap * 4) / 5
        y = h - 108
        for i, (name, sub) in enumerate(self.STEPS):
            x = i * (bw + gap)
            on = i == 2
            rbox(c, x, y, bw, 100, fill=WASH_WARM if on else WASH,
                 stroke=AMBER if on else RULE, r=4, lw=1.2 if on else 0.8)
            c.setFillColor(AMBER if on else PETROL)
            c.circle(x + bw / 2, y + 78, 10, stroke=0, fill=1)
            txt(c, x + bw / 2, y + 75, str(i + 1), "Display-Bold", 9,
                colors.white, "c")
            txt(c, x + bw / 2, y + 48, name, "Display", 10.4,
                AMBER if on else PETROL, "c")
            for j, line in enumerate(sub.split("\n")):
                txt(c, x + bw / 2, y + 30 - j * 11, line, "Body", 7.6, SLATE, "c")
            if i < 4:
                arrow(c, x + bw + 2, y + 50, x + bw + gap - 2, y + 50,
                      color=SLATE, lw=1.0, head=3.6)

        gy = h - 182
        rbox(c, 0, gy, w, 58, fill=WASH_WARM, stroke=AMBER, r=4, lw=1.1)
        txt(c, 16, gy + 36, "The human review gate", "Display-Bold", 10, AMBER)
        txt(c, 16, gy + 16, "Work on a branch  ·  commit before you start  ·  "
            "read every line of the diff  ·  git checkout . must always be free",
            "Body", 8, INK)


# ------------------------------------------------------------------ 08
class EvalLoop(Diagram):
    """Cases to agent to score to a number, with the change-one-thing return."""

    def __init__(self):
        super().__init__(height=150)

    def paint(self, c, w, h):
        boxes = [("12 cases", "task + expected", WASH, PETROL, INK),
                 ("The agent", "one variant", PETROL, None, colors.white),
                 ("Score", "substring, then judge", WASH, PETROL, INK)]
        # widths derive from the frame, so the row can never run past the margin
        gap, endw = 26, 118
        bw = (w - endw - gap * 3) / 3
        y = h - 70
        for i, (top, bottom, fill, stroke, fg) in enumerate(boxes):
            x = i * (bw + gap)
            rbox(c, x, y, bw, 52, fill=fill, stroke=stroke, r=4, lw=0.9)
            txt(c, x + bw / 2, y + 30, top, "Display", 10, fg, "c")
            txt(c, x + bw / 2, y + 14, bottom, "Body-Italic", 7.6,
                colors.HexColor("#A9C6C2") if fg is colors.white else SLATE, "c")
            arrow(c, x + bw + 6, y + 26, x + bw + gap - 6, y + 26,
                  color=PETROL if i == 0 else AMBER, lw=1.2)
        nx = 3 * (bw + gap)
        rbox(c, nx, y, endw, 52, fill=AMBER, stroke=None, r=4)
        txt(c, nx + endw / 2, y + 18, "9 / 12", "Display-Bold", 17, colors.white, "c")
        txt(c, nx + endw / 2, y - 14, "the number", "Body-Italic", 7.8, AMBER, "c")

        # the feedback edge, returning to "The agent"
        back_x = bw + gap + bw / 2
        c.saveState()
        c.setStrokeColor(AMBER)
        c.setDash(3, 2.6)
        c.setLineWidth(1.0)
        c.line(nx + endw / 2, y - 26, nx + endw / 2, y - 42)
        c.line(nx + endw / 2, y - 42, back_x, y - 42)
        c.restoreState()
        arrow(c, back_x, y - 42, back_x, y - 4, color=AMBER, lw=1.0)
        txt(c, (nx + endw / 2 + back_x) / 2, y - 39,
            "change one thing, run it again", "Body-Italic", 7.6, AMBER, "c")


# ------------------------------------------------------------------ 09
class HarnessRing(Diagram):
    """The loop in the middle; the five concerns wrapped around it."""

    CONCERNS = [
        ("Registry", "schema and function,\nkept in step"),
        ("Observability", "what ran, in what order,\nand what it cost"),
        ("Budget", "checked BEFORE the call,\nnot after"),
        ("Reliability", "one blip retries instead\nof killing the run"),
        ("Policy", "allow / ask / deny,\nas data not an if"),
    ]

    def __init__(self):
        super().__init__(height=280)

    def paint(self, c, w, h):
        # the loop, small and central, because it is the small part
        lw_, lh = 150, 54
        lx, ly = (w - lw_) / 2, h - 96
        rbox(c, lx, ly, lw_, lh, fill=PETROL, stroke=None, r=5)
        txt(c, lx + lw_ / 2, ly + 31, "Lab 3's loop", "Display-Bold", 10.6,
            colors.white, "c")
        txt(c, lx + lw_ / 2, ly + 14, "~20 lines, unchanged", "Body-Italic", 7.8,
            colors.HexColor("#A9C6C2"), "c")

        # three above-ish, two below: a ring without the geometry fuss
        top_y = h - 34
        bw, bh = 150, 46
        gap = (w - bw * 3) / 2
        for i in range(3):
            name, sub = self.CONCERNS[i]
            x = i * (bw + gap)
            rbox(c, x, top_y, bw, bh, fill=WASH, stroke=PETROL_LT, r=4, lw=0.9)
            txt(c, x + 12, top_y + 29, name, "Display-Bold", 9.4, PETROL)
            for j, line in enumerate(sub.split("\n")):
                txt(c, x + 12, top_y + 16 - j * 10, line, "Body", 7.2, SLATE)
            arrow(c, x + bw / 2, top_y - 4, lx + lw_ / 2 + (i - 1) * 48,
                  ly + lh + 4, color=PETROL_LT, lw=0.9, dash=(2, 2.4))

        bot_y = h - 168
        gap2 = w - bw * 2
        for i in range(2):
            name, sub = self.CONCERNS[3 + i]
            x = i * (bw + gap2)
            rbox(c, x, bot_y, bw, bh, fill=WASH_WARM, stroke=AMBER, r=4, lw=0.9)
            txt(c, x + 12, bot_y + 29, name, "Display-Bold", 9.4, AMBER)
            for j, line in enumerate(sub.split("\n")):
                txt(c, x + 12, bot_y + 16 - j * 10, line, "Body", 7.2, SLATE)
            arrow(c, x + bw / 2, bot_y + bh + 4, lx + lw_ / 2 + (i * 2 - 1) * 42,
                  ly - 4, color=AMBER, lw=0.9, dash=(2, 2.4))

        # the threshold strip
        ty = h - 258
        rbox(c, 0, ty, w, 56, fill=None, stroke=RULE, r=4, lw=0.8)
        txt(c, 16, ty + 36, "You need one the moment any of these is true",
            "Display-Bold", 9.2, INK)
        txt(c, 16, ty + 16, "it runs unattended  ·  it runs more than once  ·  "
            "somebody else runs it  ·  it costs real money  ·  "
            "it can do something you'd regret", "Body", 7.8, SLATE)


# ------------------------------------------------------------------ variants
def variants_table():
    """The three-prompt score comparison under the eval diagram."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Table, TableStyle
    from pdfkit import S

    rows = [("baseline", "a bare instruction", "6 / 12", "#6E7B78"),
            ("careful", "+ step by step, use the tools", "9 / 12", "#6E7B78"),
            ("grounded", "+ never invent a figure you cannot find", "11 / 12", "#B85C1E")]
    head = ParagraphStyle("vh", fontName="Display-Bold", fontSize=7.6,
                          leading=11, textColor=SLATE)
    data = [[Paragraph("SAME CASES, THREE PROMPTS", head), "", ""]]
    for name, desc, score, col in rows:
        data.append([
            Paragraph(f"<font face='Mono' size='8' color='{col}'>{name}</font>",
                      S["tight"]),
            Paragraph(f"<font size='8.6'>{desc}</font>", S["tight"]),
            Paragraph(f"<para align='right'><font face='Display-Bold' size='8.6' "
                      f"color='{col}'>{score}</font></para>", S["tight"]),
        ])
    t = Table(data, colWidths=[CW * 0.20, CW * 0.60, CW * 0.20])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WASH),
        ("SPAN", (0, 0), (-1, 0)),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
    ]))
    return t


def staircase_motif(c):
    """Cover art: nine rungs climbing, with the loop picked out."""
    from pdfkit import PAGE_W
    bw, bh = 212, 30
    x0, y0 = PAGE_W - 120 - bw, 150
    for i in range(9):
        x = x0 - i * 26
        y = y0 + i * 26
        on = i == 4
        c.saveState()
        c.setLineWidth(1.6 if on else 1.0)
        c.setStrokeColor(AMBER if on else colors.HexColor("#22665F"))
        c.roundRect(x, y, bw, bh, 4, stroke=1, fill=0)
        c.restoreState()
