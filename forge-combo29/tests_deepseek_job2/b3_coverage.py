#!/usr/bin/env python3
"""Job 2 B3: coverage table.

For each position, report
  * the white king's bucket and which half of the board it stands on (files a-d / e-h),
  * the same for the black king,
  * the output bucket.
Counts are taken from MY reference evaluator's own bucket computation, and the
bucket/flip values were already shown to match the engine's evaluation exactly in
B2, so the table describes the same buckets the engine uses.

The "half" is the king's file on the board as printed in the FEN. The engine
computes the bucket from the rank-flipped square for Black (kr = sq ^ 56), which
leaves the file unchanged, and sets flip = 7 for files e-h on a mirrored net.

Usage: b3_coverage.py <net> <fens> <out> 
"""
import json
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job2")
import deepseek_nnue_v3_ref as ref


def king_squares(pieces):
    wk = next(sq for sq, c in pieces.items() if c == 6)
    bk = next(sq for sq, c in pieces.items() if c == 12)
    return wk, bk


def main():
    net_path, fens_path, out_json = sys.argv[1:4]
    net = ref.load_net(net_path)
    with open(fens_path) as f:
        fens = [l.strip() for l in f if l.strip()]

    kb = net.king_buckets
    ob = net.output_buckets
    white = {(b, half): 0 for b in range(kb) for half in ("a-d", "e-h")}
    black = {(b, half): 0 for b in range(kb) for half in ("a-d", "e-h")}
    out_buckets = {b: 0 for b in range(ob)}
    flip_w = {0: 0, 7: 0}
    flip_b = {0: 0, 7: 0}

    for fen in fens:
        pieces, _stm = ref.parse_fen(fen)
        wk, bk = king_squares(pieces)
        cp, info = ref.evaluate(net, fen)
        half_w = "a-d" if (wk & 7) < 4 else "e-h"
        half_b = "a-d" if (bk & 7) < 4 else "e-h"
        white[(info["kb_w"], half_w)] += 1
        black[(info["kb_b"], half_b)] += 1
        out_buckets[info["ob"]] += 1
        flip_w[info["fl_w"]] += 1
        flip_b[info["fl_b"]] += 1

    # Recompute each flip from the definition in nnue_v3.hpp and compare with what the
    # evaluator used, over every position and both perspectives. (An earlier version of
    # this file compared a fixed list against itself, which proved nothing.)
    flip_mismatches = 0
    for fen in fens:
        pieces, _stm = ref.parse_fen(fen)
        wk, bk = king_squares(pieces)
        _cp, info = ref.evaluate(net, fen)
        for ksq, used, perspective_white in ((wk, info["fl_w"], True), (bk, info["fl_b"], False)):
            kr = ksq if perspective_white else ksq ^ 56
            expected = 7 if (net.mirror and (kr & 7) >= 4) else 0
            if used != expected:
                flip_mismatches += 1

    result = {
        "net": net_path, "positions": len(fens),
        "king_buckets": kb, "output_buckets": ob,
        "white_king": {f"bucket{k}_{half}": v for (k, half), v in sorted(white.items())},
        "black_king": {f"bucket{k}_{half}": v for (k, half), v in sorted(black.items())},
        "output_bucket_counts": {f"bucket{k}": v for k, v in sorted(out_buckets.items())},
        "white_flip_counts": flip_w, "black_flip_counts": flip_b,
        "min_white_cell": min(white.values()), "min_black_cell": min(black.values()),
        "min_output_cell": min(out_buckets.values()),
        "all_cells_at_least_20": min(min(white.values()), min(black.values()), min(out_buckets.values())) >= 20,
        "flip_checks": 2 * len(fens), "flip_mismatches": flip_mismatches,
    }
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)

    # Human-readable table.
    print(f"net {net_path}: {len(fens)} positions")
    print("\nwhite king: bucket x half")
    print("bucket  a-d    e-h   total")
    for b in range(kb):
        ad = white[(b, "a-d")]
        eh = white[(b, "e-h")]
        print(f"{b:>6}  {ad:>4}  {eh:>5}  {ad + eh:>6}")
    print("\nblack king: bucket x half")
    print("bucket  a-d    e-h   total")
    for b in range(kb):
        ad = black[(b, "a-d")]
        eh = black[(b, "e-h")]
        print(f"{b:>6}  {ad:>4}  {eh:>5}  {ad + eh:>6}")
    print("\noutput bucket: count")
    for b in range(ob):
        print(f"{b:>6}  {out_buckets[b]:>5}")
    print(f"\nmin cell: white {min(white.values())}, black {min(black.values())}, "
          f"output {min(out_buckets.values())}; all >= 20: {result['all_cells_at_least_20']}")


if __name__ == "__main__":
    main()
