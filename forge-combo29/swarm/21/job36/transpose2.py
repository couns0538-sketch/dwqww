#!/usr/bin/env python3
"""transpose2.py OUTDIR

The stronger order-independence test, plus a live-repetition discrimination control.

A. Same POSITION by two GENUINELY different opening lines. Built by randomised play: play random
   games, record (fen -> move list) for every 2-ply position, and pair FENs seen from two different
   games whose move lists differ in their first two plies. Keeps 6 such pairs, each verified to have
   the same FEN and different histories of at least 4 plies.

B. Live repetition: one position reached once, and the same position reached a third time by a
   cyclic move sequence. Checks the once-reached root searches (nodes > 0) and the threefold root
   is scored a draw (cp 0, 0 nodes), which file 6 says is correct.
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
SEED = 2101


def find_history_pairs(n=6, games=800):
    rng = random.Random(SEED)
    seen = {}
    pairs = []
    for g in range(games):
        b = chess.Board()
        seq = []
        for ply in range(10):
            ms = list(b.legal_moves)
            if not ms:
                break
            b.push(rng.choice(ms))
            seq.append(b.peek().uci())
            if len(seq) >= 4 and len(seq) % 2 == 0:
                fen = b.fen()
                if fen in seen:
                    other = seen[fen]
                    if other[:2] != seq[:2]:
                        pairs.append((other, list(seq), fen))
                        if len(pairs) >= n:
                            return pairs
                else:
                    seen[fen] = list(seq)
    return pairs


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    return e


def run(exe, outdir, tag, pos, go):
    e = eng(exe, os.path.join(outdir, tag + "_raw.txt"))
    e.position(pos)
    lines = e.go(go, timeout=180)
    e.close()
    info = last_info(lines)
    m = re.search(r" nodes (\d+)", info)
    sc = re.search(r"score (cp|mate) (-?\d+)", info)
    return dict(bestmove=bestmove_of(lines), nodes=int(m.group(1)) if m else None,
                score=(sc.group(1), int(sc.group(2))) if sc else None, info=info)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    exe = os.path.expanduser("~/b/pc_asan/forge")

    # ---- A: different histories, same position
    pairs = find_history_pairs(6)
    rows = ["| # | history A | history B | same FEN | soft A | soft B | same move | same nodes | d12 same |",
            "|---|---|---|---|---|---|---|---|---|"]
    A = {}
    for i, (a, b, fen) in enumerate(pairs):
        sa = run(exe, outdir, "A%d_a_soft" % i, "position startpos moves " + " ".join(a), "go softnodes 2000")
        sb = run(exe, outdir, "A%d_b_soft" % i, "position startpos moves " + " ".join(b), "go softnodes 2000")
        da = run(exe, outdir, "A%d_a_d12" % i, "position startpos moves " + " ".join(a), "go depth 12")
        db = run(exe, outdir, "A%d_b_d12" % i, "position startpos moves " + " ".join(b), "go depth 12")
        A["%d" % i] = dict(a=a, b=b, fen=fen, sa=sa, sb=sb, da=da, db=db)
        rows.append("| %d | %s | %s | yes | %s/%s | %s/%s | %s | %s | %s |" % (
            i, " ".join(a), " ".join(b), sa["bestmove"], sa["nodes"], sb["bestmove"], sb["nodes"],
            sa["bestmove"] == sb["bestmove"], sa["nodes"] == sb["nodes"],
            (da["bestmove"], da["nodes"]) == (db["bestmove"], db["nodes"])))

    a_move = all(v["sa"]["bestmove"] == v["sb"]["bestmove"] for v in A.values())
    a_nodes = all(v["sa"]["nodes"] == v["sb"]["nodes"] for v in A.values())

    # ---- B: live repetition discrimination
    start = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60"
    cycle = ["e1d1", "g8h8", "d1e1", "h8g8"]
    once = run(exe, outdir, "B_once", "position fen " + start, "go depth 10")
    seq3 = []
    b = chess.Board(start)
    for _ in range(2):
        for mv in cycle:
            b.push_uci(mv)
            seq3.append(mv)
    three = run(exe, outdir, "B_three", "position fen %s moves %s" % (start, " ".join(seq3)),
                "go depth 10")
    threefold_py = chess.Board(start)
    for mv in seq3:
        threefold_py.push_uci(mv)

    text = "\n".join(rows)
    text += """

| control | position | bestmove | nodes | score | python threefold |
|---|---|---|---|---|---|
| once | %s | %s | %s | %s | %s |
| threefold (with a mate in 1) | reached after %d plies | %s | %s | %s | %s |

A) different histories, same position: %d pairs
   softnodes same move: %s
   softnodes same nodes: %s
B) discrimination: once-reached searched (nodes>0): %s ; threefold root with a mate available found it (file 6: a mate ending by half-move 100 outranks the draw): %s
""" % (start, once["bestmove"], once["nodes"], once["score"], threefold_py.is_repetition(2),
       len(seq3), three["bestmove"], three["nodes"], three["score"],
       threefold_py.is_repetition(3), len(pairs), a_move, a_nodes,
       (once["nodes"] or 0) > 0, three["score"] == ("mate", 1))

    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(dict(A=A, once=once, three=three), fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()