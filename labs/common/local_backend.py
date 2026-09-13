"""One adapter, two local backends.

The host machine runs llama.cpp (`llama-server`), which speaks an
OpenAI-compatible API on /v1. The friends' laptops are more likely to run
Ollama, which speaks its own API on /api. Rather than write every lab twice,
this module detects which one is listening and papers over the differences.

    from local_backend import connect
    be = connect()                       # reads LOCAL_API_BASE from .env
    print(be.kind, be.model_name)
    out = be.chat([{"role": "user", "content": "hi"}])

Why this is more than plumbing: "OpenAI-compatible" turns out to be a
spectrum, not a standard. llama.cpp accepts at least three different shapes
for schema-constrained output depending on build, and forks vary. The
`probe_schema_support()` method finds out empirically instead of guessing,
which is itself a useful thing for the group to see.
"""

from __future__ import annotations

import json
import os
import time

import requests


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------

def connect(base_url: str | None = None, timeout: float = 5.0) -> "Backend":
    """Find whichever local server is listening and return an adapter."""
    base = (base_url or os.environ.get("LOCAL_API_BASE") or "http://localhost:8080").rstrip("/")

    # llama.cpp: /props is llama.cpp-specific and cheap
    try:
        r = requests.get(f"{base}/props", timeout=timeout)
        if r.ok:
            props = r.json()
            name = (props.get("model_path") or "").split("/")[-1] or "llama.cpp model"
            return LlamaCppBackend(base, name, props)
    except requests.RequestException:
        pass

    # llama.cpp behind a proxy, or anything else OpenAI-shaped
    try:
        r = requests.get(f"{base}/v1/models", timeout=timeout)
        if r.ok:
            data = r.json().get("data") or [{}]
            return LlamaCppBackend(base, data[0].get("id", "unknown"), {})
    except requests.RequestException:
        pass

    # Ollama
    ollama = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    for candidate in (base, ollama):
        try:
            r = requests.get(f"{candidate}/api/tags", timeout=timeout)
            if r.ok:
                return OllamaBackend(candidate, None)
        except requests.RequestException:
            continue

    raise ConnectionError(
        f"No local model server found.\n"
        f"  Tried llama.cpp at {base} and Ollama at {ollama}.\n"
        f"  Start one, or set LOCAL_API_BASE in .env."
    )


class NotSupported(Exception):
    """The backend or model cannot do this (e.g. no tool template)."""


# --------------------------------------------------------------------------

class Backend:
    kind = "unknown"
    model_name = "unknown"

    def chat(self, messages, schema=None, tools=None, temperature=0.2,
             max_tokens=800, think=False) -> dict:
        """Returns {"text": str, "tool_calls": list, "usage": dict}."""
        raise NotImplementedError

    def stream_tokens(self, prompt: str, max_tokens: int = 300) -> dict:
        """Times a generation. Returns ttft_s, tokens_per_s, tokens, total_s."""
        raise NotImplementedError

    def json_from(self, out: dict):
        """Best-effort parse of a chat response into a dict.

        Deliberately generous. Method A in Lab 2 is meant to fail on genuinely
        malformed output, not on a model saying "Sure! Here you go:" first —
        so we strip fences wherever they appear and fall back to the outermost
        balanced braces. Every recovery here is cleanup a real codebase would
        end up writing, which is itself the argument for constrained decoding.
        """
        text = (out.get("text") or "").strip()
        if not text:
            return None

        # Qwen-style reasoning blocks, if thinking wasn't disabled
        if "</think>" in text:
            text = text.split("</think>", 1)[1].strip()

        # a fenced block anywhere in the response
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].removeprefix("json").removeprefix("JSON").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # last resort: the outermost balanced {...}
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        return None
        return None


# --------------------------------------------------------------------------
# llama.cpp / llama-server
# --------------------------------------------------------------------------

