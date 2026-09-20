# Lab 1 — Local Inference

**Briefing for the facilitator.** Saturday 10:45 · 60 minutes · everyone round
the GPU machine.

---

## Open with

> "This is the only lab where the hardware is the subject. By the end of the
> hour you'll be able to look at any model on Hugging Face and say, without
> downloading it, whether it fits on this card and roughly how fast it'll go."

## The scenario

You have one GPU. Models come in a dozen sizes and half a dozen quantisation
levels. The question every team faces — and almost nobody answers properly — is
which combinations actually run, how fast, and what you give up.

**Your start script is the worked example.** Put it on screen. It already
encodes every decision this lab is about:

| Decision in the script | What it's trading |
|---|---|
| `IQ3_M` at 3.66 bpw, ~12 GB | Quality, for fitting a 27B model on a 16 GB card |
| `turbo3` KV cache (3-bit) | Cache precision, for a 196K context window |
| `-c 196608` | VRAM, for the ability to hold a large codebase in context |
| `-ngl 99` | Nothing — all layers on GPU, which is what you want |
| `--flash-attn on` | Nothing — strictly faster attention |

> "Somebody made five decisions in this file and every one of them was a
> trade. By the end of the hour you'll know what each one cost."

That reframing turns a config file they'd otherwise skim into the lesson.

## The core idea

Write the arithmetic on the board:

```
weights ≈ N billion params × Q bits ÷ 8  =  GB
```

Then the part people forget: **plus the KV cache**, which grows with context
length and batch size, and which is why a 196K window needs its own compression
scheme.

Work the host's numbers out loud: 27B at 3.66 bpw is roughly 12 GB of weights.
Add ~2.5 GB of 3-bit KV cache at full context. Add compute overhead. Call it
15 GB on a 16 GB card — which is why the script's comment says it "fits
comfortably" and means it *barely* fits.

## The challenges

**One: two different speeds get conflated constantly.** Time to first token is
how long before anything appears — that's what makes an interface feel
responsive. Tokens per second is how fast the rest arrives. You can have
excellent TTFT and dreadful throughput, or the reverse. Different problems,
different fixes.

**Two: running out of VRAM doesn't produce an error.** Layers spill to system
RAM and throughput collapses, often by 10x. Nothing fails. Nothing logs. It just
goes slow, and in production you find out from users.

**Three — and this is the one that matters for the rest of the weekend:**
smaller models are fine at prose and unreliable at structured output. That gap
is why Labs 3 through 8 use an API model, and it's much more convincing once
they've watched it happen than when you assert it.

## What the code has to do

**Detect the backend.** The script works against llama.cpp or Ollama, whichever
is listening. Worth pointing out: this is a real problem, not incidental
plumbing. "OpenAI-compatible" turns out to be a spectrum rather than a standard.

**Measure honestly.** Warm the model first — never benchmark a cold load, you're
timing disk I/O. Then stream the response and time the first token separately
from the rest.

**Accumulate across restarts.** `llama-server` holds exactly one model. So the
workflow is: run, restart the server with a different GGUF, run again with a
different `--label`, then `--compare`. Results persist to disk between runs.

**Test JSON reliability with no schema constraint.** This is the unaided
baseline. Lab 2 turns the constraint on, and the difference is the point.

## Running the room

Get `nvidia-smi -l 1` up in a second terminal on the big screen before you start
anything. People should be watching VRAM the whole hour.

Then deliberately break it: load the model and start a second generation
alongside the first. Watch memory fill and throughput fall off a cliff.

**Ask Friend 1:** *what does quantisation actually throw away, and why does the
model mostly still work?* He'll know about weight distributions and outlier
channels. This is his territory and it's genuinely interesting.

**Ask Friend 2:** *how would you detect that VRAM spill in production before
your users did?* There's no error to alert on. What's the metric? What's the
autoscaling policy? This is exactly the gap his track in `PORTFOLIO.md` targets.

## The punchline

> Local inference is cheap per token and expensive per unit of reliability.
> API inference is the reverse. Choose per workload, not per ideology.

## If you're short on time

Benchmark one model and skip the overload test. **Do not skip the JSON
reliability run** — it's the setup for Lab 2 and the whole justification for the
weekend's split between local and API models.
