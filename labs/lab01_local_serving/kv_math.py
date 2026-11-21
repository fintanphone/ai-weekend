#!/usr/bin/env python3
"""Lab 1 — pull the hidden numbers and do the VRAM arithmetic for real.

`ollama show` prints parameters, quantization and context length. It does NOT
print the three numbers that actually size the KV cache: layer count, KV-head
count and head dimension. They exist in the GGUF metadata; this fetches them
and does the sum.

    python kv_math.py                      # whatever Ollama has loaded
    python kv_math.py llama3.1:8b          # a named Ollama model
    python kv_math.py --gguf /path/to.gguf # straight from a file (llama.cpp)
    python kv_math.py llama3.1:8b --card 24

Two sources, same arithmetic:
  Ollama   POST /api/show with {"verbose": true} -> model_info
  llama.cpp  read the GGUF header with gguf-py
"""

import argparse
import json
import os
import sys

import requests

GiB = 1024 ** 3

# Effective bits per weight. A quant name is not its bit count: Q4_K_M is
# mixed, mostly Q4_K with some tensors at Q6_K, so it lands near 4.8.
BPW = {
    "F32": 32.0, "F16": 16.0, "BF16": 16.0,
    "Q8_0": 8.5, "Q6_K": 6.6,
    "Q5_K_M": 5.7, "Q5_K_S": 5.5, "Q5_0": 5.5, "Q5_1": 6.0,
    "Q4_K_M": 4.8, "Q4_K_S": 4.6, "Q4_0": 4.5, "Q4_1": 5.0,
    "Q3_K_L": 4.3, "Q3_K_M": 3.9, "Q3_K_S": 3.5,
    "IQ4_XS": 4.25, "IQ3_S": 3.6, "IQ3_M": 3.7, "IQ3_XXS": 3.1,
    "IQ2_M": 2.7, "IQ2_S": 2.5, "Q2_K": 3.0,
}

# general.file_type is an int, not a name. llama.cpp's llama_ftype enum.
FTYPE = {
    0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 7: "Q8_0", 8: "Q5_0", 9: "Q5_1",
    10: "Q2_K", 11: "Q3_K_S", 12: "Q3_K_M", 13: "Q3_K_L", 14: "Q4_K_S",
    15: "Q4_K_M", 16: "Q5_K_S", 17: "Q5_K_M", 18: "Q6_K", 19: "IQ2_XXS",
    20: "IQ2_XS", 21: "Q2_K_S", 22: "IQ3_XS", 23: "IQ3_XXS", 24: "IQ1_S",
    25: "IQ4_NL", 26: "IQ3_S", 27: "IQ3_M", 28: "IQ2_S", 29: "IQ2_M",
    30: "IQ4_XS", 31: "IQ1_M", 32: "BF16",
}


def from_ollama(model, host):
    """Ask Ollama for the GGUF metadata it already parsed."""
    r = requests.post(f"{host}/api/show",
                      json={"model": model, "verbose": True}, timeout=30)
    if r.status_code == 404:
        raise SystemExit(f"Ollama has no model named {model!r}.\n"
                         f"  'ollama list' shows what you have.")
    r.raise_for_status()
    d = r.json()
    info = d.get("model_info", {})
    arch = info.get("general.architecture", "llama")

    def g(key, *alts):
        for k in (key, *alts):
            if f"{arch}.{k}" in info:
                return info[f"{arch}.{k}"]
        return None

    details = d.get("details", {})
    params = info.get("general.parameter_count") or \
        _parse_params(details.get("parameter_size")
                      or info.get("general.size_label", ""))
    heads = g("attention.head_count")
    return dict(
        name=model,
        arch=arch,
        params=params,
        quant=details.get("quantization_level")
        or FTYPE.get(info.get("general.file_type"), "unknown"),
        layers=g("block_count"),
        heads=heads,
        kv_heads=g("attention.head_count_kv") or heads,
        embed=g("embedding_length"),
        key_len=g("attention.key_length"),
        val_len=g("attention.value_length"),
        attn_interval=g("full_attention_interval"),
        ssm=g("ssm.state_size"),
        max_ctx=g("context_length"),
        source=f"Ollama /api/show (verbose) at {host}",
    )


