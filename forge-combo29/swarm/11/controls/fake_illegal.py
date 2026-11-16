#!/usr/bin/env python3
"""fake_illegal.py — a FAKE engine for Opus Rule 1 ("a zero needs a planted one").

It answers `uci`/`uciok`, `isready`/`readyok` correctly, accepts every `position`, and then
answers `bestmove a1a8` to EVERY `go` — a move that is illegal in essentially every position.
A harness that claims "0 illegal bestmoves" must count this plant as illegal.

Also, on `position fen <PLANTHANG...>` it stops answering `readyok` at all, so the same file
plants both "illegal bestmove" and "hang".
"""
import sys

hanging = False
for line in sys.stdin:
    s = line.strip()
    if s == "uci":
        print("id name FAKE planted engine (seat 11 rule-1 control)", flush=True)
        print("uciok", flush=True)
    elif s == "isready":
        if hanging:
            continue          # planted hang: never send readyok
        print("readyok", flush=True)
    elif s.startswith("position"):
        if "PLANTHANG" in s:
            hanging = True
        continue
    elif s.startswith("go"):
        print("bestmove a1a8", flush=True)
    elif s == "quit":
        break
