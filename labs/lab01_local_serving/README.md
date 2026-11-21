# Lab 1 — Your GPU, Measured

**60 minutes · everyone gathered round the GPU machine**

## Goal

Stop treating inference as magic and start treating it as a capacity planning
problem. By the end you'll know what your card can serve, how fast, and where it
falls over.

You'll also watch a small model produce confidently malformed JSON, which sets
up every design decision in the rest of the weekend.

**Show [`Lab1-VRAM-Arithmetic.pdf`](Lab1-VRAM-Arithmetic.pdf) during step 2.**
Four slides: what the metadata tells you, the two sums, the table, and the model
on this machine that breaks the tidy version of the rule.

## Files

| File | What it is |
|---|---|
| `bench.py` | Speed and JSON-reliability benchmarks. Writes `bench_results.json` |
| `kv_math.py` | Pulls the hidden model metadata and does the VRAM arithmetic |
| `Lab1-VRAM-Arithmetic.pdf` | The four slides for the whiteboard session |

## Two ways to run a model locally

The room will have both, so it's worth ten minutes up front. **Ollama is
llama.cpp underneath** — it bundles the same inference engine with a model
manager on top. The difference isn't the engine. It's how much control you get
and how much you have to think about.

| | **Ollama** | **llama-server** (llama.cpp) |
|---|---|---|
| What it is | Model manager wrapping llama.cpp | The inference server itself |
| Getting a model | `ollama pull qwen3:8b` | Download a `.gguf` yourself |
| Models per process | Many — loads on demand per request | **One.** Restart to change |
| Default port | `11434` | `8080` |
| API | `/api/chat`, `/api/generate`, plus OpenAI `/v1/*` | OpenAI `/v1/*`, plus native `/completion`, `/props` |
| Context length | `num_ctx` per request, **small by default** | `-c` fixed at startup, shared across slots |
| Concurrency | Queued for you | `-np N` slots, fixed at startup |
| KV cache quantisation | Awkward | `-ctk` / `-ctv`, first-class |
| GPU offload, flash attention | Decided for you | Every flag yours (`-ngl`, `--flash-attn`) |
| Reading model metadata | `POST /api/show` with `verbose` | Startup log, or `gguf_dump` |

**Use Ollama** to try several models quickly, and on a laptop where you don't
much care about squeezing the hardware.

**Use llama-server** when you're fitting one specific model onto one specific
card — which is exactly what the machine in this room is doing. Every flag in
`start-qwen36.sh` exists because somebody decided a trade-off, and that's the
whole skill this lab is about.

> **The gotcha that will bite you.** Ollama allocates a few thousand tokens of
> context by default, not the model's maximum. llama-server allocates exactly
> what `-c` says, at startup. So the *same model* shows wildly different VRAM
> under the two, and it isn't the engine being different — it's the default.
> Step 2 makes this visible.

Both work with every lab here: `labs/common/local_backend.py` detects whichever
is listening and adapts.

## Why the host's machine

The two laptops don't have the interesting hardware. Run this one together, on
the big screen, with everyone watching `nvidia-smi`.

Laptops should still point at the GPU box so everyone can follow along — see
**If it breaks** below for the one-line `.env` setting.

## Steps

### 1. Check what you're working with

```bash
nvidia-smi
```

Note the card and total VRAM. Then, in a **second terminal**, leave this running
for the whole lab:

```bash
nvidia-smi -l 1
```

### 2. What a model actually is — and the number nobody looks at

Start with what the tooling volunteers:

```bash
ollama list && ollama show <model>        # Ollama
grep -E 'n_layer|n_head|n_embd_head' /tmp/llama-server.log    # llama-server
```

Then do the arithmetic out loud as a group:

> **Weights.** A model with **N billion parameters** at **Q bits each** needs
> about `N × Q / 8` GB. An 8B at 4-bit is ~4 GB; at 16-bit it's 16 GB and leaves
> room for nothing else. **This is why almost every local model is quantised.**

> **The KV cache**, which almost nobody sizes:
> `2 × attention layers × KV heads × head dim × bytes`, **per token**, then
> multiply by context length.

Two traps, and the slides cover both:

- **`Q4_K_M` is not 4 bits.** The `_K_M` means mixed — mostly Q4_K with some
  tensors at Q6_K, landing near 4.8 bits per weight in practice.
- **`ollama show` does not print the three numbers the cache formula needs** —
  layer count, KV-head count and head dimension. They're in the GGUF metadata,
  not on that screen.

So let the script fetch them and do the sum:

```bash
python kv_math.py                          # whatever Ollama has loaded
python kv_math.py llama3.1:8b              # a named Ollama model
python kv_math.py --gguf /path/to/model.gguf   # straight from the file
python kv_math.py --gguf model.gguf --kv-bits 3  # with a quantised cache
```

