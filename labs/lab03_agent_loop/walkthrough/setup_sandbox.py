#!/usr/bin/env python3
"""Create the fake Raspberry Pi home directory. Run this first, and again
whenever you want to reset after the agent has deleted something.

    python setup_sandbox.py
"""

from pathlib import Path

SANDBOX = Path(__file__).parent / "fake_pi_home"

# name -> size in bytes. The largest .tmp is session_a4f1.tmp, deliberately
# not the first in the list and not the one with the most obvious name.
FILES = {
    "cache_build.tmp": 18_432,
    "session_a4f1.tmp": 2_887_680,      # <-- the largest .tmp
    "upload_part1.tmp": 524_288,
    "vacuum.tmp": 912,
    "notes.txt": 2_048,                 # not a .tmp - should be ignored
    "archive.tmp.bak": 4_194_304,       # BIGGER, but does NOT match *.tmp
    "render_cache.tmp": 131_072,
}


def main():
    SANDBOX.mkdir(exist_ok=True)

    for old in SANDBOX.iterdir():
        if old.is_file():
            old.unlink()

    for name, size in FILES.items():
        (SANDBOX / name).write_bytes(b"\0" * size)

    print("Created " + str(SANDBOX))
    print()
    for name in sorted(FILES):
        marker = "  <-- largest .tmp" if name == "session_a4f1.tmp" else ""
        print("   " + name.ljust(24) + str(FILES[name]).rjust(10) + marker)
    print()
    print("Note archive.tmp.bak is bigger than session_a4f1.tmp, but it is not")
    print("a .tmp file. If the agent deletes that one, its glob was wrong.")
    print()
    print("Next:  python step1_one_turn.py")


if __name__ == "__main__":
    main()
