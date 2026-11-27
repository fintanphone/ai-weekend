#!/usr/bin/env python3
"""The weekend's closing slide: hosted or local?

    python build_closing_slide.py

One landscape A4 page. It is the bookend to Lab1-Context-KV-Weights.pdf: that
one shows what a local model costs you in VRAM, this one shows what you get
back — and what you give up.

The whole slide rests on one measured result, so the numbers live in MEASURED
below with their provenance attached. If you re-run either side, edit that
block and rebuild; do not retype a figure into the drawing code.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

from pdfkit import (
    AMBER, AMBER_LT, INK, PETROL, PETROL_LT, RED, RULE, SLATE, WASH, WASH_WARM,
    rbox, txt,
)

OUT = "Closing-Hosted-or-Local.pdf"
PW, PH = landscape(A4)
M = 18 * mm
CW = PW - 2 * M

# ------------------------------------------------------------------ the data
# Lab 2, tier 2, schema 'lax', 3 trials. "fields right" out of tickets x
# trials x 4 fields.
#
# NOTE the denominators differ. The hosted run used the current ten tier-2
# tickets. The local run was made when there were six, before the four brand
# tickets were added. The inversion held on both, but re-run the local side on
# all ten before anyone asks.
MEASURED = {
    "hosted": dict(
        name="Claude Haiku 5.5", where="hosted API",
        prompt=(120, 120), schema=(117, 120), tickets=10,
    ),
    "local": dict(
        name="Qwen3.6 27B  IQ3_M", where="one GPU, llama-server",
        prompt=(70, 72), schema=(72, 72), tickets=6,
    ),
}


def pct(pair):
    got, total = pair
    return 100.0 * got / total


def title(c, big, small):
    txt(c, M, PH - M - 16, big, "Display-Bold", 24, INK)
    txt(c, M, PH - M - 35, small, "Body-Italic", 11.5, PETROL)


def inversion_grid(c, top):
    """The 2x2. The two filled cells land on a diagonal — that IS the point."""
    labw, gap = 158, 18
    colw = (CW - labw - gap) / 2
    hh, rh = 28, 50
    cols = [M + labw + gap * 0 + 0, M + labw + colw + gap]
    cols = [M + labw, M + labw + colw + gap]
    keys = ["hosted", "local"]

    # column headers
    for i, k in enumerate(keys):
        d = MEASURED[k]
        x = cols[i]
        txt(c, x + colw / 2, top - 15, d["name"], "Display-Bold", 11.5, INK, "c")
        txt(c, x + colw / 2, top - 28, d["where"], "Body-Italic", 8.8, SLATE, "c")

    rows = [("A:  prompt-based", "prompt"), ("B:  tool schema", "schema")]
    for r, (label, field) in enumerate(rows):
        y = top - hh - (r + 1) * rh
        txt(c, M, y + rh / 2 - 4, label, "Display", 11, INK)

        best = max(keys, key=lambda k: pct(MEASURED[k][field]))
        for i, k in enumerate(keys):
            d = MEASURED[k]
            x, p = cols[i], pct(d[field])
            win = k == best
            rbox(c, x, y, colw, rh - 6,
                 fill=PETROL if win else WASH,
                 stroke=PETROL if win else RULE, r=4, lw=1.1)
            fg = colors.white if win else SLATE
            txt(c, x + 18, y + rh / 2 - 9, f"{p:.0f}%", "Display-Bold", 26, fg)
            got, tot = d[field]
            txt(c, x + colw - 18, y + rh / 2 - 2, f"{got}/{tot} fields",
                "Mono", 8.6, fg, "r")
            txt(c, x + colw - 18, y + rh / 2 - 13,
                f"{d['tickets']} tickets x 3 trials", "Body-Italic", 7.8, fg, "r")
            if win:
                txt(c, x + 18, y + rh / 2 + 12, "WINS", "Display-Bold", 7.6,
                    AMBER_LT)

    bottom = top - hh - 2 * rh
    txt(c, M, bottom - 18,
        "The two filled cells sit on a diagonal. Free text wins on the hosted "
        "model; the schema wins on the local one. Opposite conclusions, same task.",
        "Body-Bold", 10.2, INK)
    return bottom - 24


def build(path):
    c = pdfcanvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Hosted or local — what the weekend measured")
    c.setFillColor(colors.white)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    title(c, "Hosted or local?",
          "What the weekend actually measured — and why it is not the answer "
          "most people expect.")

    y = inversion_grid(c, PH - M - 52)

    # ------------------------------------------------ the mechanism
    bh = 44
    rbox(c, M, y - bh, CW, bh, fill=WASH_WARM, stroke=AMBER, r=5, lw=1.1)
    txt(c, M + 16, y - 19, "WHY", "Display-Bold", 8.4, AMBER)
    txt(c, M + 52, y - 19,
        "A constrained path forces attention onto every field. The weaker model "
        "needs that; the stronger one does not, and pays a little for it.",
        "Body-Bold", 10.4, INK)
    txt(c, M + 52, y - 34,
        "Every local miss was free text dropping a reference that was present. "
        "The hosted miss was the schema offering an escape hatch, and the model taking it.",
        "Body", 9.4, SLATE)
    y -= bh + 16

    # ------------------------------------------------ what each one gives you
    gap = 20
    colw = (CW - gap) / 2
    panels = [
        (PETROL, "Only local gives you", [
            ("Constrained decoding", "the schema becomes a sampling grammar, so bad "
             "tokens are not available to pick: impossibility, not validation"),
            ("A frozen artefact", "a GGUF behaves the same next March. This lab's premise "
             "expired because hosted models improved underneath it"),
            ("No metering, no rate limits", "and your data never leaves the building"),
        ]),
        (AMBER, "Only hosted gives you", [
            ("Capability that does not fit", "no VRAM arithmetic, no quantising a "
             "27B to IQ3_M to squeeze it on"),
            ("Nothing to operate", "and nothing to pay when idle — the whole "
             "weekend for three people is pennies"),
            ("A moving target", "it improves without asking you — a benefit and a "
             "reproducibility problem at the same time"),
        ]),
    ]
    ph = 144
    for i, (col, head, items) in enumerate(panels):
        x = M + i * (colw + gap)
        rbox(c, x, y - ph, colw, ph, fill=None, stroke=col, r=5, lw=1.2)
        c.setFillColor(col)
        c.rect(x, y - 4, colw, 4, stroke=0, fill=1)
        txt(c, x + 16, y - 24, head, "Display-Bold", 11, col)
        yy = y - 44
        for lead, rest in items:
            txt(c, x + 16, yy, lead, "Display-Bold", 9.2, INK)
            # wrap the explanation to the panel width
            words, line = rest.split(), ""
            lines = []
            for w in words:
                trial = (line + " " + w).strip()
                if c.stringWidth(trial, "Body", 8.6) > colw - 34:
                    lines.append(line)
                    line = w
                else:
                    line = trial
            lines.append(line)
            yy -= 11
            for ln in lines[:2]:
                txt(c, x + 16, yy, ln, "Body", 8.6, SLATE)
                yy -= 10.4
            yy -= 4
    y -= ph + 14

    # ------------------------------------------------ the takeaway
    rbox(c, M, y - 42, CW, 42, fill=PETROL, stroke=None, r=5)
    txt(c, M + 20, y - 20,
        "Scaffolding helps whoever is struggling and slightly hinders whoever is not.",
        "Display-Bold", 13.5, colors.white)
    txt(c, M + 20, y - 36,
        "So the answer is per workload, never per ideology — and a benchmark from "
        "one model is not a finding about a technique.",
        "Body", 10, AMBER_LT)
    y -= 42 + 10

    txt(c, M, y - 6,
        "Lab 2, tier 2, schema 'lax', 3 trials. The hosted run used the current "
        "ten tier-2 tickets; the local run was taken when there were six, before "
        "the four brand tickets.",
        "Body-Italic", 7.8, SLATE)
    txt(c, M, y - 16,
        "The inversion held on both, but re-run the local side on all ten before "
        "presenting these numbers as a matched pair.",
        "Body-Italic", 7.8, RED)

    c.showPage()
    c.save()


if __name__ == "__main__":
    import shutil
    from pathlib import Path

    for k, d in MEASURED.items():
        print(f"  {k:7} prompt {pct(d['prompt']):5.1f}%   schema {pct(d['schema']):5.1f}%"
              f"   ({d['tickets']} tickets)")

    repo = Path(__file__).resolve().parents[1]
    target = repo / "pdfs" / OUT
    target.parent.mkdir(exist_ok=True)
    build(str(target))
    print(f"\nbuilt {target}  ({target.stat().st_size/1024:.0f} KB)")
    beside = repo / "labs" / "lab02_structured_output" / OUT
    if beside.parent.exists():
        shutil.copy2(target, beside)
        print(f"  also copied to {beside.relative_to(repo)}")