class LlamaCppBackend(Backend):
    kind = "llamacpp"

    def __init__(self, base: str, model_name: str, props: dict):
        self.base = base
        self.model_name = model_name
        self.props = props
        self._schema_style: str | None = None

    # -- schema shapes, in the order we'll try them ------------------------
    SCHEMA_STYLES = {
        # OpenAI's own nested form
        "openai": lambda s: {"response_format": {
            "type": "json_schema",
            "json_schema": {"name": "extract", "strict": True, "schema": s}}},
        # llama.cpp's documented flat form
        "flat": lambda s: {"response_format": {"type": "json_schema", "schema": s}},
        # the older json_object + schema form, widely supported
        "json_object": lambda s: {"response_format": {"type": "json_object", "schema": s}},
        # top-level, read directly by llama.cpp
        "toplevel": lambda s: {"json_schema": s},
    }

    def _probe_body(self, schema: dict) -> dict:
        """Shared probe request. Crucially this sends the thinking-off flags and
        a generous token cap: a hybrid-reasoning model with thinking ON will
        spend hundreds of tokens in a <think> block before emitting any JSON,
        and a tight cap truncates it mid-thought. That looks exactly like
        'schema unsupported' and isn't."""
        return {
            "messages": [{"role": "user",
                          "content": "Reply with ok set to true. JSON only."}],
            "temperature": 0.0,
            "max_tokens": 512,
            "chat_template_kwargs": {"enable_thinking": False},
            "reasoning_budget": 0,
        }

    def probe_schema_support(self, verbose: bool = False) -> str | None:
        """Find which constrained-output path this build actually honours.

        Tries the four response_format shapes on /v1/chat/completions, then
        falls back to llama.cpp's native /completion endpoint, which has
        supported json_schema for far longer than the OpenAI layer has.

        Returns the style name, or None. Cached after the first success.
        """
        if self._schema_style:
            return self._schema_style

        tiny = {"type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"]}

        for style, build in self.SCHEMA_STYLES.items():
            try:
                out = self._post({**self._probe_body(tiny), **build(tiny)})
            except NotSupported as exc:
                if verbose:
                    print(f"    {style:<14} rejected: {str(exc)[:90]}")
                continue
            except requests.RequestException as exc:
                if verbose:
                    print(f"    {style:<14} error: {type(exc).__name__}")
                continue

            parsed = self.json_from(out)
            if isinstance(parsed, dict) and "ok" in parsed:
                if verbose:
                    print(f"    {style:<14} WORKS")
                self._schema_style = style
                return style
            if verbose:
                print(f"    {style:<14} accepted but unconstrained: "
                      f"{(out.get('text') or '')[:70]!r}")

        # Native endpoint. Older and more reliable than the OpenAI shim.
        try:
            out = self._native_completion(
                [{"role": "user", "content": "Reply with ok set to true. JSON only."}],
                schema=tiny, max_tokens=512, temperature=0.0)
            parsed = self.json_from(out)
            if isinstance(parsed, dict) and "ok" in parsed:
                if verbose:
                    print(f"    {'native':<14} WORKS  (/completion + json_schema)")
                self._schema_style = "native"
                return "native"
            if verbose:
                print(f"    {'native':<14} accepted but unconstrained")
        except (NotSupported, requests.RequestException) as exc:
            if verbose:
                print(f"    {'native':<14} unavailable: {type(exc).__name__}")

        return None

    def _apply_template(self, messages: list) -> str:
        """Render messages through the server's chat template."""
        r = requests.post(f"{self.base}/apply-template",
                          json={"messages": messages}, timeout=60)
        if r.ok:
            data = r.json()
            prompt = data.get("prompt")
            if isinstance(prompt, str):
                return prompt
        # crude fallback if the endpoint isn't there
        return "\n\n".join(f"{m['role']}: {m['content']}" for m in messages) + "\n\nassistant:"

    def _native_completion(self, messages, schema=None, max_tokens=800,
                           temperature=0.2, think=False) -> dict:
        body = {
            "prompt": self._apply_template(messages),
            "n_predict": max_tokens,
            "temperature": temperature,
            "stream": False,
            "cache_prompt": True,
        }
        if schema is not None:
            body["json_schema"] = schema
        if not think:
            body["reasoning_budget"] = 0

        r = requests.post(f"{self.base}/completion", json=body, timeout=600)
        if r.status_code in (400, 404, 501):
            raise NotSupported(r.text[:200])
        r.raise_for_status()
        data = r.json()
        return {"text": data.get("content") or "", "tool_calls": [],
                "usage": {"input_tokens": data.get("tokens_evaluated", 0),
                          "output_tokens": data.get("tokens_predicted", 0)}}

    def _post(self, payload: dict) -> dict:
        body = {"model": self.model_name, "stream": False, **payload}
        r = requests.post(f"{self.base}/v1/chat/completions", json=body, timeout=600)
        if r.status_code == 400:
            raise NotSupported(r.text[:200])
        r.raise_for_status()
        data = r.json()
        msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
        return {
            "text": msg.get("content") or "",
            "tool_calls": msg.get("tool_calls") or [],
            "usage": data.get("usage", {}),
        }

    def chat(self, messages, schema=None, tools=None, temperature=0.2,
             max_tokens=800, think=False) -> dict:
        # The native /completion path can't do tools, so only use it for
        # schema-only requests where it's the style that actually works.
        if schema is not None and tools is None:
            if self.probe_schema_support() == "native":
                return self._native_completion(messages, schema=schema,
                                               max_tokens=max_tokens,
                                               temperature=temperature, think=think)

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Qwen3.x is a hybrid thinking model and defaults to thinking ON.
        # For extraction and tool use you want it OFF: it burns tokens, slows
        # everything down, and its reasoning block confuses naive parsers.
        if not think:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
            payload["reasoning_budget"] = 0

        if schema is not None:
            style = self.probe_schema_support()
            if style is None:
                raise NotSupported("this build honours no constrained-output path")
            if style == "native":
                raise NotSupported("native path cannot be combined with tools")
            payload.update(self.SCHEMA_STYLES[style](schema))

        if tools is not None:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        return self._post(payload)

    def stream_tokens(self, prompt: str, max_tokens: int = 300) -> dict:
        start = time.perf_counter()
        first = None
        n = 0
        chunks = []

        r = requests.post(
            f"{self.base}/v1/chat/completions",
            json={"model": self.model_name,
                  "messages": [{"role": "user", "content": prompt}],
                  "stream": True, "max_tokens": max_tokens, "temperature": 0.3,
                  "chat_template_kwargs": {"enable_thinking": False},
                  "reasoning_budget": 0},
            stream=True, timeout=600,
        )
        r.raise_for_status()

        for line in r.iter_lines():
            if not line or not line.startswith(b"data: "):
                continue
            payload = line[6:]
            if payload.strip() == b"[DONE]":
                break
            try:
                delta = json.loads(payload)["choices"][0].get("delta", {})
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
            piece = delta.get("content")
            if piece:
                if first is None:
                    first = time.perf_counter()
                n += 1
                chunks.append(piece)

        end = time.perf_counter()
        gen = (end - first) if first else float("nan")
        return {"ttft_s": (first - start) if first else float("nan"),
                "total_s": end - start, "tokens": n,
                "tokens_per_s": n / gen if gen and gen > 0 else 0.0,
                "text": "".join(chunks)}


