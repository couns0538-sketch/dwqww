#!/usr/bin/env python3
"""Count AddressSanitizer / UndefinedBehaviorSanitizer lines in a stderr file."""

import sys
from pathlib import Path

MARKS = ("ERROR: AddressSanitizer", "ERROR: UndefinedBehaviorSanitizer", "SUMMARY: AddressSanitizer", "runtime error:")


def main() -> int:
    path = Path(sys.argv[1])
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = [line for line in lines if any(mark in line for mark in MARKS)]
    print(f"file {path}")
    print(f"stderr_lines {len(lines)}")
    print(f"sanitizer_lines {len(hits)}")
    for line in hits[:20]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
