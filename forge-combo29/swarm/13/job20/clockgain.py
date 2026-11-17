#!/usr/bin/env python3
"""Do the moves that CHANGE with the clock get better or worse? (bounded proxy for S-F22's open question)

S-F22 found the move changes between time controls on ~1 position in 5 at the low end, and I have
repeatedly said "whether the changed moves are BETTER is not measured". This measures it as far as it can
be done honestly without a match.

Method, for each position where 2,000 ms and 60,000 ms give DIFFERENT moves:
  1. take both moves (m_short, m_long)
  2. score each at an EQUAL, generous, fixed depth from the resulting position (negamax sign flip), the
     same technique used in job 13 so the comparison is not confounded by search time
  3. report the gap: score(m_long) - score(m_short)
        > 0  the longer clock's move is better by this measure
        < 0  the shorter clock's move is better
        = 0  equivalent
  4. ALSO report depth reached at each clock, because "the longer clock searches deeper" is the mechanism
     under test and should be visible in the data.

Limits stated up front:
  * the score comes from the SAME engine, so it is a self-consistency measure, not ground truth;
  * a fixed depth of 16 is deeper than either clock search on these positions, which is the point, but it
    is still one opinion;
  * a difference in score at depth 16 does not have to mean a difference in game result.

Settings: canonical PC20 from lib/settings.py (asserted), Threads 1, Hash 16, fresh process per search.

Usage: clockgain.py EXE FENS OUTDIR [MAXPOS] [DEPTH]
"""
import json
import os
import re
import subprocess
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from settings import PC20, describe  # noqa: E402

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
MAXPOS = int(sys.argv[4]) if len(sys.argv) > 4 else 40
DEPTH = int(sys.argv[5]) if len(sys.argv) > 5 else 16
os.makedirs(OUTDIR, exist_ok=True)
BAD = ("unknown option", "invalid value", "error")

SHORT_MS = 2000
LONG_MS = 60000


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        seen = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died in uci handshake")
            l = l.rstrip("\n")
            if l.startswith("option name"):
                seen.append(l)
            if l == "uciok":
                break
        for n, v in PC20:
            if not any(o.startswith("option name %s " % n) for o in seen):
                raise SystemExit("FAIL: option %r not advertised" % n)
            self.send("setoption name %s value %s" % (n, v))
            self.ready()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def ready(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l == "readyok":
                return

    def search(self, fen, go):
        self.send("position fen " + fen)
        self.ready()
        self.send(go)
        last = None
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during search")
            l = l.rstrip("\n")
            if l.startswith("info depth"):
                last = l
            if l.startswith("bestmove"):
                bm = l
                break
        d = re.search(r"\bdepth (\d+)", last) if last else None
        n = re.search(r"\bnodes (\d+)", last) if last else None
        mt = re.search(r"score mate (-?\d+)", last) if last else None
        cp = re.search(r"score cp (-?\d+)", last) if last else None
        return {"bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
                "depth": int(d.group(1)) if d else None,
                "nodes": int(n.group(1)) if n else None,
                "mate": int(mt.group(1)) if mt else None,
                "cp": int(cp.group(1)) if cp else None}

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def score_move(e, fen, move, depth):
    """Score a specific move at a fixed depth: play it, search the reply, negate.

    NOTE: `e` is accepted for signature compatibility but a FRESH engine is used per search. Reusing one
    process across many searches contaminates the transposition table: re-measuring position 15's h6h5 at
    depth 16 gave cp 2231 in a fresh process and 2311 after other searches had warmed the table, so the
    first version of this script (one Eng for 16 positions) produced scores that were neither. Fresh is
    the only defensible discipline for a score comparison.
    """
    b = chess.Board(fen)
    try:
        m = chess.Move.from_uci(move)
    except (ValueError, TypeError):
        return None
    if m not in b.legal_moves:
        return None
    b.push(m)
    if b.is_checkmate():
        return ("mate", 0)          # we just mated them: best possible
    if not b.legal_moves:
        return ("cp", 0)            # stalemate
    ee = Eng()
    try:
        r = ee.search(b.fen(), "go depth %d" % depth)
    finally:
        ee.close()
    if r["mate"] is not None:
        return ("mate", -r["mate"])  # their mate score, negated for us
    if r["cp"] is None:
        return None
    return ("cp", -r["cp"])


def cmp_scores(a, b):
    """Compare two scores as integers; mate scores dominate any cp score."""
    def val(s):
        if s is None:
            return None
        kind, v = s
        if kind == "mate":
            # mate in N for us is huge; being mated is hugely negative
            return 100000 - v * 100 if v > 0 else -100000 - v * 100
        return v
    va, vb = val(a), val(b)
    if va is None or vb is None:
        return None
    return vb - va


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:MAXPOS]
    e = None
    rows = []
    for i, fen in enumerate(fens):
        e1 = Eng()
        short = e1.search(fen, "go wtime %d btime %d winc 60 binc 60" % (SHORT_MS, SHORT_MS))
        e1.close()
        e2 = Eng()
        long_ = e2.search(fen, "go wtime %d btime %d winc 60 binc 60" % (LONG_MS, LONG_MS))
        e2.close()
        row = {"position": i, "fen": fen,
               "short": short, "long": long_,
               "same_move": short["bestmove"] == long_["bestmove"]}
        if not row["same_move"]:
            s_short = score_move(None, fen, short["bestmove"], DEPTH)
            s_long = score_move(None, fen, long_["bestmove"], DEPTH)
            row["score_short_move"] = s_short
            row["score_long_move"] = s_long
            row["gap_long_minus_short"] = cmp_scores(s_short, s_long)
        rows.append(row)
        if (i + 1) % 10 == 0:
            print("%d/%d" % (i + 1, len(fens)), flush=True)
    changed = [r for r in rows if not r["same_move"]]
    gaps = [r["gap_long_minus_short"] for r in changed if r.get("gap_long_minus_short") is not None]
    better = sum(1 for g in gaps if g > 0)
    worse = sum(1 for g in gaps if g < 0)
    equal = sum(1 for g in gaps if g == 0)
    depths_short = [r["short"]["depth"] for r in rows if r["short"]["depth"]]
    depths_long = [r["long"]["depth"] for r in rows if r["long"]["depth"]]

    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else None

    summary = {
        "exe": os.path.abspath(EXE), "settings": describe(PC20),
        "positions": len(rows), "short_ms": SHORT_MS, "long_ms": LONG_MS,
        "positions_changing_move": len(changed),
        "scored": len(gaps),
        "long_clock_move_BETTER": better,
        "long_clock_move_WORSE": worse,
        "equivalent_at_depth_%d" % DEPTH: equal,
        "median_gap_cp": med(gaps),
        "min_gap_cp": min(gaps) if gaps else None,
        "max_gap_cp": max(gaps) if gaps else None,
        "median_depth_short": med(depths_short),
        "median_depth_long": med(depths_long),
        "judging_depth": DEPTH,
        "note": "gap = score(long-clock move) - score(short-clock move) at equal depth; positive means the "
                "longer clock chose better. Self-consistency measure (same engine judges), not ground truth.",
    }
    json.dump({"summary": summary, "rows": rows},
              open(os.path.join(OUTDIR, "clockgain.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-36s %s" % (k, v))
    print()
    for r in changed:
        print("  pos %2d  short %-6s (d%-3s) long %-6s (d%-3s)  gap %s"
              % (r["position"], r["short"]["bestmove"], r["short"]["depth"],
                 r["long"]["bestmove"], r["long"]["depth"], r.get("gap_long_minus_short")))


main()
