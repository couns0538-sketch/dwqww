#!/usr/bin/env python3
"""The last experiment: trace every ROOT move at depth 1 on both sides of a mismatching pair.

Prints, per root move: order tried, its own node delta, how many of those were qsearch nodes, and its score.
Then compares the two sides line by line to say whether the node gap is
  (a) a move tried on one side and not the other, or
  (b) a different qsearch node count under the same move.

usage: rootmove_trace.py EXE FEN
"""
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def trace(exe, fen, depth=1):
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
    rows = []
    total = None
    while True:
        l = r().strip()
        if l.startswith("info string rootmove"):
            t = l.split()
            rows.append({"move": t[3], "nodes": int(t[5]), "qnodes": int(t[7]),
                         "score": int(t[9]), "depth": int(t[11]), "order": int(t[13])})
        if l.startswith("info") and " pv " in l:
            tt = l.split()
            total = int(tt[tt.index("nodes") + 1])
        if l.startswith("bestmove"):
            break
    p.kill()
    return rows, total


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    exe, fen = sys.argv[1], sys.argv[2]
    mfen = chess.Board(fen).mirror().fen()
    a, ta = trace(exe, fen)
    b, tb = trace(exe, mfen)
    print("FEN   : " + fen)
    print("MIRROR: " + mfen)
    print("depth 1, every ROOT move as tried")
    print("")
    print("| order | move self | nodes | qnodes | score | || move mirror (mapped) | nodes | qnodes | score |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for i in range(max(len(a), len(b))):
        ra = a[i] if i < len(a) else None
        rb = b[i] if i < len(b) else None
        rb_s = ("%s" % mir(rb["move"])) if rb else "-"
        print("| %d | %s | %s | %s | %s | | %s | %s | %s | %s |" % (
            i + 1,
            ra["move"] if ra else "-", ra["nodes"] if ra else "-", ra["qnodes"] if ra else "-", ra["score"] if ra else "-",
            rb_s, rb["nodes"] if rb else "-", rb["qnodes"] if rb else "-", rb["score"] if rb else "-"))
    print("")
    na = {r["move"]: r for r in a}
    nb = {mir(r["move"]): r for r in b}
    only_a = [k for k in na if k not in nb]
    only_b = [k for k in nb if k not in na]
    print("moves tried ONLY on self  : %s" % (only_a if only_a else "none"))
    print("moves tried ONLY on mirror: %s" % (only_b if only_b else "none"))
    print("moves tried on both       : %d" % len(set(na) & set(nb)))
    print("")
    print("| move | nodes self | nodes mirror | qnodes self | qnodes mirror | differs |")
    print("|---|---|---|---|---|---|")
    nd = qd = 0
    for k in sorted(set(na) & set(nb)):
        x, y = na[k], nb[k]
        d = (x["nodes"] != y["nodes"]) or (x["qnodes"] != y["qnodes"])
        if x["nodes"] != y["nodes"]:
            nd += 1
        if x["qnodes"] != y["qnodes"]:
            qd += 1
        print("| %s | %d | %d | %d | %d | %s |" % (k, x["nodes"], y["nodes"], x["qnodes"], y["qnodes"], d))
    print("")
    print("total nodes reported: self %s, mirror %s" % (ta, tb))
    print("moves whose NODE COUNT differs: %d" % nd)
    print("moves whose QSEARCH node count differs: %d" % qd)
    print("")
    if only_a or only_b:
        print("VERDICT (a): a move is tried on one side and not the other.")
    elif qd > 0 and nd == 0:
        print("VERDICT (b): same moves, same nodes, but a different QSEARCH depth/count.")
    elif nd > 0:
        print("VERDICT (b-variant): the same moves are tried but their subtrees cost different node counts.")
    else:
        print("VERDICT: no difference at depth 1 for this pair.")


if __name__ == "__main__":
    main()
