#!/usr/bin/env python3
"""Compare engine and reference perft files; print the counts and every difference.

Both inputs have lines "# idx depth nodes marker".
Produces the summary table and, for each differing position, a divide (per-root-move
breakdown at the shallowest differing depth) computed here from python-chess.
Usage: compare.py ENGINE REF FENS OUT_MD
"""
import sys

import chess


def perft(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return sum(1 for _ in board.generate_legal_moves())
    n = 0
    for m in board.generate_legal_moves():
        board.push(m)
        n += perft(board, depth - 1)
        board.pop()
    return n


def divide(board, depth):
    d = {}
    for m in board.generate_legal_moves():
        board.push(m)
        d[m.uci()] = perft(board, depth - 1)
        board.pop()
    return d


def load(path):
    recs = {}
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        recs[(int(parts[0]), int(parts[1]))] = (parts[2], parts[3])
    return recs


def main():
    eng = load(sys.argv[1])
    ref = load(sys.argv[2])
    fens = [l.strip() for l in open(sys.argv[3]) if l.strip()]
    out = open(sys.argv[4], "w")

    depths = sorted({d for (_, d) in eng})
    out.write("## per-depth comparison (5000 R positions)\n\n")
    out.write("depth | engine records | ref records | equal | differing | engine-not-ok | ref-not-ok\n")
    out.write("---|---|---|---|---|---|---\n")
    diffs = []
    for d in depths:
        e_ok = r_ok = eq = 0
        e_bad = r_bad = 0
        for idx in range(len(fens)):
            e = eng.get((idx, d))
            r = ref.get((idx, d))
            if e is None or r is None:
                continue
            if e[1] != "OK":
                e_bad += 1
            if r[1] != "OK":
                r_bad += 1
            if e[1] != "OK" or r[1] != "OK":
                continue
            if e[0] == r[0]:
                eq += 1
            else:
                diffs.append((idx, d, e[0], r[0]))
        out.write(f"{d} | {sum(1 for i in range(len(fens)) if (i,d) in eng)} | "
                  f"{sum(1 for i in range(len(fens)) if (i,d) in ref)} | {eq} | "
                  f"{sum(1 for x in diffs if x[1]==d)} | {e_bad} | {r_bad}\n")

    out.write("\nTOTAL differing (position,depth) pairs: %d\n" % len(diffs))
    if diffs:
        out.write("\n## every difference with its divide\n\n")
        seen = set()
        for idx, d, e, r in sorted(diffs, key=lambda x: (x[1], x[0])):
            out.write(f"\nposition {idx} depth {d}: engine {e} ref {r}\n")
            out.write("FEN " + fens[idx] + "\n")
            if idx not in seen and d >= 2:
                seen.add(idx)
                b = chess.Board(fens[idx])
                dv = divide(b, d - 0)
                # engine divide at depth d is not available from perft alone; note that
                out.write("python-chess divide depth %d: " % d + " ".join(
                    f"{k}:{v}" for k, v in sorted(dv.items())) + "\n")
    out.close()

    # also paste the machine-checkable summary to stdout
    print("differing pairs", len(diffs))
    for x in diffs[:20]:
        print("DIFF", x)


main()
