#!/usr/bin/env python3
"""extreme_safe.py EXE OUTDIR

Area 1 job 2 AGAIN (the cycle's repeat), on inputs generated from SEED 2111, driven by the
19-F12-safe driver. What differs from job3 (SEED 2101):

  - the clock values are drawn from a seed-2111 list instead of a fixed list (same KIND of
    extremes, different values, so a special case that only triggers on one particular value
    would show up as a difference)
  - every search is read to `bestmove` before the next command, and `OwnBook false` is set
  - perft 2 is compared against python-chess for EVERY case where python-chess accepts the
    FEN, and the comparison ASSERTS that a `nodes` line was found (seat 19's integrity rule)

Writes per-case raw files, a summary table, and summary.json.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

SEED = 2111
BASE = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - {hm} {fm}"


def cases():
    rng = random.Random(SEED)
    out = []
    # halfmove: the job3 list plus five seed-drawn values above 100
    hms = [0, 99, 100, 150, 9999, -1, 2147483648, 65535, 65536]
    hms += [rng.randrange(101, 200000) for _ in range(5)]
    for hm in hms:
        out.append(("hm_%s" % hm, BASE.format(hm=hm, fm=1)))
    fms = [0, 1, 10, 1000000000, -1, 65535, 65536]
    fms += [rng.randrange(2, 5000) for _ in range(3)]
    for fm in fms:
        out.append(("fm_%s" % fm, BASE.format(hm=0, fm=fm)))
    # ep square variants, drawn around the base board
    out += [
        ("ep_e3", "r3k2r/pppppppp/8/8/8/4P3/PPPP1PPP/R3K2R w KQkq e3 0 1"),
        ("ep_e6", "r3k2r/pppppppp/4P3/8/8/8/PPPP1PPP/R3K2R w KQkq e6 0 1"),
        ("ep_d6_legal", "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"),
        ("ep_z3", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq z3 0 1"),
        ("ep_e9", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq e9 0 1"),
        ("ep_e0", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq e0 0 1"),
        ("two_white_kings", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K1KR w KQkq - 0 1"),
        ("no_kings", "r7/pppppppp/8/8/8/8/PPPPPPPP/R7 w KQkq - 0 1"),
        ("white_pawn_r1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/P3K2R w kq - 0 1"),
        ("black_pawn_r8", "r3k2r/pppppppp/8/8/8/8/PPPPPPPp/R3K2R w KQkq - 0 1"),
        ("hm100_mate_in_1", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"),
        ("hm100_black_mate_in_1", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 b - - 100 60"),
    ]
    return out


def perft2(bd):
    t = 0
    for m in bd.legal_moves:
        bd.push(m)
        t += bd.legal_moves.count()
        bd.pop()
    return t


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    results = []
    for name, fen in cases():
        e = SafeEngine(exe, os.path.join(outdir, name + "_raw.txt"))
        ans = e.position("position fen " + fen)
        try:
            gl = e.go("go depth 4", timeout=60)
            go_txt, go_best = " | ".join(gl), bestmove_of(gl)
            go_info = last_info(gl)
        except Timeout:
            go_txt, go_best, go_info = "TIMEOUT", "-", ""
        try:
            pl = e.go("go perft 2", token="nodes", timeout=120)
            nodes = [int(l.split()[1]) for l in pl if l.startswith("nodes ")]
            if not nodes:
                raise AssertionError("%s: no `nodes` line in the perft answer" % name)
            eng_perft = nodes[0]
        except (Timeout, AssertionError) as exc:
            eng_perft = "MISSING(%s)" % exc
        e.close()
        refused = any("invalid FEN" in l for l in ans)
        try:
            b = chess.Board(fen)
            py_ok, py_n = True, perft2(b.copy())
        except Exception:
            py_ok, py_n = False, "-"
        results.append(dict(name=name, fen=fen, refused=refused,
                            answer=next((l for l in ans if "info string" in l), ""),
                            depth4=go_info, best=go_best, perft=eng_perft,
                            py_accepts=py_ok, py_perft=py_n))

    rows = ["| case | refused | answer | depth-4 info | bestmove | perft2 engine | py accepts | perft2 python |",
            "|---|---|---|---|---|---|---|---|"]
    mismatches = []
    for r in results:
        rows.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["refused"], r["answer"][:44].replace("|", "/"),
            r["depth4"][-46:].replace("|", "/"), r["best"], r["perft"],
            r["py_accepts"], r["py_perft"]))
        if not r["refused"] and r["py_accepts"] and str(r["perft"]) != str(r["py_perft"]):
            mismatches.append(r["name"])
    zero_node = [r["name"] for r in results if "nodes 0 " in (r["depth4"] or "")]
    rows.append("")
    rows.append("accepted-but-wrong-perft: %s" % (mismatches or "none"))
    rows.append("searches that answered with 0 nodes: %s" % (zero_node or "none"))
    rows.append("cases where a `nodes` line was MISSING (would be a parser failure): %s"
                % ([r["name"] for r in results if str(r["perft"]).startswith("MISSING")] or "none"))
    text = "\n".join(rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()