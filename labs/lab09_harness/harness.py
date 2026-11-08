#!/usr/bin/env python3
"""A harness. About 180 lines, and none of it is clever.

Lab 3's loop was twenty lines and it worked. This is that same loop with the
five things wrapped round it that you need before you would let it run while
you are asleep:

    1. a tool REGISTRY      - declare tools once, reuse them anywhere
    2. OBSERVABILITY        - every call recorded, so you can debug the trace
    3. a BUDGET             - a token ceiling, checked before each call
    4. RELIABILITY          - timeouts, retries with backoff, a turn limit
    5. a POLICY             - what may run unattended, decided by rule not if

Read it top to bottom. Notice how little of it is about AI. Rate limiting,
retries, audit logs, spend caps and authorisation are the same five problems
any service that calls a remote API has had for thirty years. That is the
point, and it is why a cloud engineer walks into this field already holding
most of the answers.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path


# ==========================================================================
#  1. REGISTRY — tools as data, not as a dict buried in a loop
# ==========================================================================

class Registry:
    """Holds tools. Knows how to describe them to a model and how to run them.

    In Lab 3 the tool list and the dispatch dict were two separate things that
    had to be kept in step by hand. Here they are one thing, which also means
    the model can never be offered a tool that has no implementation.
    """

    def __init__(self, tools: list[dict]):
        self._by_name = {t["name"]: t for t in tools}

    def schemas(self) -> list[dict]:
        """What the model sees."""
        return [t["schema"] for t in self._by_name.values()]

    def names(self) -> list[str]:
        return list(self._by_name)

    def is_destructive(self, name: str) -> bool:
        tool = self._by_name.get(name)
        return bool(tool and tool.get("destructive"))

    def call(self, name: str, arguments: dict) -> str:
        tool = self._by_name.get(name)
        if tool is None:
            # The model asked for something that does not exist. Tell it so,
            # as a normal result, rather than raising. It can recover.
            return f"ERROR: no tool named {name!r}. Available: {', '.join(self._by_name)}"
        return tool["func"](**arguments)


# ==========================================================================
#  2. POLICY — authorisation as a rule, not an if-statement
# ==========================================================================

@dataclass
class Policy:
    """Decides what may run without a human.

    Lab 3 had `if block.name == "delete_file"` hardcoded in the loop. That
    does not survive a second tool, let alone a second task. A policy is data:
    you can print it, test it, diff it in review, and load it per environment.
    """

    mode: str = "ask"                   # "allow-all" | "ask" | "deny-destructive"
    always_allow: list[str] = field(default_factory=list)

    def decide(self, name: str, destructive: bool) -> str:
        """Returns 'allow', 'ask' or 'deny'."""
        if name in self.always_allow:
            return "allow"
        if not destructive:
            return "allow"
        if self.mode == "allow-all":
            return "allow"
        if self.mode == "deny-destructive":
            return "deny"
        return "ask"


# ==========================================================================
#  3. BUDGET — a ceiling you set before you need one
# ==========================================================================

@dataclass
class Budget:
    """A token ceiling, checked BEFORE each call rather than after.

    Checking afterwards tells you how much you already spent. Checking before
    is the difference between a cap and a receipt.
    """

    max_tokens: int = 50_000
    spent: int = 0

    def would_exceed(self, estimate: int) -> bool:
        return self.spent + estimate > self.max_tokens

    def add(self, tokens: int) -> None:
        self.spent += tokens

    def remaining(self) -> int:
        return max(0, self.max_tokens - self.spent)


# ==========================================================================
#  4. THE RUN RECORD — what you get back, and what you can debug from
# ==========================================================================

@dataclass
class Run:
    run_id: str
    task: str
    answer: str = ""
    stopped_because: str = ""      # "finished" | "turn-limit" | "budget" | "error"
    turns: int = 0
    tools_run: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    seconds: float = 0.0
    events: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        return (f"{self.stopped_because}  ·  {self.turns} turns  ·  "
                f"{self.tools_run} tool calls  ·  "
                f"{self.tokens_in + self.tokens_out} tokens  ·  "
                f"{self.seconds:.1f}s")


# ==========================================================================
#  5. THE HARNESS
# ==========================================================================

class Harness:
    """Lab 3's loop, with the five concerns above wrapped round it."""

    def __init__(self, backend, registry: Registry, system: str,
                 policy: Policy | None = None, budget: Budget | None = None,
                 max_turns: int = 10, tool_timeout: float = 30.0,
                 retries: int = 2, log_path: str | Path | None = None,
                 approve=None, on_event=None):
        self.backend = backend
        self.registry = registry
        self.system = system
        self.policy = policy or Policy()
        self.budget = budget or Budget()
        self.max_turns = max_turns
        self.tool_timeout = tool_timeout
        self.retries = retries
        self.log_path = Path(log_path) if log_path else None
        self.approve = approve or (lambda name, args: False)
        self.on_event = on_event or (lambda e: None)

    # -- observability ----------------------------------------------------

    def _record(self, run: Run, kind: str, **fields):
        """One structured event. Everything that happens goes through here.

        A trace is not a nice-to-have. You cannot debug an agent from its
        final answer - by then the interesting part has already happened.
        """
        event = {"ts": round(time.time(), 3), "run_id": run.run_id,
                 "turn": run.turns, "kind": kind, **fields}
        run.events.append(event)
        self.on_event(event)
        if self.log_path:
            with self.log_path.open("a") as fh:
                fh.write(json.dumps(event) + "\n")

    # -- reliability ------------------------------------------------------

    def _call_model(self, run: Run, messages):
        """One model call, with retries and backoff on transient failures."""
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                return self.backend.chat(
                    messages, tools=self.registry.schemas(),
                    temperature=0.0, max_tokens=800)
            except Exception as exc:                      # noqa: BLE001
                last_error = exc
                wait = 2 ** attempt
                self._record(run, "model_retry", attempt=attempt + 1,
                             error=type(exc).__name__, waiting=wait)
                if attempt < self.retries:
                    time.sleep(wait)
        raise RuntimeError(f"model call failed after {self.retries + 1} attempts: "
                           f"{last_error}")

    def _run_tool(self, run: Run, name: str, arguments: dict) -> str:
        """One tool call, with retries. A failure becomes a RESULT, not a crash:
        the model is told what went wrong and gets a chance to recover."""
        for attempt in range(self.retries + 1):
            started = time.perf_counter()
            try:
                output = self.registry.call(name, arguments)
                self._record(run, "tool_ok", tool=name, args=arguments,
                             seconds=round(time.perf_counter() - started, 3),
                             chars=len(output))
                return output
            except Exception as exc:                      # noqa: BLE001
                self._record(run, "tool_error", tool=name, args=arguments,
                             attempt=attempt + 1, error=str(exc))
                if attempt < self.retries:
                    time.sleep(2 ** attempt)
        return (f"ERROR: {name} failed after {self.retries + 1} attempts. "
                f"Do not retry it; report that you could not complete the task.")

    # -- the loop ---------------------------------------------------------

    def run(self, task: str) -> Run:
        run = Run(run_id=uuid.uuid4().hex[:8], task=task)
        started = time.perf_counter()

        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": task}]

        self._record(run, "run_start", task=task,
                     tools=self.registry.names(),
                     policy=self.policy.mode,
                     budget=self.budget.max_tokens)

        while True:
            if run.turns >= self.max_turns:
                run.stopped_because = "turn-limit"
                break

            # The budget is checked BEFORE spending, with a rough estimate.
            estimate = sum(len(str(m.get("content") or "")) for m in messages) // 4
            if self.budget.would_exceed(estimate):
                self._record(run, "budget_stop", estimate=estimate,
                             remaining=self.budget.remaining())
                run.stopped_because = "budget"
                break

            run.turns += 1

            try:
                reply = self._call_model(run, messages)
            except RuntimeError as exc:
                self._record(run, "run_error", error=str(exc))
                run.stopped_because = "error"
                run.answer = str(exc)
                break

            usage = reply.get("usage") or {}
            tin = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
            tout = usage.get("completion_tokens") or usage.get("output_tokens") or 0
            run.tokens_in += tin
            run.tokens_out += tout
            self.budget.add(tin + tout)

            text = (reply.get("text") or "").strip()
            calls = reply.get("tool_calls") or []
            self._record(run, "model_reply", tokens_in=tin, tokens_out=tout,
                         said=text[:200], wants=[c["function"]["name"] for c in calls])

            if not calls:
                run.answer = text
                run.stopped_because = "finished"
                break

            messages.append({"role": "assistant", "content": text or None,
                             "tool_calls": calls})

            for call in calls:
                name = call["function"]["name"]
                raw = call["function"]["arguments"]
                arguments = json.loads(raw) if isinstance(raw, str) else raw

                verdict = self.policy.decide(name, self.registry.is_destructive(name))
                self._record(run, "policy", tool=name, verdict=verdict)

                if verdict == "deny":
                    output = ("REFUSED by policy: this tool may not run "
                              "unattended. Report that you could not complete "
                              "the task.")
                elif verdict == "ask" and not self.approve(name, arguments):
                    output = ("REFUSED by the operator. Report that you could "
                              "not complete the task.")
                else:
                    output = self._run_tool(run, name, arguments)
                    run.tools_run += 1

                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": output})

        run.seconds = time.perf_counter() - started
        self._record(run, "run_end", stopped_because=run.stopped_because,
                     turns=run.turns, tokens=run.tokens_in + run.tokens_out,
                     seconds=round(run.seconds, 2))
        return run