def from_gguf(path):
    """Read the header straight off the file — no server needed."""
    try:
        from gguf import GGUFReader
    except ImportError:
        raise SystemExit("pip install gguf")
    r = GGUFReader(path)
    kv = {}
    for field in r.fields.values():
        try:
            kv[field.name] = field.contents()
        except Exception:
            pass
    arch = kv.get("general.architecture", "llama")

    def g(key):
        return kv.get(f"{arch}.{key}")

    heads = g("attention.head_count")
    # Not every GGUF carries general.parameter_count; size_label ("27B") is
    # the usual fallback, and the filename is the last resort.
    params = kv.get("general.parameter_count") or \
        _parse_params(kv.get("general.size_label", ""))
    return dict(
        name=kv.get("general.name") or os.path.basename(path),
        arch=arch,
        params=params,
        quant=FTYPE.get(kv.get("general.file_type")) or _quant_from_name(path),
        layers=g("block_count"),
        heads=heads,
        kv_heads=g("attention.head_count_kv") or heads,
        embed=g("embedding_length"),
        key_len=g("attention.key_length"),
        val_len=g("attention.value_length"),
        attn_interval=g("full_attention_interval"),
        ssm=g("ssm.state_size"),
        max_ctx=g("context_length"),
        source=f"GGUF header of {path}",
    )


def from_server(url):
    """What a remote llama-server will tell you over HTTP — which is not enough.

    /v1/models gives n_params and n_embd; /props gives the allocated n_ctx.
    Neither exposes layer count or KV-head count, so the cache cannot be sized
    from HTTP alone. Those come from the startup log or the GGUF itself.
    """
    url = url.rstrip("/")
    meta, props = {}, {}
    try:
        d = requests.get(f"{url}/v1/models", timeout=10).json()
        meta = (d.get("data") or [{}])[0].get("meta") or {}
        name = (d.get("data") or [{}])[0].get("id", url)
    except (requests.RequestException, ValueError):
        raise SystemExit(f"No llama-server answering at {url}")
    try:
        props = requests.get(f"{url}/props", timeout=10).json()
    except (requests.RequestException, ValueError):
        pass
    gen = (props.get("default_generation_settings") or {})
    return dict(
        name=f"{name} (remote)",
        arch="unknown",
        params=meta.get("n_params"),
        quant=_quant_from_name(props.get("model_path", "")),
        layers=None, heads=None, kv_heads=None,
        embed=meta.get("n_embd"),
        key_len=None, val_len=None, attn_interval=None, ssm=None,
        max_ctx=gen.get("n_ctx") or meta.get("n_ctx_train"),
        slots=props.get("total_slots"),
        source=f"llama-server HTTP at {url}  (PARTIAL — see note)",
    )


def _parse_params(text):
    t = text.strip().upper().rstrip("B")
    try:
        return float(t) * 1e9
    except ValueError:
        return None


def _quant_from_name(path):
    up = os.path.basename(path).upper()
    for q in sorted(BPW, key=len, reverse=True):
        if q in up:
            return q
    return "unknown"


