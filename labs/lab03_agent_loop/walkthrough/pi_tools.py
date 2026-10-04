#!/usr/bin/env python3
# =============================================================================
#  THE TOOLS  —  read this first, then put it aside
# =============================================================================
#
#  Three functions the model will be allowed to ask for. Nothing clever here.
#  Read it once so you know what the tools do, then step OVER calls to them in
#  the debugger (F6) - the loop is the lesson, not these.
#
#  By default everything runs against a FAKE Pi: a local folder called
#  fake_pi_home/ with some .tmp files in it. Nothing you care about can be
#  deleted. Run setup_sandbox.py to create it.
#
#  If you have a real Raspberry Pi and want to use it, set MODE = "ssh" below.
#  Read the safety note before you do.
#
# =============================================================================

import glob
import os
import subprocess
from pathlib import Path

# --- configuration ----------------------------------------------------------

MODE = "simulate"          # "simulate" = local fake folder   "ssh" = a real Pi

PI_HOST = "pi@raspberrypi.local"       # only used when MODE == "ssh"

SANDBOX = Path(__file__).parent / "fake_pi_home"

# Safety: in ssh mode we refuse to delete anything unless you ALSO flip this.
# Two switches instead of one, deliberately. Deleting the wrong file on a real
# machine during a workshop is a bad afternoon.
ALLOW_REAL_DELETES = False


# --- a note worth making out loud -------------------------------------------
#  The model never sees PI_HOST. It never sees a username, a password or a key.
#  It asks for "the home directory" and THIS code decides what that means and
#  how to reach it. If the model could log in, the credentials would have to be
#  in its context - which means in the conversation history, resent on every
#  single call, and sitting in every log you keep.
# ----------------------------------------------------------------------------


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
#  TOOL 1  —  list files, with their sizes
# =============================================================================

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
#  TOOL 2  —  delete exactly one file
# =============================================================================

def delete_file(path: str) -> str:
    """Deletes one file. Returns a confirmation, or an explanation of refusal."""

    if MODE == "ssh":
        if not ALLOW_REAL_DELETES:
            return ("REFUSED: this is a real machine and ALLOW_REAL_DELETES is "
                    "False in pi_tools.py. Nothing was deleted.")
        done = subprocess.run(["ssh", PI_HOST, "rm -- " + path],
                              capture_output=True, text=True, timeout=30)
        if done.returncode != 0:
            return "FAILED: " + (done.stderr or "unknown error")
        return "Deleted " + path

    target = _resolve(path)

    if not target.exists():
        return "FAILED: " + path + " does not exist."

    size = target.stat().st_size
    target.unlink()
    return "Deleted " + path + " (" + str(size) + " bytes freed)."


# =============================================================================
#  TOOL 3  —  run any shell command   *** used only in step 4 ***
# =============================================================================
#  This exists so you can watch how much more dangerous it is than the two
#  narrow tools above, and how much FASTER. Step 4 makes that comparison.
#  Do not ship anything like this.

def run_command(command: str) -> str:
    """Runs an arbitrary shell command. A genuinely bad idea."""

    if MODE == "ssh":
        return "REFUSED: run_command is disabled in ssh mode. Obviously."

    done = subprocess.run(command, shell=True, cwd=str(SANDBOX),
                          capture_output=True, text=True, timeout=30)
    out = (done.stdout or "") + (done.stderr or "")
    return out.strip() or "(command produced no output)"


# =============================================================================
#  THE SCHEMAS the model gets to read
# =============================================================================
#  Note how much work the "description" lines are doing. They are the only
#  thing the model knows about any of this.

LIST_FILES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": ("List files in a directory on the Raspberry Pi. Returns "
                        "each filename with its size in bytes."),
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string",
                              "description": "Directory path. Use '~' for the home directory."},
                "pattern": {"type": "string",
                            "description": "Optional glob such as '*.tmp'. Defaults to '*'."},
            },
            "required": ["directory"],
        },
    },
}

DELETE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "delete_file",
        "description": ("Permanently delete ONE file on the Raspberry Pi. "
                        "This cannot be undone."),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string",
                         "description": "Full path of the single file to delete."},
            },
            "required": ["path"],
        },
    },
}

RUN_COMMAND_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_command",
        "description": ("Run any shell command on the Raspberry Pi and return "
                        "its output."),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command."},
            },
            "required": ["command"],
        },
    },
}

# The dispatch table: a name the model emitted -> a function we control.
# Nothing the model says can add an entry to this dictionary.

DISPATCH = {
    "list_files": list_files,
    "delete_file": delete_file,
    "run_command": run_command,
}


if __name__ == "__main__":
    print("mode:", MODE)
    print("sandbox:", SANDBOX)
    print()
    print(list_files("~", "*.tmp"))
