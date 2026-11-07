#!/usr/bin/env python3
# =============================================================================
#  STEP 0 of 4  —  A "TOOL" IS JUST A FUNCTION
# =============================================================================
#
#  Before we let a model anywhere near this, let's be completely clear about
#  what a tool actually is.
#
#  It is an ordinary Python function. You can call it yourself. It has no idea
#  a model exists. There is nothing AI about it at all.
#
#  This file contains ONE tool - list_files - and a main() that calls it half a
#  dozen different ways. No HTTP, no model, no API key, no network. Just a
#  function and some arguments.
#
#  HOW TO STEP THROUGH IT
#  ----------------------
#  Put a breakpoint on the first line of main(), then Debug As -> Python Run.
#
#  In the other walkthrough files we said "always F6, never F5". This file is
#  the exception. When you reach a list_files(...) line, press F5 (Step Into)
#  and walk through the function body. This is OUR code. Going inside it is
#  the whole point.
#
#  Run it standalone with:   python step0_tool_call_dive.py
#
# =============================================================================

import glob
import subprocess
from pathlib import Path


# =============================================================================
#  CONFIGURATION
# =============================================================================

MODE = "simulate"                        # "simulate" = local folder, "ssh" = a real Pi

PI_HOST = "pi@raspberrypi.local"         # only used when MODE == "ssh"

SANDBOX = Path(__file__).parent / "fake_pi_home"


# =============================================================================
#  HELPER  —  turn whatever the model said into a real path
# =============================================================================

def _resolve(path_from_model: str) -> Path:
    """Turn whatever the model said into a real local path.

    The model might say "~", "/home/pi", ".", or just a bare filename. All of
    those should land inside the sandbox. This is also the containment check:
    nothing outside the sandbox is reachable, whatever the model asks for.
    """
    text = (path_from_model or "~").strip()

    for prefix in ("~/", "~", "/home/pi/", "/home/pi", "./", "."):
        if text == prefix.rstrip("/") or text.startswith(prefix):
            text = text[len(prefix):]
            break

    target = (SANDBOX / text).resolve()

    if not str(target).startswith(str(SANDBOX.resolve())):
        raise ValueError("path escapes the sandbox: " + path_from_model)

    return target


# =============================================================================
#  THE TOOL
# =============================================================================
#  This is the entire thing. Nineteen lines. Press F5 on a call to it and read
#  it line by line.

def list_files(directory: str = "~", pattern: str = "*") -> str:
    """Returns a text table of filenames and sizes in bytes."""

    if MODE == "ssh":
        cmd = "cd " + directory + " && ls -l " + pattern
        done = subprocess.run(["ssh", PI_HOST, cmd],
                              capture_output=True, text=True, timeout=30)
        return done.stdout or done.stderr or "(no output)"

    folder = _resolve(directory)
    matches = sorted(glob.glob(str(folder / pattern)))
    files = [Path(m) for m in matches if Path(m).is_file()]

    if not files:
        return "No files matching '" + pattern + "' in " + directory

    lines = []
    for f in files:
        size = f.stat().st_size
        lines.append(f.name.ljust(24) + str(size).rjust(10))

    return "\n".join(lines)


# =============================================================================
#  TEST DATA  —  so this file stands on its own
# =============================================================================

SAMPLE_FILES = {
    "cache_build.tmp": 18_432,
    "session_a4f1.tmp": 2_887_680,       # the largest .tmp
    "upload_part1.tmp": 524_288,
    "vacuum.tmp": 912,
    "render_cache.tmp": 131_072,
    "notes.txt": 2_048,                  # not a .tmp
    "archive.tmp.bak": 4_194_304,        # bigger, but does NOT match *.tmp
}


def make_sandbox():
    """Create the fake Pi home directory."""
    SANDBOX.mkdir(exist_ok=True)
    for old in SANDBOX.iterdir():
        if old.is_file():
            old.unlink()
    for name, size in SAMPLE_FILES.items():
        (SANDBOX / name).write_bytes(b"\0" * size)


