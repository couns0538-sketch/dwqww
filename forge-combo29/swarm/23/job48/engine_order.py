#!/usr/bin/env python3
"""job48b : compare the 0-node move against the ENGINE's OWN generation order (`go perft 1` divide).

WHY THIS EXISTS: job 48's P2 compared against python-chess's legal-move iteration order, which is NOT the engine's
generation order — so "index 18 in python-chess" said nothing about a claim about the engine's generator. The engine
prints its own order in a `go perft 1` divide, which is the right yardstick.

TWO NEAR-MISSES RECORDED, because both could have produced a silent wrong number:
  1. the summary line is `nodes 19`, NOT `Nodes searched` (that is Stockfish's wording). My first driver waited for the
     former, blocked forever, and had to be killed. A hang is at least visible; a driver that had read ZERO moves from
     the divide and reported "not in list" would have looked like a result.
  2. a divide line is `<move>: <count>`; the loop must also ASSERT it saw a nonzero number of move lines, or an
     unparsed divide reads as "the engine's order is empty".

PRINTED WITH EVERY ROW: the divide's first move, the 0-node move's index, and the count of move lines parsed, so the
reader can see the parse population beside the answer.
"""
import re, subprocess, sys, os

BASE = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/build/forge")
MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?) : (\d+)$".replace(" : ", ": "))
SUMMARY = re.compile(r"^nodes (\d+)$")

CASES = [
    ("D1 threefold W", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
     "d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1", "d5d1"),
    ("D2 threefold B", "1K6/8/8/3R4/8/8/8/k7 b - - 0 1",
     "a1b1 d5d6 b1a1 d6d5 a1b1 d5d6 b1a1 d6d5", "a1b1"),
    ("D3 threefold c1", "7k/8/8/8/8/8/8/K1R5 w - - 0 1",
     "c1c7 h8g8 c7c1 g8h8 c1c7 h8g8 c7c1 g8h8", "c1b1"),
    ("D4 halfmove150", "1K6/8/8/3R4/8/8/8/k7 w - - 150 1", None, "d5d1"),
    ("D5 bare kings", "8/8/8/8/8/8/8/K6k w - - 0 1", None, "a1b1"),
    ("C1 CONTROL(searched)", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", None, "d5b5"),
]


def perft_order(fen, moves):
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    opts = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died during uci")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + moves) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    order = []
    total = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in perft")
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            order.append(m.group(1))
        ms = SUMMARY.match(s)
        if ms:
            total = int(ms.group(1))
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return order, total


print("engine:", BASE)
print("| case | 0-node/served move | index in ENGINE order | 1st move of divide | move lines | nodes |")
print("|---|---|---|---|---|---|")
bad = 0
for label, fen, moves, bm in CASES:
    order, total = perft_order(fen, moves)
    if not order:
        print("| %s | %s | **PARSE FAILURE: no move lines** | - | 0 | %s |" % (label, bm, total))
        bad += 1
        continue
    if total is not None and total != len(order):
        print("| %s | %s | **PARSE FAILURE: %d lines vs nodes %d** | - | %d | %d |" % (
            label, bm, len(order), total, len(order), total))
        bad += 1
        continue
    idx = order.index(bm) if bm in order else -1
    print("| %s | %s | %s | %s | %d | %s |" % (
        label, bm, idx if idx >= 0 else "NOT IN DIVIDE", order[0], len(order), total))
print()
if bad:
    print("HARD FAILURE: %d case(s) could not be parsed — the table above is NOT a result." % bad)
    sys.exit(2)
print("The divide IS the engine's generation order, so an index of 0 means the 0-node move is the engine's FIRST")
print("generated move. Any other index means the move came from somewhere else in the 0-node path.")
