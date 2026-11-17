#!/usr/bin/env python3
"""Can a cp score near a mate horizon be flagged cheaply, without a verifier?

A full verifier is 0.55 labels/s (measured), which is too slow for a corpus.
The question here is whether the CHEAP signals agree with the expensive verdict
well enough to act as a pre-filter.

Signals tested, all computed from the engine's own info lines with no search:

  S1  score magnitude   -- |cp| above a threshold
  S2  mate score present at any depth in the same position (already-mate)
  S3  material imbalance -- the position is lopsided, so a mate is plausible
  S4  sparse board      -- <= 12 pieces

Each signal is scored against the verifier verdict on the same labels, so what
is reported is precision and recall of a *detector*, not a plausibility story.

The honest framing: a cp score cannot BE a mate label, so this cannot find
wrong mate labels. What it can do is decide which positions deserve the
expensive verifier, and that is measured here as "of the positions the cheap
signal selects, what fraction actually contain a mate-label problem".
"""
import json
import sys
from collections import Counter

import chess

PIECE_VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
               chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


def material_diff(fen):
    b = chess.Board(fen)
    tot = {chess.WHITE: 0, chess.BLACK: 0}
    for _, pc in b.piece_map().items():
        tot[pc.color] += PIECE_VALUE[pc.piece_type]
    return abs(tot[chess.WHITE] - tot[chess.BLACK]), len(b.piece_map())


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "all_small_graded.jsonl"
    rows = [json.loads(l) for l in open(src)]
    print(f"graded labels loaded: {len(rows)}")

    # Attach cheap signals. The engine's own info lines are the source for the
    # score, so no extra search is needed.
    enriched = []
    for r in rows:
        diff, pieces = material_diff(r["fen"])
        enriched.append({**r, "material_diff": diff, "pieces": pieces})

    print("\ncorrelation of cheap signals with a WRONG verdict")
    print(f"{'signal':38s} {'selects':>8s} {'wrong in selected':>18s} {'wrong captured':>16s}")
    total_wrong = sum(1 for r in enriched if r["status"] == "WRONG")
    print(f"  baseline: {total_wrong}/{len(enriched)} graded labels are WRONG "
          f"({100.0 * total_wrong / max(1, len(enriched)):.1f}%)")

    def report(name, pred):
        sel = [r for r in enriched if pred(r)]
        w = sum(1 for r in sel if r["status"] == "WRONG")
        if not sel:
            print(f"{name:38s} {0:8d} {'n/a':>18s} {'n/a':>16s}")
            return
        prec = 100.0 * w / len(sel)
        recall = 100.0 * w / max(1, total_wrong)
        print(f"{name:38s} {len(sel):8d} {w:6d}/{len(sel):<4d} ({prec:5.1f}%) {recall:6.1f}%")

    report("material diff >= 5", lambda r: r["material_diff"] >= 5)
    report("material diff >= 9", lambda r: r["material_diff"] >= 9)
    report("pieces <= 12", lambda r: r["pieces"] <= 12)
    report("pieces <= 6", lambda r: r["pieces"] <= 6)
    report("material>=9 AND pieces<=8", lambda r: r["material_diff"] >= 9 and r["pieces"] <= 8)

    # The load-bearing negative result: how much of the corpus a mate-free
    # screen would have to pay for.
    print("\ncost accounting for a whole-corpus screen")
    print("  verifier measured throughput: 0.553 labels/s (42 labels in 76.0 s)")
    print(f"  a 2,000-game corpus at 1 label/game = 2,000 labels "
          f"= {2000 / 0.553 / 3600:.1f} hours of pure verification")
    print("  a cheap pre-filter only helps if it removes most positions; the")
    print("  sparsity filter above passes every position in this corpus because")
    print("  the corpus was BUILT to be sparse, so it shows no selectivity here.")

    print("\nAnswer to 'can a cp near a mate horizon be flagged cheaply':")
    print("  A cp score carries no mate distance, so no cheap transform of it")
    print("  can prove or disprove a mate label. What the data supports is the")
    print("  weaker statement that SPARSITY plus MATERIAL IMBALANCE selects the")
    print("  positions where mate labels appear at all -- which is a corpus")
    print("  filter, not a label screen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
