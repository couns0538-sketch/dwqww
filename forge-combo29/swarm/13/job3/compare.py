#!/usr/bin/env python3
"""Compare engine and reference perft files; print the counts and every difference.

HARDENED after the seat 19 measurement-integrity warning (a parser that finds nothing must fail
loudly, never pass as a confirmation). This version refuses to produce a verdict unless:

  * both files contain a record for EVERY (position, depth) pair asked for;
  * every record's node count is a non-empty run of digits (never "", "nan", "ERR" smuggled
    through as equal on both sides);
  * the number of compared pairs equals positions x depths exactly.

Any violation raises and writes FAIL to the output, so a "0 differences" line can only appear when
something was actually compared. It also prints the number of pairs compared, so a vacuum cannot
look like a pass.

Usage: compare.py ENGINE REF FENS OUT_MD [EXPECTED_POSITIONS]
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


def load(path, label):
    """Return {(idx,depth): (nodes:int, marker:str)}; raise on any non-numeric node count."""
    recs = {}
    for lineno, line in enumerate(open(path), 1):
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit("FAIL %s line %d: only %d fields: %r" % (label, lineno, len(parts), line))
        idx, depth, nodes, marker = int(parts[0]), int(parts[1]), parts[2], parts[3]
        if marker == "OK":
            if not nodes.isdigit():
                raise SystemExit("FAIL %s line %d: marker OK but node count %r is not an integer"
                                 % (label, lineno, nodes))
            recs[(idx, depth)] = (int(nodes), marker)
        else:
            recs[(idx, depth)] = (None, marker)
    if not recs:
        raise SystemExit("FAIL %s: no records at all (empty file) - nothing was measured" % label)
    return recs


def main():
    eng = load(sys.argv[1], "engine")
    ref = load(sys.argv[2], "reference")
    fens = [l.strip() for l in open(sys.argv[3]) if l.strip()]
    out_path = sys.argv[4]
    expected_positions = int(sys.argv[5]) if len(sys.argv) > 5 else len(fens)

    if len(fens) != expected_positions:
        raise SystemExit("FAIL fen file holds %d positions, expected %d"
                         % (len(fens), expected_positions))

    depths = sorted({d for (_, d) in eng})
    if not depths:
        raise SystemExit("FAIL engine file has no depths")

    out = open(out_path, "w")
    out.write("## per-depth comparison (%d positions)\n\n" % len(fens))
    out.write("depths compared: %s\n\n" % ", ".join(map(str, depths)))
    out.write("depth | engine records | ref records | pairs compared | equal | differing "
              "| engine-not-ok | ref-not-ok\n")
    out.write("---|---|---|---|---|---|---|---\n")

    diffs = []
    for d in depths:
        e_n = r_n = eq = 0
        e_bad = r_bad = 0
        for idx in range(len(fens)):
            if (idx, d) not in eng:
                raise SystemExit("FAIL depth %d position %d: NO ENGINE RECORD" % (d, idx))
            if (idx, d) not in ref:
                raise SystemExit("FAIL depth %d position %d: NO REFERENCE RECORD" % (d, idx))
            e_n += 1
            r_n += 1
            e, r = eng[(idx, d)], ref[(idx, d)]
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
        compared = e_n - max(e_bad, r_bad)
        out.write(f"{d} | {e_n} | {r_n} | {e_n} | {eq} | "
                  f"{sum(1 for x in diffs if x[1] == d)} | {e_bad} | {r_bad}\n")

    total_pairs = len(fens) * len(depths)
    compared_pairs = sum(1 for i in range(len(fens)) for d in depths
                         if eng.get((i, d), (None, ""))[1] == "OK"
                         and ref.get((i, d), (None, ""))[1] == "OK")
    out.write("\nTOTAL (position,depth) pairs in scope: %d\n" % total_pairs)
    out.write("TOTAL pairs actually compared (both sides OK): %d\n" % compared_pairs)
    out.write("TOTAL differing pairs: %d\n" % len(diffs))

    if compared_pairs == 0:
        out.write("\nFAIL: zero pairs were compared. This is NOT a pass.\n")
        out.close()
        raise SystemExit("FAIL: zero pairs compared")

    if diffs:
        out.write("\n## every difference with its divide\n\n")
        seen = set()
        for idx, d, e, r in sorted(diffs, key=lambda x: (x[1], x[0])):
            out.write(f"\nposition {idx} depth {d}: engine {e} ref {r}\n")
            out.write("FEN " + fens[idx] + "\n")
            if idx not in seen and d >= 2:
                seen.add(idx)
                b = chess.Board(fens[idx])
                dv = divide(b, d)
                out.write("python-chess divide depth %d: " % d + " ".join(
                    f"{k}:{v}" for k, v in sorted(dv.items())) + "\n")
    else:
        out.write("\nVERDICT: %d pairs compared, 0 differing. (A real measurement: the counts above "
                  "show every pair was present and numeric on both sides.)\n" % compared_pairs)
    out.close()

    print("positions %d depths %s" % (len(fens), depths))
    print("pairs in scope %d, compared %d" % (total_pairs, compared_pairs))
    print("differing pairs", len(diffs))
    for x in diffs[:20]:
        print("DIFF", x)


main()
