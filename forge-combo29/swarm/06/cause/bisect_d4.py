#!/usr/bin/env python3
"""THE DECISIVE BISECTION at depth 4: same positions visited? same evaluations? same picker scores?

Logs every visited node on both sides (position, ply, static eval, in-check), folds each position
through the colour mirror to get a canonical id, then asks:
  - which positions were visited on BOTH sides
  - for those, is the static evaluation identical
  - which positions were visited on only one side (the path divergence)
The answer names which of the two possible conclusions holds.

usage: bisect_d4.py EXE FEN DEPTH
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def dump(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def w(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def r():
        l = p.stdout.readline()
        if l == "":
            raise RuntimeError("died")
        return l

    def rd():
        while True:
            if r().strip() == "readyok":
                return

    w("uci")
    while r().strip() != "uciok":
        pass
    for n, v in [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")] + S14:
        w("setoption name %s value %s" % (n, v)); w("isready"); rd()
    w("ucinewgame"); w("isready"); rd()
    w("position fen " + fen); w("isready"); rd()
    w("go depth %d" % depth)
    nodes = []
    score = None
    while True:
        l = r().strip()
        if l.startswith("info string node "):
            t = l.split()
            nodes.append({"ply": int(t[4]), "eval": int(t[6]), "check": t[8],
                          "fen": " ".join(t[10:])})
        elif l.startswith("info") and " pv " in l:
            tt = l.split()
            score = (tt[tt.index("score") + 1], int(tt[tt.index("score") + 2]),
                     int(tt[tt.index("nodes") + 1]))
        elif l.startswith("bestmove"):
            break
    p.kill()
    return nodes, score


def canon(fen):
    """Fold the colour mirror: the smaller of (fen, mirror(fen)) is the canonical id."""
    try:
        b = chess.Board(fen)
    except Exception:
        return None, fen
    m = b.mirror().fen()
    return (fen if fen <= m else m), fen


def main():
    exe, fen, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
    mfen = chess.Board(fen).mirror().fen()
    na, sa = dump(exe, fen, depth)
    nb, sb = dump(exe, mfen, depth)
    print("FEN   : " + fen)
    print("MIRROR: " + mfen)
    print("depth : %d" % depth)
    print("score self   : %s %s, nodes %s" % sa)
    print("score mirror : %s %s, nodes %s" % sb)
    print("")
    print("nodes logged: self %d, mirror %d" % (len(na), len(nb)))

    def build(rows):
        d = {}
        for r in rows:
            cid, raw = canon(r["fen"])
            if cid is None:
                continue
            d.setdefault(cid, []).append(r)
        return d

    da, db = build(na), build(nb)
    common = set(da) & set(db)
    only_a = set(da) - set(db)
    only_b = set(db) - set(da)
    print("distinct canonical positions: self %d, mirror %d" % (len(da), len(db)))
    print("  visited on BOTH sides : %d" % len(common))
    print("  visited on self only  : %d" % len(only_a))
    print("  visited on mirror only: %d" % len(only_b))
    print("")
    print("=== for positions visited on BOTH sides, compare the static evaluation ===")
    print("| canonical position (first 60 chars) | eval self | eval mirror | equal |")
    print("|---|---|---|---|")
    ne = 0
    for cid in sorted(common)[:40]:
        ea = da[cid][0]["eval"]
        eb = db[cid][0]["eval"]
        if ea != eb:
            ne += 1
        print("| %s | %d | %d | %s |" % (cid[:60], ea, eb, ea == eb))
    if len(common) > 40:
        print("| ... %d more | | | |" % (len(common) - 40))
    print("")
    print("common positions whose static eval DIFFERS: %d of %d" % (ne, len(common)))
    print("")
    print("=== positions visited on ONE side only (the path divergence) ===")
    print("| side | canonical position (first 70 chars) | eval |")
    print("|---|---|---|")
    for cid in sorted(only_a)[:12]:
        print("| self only | %s | %d |" % (cid[:70], da[cid][0]["eval"]))
    for cid in sorted(only_b)[:12]:
        print("| mirror only | %s | %d |" % (cid[:70], db[cid][0]["eval"]))
    print("")
    print("VERDICT")
    if ne > 0:
        print("  A: a position present on BOTH sides has a DIFFERENT static evaluation (%d of %d)." % (ne, len(common)))
        print("     A genuine evaluation asymmetry exists below the root; its first occurrence is where")
        print("     the score divergence begins.")
    else:
        print("  B: EVERY position common to both sides scores IDENTICALLY (0 of %d differ), and only the" % len(common))
        print("     visited set differs (%d self-only, %d mirror-only). So ordering triggered a path"
              % (len(only_a), len(only_b)))
        print("     divergence that only looks like an evaluation asymmetry.")


if __name__ == "__main__":
    main()
