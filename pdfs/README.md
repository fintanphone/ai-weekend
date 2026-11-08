# PDF sources

The five lab introduction PDFs are generated, not hand-made. The source is
here so the wording can be changed without starting over.

| Script | Produces | Goes in |
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
python pdf_skills.py        # writes to the current directory
```

Then copy the PDF into its lab folder. The fonts are the ones Linux
distributions ship as `fonts-crosextra-caladea`, `fonts-dejavu` and Poppins
from Google Fonts; if a font is missing, `registerFont` fails loudly rather
than silently substituting.

## House style, if you add a sixth

Each one is five or six pages and follows the same spine:

1. **Cover** — eyebrow, title, one-sentence subtitle, who it's for
2. **What it actually is** — the definition, with the diagram that carries it
3. **Example 1** — a worked case, usually as a transcript
4. **Example 2** — a second case of a *different shape*, not a variation
5. **Where it goes wrong** — honest, specific, before anyone gets excited
6. **What to take into the lab** — three callouts, one sentence each

The two examples earn their place by being different kinds of use, not two
flavours of the same one. For MCP that is exposing a server versus consuming
one; for evals it is improving a system versus surviving a model change.

Keep the running takeaway honest. Every one of these says where the thing
fails, and two of them (`pdf_harness.py`, `pdf_mcp.py`) spend a full page
arguing against over-using it.