def show(label, call_text, result):
    """Print one demo neatly."""
    print()
    print("  " + label)
    print("  " + "-" * 68)
    print("      " + call_text)
    print()
    for line in str(result).splitlines():
        print("          " + line)


# =============================================================================
#  MAIN  —  six ways to call one function
# =============================================================================

def main():

    make_sandbox()

    print()
    print("=" * 72)
    print("  A TOOL IS JUST A FUNCTION")
    print("=" * 72)
    print()
    print("  Sandbox: " + str(SANDBOX))
    print("  Mode   : " + MODE + "   (no network, no model, nothing remote)")

    # ---- 1. no arguments at all -------------------------------------------
    #  Both parameters have defaults, so this lists everything in the home
    #  directory. Note the two files that are NOT .tmp.

    show("1. Called with no arguments  (defaults: '~' and '*')",
         'list_files()',
         list_files())

    # ---- 2. the call the model actually makes -----------------------------
    #  This is the exact call you will see in step 1 of the walkthrough, when
    #  the model asks for it. Same function. Same arguments. No difference.

    show("2. The call the model makes in step 1",
         'list_files("~", "*.tmp")',
         list_files("~", "*.tmp"))

    print()
    print("          ^ five files. archive.tmp.bak is NOT in that list, even")
    print("            though it is the biggest file in the folder, because")
    print("            '*.tmp' does not match a name ending in '.bak'.")

    # ---- 3. keyword arguments, same result --------------------------------
    #  Worth showing because the model always sends named arguments. This is
    #  what json.loads() of its arguments string unpacks into.

    show("3. Same call, keyword style  (how the model's arguments arrive)",
         'list_files(directory="~", pattern="*.tmp")',
         list_files(directory="~", pattern="*.tmp"))

    # ---- 4. a different pattern -------------------------------------------

    show("4. A different pattern",
         'list_files("~", "*.txt")',
         list_files("~", "*.txt"))

    # ---- 5. the empty case ------------------------------------------------
    #  Nothing matches. The function does not crash and does not return an
    #  empty string - it returns a SENTENCE, because the thing reading this is
    #  a language model.

    show("5. Nothing matches",
         'list_files("~", "*.log")',
         list_files("~", "*.log"))

    print()
    print("          ^ a sentence, not an empty string and not an exception.")
    print("            Tool output is read by a model, so it should read like")
    print("            something a model can act on.")

    # ---- 6. the containment check -----------------------------------------
    #  The model could ask for anything. This is where that gets stopped - in
    #  the function, not in the prompt.

    print()
    print("  6. Asking for somewhere it should not be allowed")
    print("  " + "-" * 68)
    print('      list_files("../../../etc")')
    print()
    try:
        result = list_files("../../../etc")
        print("          " + str(result))
        print()
        print("          ^ THAT SHOULD NOT HAVE WORKED.")
    except ValueError as error:
        print("          ValueError: " + str(error))
        print()
        print("          ^ refused. Note WHERE that check lives: inside")
        print("            _resolve(), in our code. Not in a prompt, not in an")
        print("            instruction to the model. You cannot secure a tool")
        print("            by asking the model nicely.")

    # ---- the bridge -------------------------------------------------------

    print()
    print("=" * 72)
    print("  SO WHAT DOES THE MODEL ACTUALLY ADD?")
    print("=" * 72)
    print()
    print("  Nothing was different about any of those six calls. We chose the")
    print("  arguments and Python ran the function.")
    print()
    print("  When the model is involved, exactly one thing changes: it decides")
    print("  what to put in the brackets. It sends us this -")
    print()
    print('      {"name": "list_files",')
    print('       "arguments": "{\\"directory\\": \\"~\\", \\"pattern\\": \\"*.tmp\\"}"}')
    print()
    print("  - and our code turns that into demo 2 above. That is the entire")
    print("  difference between this file and an agent.")
    print()
    print("  Next:  python step1_one_turn.py")
    print()


if __name__ == "__main__":
    main()