# --------------------------------------------------------------------------
# Ollama
# --------------------------------------------------------------------------

class OllamaBackend(Backend):
    kind = "ollama"

    def __init__(self, base: str, model: str | None):
        self.base = base
        self.model_name = model or os.environ.get("LOCAL_MODEL_MID", "qwen3:8b")

    def use_model(self, model: str) -> "OllamaBackend":
        self.model_name = model
        return self

    def probe_schema_support(self) -> str | None:
        return "format"          # Ollama has had this since 0.5

    def chat(self, messages, schema=None, tools=None, temperature=0.2,
             max_tokens=800, think=False) -> dict:
        body = {"model": self.model_name, "messages": messages, "stream": False,
                "think": think,
                "options": {"temperature": temperature, "num_predict": max_tokens}}
        if schema is not None:
            body["format"] = schema
        if tools is not None:
            body["tools"] = tools

        r = requests.post(f"{self.base}/api/chat", json=body, timeout=600)
        if r.status_code == 400:
            raise NotSupported(r.text[:200])
        r.raise_for_status()
        data = r.json()
        msg = data.get("message", {})
        return {"text": msg.get("content") or "",
                "tool_calls": msg.get("tool_calls") or [],
                "usage": {"input_tokens": data.get("prompt_eval_count", 0),
                          "output_tokens": data.get("eval_count", 0)}}

    def stream_tokens(self, prompt: str, max_tokens: int = 300) -> dict:
        start = time.perf_counter()
        first = None
        n = 0
        chunks = []

        r = requests.post(
            f"{self.base}/api/generate",
            json={"model": self.model_name, "prompt": prompt, "stream": True,
                  "think": False,
                  "options": {"num_predict": max_tokens, "temperature": 0.3}},
            stream=True, timeout=600,
        )
        r.raise_for_status()

        for line in r.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            piece = chunk.get("response", "")
            if piece:
                if first is None:
                    first = time.perf_counter()
                n += 1
                chunks.append(piece)
            if chunk.get("done"):
                break

        end = time.perf_counter()
        gen = (end - first) if first else float("nan")
        return {"ttft_s": (first - start) if first else float("nan"),
                "total_s": end - start, "tokens": n,
                "tokens_per_s": n / gen if gen and gen > 0 else 0.0,
                "text": "".join(chunks)}