**Run it twice, with `--kv-bits 16` then `--kv-bits 3`.** Watch the bottom row
flip from "DOES NOT FIT" to "fits". That one keystroke explains how a 27B runs
at 196k context on a 16 GB card, and it's the most useful thing in the hour.

> **Friend 1's question:** what does quantisation actually throw away, and why
> does the model mostly still work? He'll know about weight distributions. Let
> him explain it.

### 3. Benchmark

```bash
python bench.py --label "27B IQ3_M"
```

The script detects whichever backend is running. **On llama.cpp you benchmark
one model at a time** — `llama-server` holds a single GGUF — so the workflow is:
run it, restart the server with a different model or quant, run it again, then:

```bash
python bench.py --compare
```

Results accumulate in `bench_results.json`, so the comparison survives the
restarts. On Ollama you can loop in one go with
`--models qwen3:8b,llama3.2:3b`.

Record the numbers — you'll want them in Lab 8 when you compare against API
costs.

Two metrics that matter and get conflated constantly:

- **TTFT (time to first token)** — how long until the user sees *anything*.
  This is what makes an interface feel responsive.
- **Tokens/sec** — how fast it produces the rest. This is what makes it feel fast.

You can have good TTFT and terrible throughput, or the reverse. They're
different problems with different fixes.

### 4. Break it

Start a second generation while the first is still running.

```bash
ollama run qwen3:14b "write a long essay about shipping containers"   # Ollama
curl -s localhost:8080/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"write a long essay about shipping containers"}],"max_tokens":2000}' &
```

On llama-server, whether this queues or runs concurrently depends on `-np`. With
one slot the second request simply waits — which is its own lesson about serving
three people from one box.

Watch `nvidia-smi`. When VRAM fills, layers spill to system RAM and throughput
collapses — often by 10x or more. **There's no error. It just gets slow.**

> **Friend 2's question:** how would you detect this in production before your
> users did? What's the metric, what's the alert, what's the autoscaling policy?
> This is exactly his territory.

### 5. The JSON test — the important bit

```bash
python bench.py --json-test --trials 5 --label "27B IQ3_M"
```

Same task, five attempts, counting how often you get parseable JSON with all
the required fields. **No schema constraint here** — this is the model unaided,
which is the honest baseline. Lab 2 turns the constraint on and the difference
is dramatic.

## Expected output

The 3B model will fail some or most trials. It'll add code fences, add a
preamble, invent extra keys, or hallucinate a severity level that wasn't in your
enum. The 8B model will do noticeably better. The 14B better again.

Nothing will be perfect, and **that's the lesson.**

## Discussion (10 min, laptops closed)

1. Which failures would your code catch, and which would silently poison a
   downstream system? The second kind is much worse and much more common.
2. If a single generation takes 8 seconds on your card, how many concurrent
   users can you serve? What's the queue depth before someone waits a minute?
3. When is running this yourself cheaper than paying per token? What has to be
   true? (Hold onto this — it's a portfolio project in `PORTFOLIO.md`.)

## If it breaks

**Connecting a laptop to the GPU box**
The server needs `--host 0.0.0.0` (the workshop script already has it), the
box's firewall needs port 8080 open, and the laptop needs this in `.env` **at
the repo root**:

```
LOCAL_API_BASE=http://<gpu-box-ip>:8080
```

`load_dotenv()` searches upward from your working directory, so run the labs
from inside the repo or the file is never found.

**`Nothing is listening at http://...`**
That address came from `LOCAL_API_BASE`, and the labs deliberately do **not**
fall back to something else — benchmarking a model you didn't choose is worse
than an error. Start the server there, or fix the address.

**Every connection prints which backend it got**

```
  → llamacpp at http://192.168.1.40:8080  ·  Qwen3.6-27B-NEO-CODE-IQ3_M.gguf
```

If that line says Ollama when you expected llama.cpp, your `.env` isn't being
read. Check it before debugging anything else.

**`404 ... model not found` (Ollama)**
The model isn't pulled on *that* machine. `ollama list` shows what is;
`ollama pull <model>` fixes it. These are multi-GB, so do it before Saturday.

**Throughput looks absurdly low on a hybrid-reasoning model**
It's thinking. Qwen3.x and similar default to reasoning ON, which burns a large
number of tokens before answering. The labs request thinking off per call; you
can also set `--reasoning-budget 0` on the server.

**Everything is absurdly slow, GPU shows 0% utilisation**
It's running on CPU. Check `nvidia-smi` sees the card at all, then check your
CUDA drivers. On WSL2 you need the Windows-side NVIDIA driver, not a Linux one.

**A model won't load at all**
Expected if it doesn't fit. Use a smaller quantisation, or run `kv_math.py`
first and find out *before* you wait for the load — a model that doesn't fit is
itself a useful data point.

## Takeaway

Write this on the whiteboard before moving on:

> Local inference is cheap per token and expensive per unit of reliability.
> API inference is the reverse. Choose per workload, not per ideology.
