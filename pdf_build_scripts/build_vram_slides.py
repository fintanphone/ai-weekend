#!/usr/bin/env python3
"""Lab 1 whiteboard slides — reading `ollama show`, and the VRAM arithmetic.

    python build_vram_slides.py

Three landscape A4 slides, meant to be on a screen while the room does the
sum together:

    1. what the output tells you, and the number it leaves out
    2. the two calculations
    3. the table, and why it does not fit

Numbers are computed here, not typed in, so the slides cannot drift from the
arithmetic. Change MODEL below to re-cut them for a different model.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

from pdfkit import (
    AMBER, AMBER_LT, GREEN, INK, PETROL, PETROL_LT, RED, RULE, SLATE,
    WASH, WASH_WARM, arrow, colors, rbox, txt,
)

OUT = "Lab1-VRAM-Arithmetic.pdf"
PW, PH = landscape(A4)
M = 18 * mm
CW = PW - 2 * M
GiB = 1024 ** 3

# ---------------------------------------------------------------- the model
MODEL = dict(
    label="Llama 3.1 8B Instruct",
    shown=[("architecture", "llama", False),
           ("parameters", "8.0B", True),
           ("context length", "131072", True),
           ("embedding length", "4096", False),
           ("quantization", "Q4_K_M", True),
           ("template source", "go_template", False)],
    params=8.0e9,
    bpw_nominal=4.0,
    bpw_actual=4.8,       # Q4_K_M is mixed: mostly Q4_K, some Q6_K
    layers=32,
    kv_heads=8,
    q_heads=32,
    head_dim=128,
    kv_bytes=2,           # fp16 cache
    card_gib=16,
)

PER_TOK = (2 * MODEL["layers"] * MODEL["kv_heads"] * MODEL["head_dim"]
           * MODEL["kv_bytes"])
W_NOM = MODEL["params"] * MODEL["bpw_nominal"] / 8
W_ACT = MODEL["params"] * MODEL["bpw_actual"] / 8
CONTEXTS = [4096, 8192, 32768, 65536, 131072]

# ------------------------------------------------- the counter-example
# A hybrid attention/SSM model, read off the GGUF header of the 27B that
# runs on the workshop machine. It breaks the tidy formula three ways.
QWEN = dict(
    label="Qwen 3.6 27B  (qwen35)",
    params=27e9,
    bpw=3.7,                 # IQ3_M
    layers=64,
    attn_interval=4,         # full attention on every 4th layer only
    heads=24,
    kv_heads=4,
    key_len=256,             # stored, because 5120/24 is not an integer
    val_len=256,
    embed=5120,
    max_ctx=262144,
    run_ctx=196608,          # what the start script actually asks for
    run_kv_bits=3,           # -ctk turbo3 -ctv turbo3
)
Q_ATTN = QWEN["layers"] // QWEN["attn_interval"]
Q_PER_TOK_F16 = Q_ATTN * (QWEN["key_len"] + QWEN["val_len"]) * QWEN["kv_heads"] * 2
Q_PER_TOK_RUN = Q_ATTN * (QWEN["key_len"] + QWEN["val_len"]) * QWEN["kv_heads"] \
    * QWEN["run_kv_bits"] / 8
Q_NAIVE = QWEN["layers"] * (QWEN["key_len"] + QWEN["val_len"]) * QWEN["kv_heads"] * 2
Q_W = QWEN["params"] * QWEN["bpw"] / 8


def footer(c, n):
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(M, M - 6 * mm, PW - M, M - 6 * mm)
    txt(c, M, M - 11 * mm, "LAB 1  ·  WHAT YOUR GPU CAN ACTUALLY HOLD",
        "Display-Light", 7.4, SLATE)
    txt(c, PW - M, M - 11 * mm, f"{n} / 4", "Mono", 7.4, SLATE, "r")


def title(c, big, small):
    txt(c, M, PH - M - 16, big, "Display-Bold", 23, INK)
    txt(c, M, PH - M - 34, small, "Body-Italic", 11.5, PETROL)


# ---------------------------------------------------------------- slide 1
def slide1(c):
    title(c, "What `ollama show` tells you",
          "Three numbers matter. One of them is a trap, and the most important "
          "number is not on the screen at all.")

    top = PH - M - 62          # content starts here on every slide
    bh = 290

    # the terminal block
    bw = CW * 0.52
    bx, by = M, top - bh
    rbox(c, bx, by, bw, bh, fill=colors.HexColor("#102B28"), stroke=None, r=6)
    txt(c, bx + 18, by + bh - 30, "$ ollama show llama3.1:8b", "Mono", 10,
        colors.HexColor("#7FB3AD"))
    txt(c, bx + 18, by + bh - 56, "Model", "Mono", 10,
        colors.HexColor("#E6EDEB"))
    y = by + bh - 84
    for key, val, hot in MODEL["shown"]:
        col = AMBER_LT if hot else colors.HexColor("#8A9B98")
        txt(c, bx + 34, y, key, "Mono", 10, col)
        txt(c, bx + 200, y, val, "Mono", 10,
            colors.white if hot else colors.HexColor("#8A9B98"))
        if hot:
            c.setFillColor(AMBER)
            c.rect(bx + 21, y - 2, 4, 12, stroke=0, fill=1)
        y -= 27

    # annotations on the right — heights match the terminal block
    ax = M + bw + 26
    aw = CW - bw - 26
    notes = [
        (AMBER, "parameters  8.0B",
         "Feeds the weights sum. The number\neveryone already knows to look at."),
        (AMBER, "quantization  Q4_K_M",
         "NOT 4 bits. The _K_M means mixed —\nmostly Q4_K with some Q6_K.\nAbout 4.8 bits per weight in practice."),
        (RED, "context length  131072",
         "The trap. This is what the model\nSUPPORTS, not what gets allocated.\nSizing the cache for it needs 16 GiB."),
    ]
    nh, ngap = 90, 10
    ny = top
    for col, head, body in notes:
        rbox(c, ax, ny - nh, aw, nh, fill=WASH_WARM if col is AMBER else None,
             stroke=col, r=4, lw=1.0)
        txt(c, ax + 14, ny - 26, head, "Mono", 9.4, col)
        for i, line in enumerate(body.split("\n")):
            txt(c, ax + 14, ny - 45 - i * 13, line, "Body", 8.6, INK)
        ny -= nh + ngap

    # the missing piece
    mh = 80
    my = by - 26 - mh
    rbox(c, M, my, CW, mh, fill=None, stroke=PETROL, r=5, lw=1.4)
    txt(c, M + 18, my + mh - 26, "What it does NOT tell you — and what you "
        "actually need:", "Display-Bold", 11.4, PETROL)
    txt(c, M + 18, my + mh - 48, f"layers with attention ({MODEL['layers']})"
        f"      ·      KV heads ({MODEL['kv_heads']})"
        f"      ·      head dimension ({MODEL['head_dim']})", "Mono", 10, INK)
    txt(c, M + 18, my + 16, "Those three size the KV cache — and the KV cache "
        "is what fills your card.   Get them from the GGUF header, not from "
        "this screen.", "Body-Italic", 9.4, SLATE)
    footer(c, 1)


# ---------------------------------------------------------------- slide 2
def slide2(c):
    title(c, "The two sums",
          "One for the weights, one for the cache. The second is the one "
          "nobody does.")

    top = PH - M - 62
    colw = (CW - 30) / 2
    h = 252
    y = top - h

    # --- weights ---
    x = M
    rbox(c, x, y, colw, h, fill=WASH, stroke=PETROL_LT, r=6, lw=1.0)
    txt(c, x + 20, y + h - 30, "1  ·  THE WEIGHTS", "Display-Bold", 11, PETROL)
    txt(c, x + 20, y + h - 62, "parameters  ×  bits  ÷  8", "Mono", 12, INK)
    txt(c, x + 20, y + h - 96, "The formula everyone knows:", "Body-Italic",
        9.2, SLATE)
    txt(c, x + 20, y + h - 120, f"8.0e9  ×  4  ÷  8  =  {W_NOM/GiB:.2f} GiB",
        "Mono", 11.5, SLATE)
    txt(c, x + 20, y + h - 160, "But Q4_K_M is not 4 bits:", "Body-Italic",
        9.2, AMBER)
    txt(c, x + 20, y + h - 188, f"8.0e9  ×  4.8  ÷  8  =  {W_ACT/GiB:.2f} GiB",
        "Mono", 14, AMBER)
    txt(c, x + 20, y + 18, f"Check it: the file on disk is about "
        f"{W_ACT/1e9:.1f} GB.", "Body-Italic", 9, SLATE)

    # --- kv cache ---
    x2 = M + colw + 30
    rbox(c, x2, y, colw, h, fill=WASH_WARM, stroke=AMBER, r=6, lw=1.0)
    txt(c, x2 + 20, y + h - 30, "2  ·  THE KV CACHE, PER TOKEN",
        "Display-Bold", 11, AMBER)
    txt(c, x2 + 20, y + h - 62,
        "2  ×  attn layers  ×  kv-heads  ×  dim  ×  bytes", "Mono", 11, INK)
    txt(c, x2 + 20, y + h - 82, "the 2 is K and V, stored separately   ·   "
        "ATTENTION layers, not all layers — slide 4", "Body-Italic", 8.8, SLATE)
    txt(c, x2 + 20, y + h - 124,
        f"2 × {MODEL['layers']} × {MODEL['kv_heads']} × {MODEL['head_dim']} × "
        f"{MODEL['kv_bytes']}", "Mono", 11.5, INK)
    txt(c, x2 + 20, y + h - 160, f"=  {PER_TOK:,} bytes", "Mono", 11.5, INK)
    txt(c, x2 + 20, y + h - 190, f"=  {PER_TOK/1024:.0f} KiB per token",
        "Mono", 14, AMBER)
    txt(c, x2 + 20, y + 42, "Then multiply by context length.", "Body-Italic",
        9.2, SLATE)
    txt(c, x2 + 20, y + 18, "That multiplication is the whole lesson.",
        "Body-BoldItalic", 9.6, AMBER)

    # --- GQA note ---
    gh = 96
    gy = y - 26 - gh
    rbox(c, M, gy, CW, gh, fill=None, stroke=PETROL, r=5, lw=1.2)
    txt(c, M + 18, gy + gh - 26, "Why kv-heads, and not just heads?",
        "Display-Bold", 11.4, PETROL)
    mha = CONTEXTS[-1] * 2 * MODEL["layers"] * MODEL["q_heads"] * \
        MODEL["head_dim"] * MODEL["kv_bytes"]
    txt(c, M + 18, gy + gh - 50, f"Grouped-query attention: "
        f"{MODEL['q_heads']} query heads share just {MODEL['kv_heads']} "
        f"key/value heads — {MODEL['q_heads']//MODEL['kv_heads']}:1. Only the "
        f"KV heads cost cache.", "Body", 9.6, INK)
    txt(c, M + 18, gy + gh - 70, f"Without it, that same 131k cache would be "
        f"{mha/GiB:.0f} GiB instead of {CONTEXTS[-1]*PER_TOK/GiB:.0f} GiB.",
        "Body", 9.6, INK)
    txt(c, M + 18, gy + 16, "Long context on consumer hardware is an "
        "attention-architecture win, not a memory-price one.", "Body-Italic",
        9.4, SLATE)
    footer(c, 2)


# ---------------------------------------------------------------- slide 3
def slide3(c):
    title(c, "What to look for in the result",
          "Weights are fixed. The cache is a dial — and at full context it is "
          "bigger than the model.")

    rows = [(ctx, ctx * PER_TOK, ctx * PER_TOK + W_ACT) for ctx in CONTEXTS]
    cap = MODEL["card_gib"] * GiB

    y = PH - M - 72
    colx = [M + 14, M + 150, M + 290, M + 430]
    txt(c, colx[0], y, "CONTEXT", "Display-Bold", 8.8, SLATE)
    txt(c, colx[1], y, "KV CACHE", "Display-Bold", 8.8, SLATE)
    txt(c, colx[2], y, "+ WEIGHTS", "Display-Bold", 8.8, SLATE)
    txt(c, colx[3], y, "ON A 16 GiB CARD", "Display-Bold", 8.8, SLATE)

    # the bar track starts after the text columns
    tx = M + 600
    tw = PW - M - tx - 56      # leave room for the 16 GiB label
    scale = tw / (22 * GiB)
    head_y = y

    y -= 14
    for ctx, kv, tot in rows:
        y -= 44
        over = tot > cap
        if over:
            rbox(c, M, y - 11, CW, 40, fill=colors.HexColor("#F6E9E6"),
                 stroke=None, r=4)
        txt(c, colx[0], y, f"{ctx:,}", "Mono", 11, RED if over else INK)
        txt(c, colx[1], y, f"{kv/GiB:.2f} GiB", "Mono", 11, RED if over else INK)
        txt(c, colx[2], y, f"{tot/GiB:.2f} GiB", "Mono", 11,
            RED if over else INK)
        txt(c, colx[3], y, "does NOT fit" if over else "fits",
            "Display-Bold", 10.4, RED if over else GREEN)
        # proportional bar, weights then cache
        c.setFillColor(PETROL)
        c.rect(tx, y - 4, W_ACT * scale, 17, stroke=0, fill=1)
        c.setFillColor(RED if over else AMBER)
        c.rect(tx + W_ACT * scale, y - 4, kv * scale, 17, stroke=0, fill=1)

    # the card limit
    lx = tx + cap * scale
    c.saveState()
    c.setStrokeColor(INK)
    c.setDash(2.5, 2.5)
    c.setLineWidth(1.2)
    c.line(lx, y - 16, lx, head_y - 6)
    c.restoreState()
    txt(c, lx + 5, head_y - 2, "16 GiB", "Display-Bold", 8.6, INK)
    c.setFillColor(PETROL)
    c.rect(tx, y - 34, 9, 9, stroke=0, fill=1)
    txt(c, tx + 13, y - 33, "weights", "Body", 8.4, SLATE)
    c.setFillColor(AMBER)
    c.rect(tx + 74, y - 34, 9, 9, stroke=0, fill=1)
    txt(c, tx + 87, y - 33, "KV cache", "Body", 8.4, SLATE)

    # punchline
    ph_, py = 118, M + 10
    rbox(c, M, py, CW, ph_, fill=WASH, stroke=None, r=6)
    c.setFillColor(AMBER)
    c.rect(M, py, 3.5, ph_, stroke=0, fill=1)
    txt(c, M + 22, py + ph_ - 28, "At its advertised context length, the cache "
        "alone fills the whole card.", "Display-Bold", 14, INK)
    txt(c, M + 22, py + ph_ - 50, "Everyone sizes a model by its parameter "
        "count. Almost nobody sizes the cache — and the cache is what actually "
        "stops it fitting.", "Body", 10, INK)
    txt(c, M + 22, py + 36, "WHAT YOU WILL ACTUALLY SEE", "Display-Bold", 8.8,
        AMBER)
    txt(c, M + 22, py + 20, "nvidia-smi will show about 5 GiB, not 20 — because "
        "Ollama allocates a few thousand tokens of context by default, not "
        "131,072.", "Body", 9.4, SLATE)
    txt(c, M + 22, py + 6, "Raise num_ctx to 65536 and watch it jump by 8 GiB. "
        "That demonstration beats the arithmetic.", "Body", 9.4, SLATE)
    footer(c, 3)


# ---------------------------------------------------------------- slide 4
def slide4(c):
    title(c, "When the tidy formula doesn't hold",
          "The 27B on this machine is not shaped like the model on the last "
          "three slides. It breaks the rule three ways.")

    top = PH - M - 62
    bh = 232
    bw = CW * 0.44
    bx, by = M, top - bh

    # the header extract
    rbox(c, bx, by, bw, bh, fill=colors.HexColor("#102B28"), stroke=None, r=6)
    txt(c, bx + 18, by + bh - 28, "gguf_dump --no-tensors", "Mono", 9.5,
        colors.HexColor("#7FB3AD"))
    lines = [
        ("general.architecture", "qwen35", False),
        ("general.size_label", "27B", True),
        ("block_count", "64", False),
        ("full_attention_interval", "4", True),
        ("attention.head_count", "24", False),
        ("attention.head_count_kv", "4", False),
        ("attention.key_length", "256", True),
        ("ssm.state_size", "128", True),
        ("general.file_type", "27", True),
    ]
    yy = by + bh - 56
    for key, val, hot in lines:
        col = AMBER_LT if hot else colors.HexColor("#8A9B98")
        txt(c, bx + 18, yy, key, "Mono", 8.6, col)
        txt(c, bx + 252, yy, val, "Mono", 8.6,
            colors.white if hot else colors.HexColor("#8A9B98"))
        yy -= 19

    # the three breaks
    ax = M + bw + 24
    aw = CW - bw - 24
    breaks = [
        ("1", "Head dimension is stored, not derived",
         f"{QWEN['embed']} / {QWEN['heads']} = 213.33 — not an integer. "
         f"This model\nsets attention.key_length = {QWEN['key_len']} explicitly."),
        ("2", "Only every 4th layer has attention",
         f"{QWEN['layers']} blocks, but full_attention_interval = "
         f"{QWEN['attn_interval']}.\nSo {Q_ATTN} layers hold a KV cache; the other "
         f"{QWEN['layers']-Q_ATTN} are SSM\nlayers with a FIXED state that never grows."),
        ("3", "No parameter_count, and the quant is an integer",
         "size_label = '27B' instead, and file_type 27\nis the enum for IQ3_M. "
         "Both need a lookup."),
    ]
    ny = top
    nh = 76
    for num, head, body in breaks:
        rbox(c, ax, ny - nh, aw, nh, fill=WASH_WARM, stroke=AMBER, r=4, lw=1.0)
        c.setFillColor(AMBER)
        c.circle(ax + 20, ny - 22, 10, stroke=0, fill=1)
        txt(c, ax + 20, ny - 25, num, "Display-Bold", 9.5, colors.white, "c")
        txt(c, ax + 38, ny - 26, head, "Display-Bold", 10, INK)
        for i, line in enumerate(body.split("\n")):
            txt(c, ax + 38, ny - 44 - i * 11.5, line, "Body", 8.4, SLATE)
        ny -= nh + 2

    # the comparison
    gh = 152
    gy = by - 20 - gh
    rbox(c, M, gy, CW, gh, fill=WASH, stroke=None, r=6)
    c.setFillColor(PETROL)
    c.rect(M, gy, 3.5, gh, stroke=0, fill=1)
    txt(c, M + 22, gy + gh - 26, "A model three times the size, with a cache "
        "ten times smaller per token", "Display-Bold", 13, INK)
    cols = [M + 22, M + 330, M + 530, M + 700]
    rows = [
        ("", "Llama 3.1 8B", "Qwen 3.6 27B", ""),
        ("layers holding a KV cache", f"{MODEL['layers']} of {MODEL['layers']}",
         f"{Q_ATTN} of {QWEN['layers']}", "4x"),
        ("grouped-query ratio",
         f"{MODEL['q_heads']//MODEL['kv_heads']}:1",
         f"{QWEN['heads']//QWEN['kv_heads']}:1", "1.5x"),
        ("KV per token, fp16", f"{PER_TOK/1024:.0f} KiB",
         f"{Q_PER_TOK_F16/1024:.0f} KiB", ""),
        ("KV per token, as actually run", "—",
         f"{Q_PER_TOK_RUN/1024:.0f} KiB  (turbo3)", "5.3x"),
    ]
    ry = gy + gh - 50
    for i, (label, a, b, gain) in enumerate(rows):
        bold = i == 0
        f = "Display-Bold" if bold else "Body"
        txt(c, cols[0], ry, label, "Body", 9, SLATE)
        txt(c, cols[1], ry, a, f if bold else "Mono", 9.2,
            SLATE if bold else INK)
        txt(c, cols[2], ry, b, f if bold else "Mono", 9.2,
            SLATE if bold else AMBER)
        if gain:
            txt(c, M + CW - 22, ry, gain + " better", "Display-Bold", 9,
                GREEN, "r")
        ry -= 17
    txt(c, M + 22, gy + 10, "Quantising the weights is what lets it load. The "
        "architecture and the KV quant are what give it 196k of context — and "
        "neither is on the `ollama show` screen.", "Body-Italic", 9.4, PETROL)
    footer(c, 4)


def build(path):
    c = pdfcanvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Lab 1 — VRAM arithmetic")
    for fn in (slide1, slide2, slide3, slide4):
        c.setFillColor(colors.white)
        c.rect(0, 0, PW, PH, stroke=0, fill=1)
        fn(c)
        c.showPage()
    c.save()


if __name__ == "__main__":
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    target = repo / "pdfs" / OUT
    target.parent.mkdir(exist_ok=True)
    build(str(target))
    print(f"built {target}  ({target.stat().st_size/1024:.0f} KB)")

    beside = repo / "labs" / "lab01_local_serving" / OUT
    if beside.parent.exists():
        import shutil
        shutil.copy2(target, beside)
        print(f"  also copied to {beside.relative_to(repo)}")
