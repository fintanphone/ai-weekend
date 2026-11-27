#!/usr/bin/env python3
"""Lab 1 — weights, KV cache and context length, drawn to scale.

    python build_context_graphic.py

Two landscape A4 slides:

    1. the three things, and one short interaction to put numbers on them
    2. the same three things as bars on a 16 GiB card, to scale

The point of the picture is the ratio. For a dozen tokens of conversation the
cache is a hairline, the weights are most of the card, and the number you typed
after --ctx-size is bigger than both. People believe that much faster when they
can see the sliver.

Every figure is computed from MODEL below, so the drawing cannot drift from the
arithmetic. The bars are literally to scale: 1 GiB is a fixed number of points.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

from pdfkit import (
    AMBER, AMBER_LT, INK, PETROL, PETROL_LT, RED, RULE, SLATE,
    WASH, WASH_WARM, rbox, txt,
)

OUT = "Lab1-Context-KV-Weights.pdf"
PW, PH = landscape(A4)
M = 18 * mm
CW = PW - 2 * M
KiB, MiB, GiB = 1024, 1024 ** 2, 1024 ** 3

# ---------------------------------------------------------------- the model
# Llama 3.1 8B Instruct at Q4_K_M — the same model as the VRAM slides, so the
# two decks agree.
MODEL = dict(
    label="Llama 3.1 8B Instruct · Q4_K_M",
    params=8.0e9,
    bpw=4.8,          # Q4_K_M is mixed, not 4 bits
    layers=32,
    kv_heads=8,
    head_dim=128,
    kv_bytes=2,       # fp16 cache
    max_ctx=131072,
    card_gib=16,
)

# The one piece of arithmetic the whole picture rests on.
PER_TOK = 2 * MODEL["layers"] * MODEL["kv_heads"] * MODEL["head_dim"] * MODEL["kv_bytes"]
WEIGHTS = MODEL["params"] * MODEL["bpw"] / 8

# One short interaction. Token splits are schematic — a real tokeniser would
# cut them slightly differently, which does not change any of the sizes.
PROMPT = ["Explain", " the", " KV", " cache", " in", " one", " short", " para",
          "graph", "."]
N_REPLY = 42
N_TOK = len(PROMPT) + N_REPLY
USED = N_TOK * PER_TOK

RESERVED = MODEL["max_ctx"] * PER_TOK
SMALL_CTX = 8192
MID_CTX = 32768
CARD = MODEL["card_gib"] * GiB


def gib(n):
    return f"{n / GiB:.2f} GiB"


def title(c, big, small):
    txt(c, M, PH - M - 16, big, "Display-Bold", 23, INK)
    txt(c, M, PH - M - 34, small, "Body-Italic", 11.5, PETROL)


def chip(c, x, y, w, h, fill, stroke, label=None, size=6.2):
    rbox(c, x, y, w, h, fill=fill, stroke=stroke, r=1.8, lw=0.6)
    if label:
        txt(c, x + w / 2, y + h / 2 - 2.2, label.strip(), "Mono", size, INK, "c")


# ============================================================= slide 1
def slide1(c):
    title(c, "Weights, KV cache, context length",
          "Three different things, three different reasons they take up VRAM. "
          "Only one of them grows when you talk to the model.")

    top = PH - M - 62

    # ---------------------------------------------- band 1: the interaction
    bh = 128
    bw = CW * 0.56
    by = top - bh
    rbox(c, M, by, bw, bh, fill=WASH, stroke=RULE, r=5)
    txt(c, M + 16, by + 106, "ONE SHORT INTERACTION", "Display-Bold", 8.4, PETROL)
    # prompt and generated tokens alike — every one of them gets a slice
    txt(c, M + bw - 16, by + 106, f"{N_TOK} tokens in the cache",
        "Display-Bold", 9.4, INK, "r")

    # prompt tokens, big enough to read
    txt(c, M + 16, by + 88, "you type", "Body-Italic", 8.6, SLATE)
    cx, cw = M + 16, 35.5
    for tok in PROMPT:
        chip(c, cx, by + 68, cw, 15, WASH_WARM, PETROL_LT, tok)
        cx += cw + 2.5
    txt(c, M + 16, by + 56, f"{len(PROMPT)} tokens", "Display", 7.6, PETROL)

    # reply tokens, small, because there are more of them
    txt(c, M + 16, by + 40, "it writes back", "Body-Italic", 8.6, SLATE)
    cx = M + 16
    for _ in range(N_REPLY):
        chip(c, cx, by + 16, 6.0, 14, AMBER_LT, AMBER)
        cx += 7.2
    txt(c, cx + 8, by + 21, f"{N_REPLY} tokens", "Display", 7.6, AMBER)

    # ---------------------------------------------- band 1b: per-token cost
    ax = M + bw + 22
    aw = CW - bw - 22
    rbox(c, ax, by, aw, bh, fill=None, stroke=AMBER, r=5, lw=1.1)
    txt(c, ax + 16, by + bh - 22, "WHAT ONE TOKEN COSTS", "Display-Bold", 8.4, AMBER)

    rows = [("2", "keys and values"),
            (f"x {MODEL['layers']}", "layers"),
            (f"x {MODEL['kv_heads']}", "key/value heads"),
            (f"x {MODEL['head_dim']}", "head dimension"),
            (f"x {MODEL['kv_bytes']}", "bytes, fp16")]
    y = by + 90
    for a, b in rows:
        txt(c, ax + 20, y, a, "Mono", 9, INK)
        txt(c, ax + 62, y, b, "Body", 8.8, SLATE)
        y -= 12.5
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(ax + 20, y + 5, ax + aw - 20, y + 5)
    txt(c, ax + 20, y - 11, f"= {PER_TOK // KiB} KiB", "Display-Bold", 11.5, AMBER)
    txt(c, ax + aw - 20, y - 10, f"per token    x {N_TOK} = {USED / MiB:.1f} MiB",
        "Mono", 8.4, PETROL, "r")

    # ---------------------------------------------- band 2: the three things
    gap, n = 20, 3
    colw = (CW - gap * (n - 1)) / n
    ty = by - 24
    thh = 212
    cards = [
        (PETROL, "WEIGHTS", "what the model is",
         ["8.0B parameters at about 4.8 bits",
          "each. Loaded once at startup,",
          "identical for every request, and",
          "unchanged by anything you say."],
         gib(WEIGHTS), "fixed"),
        (AMBER, "KV CACHE", "what it remembers of this chat",
         [f"One {PER_TOK // KiB} KiB slice per token,",
          "appended as each token arrives —",
          "the ones you typed and the ones",
          "it generates while replying."],
         f"{USED / MiB:.1f} MiB", f"for our {N_TOK} tokens"),
        (RED, "CONTEXT LENGTH", "the ceiling you choose",
         ["How many slices you promise to",
          "have room for. A reservation, not",
          "a measurement: the server takes",
          "the VRAM whether you use it or not."],
         gib(RESERVED), f"reserved at {MODEL['max_ctx']:,}"),
    ]

    for i, (col, head, sub, body, big, note) in enumerate(cards):
        x = M + i * (colw + gap)
        rbox(c, x, ty - thh, colw, thh, fill=None, stroke=col, r=5, lw=1.2)
        c.setFillColor(col)
        c.rect(x, ty - 4, colw, 4, stroke=0, fill=1)

        txt(c, x + 16, ty - 24, head, "Display-Bold", 11, col)
        txt(c, x + 16, ty - 38, sub, "Body-Italic", 8.8, SLATE)

        # the little diagram: a solid block, a growing row, a big dashed box
        dy = ty - 100
        if i == 0:
            rbox(c, x + 16, dy, colw - 32, 46, fill=PETROL, stroke=None, r=3)
            txt(c, x + colw / 2, dy + 20, "one block, always the same size",
                "Display", 7, colors.white, "c")
        elif i == 1:
            for k in range(14):
                shade = AMBER if k < 8 else AMBER_LT
                chip(c, x + 16 + k * 11.5, dy + 14, 8.5, 20, shade, AMBER)
            txt(c, x + 16, dy + 3, "one slice per token, appended",
                "Display", 7, SLATE)
        else:
            rbox(c, x + 16, dy + 2, colw - 32, 44, fill=None, stroke=RED, r=3,
                 lw=1.1, dash=(2.5, 2.5))
            for k in range(8):
                chip(c, x + 20 + k * 11.5, dy + 14, 8.5, 20, AMBER_LT, AMBER)
            txt(c, x + 20 + 8 * 11.5 + 6, dy + 21, "...", "Display", 9, RED)
            txt(c, x + 16, dy - 10, "mostly empty, entirely paid for",
                "Display", 7, RED)

        yy = ty - 128
        for line in body:
            txt(c, x + 16, yy, line, "Body", 8.9, INK)
            yy -= 12.6

        txt(c, x + 16, ty - thh + 20, big, "Display-Bold", 15, col)
        txt(c, x + colw - 16, ty - thh + 21, note, "Body-Italic", 8.4, SLATE, "r")

    # ---------------------------------------------- footer
    fy = ty - thh - 26
    rbox(c, M, fy - 30, CW, 30, fill=WASH_WARM, stroke=AMBER_LT, r=4)
    txt(c, M + 16, fy - 19,
        f"The weights are {WEIGHTS / USED:,.0f}x the cache you actually used. "
        f"The reservation is {RESERVED / USED:,.0f}x it. "
        f"Only the middle one grows when you talk.",
        "Body-Bold", 10.4, INK)


# ============================================================= slide 2
def slide2(c):
    title(c, f"The same three things, to scale on a {MODEL['card_gib']} GiB card",
          "One bar per decision. The only one that changes whether the model "
          "loads at all is the number you typed after --ctx-size.")

    top = PH - M - 70
    lx, bx = M, M + 158
    span = PW - M - bx
    ceiling = 21 * GiB                      # drawing range
    ppg = span / (ceiling / GiB)            # points per GiB
    card_x = bx + (CARD / GiB) * ppg

    # Weights are always petrol and cache is always amber, exactly as on slide 1.
    # Red means one thing only: the part that does not fit on the card.
    bars = [
        ("weights only", WEIGHTS, gib(WEIGHTS),
         "loaded once, before anyone types anything"),
        (f"+ the {N_TOK} tokens above", WEIGHTS + USED,
         f"{WEIGHTS / GiB:.2f} GiB + {USED / MiB:.1f} MiB",
         f"the amber sliver is {USED / GiB * ppg:.2f} pt wide — that is the "
         f"conversation you actually had"),
        (f"+ cache for --ctx-size {SMALL_CTX:,}", WEIGHTS + SMALL_CTX * PER_TOK,
         gib(WEIGHTS + SMALL_CTX * PER_TOK), "fits, with room for a second model"),
        (f"+ cache for --ctx-size {MID_CTX:,}", WEIGHTS + MID_CTX * PER_TOK,
         gib(WEIGHTS + MID_CTX * PER_TOK),
         "fits, and is more context than most tasks need"),
        (f"+ cache for --ctx-size {MODEL['max_ctx']:,}", WEIGHTS + RESERVED,
         gib(WEIGHTS + RESERVED), "will not load — and you never sent a token"),
    ]

    bh, bgap = 34, 20
    y = top
    for label, total, value, note in bars:
        # the card's capacity, behind everything
        rbox(c, bx, y - bh, card_x - bx, bh, fill=WASH, stroke=RULE, r=0, lw=0.7)

        wpt = WEIGHTS / GiB * ppg
        rbox(c, bx, y - bh, wpt, bh, fill=PETROL, stroke=None, r=0)

        epx = (total - WEIGHTS) / GiB * ppg
        if epx > 0:
            inside = max(0.0, min(epx, card_x - (bx + wpt)))
            if inside > 0:
                rbox(c, bx + wpt, y - bh, inside, bh, fill=AMBER, stroke=None, r=0)
            over = epx - inside
            if over > 0:                      # the only red on the slide
                c.saveState()
                c.setFillColor(RED)
                c.rect(card_x, y - bh, over, bh, stroke=0, fill=1)
                c.restoreState()

        over_card = total > CARD
        txt(c, lx, y - bh / 2 - 3.4, label, "Display", 9.2, INK)
        end = bx + total / GiB * ppg
        if end + 72 > PW - M:          # no room outside — put it inside the bar
            txt(c, end - 12, y - bh / 2 - 3.4, value, "Display-Bold", 9.6,
                colors.white, "r")
        else:
            txt(c, end + 8, y - bh / 2 - 3.4, value, "Display-Bold", 9.6,
                RED if over_card else INK)
        txt(c, lx, y - bh - 9, note, "Body-Italic", 8.2,
            RED if over_card else SLATE)
        y -= bh + bgap

    # the card limit
    bottom = y + bgap - 8
    c.saveState()
    c.setStrokeColor(RED)
    c.setLineWidth(1.4)
    c.setDash(4, 3)
    c.line(card_x, bottom, card_x, top + 8)
    c.restoreState()
    txt(c, card_x, top + 14, f"{MODEL['card_gib']} GiB — the card", "Display-Bold",
        9, RED, "c")

    # scale ticks
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    for g in range(0, 22, 4):
        tx = bx + g * ppg
        c.line(tx, bottom, tx, bottom - 4)
        txt(c, tx, bottom - 14, f"{g}", "Display-Light", 7.4, SLATE, "c")
    txt(c, bx + span, bottom - 14, "GiB", "Display-Light", 7.4, SLATE, "r")

    # ---------------------------------------------- the three sentences
    fy = bottom - 34
    notes = [
        (PETROL, "The weights do not care",
         ["how much you type. They are",
          "the same for one token and",
          "for a hundred thousand."]),
        (AMBER, "What you used is invisible",
         [f"{USED / MiB:.1f} MiB on a {MODEL['card_gib']} GiB card.",
          "You will never spot it on",
          "a memory graph."]),
        (RED, "The reservation decides",
         ["whether the model loads.",
          "It is paid up front, in full,",
          "before the first token."]),
    ]
    gap = 20
    colw = (CW - gap * 2) / 3
    for i, (col, head, lines) in enumerate(notes):
        x = M + i * (colw + gap)
        rbox(c, x, fy - 70, colw, 70, fill=WASH if col is not RED else WASH_WARM,
             stroke=col, r=4, lw=1.0)
        txt(c, x + 14, fy - 21, head, "Display-Bold", 9.2, col)
        yy = fy - 36
        for line in lines:
            txt(c, x + 14, yy, line, "Body", 8.8, INK)
            yy -= 12.4

    # the practical line
    py = fy - 70 - 14
    txt(c, M, py - 8,
        f"So --ctx-size {SMALL_CTX:,} is not a limitation you put up with. It is the "
        f"number you choose on purpose, and {gib(RESERVED - SMALL_CTX * PER_TOK)} "
        f"is what it hands back.",
        "Body-Bold", 10, INK)
    txt(c, M, py - 24,
        "Quantising the cache (-ctk q8_0 -ctv q8_0) halves every amber figure above. "
        "Ollama sizes its cache from num_ctx in exactly the same way,",
        "Body-Italic", 8.8, SLATE)
    txt(c, M, py - 36,
        "but defaults to a far smaller window — which is why the same model can 'fit' "
        "under Ollama and refuse to load under llama-server.",
        "Body-Italic", 8.8, SLATE)


def build(path):
    c = pdfcanvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Lab 1 — weights, KV cache and context length")
    for fn in (slide1, slide2):
        c.setFillColor(colors.white)
        c.rect(0, 0, PW, PH, stroke=0, fill=1)
        fn(c)
        c.showPage()
    c.save()


if __name__ == "__main__":
    from pdfkit import publish

    print(f"\n  per token   {PER_TOK:,} bytes  ({PER_TOK // KiB} KiB)")
    print(f"  weights     {gib(WEIGHTS)}")
    print(f"  {N_TOK} tokens   {USED / MiB:.2f} MiB")
    print(f"  {MODEL['max_ctx']:,} ctx  {gib(RESERVED)}")
    print(f"  ratios      weights/used {WEIGHTS / USED:,.0f}x   "
          f"reserved/used {RESERVED / USED:,.0f}x\n")
    publish(build, OUT, "lab01_local_serving")
