#!/usr/bin/env python3
"""Lab 5 — progressive disclosure, implemented from scratch.

The point of this file is to show there is no magic. A skill is a folder with a
markdown file in it. "Progressive disclosure" is: put the description in the
system prompt, and give the model a tool that reads the rest.

    python skill_runner.py "profile the shipments file"
    python skill_runner.py --no-skills "profile the shipments file"   # the contrast
    python skill_runner.py --show-context "..."                       # token accounting
"""

import argparse
import json
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
HERE = Path(__file__).parent
SKILLS_DIR = HERE / "skills"
DATA_DIR = HERE.parent / "lab03_agent_loop" / "workspace"

client = anthropic.Anthropic()


# --------------------------------------------------------------------------
# Discovery — read ONLY the frontmatter. This is level 1 of disclosure.
# --------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, match.group(2)


def discover_skills() -> dict[str, dict]:
    skills = {}
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        meta, body = parse_frontmatter(path.read_text())
        name = meta.get("name", path.parent.name)
        skills[name] = {
            "name": name,
            "description": meta.get("description", ""),
            "body": body,
            "path": path,
        }
    return skills


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------

def build_tools(skills: dict) -> list[dict]:
    tools = [
        {
            "name": "read_file",
            "description": "Read a data file from the workspace.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        }
    ]
    if skills:
        tools.append(
            {
                "name": "read_skill",
                "description": (
                    "Load the full instructions for one of the available skills. "
                    "Call this before starting work if a skill is relevant."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "enum": sorted(skills)}
                    },
                    "required": ["name"],
                },
            }
        )
    return tools


def tool_read_file(path: str) -> str:
    target = (DATA_DIR / path).resolve()
    if not target.is_relative_to(DATA_DIR.resolve()):
        return "ERROR: path escapes the workspace."
    if not target.exists():
        available = ", ".join(p.name for p in DATA_DIR.glob("*"))
        return f"ERROR: not found. Available: {available}"
    return target.read_text(errors="replace")[:8000]


# --------------------------------------------------------------------------
# System prompt — level 1: names and descriptions only
# --------------------------------------------------------------------------

BASE_SYSTEM = "You are a data analyst assistant with access to a small workspace."

SKILLS_BLOCK = """

## Available skills

You have skills available. Each is a set of detailed instructions you can load
on demand. Only the name and description are shown here. If a skill is relevant
to the task, call `read_skill` to load its full instructions BEFORE you start
work, then follow them exactly.

{listing}
"""


def build_system(skills: dict) -> str:
    if not skills:
        return BASE_SYSTEM
    listing = "\n".join(f"- **{s['name']}**: {s['description']}" for s in skills.values())
    return BASE_SYSTEM + SKILLS_BLOCK.format(listing=listing)


# --------------------------------------------------------------------------

def run(task: str, use_skills: bool, show_context: bool, max_turns: int = 8) -> None:
    skills = discover_skills() if use_skills else {}
    system = build_system(skills)
    tools = build_tools(skills)
    messages = [{"role": "user", "content": task}]

    if show_context:
        full = sum(len(s["body"]) for s in skills.values())
        print("\n\033[95m--- context accounting ---\033[0m")
        print(f"skills discovered:        {len(skills)}")
        print(f"system prompt chars:      {len(system)}")
        print(f"full skill bodies chars:  {full}   \033[90m(NOT loaded yet)\033[0m")
        if full:
            print(f"saved up front:           {100 * full / (full + len(system)):.0f}%")
        print("\033[95m--------------------------\033[0m")

    for turn in range(1, max_turns + 1):
        print(f"\n\033[90m─── turn {turn} ───\033[0m")
        response = client.messages.create(
            model=MODEL, max_tokens=3000, system=system, tools=tools, messages=messages
        )

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(block.text.strip())

        if response.stop_reason != "tool_use":
            print(f"\n\033[92m✓ done in {turn} turn(s)\033[0m")
            return

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "read_skill":
                name = block.input["name"]
                out = skills[name]["body"] if name in skills else f"ERROR: no skill {name!r}"
                print(f"\033[96m→ read_skill({name})  [+{len(out)} chars into context]\033[0m")
            else:
                out = tool_read_file(**block.input)
                print(f"\033[93m→ {block.name}({json.dumps(block.input)})\033[0m")

            results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        messages.append({"role": "user", "content": results})

    print("\n\033[91mHit turn limit.\033[0m")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", default="Profile the shipments.csv file for me.")
    ap.add_argument("--no-skills", action="store_true", help="run without skills, for contrast")
    ap.add_argument("--show-context", action="store_true")
    args = ap.parse_args()

    print(f"\n\033[1mTask:\033[0m {args.task}")
    print(f"\033[1mSkills:\033[0m {'disabled' if args.no_skills else 'enabled'}")
    run(args.task, not args.no_skills, args.show_context)
