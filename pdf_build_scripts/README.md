# PDF build scripts

The five lab introduction PDFs are generated, not hand-made. The source lives
here so the wording can be changed without starting over.

| Script | Produces | Also copied to |
|---|---|---|
| `pdf_skills.py` | `Skills-Intro.pdf` | `labs/lab05_skills/` |
| `pdf_mcp.py` | `MCP-Intro.pdf` | `labs/lab06_mcp/` |
| `pdf_agentic_coding.py` | `Agentic-Coding-Intro.pdf` | `labs/lab07_agentic_coding/` |
| `pdf_evals.py` | `Evals-Intro.pdf` | `labs/lab08_evals/` |
| `pdf_harness.py` | `Harness-Intro.pdf` | `labs/lab09_harness/` |

`pdfkit.py` holds everything shared: the palette, the three typefaces, the
paragraph styles, the cover, the page furniture, and the `callout`,
`transcript` and `two_col` helpers. Each lab's script adds only its own
diagrams and its own words.

## Rebuilding

```bash
pip install reportlab
python pdf_skills.py
```

Output goes to `../pdfs/` and is then copied into the lab folder, so the two
copies never drift. Run all five with:

```bash
for f in pdf_*.py; do python "$f"; done
```

The fonts are the ones Linux distributions ship as `fonts-crosextra-caladea`
and `fonts-dejavu`, plus Poppins from Google Fonts. If one is missing,
`registerFont` fails loudly rather than silently substituting — which is what
you want, because a silent fallback is only visible once it's printed.

## House style, if you add a sixth

Five or six pages, following the same spine:

1. **Cover** — eyebrow, title, one-sentence subtitle, who it's for
2. **What it actually is** — the definition, with the diagram that carries it
3. **Example 1** — a worked case, usually as a transcript
4. **Example 2** — a second case of a *different shape*, not a variation
5. **Where it goes wrong** — honest and specific, before anyone gets excited
6. **What to take into the lab** — three callouts, one sentence each

The two examples earn their place by being different kinds of use. For MCP
that's exposing a server versus consuming one; for evals it's improving a
system versus surviving a model change. Two flavours of the same use is a
wasted page.

Keep the honesty. Every one of these says where the thing fails, and two
(`pdf_harness.py`, `pdf_mcp.py`) spend a full page arguing against
over-using it. That's deliberate — an introduction that only shows the good
parts is an advert, and the audience can tell.

## A check worth running before you ship one

```python
import pdfplumber
for page in pdfplumber.open("../pdfs/Skills-Intro.pdf").pages:
    for w in page.extract_words():
        if float(w["x0"]) < 55 or float(w["x1"]) > 548:
            print("overflow:", w["text"])
```

Text running outside the margins is the failure that survives a quick look at
a thumbnail, and it's the one reviewers notice first.
