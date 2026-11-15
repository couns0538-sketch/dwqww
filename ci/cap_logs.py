"""Caps the result files of a suite before upload (Opus, 2026-11-15). A file larger than 1 MB is replaced by its first
300 lines and a note with its size, sha256, line count and how many sanitizer reports the whole file held, so the
counts survive the cut. Files that are not text are removed and listed in CAPPED.txt.

    python cap_logs.py <results dir>
"""
from __future__ import annotations

import hashlib
import os
import sys

LIMIT = 1_000_000
MARKS = ("WARNING: ThreadSanitizer:", "ERROR: AddressSanitizer", "ERROR: LeakSanitizer", "runtime error:")


def main() -> int:
    root = sys.argv[1]
    notes = []
    for dirpath, _, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                os.remove(p)
                notes.append(f"{p}: a link, removed")
                continue
            data = open(p, "rb").read()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                os.remove(p)
                notes.append(f"{p}: not UTF-8 text ({len(data)} bytes), removed")
                continue
            if len(data) > LIMIT:
                head = "\n".join(text.splitlines()[:300])
                counts = ", ".join(f"'{m}' {text.count(m)}" for m in MARKS)
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(head + f"\n\n[CUT by cap_logs.py: the whole file had {len(data)} bytes, "
                                    f"{text.count(chr(10))} lines, sha256 {hashlib.sha256(data).hexdigest()}; "
                                    f"counts in the whole file: {counts}]\n")
                notes.append(f"{p}: {len(data)} bytes, cut to its first 300 lines")
    if notes:
        with open(os.path.join(root, "CAPPED.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(notes) + "\n")
    print(f"cap_logs: {len(notes)} files changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
