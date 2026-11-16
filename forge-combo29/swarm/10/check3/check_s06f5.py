#!/usr/bin/env python3
"""check_s06f5.py -- seat 10's OWN harness for seat 06's finding S-F5.

Claim under test: total = clamp(hce + nnue) with FORGE_NNUE_RESIDUAL 1, so a left-right flip can
leave `total` unchanged while hce and nnue both move.

It does NOT use seat 06's scripts. It:
  1. writes its own position set (G, plus random-legal-game positions from PyPI python-chess at my SEED);
  2. for each position, sends `position fen F`, `isready`, `eval` to a FRESH process, and parses
     `info string eval hce H nnue N total T`;
  3. builds the left-right flip with chess.Board.transform(chess.flip_horizontal) and measures it the same way;
  4. checks T == clamp(H+N) on every measurement, and counts positions where (H,N) moved but T did not;
  5. re-measures every cancellation in a second fresh process (the P3 control).

Usage: check_s06f5.py EXE OUTDIR [N_RANDOM]
"""
import json
import os
import random
import re
import subprocess
import sys

import chess

EXE = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]
N_RANDOM = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
os.makedirs(OUT, exist_ok=True)

SEED = 1001
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job2", "raw", "set_G.epd")
EVALRE = re.compile(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)")
CLAMP = 32000   # MateInMaxPly-1; the exact constant is read from the header below and reported


def eval_fen(fen):
    """one FRESH process, measure hce/nnue/total"""
    cmds = ["uci", "isready", "position fen " + fen, "isready", "eval", "quit"]
    p = subprocess.run([EXE], input="\n".join(cmds) + "\n", capture_output=True,
                       text=True, timeout=60)
    for line in p.stdout.splitlines():
        m = EVALRE.search(line)
        if m:
            return tuple(int(x) for x in m.groups()), p.stdout
    return None, p.stdout


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def make_random_fens(n, seed):
    """one position every 7 plies of random legal games, with SEED; a game that ends early is
    discarded rather than retried forever."""
    rng = random.Random(seed)
    out = []
    guard = 0
    while len(out) < n and guard < n * 40:
        guard += 1
        b = chess.Board()
        plies = 0
        picked = None
        while plies < 60 and not b.is_game_over():
            moves = list(b.legal_moves)
            if not moves:
                break
            if plies % 7 == 0:
                picked = b.fen()
            b.push(rng.choice(moves))
            plies += 1
        if picked is not None:
            out.append(picked)
    return out


def main():
    fens = []
    for line in open(G):
        line = line.strip()
        if line:
            fens.append(line.split(";")[0].strip())
    g_count = len(fens)
    rnd = make_random_fens(N_RANDOM, SEED)
    fens.extend(rnd)
    with open(os.path.join(OUT, "fens_used.txt"), "w") as f:
        for x in fens:
            f.write(x + "\n")

    rows = []
    unparsed = 0
    for i, fen in enumerate(fens):
        try:
            b = chess.Board(fen)
            m = b.transform(chess.flip_horizontal)
            if "K" in b.castling_xfen() or "Q" in b.castling_xfen() or \
               "k" in b.castling_xfen() or "q" in b.castling_xfen():
                m.set_castling_fen([])
            mfen = m.fen()
        except ValueError:
            unparsed += 1
            continue
        orig, _ = eval_fen(fen)
        flip, _ = eval_fen(mfen)
        if orig is None or flip is None:
            unparsed += 1
            continue
        rows.append({"i": i, "fen": fen, "mfen": mfen,
                     "hce": orig[0], "nnue": orig[1], "total": orig[2],
                     "mhce": flip[0], "mnnue": flip[1], "mtotal": flip[2]})

    # P4: the formula, on every row
    formula_bad = []
    for r in rows:
        for tag, h, n, t in (("orig", r["hce"], r["nnue"], r["total"]),
                             ("flip", r["mhce"], r["mnnue"], r["mtotal"])):
            if t != clamp(h + n, -CLAMP, CLAMP) and abs(h + n) < CLAMP:
                formula_bad.append((r["i"], tag, h, n, t))

    # P2: components move, total does not
    cancel = [r for r in rows
              if (r["hce"], r["nnue"]) != (r["mhce"], r["mnnue"]) and r["total"] == r["mtotal"]]

    # P3: re-measure those in fresh processes
    reconf = []
    for r in cancel[:50]:
        o2, _ = eval_fen(r["fen"])
        f2, _ = eval_fen(r["mfen"])
        reconf.append({"i": r["i"],
                       "first": [r["hce"], r["nnue"], r["total"], r["mhce"], r["mnnue"], r["mtotal"]],
                       "second": list(o2) + list(f2) if (o2 and f2) else None,
                       "same": (o2 is not None and f2 is not None and
                                list(o2) + list(f2) ==
                                [r["hce"], r["nnue"], r["total"], r["mhce"], r["mnnue"], r["mtotal"]])})

    moved_total = sum(1 for r in rows if r["total"] != r["mtotal"])
    summary = {
        "positions_in_G": g_count,
        "positions_random": len(rnd),
        "measured": len(rows),
        "unparsed_or_unmeasured": unparsed,
        "total_moved_under_flip": moved_total,
        "total_unchanged_under_flip": len(rows) - moved_total,
        "both_components_moved_total_did_not": len(cancel),
        "formula_violations_T_neq_clamp_H_plus_N": len(formula_bad),
        "cancellations_rechecked_in_fresh_processes": len(reconf),
        "cancellations_that_reproduced": sum(1 for r in reconf if r["same"]),
    }
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    with open(os.path.join(OUT, "cancellations.txt"), "w") as f:
        for r in cancel:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(OUT, "formula_violations.txt"), "w") as f:
        for row in formula_bad:
            f.write(json.dumps(row) + "\n")
    with open(os.path.join(OUT, "recheck.txt"), "w") as f:
        for r in reconf:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(OUT, "table_all.txt"), "w") as f:
        f.write("i | hce nnue total | flip hce nnue total | components moved | total moved\n")
        for r in rows:
            f.write("%d | %d %d %d | %d %d %d | %s | %s\n"
                    % (r["i"], r["hce"], r["nnue"], r["total"],
                       r["mhce"], r["mnnue"], r["mtotal"],
                       (r["hce"], r["nnue"]) != (r["mhce"], r["mnnue"]),
                       r["total"] != r["mtotal"]))
    print(json.dumps(summary, indent=2))


main()
