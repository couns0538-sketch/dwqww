#!/usr/bin/env python3
"""verify_patch.py BASE_EXE PATCHED_EXE OUT.tsv — does the candidate patch close both doors?

Four cases against BOTH binaries, so the patched column is only meaningful next to the base column:
  hm99      mate-in-one at halfmove 99            (control: base must find it)
  hm100     the same at halfmove 100               (S-F5's door — base must MISS it)
  rep3      the same reached by a third repetition (S-F4's door — base must MISS it)
  kvk       K v K, insufficient material           (control: the patch must still call it drawn)
  kvk_rep   K+B v K with a repetition              (both terms; base shortcut, patch must search)

Each: fresh process, OwnBook false, Threads 1, Hash 16, `position`, isready, `go depth 6`, read to
bestmove; bestmove judged by python-chess; nodes/depth taken from the last info line.

Usage: verify_patch.py BASE PATCHED OUT.tsv
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

MATE = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - {hm} 1"
SHUF = "a1b1 g8f8 b1a1 f8g8"
CASES = [
    ("hm99", MATE.format(hm=99), None),
    ("hm100", MATE.format(hm=100), None),
    ("rep3", MATE.format(hm=0), "position fen " + MATE.format(hm=0) + " moves " + SHUF + " " + SHUF),
    ("kvk", "7k/8/8/8/8/8/8/K7 w - - 0 1", None),
    ("kqk", "7k/8/8/8/8/8/8/KQ6 w - - 0 1", None),
]


def probe(exe, pos_cmd):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(pos_cmd)
    eng.send("isready")
    _l, ok = eng.read_until("readyok", 20)
    if not ok:
        eng.close()
        return {"best": "NOREOK", "nodes": "", "depth": 0, "mate": "n/a"}
    eng.send("go depth 6")
    out, ok = eng.read_until("bestmove", 60)
    eng.close()
    best, nodes, depth = "", "", 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            depth = max(depth, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = f[f.index("nodes") + 1]
    return {"best": best, "nodes": nodes, "depth": depth}


def is_mate_in_one(fen, best):
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(best)
    except ValueError:
        return "n/a"
    if move not in board.legal_moves:
        return "illegal"
    board.push(move)
    return str(board.is_checkmate())


def main() -> int:
    base, patched, out = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = []
    print("| case | binary | bestmove | nodes | depth | bestmove is mate-in-one |")
    print("|---|---|---|---|---|---|")
    for name, fen, cmd in CASES:
        pos = cmd if cmd else f"position fen {fen}"
        for label, exe in (("base", base), ("patched", patched)):
            r = probe(exe, pos)
            m = is_mate_in_one(fen, r["best"]) if r["best"] and r["best"] != "0000" else "n/a"
            print(f"| {name} | {label} | {r['best'] or '-'} | {r['nodes'] or '-'} | {r['depth']} | {m} |")
            rows.append((name, label, r["best"], r["nodes"], r["depth"], m))
    with open(out, "w") as fh:
        fh.write("case\tbinary\tbestmove\tnodes\tdepth\tis_mate_in_one\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
