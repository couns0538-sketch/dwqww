#!/usr/bin/env python3
"""drawnroot_pc20.py EXE LABEL OUTDIR — my drawn-root findings re-run on a build under PC20.

My findings this tests:
  S-F5/S-C1  mate in one at halfmove 100 answered with 0 nodes and the first legal move
  S-F4       the same door through board.is_repetition()
  S-F17      my patch closes both (base tree only)
  S-F18      claimable vs automatic draws
FABLE_TO_swarm_3 says the PC build REPAIRS this: "the PC's engine searches such a root like any other
(only a root with insufficient material is still answered at once)", and that a second repetition is
searched normally anyway because `Board::is_repetition` needs matches >= 2.

So this script records, per case, on the PC r15 build under PC20 with Threads 1:
  halfmove 99 / 100 / 150 mate-in-one, the third-repetition mate, K v K, KQ v K at halfmove 150,
  and the counter-resetting pawn-move mate from seat 01.
For each: bestmove, score, nodes, last depth. A repaired build must SEARCH the mate cases (nodes > 0,
score mate) and must still answer K v K from the shortcut (0 nodes).

Usage: drawnroot_pc20.py EXE LABEL OUTDIR
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
MATE = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - {hm} 1"
SHUF = "a1b1 g8f8 b1a1 f8g8"
CASES = [
    ("hm99_mate1", ("position fen " + MATE.format(hm=99))),
    ("hm100_mate1", ("position fen " + MATE.format(hm=100))),
    ("hm150_mate1", ("position fen " + MATE.format(hm=150))),
    ("rep3_mate1", ("position fen " + MATE.format(hm=0) + " moves " + SHUF + " " + SHUF)),
    ("counterreset_hm100", "position fen 8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1"),
    ("kvk_hm0", "position fen 7k/8/8/8/8/8/8/K7 w - - 0 1"),
    ("kqk_hm150", "position fen 8/5K2/7Q/4k3/8/8/8/8 w - - 150 1"),
]
FENS = {
    "hm99_mate1": MATE.format(hm=99), "hm100_mate1": MATE.format(hm=100),
    "hm150_mate1": MATE.format(hm=150), "rep3_mate1": MATE.format(hm=0),
    "counterreset_hm100": "8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1",
    "kvk_hm0": "7k/8/8/8/8/8/8/K7 w - - 0 1", "kqk_hm150": "8/5K2/7Q/4k3/8/8/8/8 w - - 150 1",
}


def probe(exe, pos, depth=12):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(pos)
    eng.send("isready")
    _l, ok = eng.read_until("readyok", 20)
    if not ok:
        eng.close()
        return {"best": "NOREOK", "score": "", "nodes": "", "depth": 0}
    eng.send(f"go depth {depth}")
    out, ok = eng.read_until("bestmove", 300)
    eng.close()
    best, score, nodes, d = "", "", "", 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            d = max(d, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = f[f.index("nodes") + 1]
            if "score" in f:
                score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
    return {"best": best, "score": score, "nodes": nodes, "depth": d}


def main() -> int:
    exe, label, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    print(f"build {label}, settings PC20, Threads 1 sent explicitly, go depth 12")
    print()
    print("| case | bestmove | score | nodes | depth | searched? | bestmove is mate |")
    print("|---|---|---|---|---|---|---|")
    rows = []
    for name, pos in CASES:
        r = probe(exe, pos)
        try:
            moved = chess.Move.from_uci(r["best"]) in chess.Board(FENS[name]).legal_moves
            board = chess.Board(FENS[name])
            board.push(chess.Move.from_uci(r["best"]))
            mate = board.is_checkmate()
        except ValueError:
            mate = "n/a"
        searched = "YES" if r["nodes"] not in ("", "0") else "NO (shortcut)"
        print(f"| {name} | {r['best'] or '-'} | {r['score'] or '-'} | {r['nodes'] or '-'} | "
              f"{r['depth']} | {searched} | {mate} |")
        rows.append((name, r["best"], r["score"], r["nodes"], r["depth"], searched, mate))
    with open(os.path.join(outdir, "drawnroot.tsv"), "w") as fh:
        fh.write("case\tbestmove\tscore\tnodes\tdepth\tsearched\tis_mate\n")
        for row in rows:
            fh.write("\t".join(str(x) for x in row) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
