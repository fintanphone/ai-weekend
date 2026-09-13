# Before You Arrive

**Send this to both friends at least a week ahead.** Ask them to confirm
`check_setup.py` passes on their laptop. Nothing ruins a workshop faster than
spending Saturday morning on Python installs.

Budget 45 minutes. If you hit a wall, message the host rather than fighting it
alone — that's the whole point of doing it in advance.

---

## 1. Python 3.11 or newer

```bash
python3 --version
```

If that's below 3.11, install a newer one. On macOS use `brew install python@3.12`.
On Windows use the python.org installer and **tick "Add Python to PATH"**. On
Linux your package manager is fine.

## 2. Clone the repo and make a virtualenv

```bash
git clone <repo-url> ai-agents-weekend
cd ai-agents-weekend

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

The install pulls down a sentence-transformers model on first use (~90MB), so
don't leave it until you're on workshop wifi with three people downloading at once.

## 3. Get an API key

Create an account at <https://console.anthropic.com>, generate an API key, and
put it in a `.env` file in the repo root:

```bash
cp .env.example .env
```

Then edit `.env` and paste your key after `ANTHROPIC_API_KEY=`.

**Cost:** the whole weekend runs on a few euro of credit per person. Add $10 and
you'll finish with change. Current per-token rates are on
<https://www.anthropic.com/pricing> — worth a look anyway, since Lab 8 covers
cost management and you'll want the real numbers.

`.env` is gitignored. Don't commit your key. Don't paste it into a chat window.

## 4. Install Claude Code

Used in Lab 6 and Lab 7. Needs Node.js 18+.

```bash
node --version
npm install -g @anthropic-ai/claude-code
claude --version
```

Docs: <https://docs.claude.com/en/docs/claude-code/overview>

## 5. A local model server — host only

Labs 1 and 2b talk to a local model. They auto-detect the backend, so either
of these works and you don't need both.

**llama.cpp (`llama-server`).** If you already run one, you're done. Set the
port in `.env`:

```
LOCAL_API_BASE=http://localhost:8080
```

Two flags matter for the labs. `--jinja` enables tool calling, and for
extraction and tool use you want thinking **off** on hybrid-reasoning models —
the labs request that per-call, but setting `--reasoning-budget 0` on the server
saves a lot of wasted tokens.

**Ollama.** Simpler if you don't already have a llama.cpp build.

```bash
ollama pull llama3.2:3b        # ~2GB   deliberately too small, for contrast
ollama pull qwen3:8b           # ~5GB   the workhorse
ollama pull qwen3:14b          # ~9GB   pushes a 12-16GB card
```

Friends can skip this entirely. Labs 1 and 2b run on the host's GPU machine with
everyone watching, since that's where the interesting hardware is.

To check what the labs can see — backend, model, constrained output and tool
calling, with the reason for anything that fails:

```bash
python labs/common/local_backend.py
```

Run this before Saturday. It's the single most useful thing to check, because
the constrained-output path varies between llama.cpp builds.

## 6. Verify

```bash
python check_setup.py
```

You want all green. Yellow warnings on the Ollama checks are fine for the two
laptops without GPUs.

---

## Optional but recommended reading

Thirty minutes, the night before. Not homework, just orientation.

- **Anthropic — Building effective agents**
  <https://www.anthropic.com/engineering/building-effective-agents>
  The single best piece on when *not* to build an agent.

- **Agent Skills specification** <https://agentskills.io>
  Short. Skim the spec page so Lab 5 lands faster.

- **Model Context Protocol** <https://modelcontextprotocol.io>
  Read the "Core concepts" page only.

---

## Turn up with

- Your laptop and charger
- A terminal you're comfortable in
- One real problem from your own life or work that you'd like an agent to solve

That last one matters more than it sounds. The Sunday capstone works far better
when people build for a problem they actually have.
