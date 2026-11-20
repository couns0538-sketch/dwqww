#!/usr/bin/env python3
"""Print sanitizer lines from a harness transcript."""
from __future__ import annotations

import sys
from pathlib import Path

KEYS = (
    "AddressSanitizer",
    "UndefinedBehaviorSanitizer",
    "runtime error:",
    "heap-buffer-overflow",
    "LeakSanitizer",
    "SUMMARY:",
)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: count_san.py TRANSCRIPT...")
    for name in sys.argv[1:]:
        lines = Path(name).read_text(errors="replace").splitlines()
        hits = [line for line in lines if any(key in line for key in KEYS)]
        print(f"file {name}")
        print(f"sanitizer_lines {len(hits)}")
        for line in hits:
            print(line[:300])


if __name__ == "__main__":
    main()
