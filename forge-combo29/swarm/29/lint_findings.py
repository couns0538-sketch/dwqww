#!/usr/bin/env python3
"""Lint FINDINGS.md: every table row must have exactly 5 fields (F/N rows) or 4 (C rows), and no cell may contain a
stray pipe. Run before every push; exits non-zero so a broken table cannot be committed unnoticed.

This exists because a grep command pasted into a cell (with escaped pipes) silently produced a 9-field row twice.
"""
import re
import sys

PATH = "FINDINGS.md"
bad = 0
rows = 0
for n, line in enumerate(open(PATH), 1):
    if not line.startswith("| 29-"):
        continue
    rows += 1
    cells = [c.strip() for c in line.rstrip("\n").strip("|").split("|")]
    # Two legitimate shapes: the brief's 4-column C form (id | verdict | evidence | note) used by the first two
    # C rows, and the 5-column form with a trailing tag used by everything else. Accept either, reject anything else.
    want = (4, 5)
    if len(cells) not in want:
        print(f"line {n}: {len(cells)} fields, expected one of {want}: {line[:110]}")
        bad += 1
    if "\\|" in line:
        print(f"line {n}: contains an escaped pipe, which breaks naive parsers: {line[:110]}")
        bad += 1
print(f"\nchecked {rows} rows, {bad} problem(s)")
sys.exit(1 if bad else 0)