def report(m, card_gib, kv_bits):
    head_dim = m["key_len"] or (m["embed"] // m["heads"] if m["embed"] and
                                m["heads"] else None)
    missing = [k for k in ("layers", "kv_heads", "params") if not m.get(k)]
    if not head_dim:
        missing.append("head_dim")
    if missing:
        flags = {"layers": "--layers", "kv_heads": "--kv-heads",
                 "params": "--params", "head_dim": "--head-dim"}
        raise SystemExit(
            f"\n  Missing: {', '.join(missing)}\n"
            f"  Source was: {m['source']}\n\n"
            f"  A remote llama-server does not expose these over HTTP — only\n"
            f"  n_params and n_embd. Get them one of these ways:\n\n"
            f"    on the GPU box:  grep -E 'n_layer|n_head_kv|n_embd_head' "
            f"/tmp/llama-server.log\n"
            f"    or:              python kv_math.py --gguf /path/to/model.gguf\n\n"
            f"  Then type them in from anywhere — no server needed:\n"
            f"    python kv_math.py "
            + " ".join(f"{flags[k]} N" for k in missing) + "\n")

    bpw = BPW.get(str(m["quant"]).upper())
    weights = m["params"] * bpw / 8 if bpw else None
    kv_bytes = kv_bits / 8

    # K and V can have different widths; most models set them equal.
    k_dim = m["key_len"] or head_dim
    v_dim = m.get("val_len") or k_dim

    # Hybrid attention/SSM models put full attention on only every Nth layer.
    # The rest hold a fixed-size recurrent state that does NOT grow with
    # context, so counting all layers overstates the cache several times over.
    interval = m.get("attn_interval")
    attn_layers = m["layers"] // interval if interval else m["layers"]

    per_tok = attn_layers * (k_dim + v_dim) * m["kv_heads"] * kv_bytes

    print(f"\n  {m['name']}   ({m['arch']}, {m['quant']})")
    print(f"  source: {m['source']}\n")

    hand = m["arch"] == "manual"
    print("  The numbers you gave" if hand
          else "  What the tooling already told you")
    print(f"    parameters        {m['params']/1e9:.1f}B")
    print(f"    quantization      {m['quant']}"
          + (f"   ~{bpw} bits/weight effective" if bpw else "   (unknown bpw)"))
    if m["max_ctx"]:
        print(f"    context length    {m['max_ctx']:,}")
    if m["embed"]:
        print(f"    embedding length  {m['embed']}")

    print("" if hand else "\n  What it did NOT tell you")
    print(f"    layers            {m['layers']}")
    if m["heads"]:
        print(f"    attention heads   {m['heads']}")
    print(f"    KV heads          {m['kv_heads']}"
          + (f"   ({m['heads']//m['kv_heads']}:1 grouped-query)"
             if m["heads"] else ""))
    print(f"    head dimension    {k_dim}"
          + ("  (stored, NOT embedding/heads)" if m["key_len"]
             else "   (embedding / heads)"))
    if interval:
        print(f"    attention every   {interval} layers  ->  {attn_layers} "
              f"full-attention, {m['layers'] - attn_layers} recurrent/SSM")

    if weights:
        print(f"\n  Weights   {m['params']/1e9:.0f}e9 x {bpw} / 8 "
              f"= {weights/GiB:.2f} GiB")
    print(f"  KV/token  {attn_layers} x ({k_dim}+{v_dim}) x {m['kv_heads']} x "
          f"{kv_bytes:g} = {per_tok:,.0f} B = {per_tok/1024:.0f} KiB")
    if interval:
        naive = m["layers"] * (k_dim + v_dim) * m["kv_heads"] * kv_bytes
        print(f"            counting all {m['layers']} layers would say "
              f"{naive/1024:.0f} KiB — {naive/per_tok:.0f}x too much")
    if m.get("ssm"):
        print(f"            the {m['layers'] - attn_layers} SSM layers hold a "
              f"FIXED state; it does not grow with context")

    cap = card_gib * GiB
    print(f"\n  {'context':>10} {'KV cache':>12} {'+ weights':>12}   "
          f"on a {card_gib} GiB card")
    print("  " + "-" * 56)
    ctxs = [4096, 8192, 32768, 65536]
    if m["max_ctx"] and m["max_ctx"] not in ctxs:
        ctxs.append(m["max_ctx"])
    for ctx in sorted(ctxs):
        kv = ctx * per_tok
        tot = kv + (weights or 0)
        print(f"  {ctx:>10,} {kv/GiB:>9.2f} GiB {tot/GiB:>9.2f} GiB   "
              f"{'DOES NOT FIT' if tot > cap else 'fits'}")
    if kv_bits == 16:
        print(f"\n  KV cache is fp16 here. Quantising it (--kv-bits 8, or 4) "
              f"divides\n  every cache figure above — which is how a big model "
              f"gets a long context.")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?", help="Ollama model name")
    ap.add_argument("--gguf", help="read a .gguf file instead")
    ap.add_argument("--server", help="a running llama-server URL (partial data)")
    ap.add_argument("--host", default=os.environ.get(
        "OLLAMA_HOST", "http://localhost:11434").rstrip("/"))
    # Type the numbers in yourself — works with no server at all, which is how
    # anyone on a laptop explores the model on the big screen.
    ap.add_argument("--layers", type=int)
    ap.add_argument("--kv-heads", type=int)
    ap.add_argument("--head-dim", type=int)
    ap.add_argument("--params", type=float, help="in billions, e.g. 27")
    ap.add_argument("--quant", help="e.g. IQ3_M, Q4_K_M")
    ap.add_argument("--attn-interval", type=int,
                    help="hybrid models: attention on every Nth layer")
    ap.add_argument("--max-ctx", type=int)
    ap.add_argument("--card", type=float, default=16, help="VRAM in GiB")
    ap.add_argument("--kv-bits", type=float, default=16,
                    help="KV cache precision: 16, 8, 4...")
    a = ap.parse_args()

    manual = dict(layers=a.layers, kv_heads=a.kv_heads, key_len=a.head_dim,
                  params=a.params * 1e9 if a.params else None, quant=a.quant,
                  attn_interval=a.attn_interval, max_ctx=a.max_ctx)

    if a.gguf:
        meta = from_gguf(a.gguf)
    elif a.server:
        meta = from_server(a.server)
    elif all(manual[k] for k in ("layers", "kv_heads", "key_len", "params")):
        # everything given by hand: no server needed at all
        meta = dict(name="(from the numbers you gave)", arch="manual",
                    heads=None, embed=None, val_len=None, ssm=None,
                    source="typed in by hand", **manual)
    else:
        name = a.model
        if not name:
            r = requests.get(f"{a.host}/api/tags", timeout=10)
            r.raise_for_status()
            names = [m["name"] for m in r.json().get("models", [])]
            if not names:
                raise SystemExit("No models pulled. Try: ollama pull llama3.1:8b")
            name = names[0]
            print(f"  (no model given — using {name!r}; "
                  f"others: {', '.join(names[1:]) or 'none'})")
        meta = from_ollama(name, a.host)

    # A hand-given value always wins over whatever was detected.
    for k, v in manual.items():
        if v is not None:
            meta[k] = v

    report(meta, a.card, a.kv_bits)
