#!/usr/bin/env python3
"""Count sanitizer report lines in a log. Usage: count_sanitizer.py LOG"""
import sys
from pathlib import Path

MARKS = ("AddressSanitizer", "runtime error:", "SUMMARY:")


def main() -> None:
    text = Path(sys.argv[1]).read_text(errors="replace")
    hits = [line for line in text.splitlines() if any(mark in line for mark in MARKS)]
    print(f"sanitizer_lines {len(hits)}")
    for line in hits[:40]:
        print(line)


if __name__ == "__main__":
    main()
