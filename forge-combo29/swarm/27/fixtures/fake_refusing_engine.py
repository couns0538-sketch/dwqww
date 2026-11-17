#!/usr/bin/env python3
"""A minimal fake UCI engine that reproduces S-C84: it diagnoses an illegal FEN, then answers anyway.

Every print flushes. The first version of this fixture was written inline into a tempfile and buffered its
stdout when piped, so the reader saw silence and the self-test waited 30 s on "no uciok" - a fake engine that
cannot answer is indistinguishable from a real bug, and the time went into suspecting the reader instead.

It declares Hash / Threads / OwnBook so the `none` option list (3 options) applies cleanly.
It replies `readyok` to `isready` and ignores everything else except `go` and `quit`.
"""
import sys


def say(x):
    print(x, flush=True)


for ln in sys.stdin:
    c = ln.strip()
    if c == "uci":
        say("id name fake-refusing-engine")
        say("option name Hash type spin default 16 min 1 max 1024")
        say("option name Threads type spin default 1 min 1 max 8")
        say("option name OwnBook type check default true")
        say("uciok")
    elif c == "isready":
        say("readyok")
    elif c.startswith("go"):
        # this is the S-C84 behaviour, in three lines
        say("info string invalid FEN: kings may not be adjacent")
        say("info depth 1 seldepth 1 score cp 30 nodes 26 pv e2e4")
        say("bestmove e2e4")
    elif c == "quit":
        break
