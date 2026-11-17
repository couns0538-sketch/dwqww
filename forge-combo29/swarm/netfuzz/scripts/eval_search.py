#!/usr/bin/env python3
"""Does the accepted (re-checksummed) net produce a DIFFERENT EVALUATION anywhere?

The first probe found the flipped weight's lane is reached by a legal position, but
the accumulator value at that lane was negative in both nets (-148 vs -301), and
SCReLU clamps negatives to 0 -- so the evaluations agreed by MASKING, not because
the corruption was unreachable. That is exactly the trap the brief warns about: a
null from a corpus that could not reach the condition.

So this searches for positions where the difference survives the clamp, i.e. where
the lane's accumulator is positive in at least one of the two nets.

Usage: eval_search.py <probe> <pristine> <corrupt> <out.json> [extra fens files...]
"""
import json
import subprocess
import sys

FEATURE = 2053
LANE = 284


def lane(probe, net, fen):
    proc = subprocess.run([probe, "lane", net, fen, str(FEATURE), str(LANE)],
                          capture_output=True, text=True, timeout=60)
    out = {}
    for line in proc.stdout.splitlines():
        if line.startswith("LANE\t"):
            for part in line.split("\t")[1:]:
                bits = part.split()
                if len(bits) == 2 and bits[0] in ("white_acc", "black_acc", "w1", "hits"):
                    out[bits[0]] = int(bits[1])
            break
    return out


def evaluate(probe, net, fen):
    proc = subprocess.run([probe, "eval", net, fen], capture_output=True, text=True, timeout=60)
    for line in proc.stdout.splitlines():
        if line.startswith("EVAL\t"):
            return int(line.split("\t")[1])
    return None


def board_to_fen(pieces):
    """pieces: dict square_index -> letter, 0 = a1 .. 63 = h8."""
    rows = []
    for rank in range(7, -1, -1):
        row = ""
        empty = 0
        for file in range(8):
            square = rank * 8 + file
            char = pieces.get(square)
            if char is None:
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += char
        if empty:
            row += str(empty)
        rows.append(row)
    return "/".join(rows) + " w - - 0 1"


def generate():
    """Put a BLACK bishop on f1 (square 5, the flipped feature) with the white king on
    a square in bucket 2, and vary everything else so the corrupted lane can land
    above zero. Squares are 0 = a1 .. 63 = h8, so rank 1 is 0..7."""
    for king_sq in (2, 3, 4, 5, 6, 7):                # c1..h1; bucket 2 per the king map
        if king_sq == 5:
            continue                                   # bishop cannot share the king square
        for pawn in (None, 8, 9, 10, 12, 16, 24):
            for extra in (None, 0, 7, 56, 63, 40):
                pieces = {king_sq: "K", 5: "b"}
                pieces[63 if king_sq != 63 else 62] = "k"
                if pawn is not None and pawn not in pieces and pawn != king_sq:
                    pieces[pawn] = "P"
                if extra is not None and extra not in pieces and extra != king_sq:
                    pieces[extra] = "p"
                yield board_to_fen(pieces)


def main():
    probe, pristine, corrupt, outpath = sys.argv[1:5]
    extra = sys.argv[5:]

    fens = list(generate())
    for path in extra:
        with open(path) as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    fens.append(line.split(";")[0].strip())

    differing = []
    reaching_same = []
    checked = 0
    for fen in fens:
        before = evaluate(probe, pristine, fen)
        after = evaluate(probe, corrupt, fen)
        if before is None or after is None:
            continue
        checked += 1
        info_a = lane(probe, pristine, fen)
        info_b = lane(probe, corrupt, fen)
        if before != after:
            differing.append({"fen": fen, "eval_pristine": before, "eval_rechecksummed": after,
                              "delta": after - before,
                              "lane_pristine": info_a.get("white_acc"),
                              "lane_corrupt": info_b.get("white_acc"),
                              "hits": info_a.get("hits")})
        elif info_a.get("hits", 0) > 0:
            reaching_same.append({"fen": fen, "eval": before,
                                  "lane_pristine": info_a.get("white_acc"),
                                  "lane_corrupt": info_b.get("white_acc")})

    payload = {"feature": FEATURE, "lane": LANE, "positions_checked": checked,
               "reached_feature_same_eval": len(reaching_same),
               "positions_with_different_eval": differing,
               "examples_masked": reaching_same[:5]}
    print(json.dumps(payload, indent=1)[:5000])
    with open(outpath, "w") as handle:
        json.dump(payload, handle, indent=1)


if __name__ == "__main__":
    main()
