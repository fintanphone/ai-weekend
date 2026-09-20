# Lab 1 — Your GPU, Measured

**60 minutes · everyone gathered round the GPU machine**

## Goal

Stop treating inference as magic and start treating it as a capacity planning
problem. By the end you'll know what your card can serve, how fast, and where it
falls over.

You'll also watch a small model produce confidently malformed JSON, which sets
up every design decision in the rest of the weekend.

## Why the host's machine

The two laptops don't have the interesting hardware. Run this one together, on
the big screen, with everyone watching `nvidia-smi`.

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

### 2. Look at what a model actually is

```bash
ollama list
ollama show qwen3:8b
```

Look at the parameter count, the quantisation, and the file size on disk. Do the
arithmetic out loud as a group:

> A model with **N billion parameters** at **Q bits per parameter** needs roughly
> `N × Q / 8` GB just to hold the weights. Then add the KV cache, which grows
> with your context length and batch size.

An 8B model at 4-bit quantisation is about 4GB of weights. At 16-bit it's 16GB
and won't leave room for anything else on a 12–16GB card. **This is why almost
every local model you'll ever run is quantised.**

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

Load the 14B model, then in a third terminal start a second generation while the
first is still running.

```bash
ollama run qwen3:14b "write a long essay about shipping containers"
```

Watch `nvidia-smi`. When VRAM fills, layers spill to system RAM and throughput
collapses — often by 10x or more. There's no error. It just gets slow.

> **Friend 2's question:** how would you detect this in production before your
> users did? What's the metric, what's the alert, what's the autoscaling policy?
> This is exactly his territory.

### 5. The JSON test — the important bit

```bash
python bench.py --json-test --trials 5 --label "27B IQ3_M"
```

Same task, five attempts, counting how often you get parseable JSON with all
the required fields. **No schema constraint here** — this is the model unaided,
which is the honest baseline. Lab 2b turns the constraint on and the difference
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

**No local model server found**
Nothing is listening. Start `llama-server` (or `ollama serve`) and check
`LOCAL_API_BASE` in `.env` matches the port. Run
`python ../common/local_backend.py` to see what the labs can detect.

**404 model not found (Ollama)**
`ollama pull <model>`. These are multi-GB, so ideally do this before Saturday.

**Throughput looks absurdly low on a hybrid-reasoning model**
It's thinking. Qwen3.x and similar default to reasoning ON, which burns a large
number of tokens before answering. The labs request thinking off per call; you
can also set `--reasoning-budget 0` on the server.

**Everything is absurdly slow, GPU shows 0% utilisation**
It's running on CPU. Check `nvidia-smi` sees the card at all, then check your
CUDA drivers. On WSL2 you need the Windows-side NVIDIA driver, not a Linux one.

**14B model won't load**
Expected on 12GB. Use a smaller quantisation (`qwen3:14b-q4_K_M`) or skip it and
note the failure — a model that doesn't fit is itself a useful data point.

## Takeaway

Write this on the whiteboard before moving on:

> Local inference is cheap per token and expensive per unit of reliability.
> API inference is the reverse. Choose per workload, not per ideology.
