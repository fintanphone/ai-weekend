#!/usr/bin/env python3
"""Lab 3 — an agent, by hand, no frameworks.

This is the whole thing. Everything else in the field is a variation on it.

    python agent.py "How many Python files are in the workspace, and how many
                     lines does the largest one have?"
    python agent.py --verbose "..."     # show the raw message list each turn

Read it top to bottom before you run it. It's about 120 lines including the
tools, and there is nothing hidden.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
WORKSPACE = Path(__file__).parent / "workspace"

client = anthropic.Anthropic()


# ==========================================================================
# 1. THE TOOLS
#
# A tool is two things: a JSON Schema the model reads, and a Python function
# the model never sees. The model chooses; your code executes. Always.
# ==========================================================================

TOOLS = [
    {
        "name": "list_files",
        "description": (
            "List files in the workspace directory. Use this first if you need "
            "to know what files exist before reading them."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern, e.g. '*.py' or '**/*.csv'. Defaults to '*'.",
                }
            },
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a text file in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the workspace."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "calculate",
        "description": (
            "Evaluate an arithmetic expression. Use this for any arithmetic "
            "rather than working it out yourself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "e.g. '(1204 * 3) / 7'"}
            },
            "required": ["expression"],
        },
    },
]


def tool_list_files(pattern: str = "*") -> str:
    files = sorted(p for p in WORKSPACE.glob(pattern) if p.is_file())
    if not files:
        return f"No files matching {pattern!r}."
    return "\n".join(f"{p.relative_to(WORKSPACE)} ({p.stat().st_size} bytes)" for p in files)


def tool_read_file(path: str) -> str:
    target = (WORKSPACE / path).resolve()

    # Containment check. Without this, path='../../.env' reads your API key.
    # Note where this lives: in YOUR code, not in the model's instructions.
    if not target.is_relative_to(WORKSPACE.resolve()):
        return "ERROR: path escapes the workspace. Refused."
    if not target.exists():
        return f"ERROR: {path} does not exist."

    content = target.read_text(errors="replace")
    if len(content) > 8000:
        return content[:8000] + f"\n\n[truncated — file is {len(content)} chars]"
    return content


def tool_calculate(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "ERROR: expression contains disallowed characters."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"


DISPATCH = {
    "list_files": tool_list_files,
    "read_file": tool_read_file,
    "calculate": tool_calculate,
}


# ==========================================================================
# 2. THE LOOP
#
# This is the agent. Twenty-five lines. That's genuinely all it is.
# ==========================================================================

SYSTEM = """You are a careful assistant with access to a small file workspace.

Work step by step. Use tools rather than guessing — if you need to know what
files exist, list them; if you need arithmetic, calculate it. When you have
enough information, give a direct answer and stop calling tools."""


def run_agent(task: str, max_turns: int = 10, verbose: bool = False) -> str:
    messages = [{"role": "user", "content": task}]

    for turn in range(1, max_turns + 1):
        print(f"\n\033[90m─── turn {turn} ───\033[0m")

        if verbose:
            print(f"\033[90m{json.dumps(messages, indent=2, default=str)[:1500]}\033[0m")

        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        # Show the model's reasoning as it goes.
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\033[94m{block.text.strip()}\033[0m")

        # The model is done when it stops asking for tools.
        if response.stop_reason != "tool_use":
            final = "".join(b.text for b in response.content if b.type == "text")
            print(f"\n\033[92m✓ finished in {turn} turn(s)\033[0m")
            return final

        # Append the model's turn verbatim. The API is stateless — if you don't
        # send it back, it never happened.
        messages.append({"role": "assistant", "content": response.content})

        # Run every tool the model asked for, collect the results.
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"\033[93m→ {block.name}({json.dumps(block.input)})\033[0m")
            fn = DISPATCH.get(block.name)
            output = fn(**block.input) if fn else f"ERROR: no tool named {block.name}"
            preview = output if len(output) < 300 else output[:300] + " […]"
            print(f"\033[90m← {preview}\033[0m")

            results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": output}
            )

        messages.append({"role": "user", "content": results})

    return "Hit the turn limit without finishing."


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", default=(
        "How many Python files are in the workspace, and how many total lines "
        "do they contain between them?"
    ))
    ap.add_argument("--max-turns", type=int, default=10)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not WORKSPACE.exists():
        print(f"Workspace missing. Run: python make_workspace.py", file=sys.stderr)
        sys.exit(1)

    print(f"\n\033[1mTask:\033[0m {args.task}")
    answer = run_agent(args.task, args.max_turns, args.verbose)
    print(f"\n\033[1mAnswer:\033[0m {answer}\n")
