#!/usr/bin/env python3
"""Pre-flight check. Run this before the workshop, on every machine.

    python check_setup.py

Green = good. Yellow = fine on a laptop without a GPU. Red = fix before Saturday.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

OK, WARN, FAIL = "\033[92m  OK  \033[0m", "\033[93m WARN \033[0m", "\033[91m FAIL \033[0m"
results = []


def report(status, label, detail=""):
    results.append(status)
    print(f"[{status}] {label}" + (f"  —  {detail}" if detail else ""))


def check_python():
    v = sys.version_info
    if (v.major, v.minor) >= (3, 11):
        report(OK, "Python version", f"{v.major}.{v.minor}.{v.micro}")
    else:
        report(FAIL, "Python version", f"{v.major}.{v.minor} — need 3.11+")


def check_packages():
    for pkg, importname in [
        ("anthropic", "anthropic"),
        ("python-dotenv", "dotenv"),
        ("requests", "requests"),
        ("numpy", "numpy"),
        ("sentence-transformers", "sentence_transformers"),
        ("mcp", "mcp"),
    ]:
        try:
            __import__(importname)
            report(OK, f"package: {pkg}")
        except ImportError:
            report(FAIL, f"package: {pkg}", "pip install -r requirements.txt")


def check_api_key():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        report(FAIL, "ANTHROPIC_API_KEY", "not set — see SETUP.md step 3")
        return
    if not key.startswith("sk-"):
        report(WARN, "ANTHROPIC_API_KEY", "set, but doesn't look like a key")
        return

    try:
        import anthropic

        client = anthropic.Anthropic()
        model = os.environ.get("WORKSHOP_MODEL", "claude-sonnet-5")
        client.messages.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": "Reply with the single word: ready"}],
        )
        report(OK, "Anthropic API", f"live call succeeded ({model})")
    except Exception as exc:  # noqa: BLE001
        report(FAIL, "Anthropic API", f"{type(exc).__name__}: {str(exc)[:90]}")


def check_binary(name, args, label, required=True):
    if shutil.which(name) is None:
        report(FAIL if required else WARN, label, "not on PATH")
        return
    try:
        out = subprocess.run(
            [name, *args], capture_output=True, text=True, timeout=20
        ).stdout.strip().splitlines()
        report(OK, label, out[0] if out else "installed")
    except Exception:  # noqa: BLE001
        report(WARN, label, "installed but did not respond")


def check_local_server():
    """Either llama.cpp or Ollama is fine — the labs detect whichever is up."""
    sys.path.insert(0, str(Path(__file__).parent / "labs" / "common"))
    try:
        from local_backend import connect
    except ImportError:
        report(WARN, "local backend", "labs/common/local_backend.py not found")
        return

    try:
        be = connect(timeout=3)
    except Exception:  # noqa: BLE001
        base = os.environ.get("LOCAL_API_BASE", "http://localhost:8080")
        report(WARN, "local model server",
               f"nothing at {base} or Ollama — fine on a laptop without a GPU")
        return

    report(OK, f"local server ({be.kind})", be.model_name)

    try:
        style = be.probe_schema_support()
    except Exception:  # noqa: BLE001
        style = None
    if style:
        report(OK, "constrained decoding", f"response_format style: {style}")
    else:
        report(WARN, "constrained decoding",
               "no response_format shape honoured — Lab 2b method B unavailable")


def check_gpu():
    if shutil.which("nvidia-smi") is None:
        report(WARN, "NVIDIA GPU", "no nvidia-smi — expected on non-GPU laptops")
        return
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()
        report(OK, "NVIDIA GPU", out)
    except Exception:  # noqa: BLE001
        report(WARN, "NVIDIA GPU", "nvidia-smi present but failed")


def main():
    print("\n=== Agentic AI Weekend — pre-flight check ===\n")
    check_python()
    check_packages()
    check_api_key()
    print()
    check_binary("node", ["--version"], "Node.js")
    check_binary("claude", ["--version"], "Claude Code")
    check_local_server()
    check_gpu()

    fails = results.count(FAIL)
    warns = results.count(WARN)
    print(f"\n--- {len(results) - fails - warns} ok, {warns} warnings, {fails} failures ---")
    if fails:
        print("\nFix the failures before the workshop. Ask the host if stuck.\n")
        sys.exit(1)
    print("\nReady. See you Saturday.\n")


if __name__ == "__main__":
    main()