# --------------------------------------------------------------------------

def normalise_tool_args(call: dict):
    """Tool-call arguments arrive as a JSON string or an object, backend
    depending. Flatten both to a dict."""
    fn = call.get("function", call)
    args = fn.get("arguments", {})
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return None
    return args


def diagnose(base_url: str | None = None) -> None:
    """Print exactly what this server supports, and why anything fails."""
    print()
    try:
        be = connect(base_url)
    except ConnectionError as exc:
        print(f"\033[91m{exc}\033[0m\n")
        return

    print(f"  backend   {be.kind}")
    print(f"  model     {be.model_name}")
    print(f"  base      {be.base}")

    try:
        out = be.chat([{"role": "user", "content": "Say the single word: ready"}],
                      max_tokens=64)
        print(f"  plain     OK — {out['text'].strip()[:50]!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"  plain     \033[91mFAILED — {type(exc).__name__}: {exc}\033[0m")
        return

    print("\n  constrained output — trying each path in turn:")
    style = be.probe_schema_support(verbose=True)
    if style:
        print(f"\n  \033[92m→ using: {style}\033[0m")
    else:
        print("\n  \033[93m→ none worked. Lab 2b method B will be skipped;"
              " A and C still run.\033[0m")

    print("\n  tool calling:")
    tool = [{"type": "function", "function": {
        "name": "ping", "description": "Reply to a ping.",
        "parameters": {"type": "object",
                       "properties": {"msg": {"type": "string"}},
                       "required": ["msg"]}}}]
    try:
        out = be.chat([{"role": "user", "content": "Call ping with msg='hello'."}],
                      tools=tool, max_tokens=256)
        if out["tool_calls"]:
            args = normalise_tool_args(out["tool_calls"][0])
            print(f"    \033[92mWORKS\033[0m — {args}")
        else:
            print(f"    \033[93mno tool call made\033[0m — replied {out['text'][:60]!r}")
            print("    if this persists, check the server was started with --jinja")
    except NotSupported as exc:
        print(f"    \033[93mrejected\033[0m — {str(exc)[:90]}")
        print("    usually means no --jinja, or the model has no tool template")
    except Exception as exc:  # noqa: BLE001
        print(f"    \033[91m{type(exc).__name__}: {exc}\033[0m")
    print()


if __name__ == "__main__":
    import sys
    diagnose(sys.argv[1] if len(sys.argv) > 1 else None)
