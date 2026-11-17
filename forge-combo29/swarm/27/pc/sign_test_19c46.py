#!/usr/bin/env python3
"""sign_test_19c46.py <exe> <positions-file> <outdir> [--n 200] [--budget 2000]

19-C46 claims PC20 is SHALLOWER than S14 at the self-play budget (`go softnodes 2000`): their 6-position
sweep summed 43 against S14's 45, and the one-option-at-a-time blamed TtPruneV2.

My 8-position set gave the OPPOSITE sign at every budget below 8000 (PC20 +6 at 2000), with zero
non-determinism over 3 reps. Eight positions can be an unlucky sample, so this script widens to a real
population: the repo's own self-play-derived `positions.txt` (walk-depth 4, opening plies 8-12), the same
family the owner's matches produce.

Measured, per position, at one budget:
  - depth of the last `info depth` line
  - nodes of that line (to report the overshoot against the budget, since depth at a fixed NODE budget is
    a trade of breadth for depth, not a free win)
  - whether the two configs chose the same move

Reported as a SIGN TEST on depth difference with ties counted, plus a paired comparison restricted to
positions where the two configs agreed on the move (so "deeper" is not just "different tree").

A settings-count assertion runs on every config: S14 = 16 accepted options, PC20 = 22. If the count is
wrong the run aborts rather than mislabelling a row.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time

import chess

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]
BASEOPT = ["Hash 16", "Threads 1"]
CONFIGS = {"S14": BASEOPT + S14, "PC20": BASEOPT + S14 + PC20X}
EXPECT_N = {"S14": 16, "PC20": 22}


class Missing(Exception):
    pass


def legal(fen):
    """Every position is checked before it is measured. A malformed FEN silently plays as startpos in some
    engines, which would quietly turn the whole population into one repeated position."""
    fields = fen.split()
    if len(fields) < 4:
        return False, "too few fields (%d)" % len(fields)
    if fields[1] not in ("w", "b"):
        return False, "bad side %r" % fields[1]
    if not re.fullmatch(r"(-|[KQkq]+)", fields[2]):
        return False, "bad castling %r" % fields[2]
    if fields[3] != "-" and not re.fullmatch(r"[a-h][36]", fields[3]):
        return False, "bad ep %r" % fields[3]
    board = fields[0]
    if board.count("K") != 1 or board.count("k") != 1:
        return False, "not exactly one king per side"
    rows = board.split("/")
    if len(rows) != 8:
        return False, "board is not 8 ranks"
    for r in rows:
        n = sum(int(c) if c.isdigit() else 1 for c in r)
        if n != 8:
            return False, "rank %r sums to %d" % (r, n)
    # The shape checks above are necessary but not sufficient - a rank can sum to 8 with the pawns on the
    # wrong side, or a king can stand in check. python-chess is the referee.
    try:
        b = chess.Board(fen)
    except ValueError as e:
        return False, "python-chess refused: %s" % e
    if not b.is_valid():
        return False, "python-chess: invalid (%s)" % b.status()
    return True, "ok"


def one_run(exe, settings, fen, budget, expect, timeout=900):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        lines, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        accepted = 0
        for item in settings:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise Missing("option %r not advertised" % name)
            s("setoption name %s value %s" % (name, val))
            s("isready")
            l2, ok2 = until(lambda x: x.strip() == "readyok")
            if not ok2:
                raise Missing("no readyok after %r" % item)
            for l in l2:
                if "unknown option" in l or "invalid value" in l:
                    raise Missing("bad option %r: %s" % (item, l))
            accepted += 1
        if accepted != expect:
            raise Missing("accepted %d options, label promises %d" % (accepted, expect))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        l3, ok3 = until(lambda x: x.strip() == "readyok")
        if not ok3:
            raise Missing("no readyok after position")
        for l in l3:
            if "illegal" in l.lower() or "error" in l.lower():
                raise Missing("engine rejected position: " + l)
        s("go softnodes %d" % budget)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not ok:
            raise Missing("no bestmove")
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth line")
        last = infos[-1]
        d = re.search(r"info depth (\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove"))
        parts = bm.split()
        return {"depth": int(d.group(1)), "nodes": int(n.group(1)) if n else None,
                "score": [sc.group(1), int(sc.group(2))] if sc else None,
                "bestmove": parts[1] if len(parts) > 1 else None, "n_info": len(infos)}
    finally:
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=20)
        except Exception:
            p.kill()


def load_positions(path, n, seed):
    out, seen, rejected = [], set(), []
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        ok, why = legal(ln)
        if not ok:
            rejected.append({"fen": ln, "why": why})
            continue
        if ln in seen:
            continue
        seen.add(ln)
        out.append(ln)
    rng = random.Random(seed)
    if n and len(out) > n:
        out = rng.sample(out, n)
    return out, rejected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("positions"); ap.add_argument("outdir")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--budget", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=2701)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)

    fens, rejected = load_positions(a.positions, a.n, a.seed)
    if not fens:
        raise SystemExit("no legal positions loaded")
    print("loaded %d legal distinct positions, rejected %d" % (len(fens), len(rejected)))

    R = {"exe": exe,
         "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
         "budget": a.budget, "seed": a.seed, "source": a.positions,
         "n_positions": len(fens), "rejected": rejected[:20], "n_rejected": len(rejected),
         "cells": []}

    for fi, fen in enumerate(fens):
        row = {"fen": fen}
        for cfg in ("S14", "PC20"):
            row[cfg] = one_run(exe, CONFIGS[cfg], fen, a.budget, EXPECT_N[cfg])
        row["d_depth"] = row["PC20"]["depth"] - row["S14"]["depth"]
        row["same_move"] = row["PC20"]["bestmove"] == row["S14"]["bestmove"]
        R["cells"].append(row)
        if (fi + 1) % 25 == 0:
            print("  %d/%d done" % (fi + 1, len(fens)))

    dd = [c["d_depth"] for c in R["cells"]]
    pos = sum(1 for v in dd if v > 0); neg = sum(1 for v in dd if v < 0); tie = sum(1 for v in dd if v == 0)
    both = sum(dd)
    agree = [c["d_depth"] for c in R["cells"] if c["same_move"]]
    R["sign_test"] = {"positive": pos, "negative": neg, "tie": tie, "n": len(dd),
                      "sum_d_depths": both,
                      "mean_d_depth": both / len(dd)}
    R["agreed_move_only"] = {"n": len(agree), "positive": sum(1 for v in agree if v > 0),
                             "negative": sum(1 for v in agree if v < 0),
                             "tie": sum(1 for v in agree if v == 0),
                             "sum_d_depth": sum(agree)}
    s14n = sum(c["S14"]["nodes"] or 0 for c in R["cells"])
    pc20n = sum(c["PC20"]["nodes"] or 0 for c in R["cells"])
    R["nodes"] = {"S14_total": s14n, "PC20_total": pc20n, "ratio": pc20n / s14n if s14n else None,
                  "S14_overshoot": s14n / (a.budget * len(fens)),
                  "PC20_overshoot": pc20n / (a.budget * len(fens))}

    print("\n-- SIGN TEST on depth at softnodes %d, %d positions --" % (a.budget, len(dd)))
    print("  PC20 deeper %d, shallower %d, equal %d" % (pos, neg, tie))
    print("  summed depth difference %+d, mean %+.3f ply" % (both, both / len(dd)))
    print("-- restricted to positions where both chose the SAME move (n=%d) --" % len(agree))
    print("  deeper %d, shallower %d, equal %d, summed %+d"
          % (R["agreed_move_only"]["positive"], R["agreed_move_only"]["negative"],
             R["agreed_move_only"]["tie"], R["agreed_move_only"]["sum_d_depth"]))
    print("-- nodes --")
    print("  S14 %d (%.2fx budget), PC20 %d (%.2fx budget), ratio %.3f"
          % (s14n, R["nodes"]["S14_overshoot"], pc20n, R["nodes"]["PC20_overshoot"], R["nodes"]["ratio"]))

    out = os.path.join(a.outdir, "sign_19c46_%d.json" % a.budget)
    with open(out, "w") as f:
        json.dump(R, f, indent=2)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
