#!/usr/bin/env python3
"""Count sanitizer lines in a raw engine log."""
import sys
from pathlib import Path

MARKERS = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "runtime error:")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: san_lines.py raw.txt ...")
    for name in sys.argv[1:]:
        lines = [
            line
            for line in Path(name).read_text(errors="replace").splitlines()
            if any(marker in line for marker in MARKERS)
        ]
        print(f"{name} sanitizer_lines {len(lines)}")
        for line in lines[:3]:
            print(line)


if __name__ == "__main__":
    main()
