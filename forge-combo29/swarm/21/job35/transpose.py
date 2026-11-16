#!/usr/bin/env python3
"""transpose.py OUTDIR

Is `go softnodes` order-dependent? Build positions reachable by two different move orders
(true transpositions), then compare the engine's answer for each order.

Pairs are generated with python-chess by taking a random game and finding two move orders that
reach the same FEN: for each candidate position, try every pair of legal white moves whose orders
commute (two different white pieces moving to squares that do not interact), plus the black reply
between them.

For each pair: `position startpos moves <order A>` and `<order B>`, then `go softnodes 2000` and
`go depth 12`, comparing bestmove and node count.
"""
import json
import os
import random
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


def find_pairs(n=10):
    """Find move-order pairs (A, B) of equal length reaching identical FENs."""
    rng = random.Random(SEED)
    pairs = []
    tries = 0
    while len(pairs) < n and tries < 4000:
        tries += 1
        # two commuting white moves with one black reply between them
        w1 = rng.choice(["g1f3", "b1c3", "d2d4", "e2e4", "c2c4", "g2g3", "b2b3"])
        w2 = rng.choice(["g1f3", "b1c3", "d2d4", "e2e4", "c2c4", "g2g3", "b2b3", "f1e2", "c1d2"])
        if w1 == w2:
            continue
        b_reply = rng.choice(["g8f6", "b8c6", "d7d5", "e7e5", "c7c5"])
        for order in (["A", "B"], ["B", "A"]):
            pass
        seqA = [w1, b_reply, w2]
        seqB = [w2, b_reply, w1]
        bA, bB = chess.Board(), chess.Board()
        okA = okB = True
        for mv in seqA:
            try:
                bA.push_uci(mv)
            except Exception:
                okA = False
                break
        for mv in seqB:
            try:
                bB.push_uci(mv)
            except Exception:
                okB = False
                break
        if not (okA and okB):
            continue
        if bA.fen() != bB.fen():
            continue
        key = bA.fen()
        if any(p[2] == key for p in pairs):
            continue
        # the FENs are equal, so the positions are the same; history differs
        pairs.append((seqA, seqB, key))
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


def run(exe, outdir, tag, moves, go):
    e = eng(exe, os.path.join(outdir, tag + "_raw.txt"))
    e.position("position startpos moves " + " ".join(moves))
    lines = e.go(go, timeout=120)
    e.close()
    info = last_info(lines)
    import re
    m = re.search(r" nodes (\d+)", info)
    return dict(bestmove=bestmove_of(lines), nodes=int(m.group(1)) if m else None, info=info)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    pairs = find_pairs(10)
    exe = os.path.expanduser("~/b/pc_asan/forge")
    rows = ["| # | order A | order B | same FEN | softnodes A | softnodes B | same move | same nodes | depth12 same |",
            "|---|---|---|---|---|---|---|---|---|"]
    R = {}
    for i, (a, b, fen) in enumerate(pairs):
        sa = run(exe, outdir, "p%d_a_soft" % i, a, "go softnodes 2000")
        sb = run(exe, outdir, "p%d_b_soft" % i, b, "go softnodes 2000")
        da = run(exe, outdir, "p%d_a_d12" % i, a, "go depth 12")
        db = run(exe, outdir, "p%d_b_d12" % i, b, "go depth 12")
        R["%d" % i] = dict(a=a, b=b, fen=fen, sa=sa, sb=sb, da=da, db=db)
        rows.append("| %d | %s | %s | yes | %s/%s | %s/%s | %s | %s | %s |" % (
            i, " ".join(a), " ".join(b),
            sa["bestmove"], sa["nodes"], sb["bestmove"], sb["nodes"],
            sa["bestmove"] == sb["bestmove"], sa["nodes"] == sb["nodes"],
            (da["bestmove"], da["nodes"]) == (db["bestmove"], db["nodes"])))
    sn_move = all(v["sa"]["bestmove"] == v["sb"]["bestmove"] for v in R.values())
    sn_nodes = all(v["sa"]["nodes"] == v["sb"]["nodes"] for v in R.values())
    d12 = all((v["da"]["bestmove"], v["da"]["nodes"]) == (v["db"]["bestmove"], v["db"]["nodes"])
              for v in R.values())
    text = "\n".join(rows)
    text += ("\n\npairs: %d\nsoftnodes same move: %s\nsoftnodes same nodes: %s\n"
             "depth 12 same move+nodes: %s\n" % (len(pairs), sn_move, sn_nodes, d12))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()