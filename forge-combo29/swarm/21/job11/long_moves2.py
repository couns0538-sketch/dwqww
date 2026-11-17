#!/usr/bin/env python3
"""long_moves2.py EXE OUTDIR [NPLIES]

Area 1 job 3 AGAIN on a seed-2111 game, with the 19-F12-safe driver.

Per case a FRESH process, and `go perft` is read to its `nodes` line (asserted present — an
empty parse raises instead of comparing nothing).

Cases:
  1. the whole 1,000-ply legal list: perft 1 and perft 2 vs python-chess
  2. the same list with one illegal move (with a real piece on the from-square) at ply
     1, 10 and 500: the kept position vs the legal prefix, at perft 1 and perft 2
  3. a non-UCI token at ply 1

python-chess perft 2 is computed on a board copy per move.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of  # noqa: E402,F401

import chess

SEED = 2111
STRIDE = 7


def build(nplies):
    rng = random.Random(SEED)
    b = chess.Board()
    plies, boards = [], [b.copy()]
    while len(plies) < nplies:
        ms = list(b.legal_moves)
        if not ms:
            break
        b.push(rng.choice(ms))
        plies.append(b.peek().uci())
        boards.append(b.copy())
    return plies, boards


def perft2(bd):
    t = 0
    for m in bd.legal_moves:
        c = bd.copy()
        c.push(m)
        t += c.legal_moves.count()
    return t


def illegal_token(board):
    legal = {m.uci() for m in board.legal_moves}
    for frm in chess.SQUARES:
        p = board.piece_at(frm)
        if p is None:
            continue
        for to in chess.SQUARES:
            if frm == to:
                continue
            tok = chess.square_name(frm) + chess.square_name(to)
            if tok in legal:
                continue
            tgt = board.piece_at(to)
            if tgt is not None and tgt.color == p.color:
                return tok
    for frm in chess.SQUARES:
        if board.piece_at(frm) is None:
            continue
        for to in chess.SQUARES:
            tok = chess.square_name(frm) + chess.square_name(to)
            if tok not in legal and frm != to:
                return tok
    raise RuntimeError("no illegal token")


def nodes_of(lines, case):
    vals = [int(l.split()[1]) for l in lines if l.startswith("nodes ")]
    if not vals:
        raise AssertionError("%s: no `nodes` line — the check measured nothing" % case)
    return vals[0]


def measure(exe, outdir, tag, seq):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"))
    ans = e.position("position startpos moves " + " ".join(seq))
    n1 = nodes_of(e.go("go perft 1", token="nodes", timeout=180), tag + " perft1")
    n2 = nodes_of(e.go("go perft 2", token="nodes", timeout=300), tag + " perft2")
    e.close()
    return dict(answer=[l for l in ans if "info string" in l], perft1=n1, perft2=n2)


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    nplies = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    os.makedirs(outdir, exist_ok=True)
    plies, boards = build(nplies)
    with open(os.path.join(outdir, "game_moves.txt"), "w") as fh:
        fh.write("SEED %d, %d plies\n" % (SEED, len(plies)))
        for i, m in enumerate(plies, 1):
            fh.write("%d %s\n" % (i, m))

    res = {}
    res["full"] = measure(exe, outdir, "full", plies)
    res["full"]["py1"] = boards[-1].legal_moves.count()
    res["full"]["py2"] = perft2(boards[-1].copy())

    for k in (1, 10, 500):
        if k > len(plies):
            continue
        tok = illegal_token(boards[k - 1])
        seq = plies[:k - 1] + [tok] + plies[k - 1:]
        r = measure(exe, outdir, "illegal_%d" % k, seq)
        r["token"] = tok
        r["py1"] = boards[k - 1].legal_moves.count()
        r["py2"] = perft2(boards[k - 1].copy())
        res["illegal_%d" % k] = r

    r = measure(exe, outdir, "garbage_1", ["z9z9"] + plies)
    r["py1"] = boards[0].legal_moves.count()
    r["py2"] = perft2(boards[0].copy())
    res["garbage_1"] = r

    rows = ["| case | answer line | perft1 engine | perft1 python | perft2 engine | perft2 python |",
            "|---|---|---|---|---|---|"]
    ok = True
    for tag, r in res.items():
        rows.append("| %s | %s | %d | %d | %d | %d |" % (
            tag, " ;; ".join(r["answer"])[:70] or "none", r["perft1"], r["py1"],
            r["perft2"], r["py2"]))
        if r["perft1"] != r["py1"] or r["perft2"] != r["py2"]:
            ok = False
    text = "\n".join(rows)
    verdict = ("CONFIRMS the prefix rule on the SEED 2111 game" if ok
               else "REFUTES (a perft differs from python-chess)")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n\n=> " + verdict + "\n")
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(text + "\n\n=> " + verdict)


if __name__ == "__main__":
    main()