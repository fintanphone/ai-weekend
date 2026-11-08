#!/usr/bin/env python3
"""Tools for Lab 9, in two unrelated groups.

Group A - OPS. An on-call scenario: check disk, read a log, restart a service.
Group B - REPORTING. A data scenario: list datasets, read one, write a report.

Two groups on purpose. Steps 1 and 2 use group A; step 3 uses group B to prove
the harness is not secretly built around one task.

Everything runs against a local sandbox folder. Nothing real is touched.
"""

import json
import random
from pathlib import Path

SANDBOX = Path(__file__).parent / "sandbox"

# Deliberately flaky, so step 1 can show a transient failure killing a run.
# Set to 0.0 for a quiet demo.
FLAKE_RATE = 0.0


class ToolFailure(Exception):
    """A tool failed in a way that might succeed on a retry."""


def _maybe_flake(name):
    if FLAKE_RATE and random.random() < FLAKE_RATE:
        raise ToolFailure(f"{name}: connection reset by peer")


# ==========================================================================
#  GROUP A — ops
# ==========================================================================

def check_disk(path: str = "/") -> str:
    """Disk usage for a mount point."""
    _maybe_flake("check_disk")
    table = {
        "/": ("48G", "41G", "4.6G", "90%"),
        "/var": ("20G", "19G", "0.4G", "98%"),
        "/home": ("100G", "22G", "78G", "22%"),
    }
    if path not in table:
        return f"No such mount point: {path}. Known: {', '.join(table)}"
    size, used, avail, pct = table[path]
    return (f"Filesystem  Size  Used  Avail  Use%\n"
            f"{path:<11} {size:>4}  {used:>4}  {avail:>5}  {pct:>4}")


def read_log(service: str, lines: int = 20) -> str:
    """Tail of a service's log."""
    _maybe_flake("read_log")
    logs = {
        "ingest": (
            "14:02:11 INFO  batch 4471 started\n"
            "14:02:19 WARN  disk usage on /var at 94%\n"
            "14:03:02 WARN  disk usage on /var at 96%\n"
            "14:03:44 ERROR could not write spool file: No space left on device\n"
            "14:03:44 ERROR batch 4471 aborted\n"
            "14:04:10 INFO  retrying batch 4471\n"
            "14:04:12 ERROR could not write spool file: No space left on device"),
        "api": (
            "14:01:00 INFO  listening on :8080\n"
            "14:05:33 INFO  200 GET /health\n"
            "14:05:48 INFO  200 GET /health"),
    }
    if service not in logs:
        return f"No log for service {service!r}. Known: {', '.join(logs)}"
    return logs[service]


def restart_service(name: str) -> str:
    """Restart a service. Interrupts anything in flight."""
    _maybe_flake("restart_service")
    return f"Service {name} restarted. 2 in-flight requests dropped."


# ==========================================================================
#  GROUP B — reporting
# ==========================================================================

def list_datasets() -> str:
    """List the CSV datasets available."""
    _maybe_flake("list_datasets")
    files = sorted(SANDBOX.glob("*.csv"))
    if not files:
        return "No datasets. Run setup_sandbox.py."
    return "\n".join(f"{f.name:<20} {f.stat().st_size:>7} bytes" for f in files)


def read_dataset(name: str) -> str:
    """Read one dataset in full."""
    _maybe_flake("read_dataset")
    target = (SANDBOX / name).resolve()
    if not str(target).startswith(str(SANDBOX.resolve())):
        return "ERROR: path escapes the sandbox."
    if not target.exists():
        return f"No dataset called {name!r}."
    return target.read_text()[:4000]


def write_report(filename: str, content: str) -> str:
    """Write a report file into the sandbox. Overwrites without warning."""
    _maybe_flake("write_report")
    target = (SANDBOX / filename).resolve()
    if not str(target).startswith(str(SANDBOX.resolve())):
        return "ERROR: path escapes the sandbox."
    existed = target.exists()
    target.write_text(content)
    verb = "Overwrote" if existed else "Wrote"
    return f"{verb} {filename} ({len(content)} bytes)."


# ==========================================================================
#  SCHEMAS
# ==========================================================================
#  Note the shape: each entry pairs a JSON Schema with the function AND with
#  metadata of our own - whether it is destructive. The model never sees the
#  metadata. It is there for the harness to make decisions about.

def _fn(name, description, properties, required, func, destructive=False):
    return {
        "name": name,
        "destructive": destructive,
        "func": func,
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {"type": "object", "properties": properties,
                               "required": required},
            },
        },
    }


OPS_TOOLS = [
    _fn("check_disk", "Check disk usage for a mount point on the server.",
        {"path": {"type": "string",
                  "description": "Mount point, e.g. '/' or '/var'."}},
        ["path"], check_disk),
    _fn("read_log", "Read the recent log output for a named service.",
        {"service": {"type": "string", "description": "Service name, e.g. 'ingest'."},
         "lines": {"type": "integer", "description": "How many lines. Default 20."}},
        ["service"], read_log),
    _fn("restart_service", "Restart a service. This interrupts anything in flight.",
        {"name": {"type": "string", "description": "Service to restart."}},
        ["name"], restart_service, destructive=True),
]

REPORT_TOOLS = [
    _fn("list_datasets", "List the CSV datasets available to read.",
        {}, [], list_datasets),
    _fn("read_dataset", "Read the full contents of one dataset.",
        {"name": {"type": "string", "description": "Filename, e.g. 'sales.csv'."}},
        ["name"], read_dataset),
    _fn("write_report", "Write a report file. Overwrites any existing file.",
        {"filename": {"type": "string"}, "content": {"type": "string"}},
        ["filename", "content"], write_report, destructive=True),
]


if __name__ == "__main__":
    print("OPS   :", ", ".join(t["name"] for t in OPS_TOOLS))
    print("REPORT:", ", ".join(t["name"] for t in REPORT_TOOLS))
    print()
    print(check_disk("/var"))
