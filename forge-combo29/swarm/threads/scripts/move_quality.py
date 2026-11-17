#!/usr/bin/env python3
"""When a threaded search returns a different move, is it a WORSE move or a tie?

This is the question an owner has, and node-count instability does not answer it. Two
measurements, both needed:

1. SCORE GAP: for each position where the threaded move differed from the Threads-1
   move, re-search each of the two moves alone at the same depth with `searchmoves`
   pinned, at Threads 1, and record the score difference. A tie-breaking flip shows a
   small gap; a real loss shows a large one.

   The findings warn (trap 4a) that `searchmoves` is NOT a no-op control: it changes
   the root TT store and reorders equal-scoring moves, so a pinned SCORE is not the
   in-tree score. That warning is about using a pinned score as an ABSOLUTE number.
   Here both arms are pinned identically and the comparison is between two pinned
   values on the same board, which is the one `searchmoves` use the record allows --
   and the gap is reported with that scope attached, not as an engine score.

2. DEPTH TREND: a real loss deepens with depth; a tie-break does not. Re-measure the
   gap at depth+4. A gap that shrinks toward 0 is a horizon/tie artefact.

Usage: python3 move_quality.py <exe> <determinism.jsonl> <out.json> [pad]
"""
import json
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402


def pinned_score(e, fen, move, depth):
    """Score of one root move, pinned, at Threads 1. `searchmoves <one legal move>`."""
    e.ucinewgame()
    e.position(fen)
    info, best, _ = e.go(f"depth {depth} searchmoves {move}", timeout=300.0)
    d = last_depth_info(info)
    if d is None:
        return None
    return d.get("score")


def main():
    exe = os.path.abspath(sys.argv[1])
    det = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    depth = int(sys.argv[4]) if len(sys.argv) > 4 else 12

    # positions where Threads 4 gave more than one distinct bestmove across repeats
    per = defaultdict(list)
    for r in det:
        if r["threads"] == 4:
            per[r["idx"]].append(r)
    unstable = {i: rs for i, rs in per.items() if len({r["sig"]["bestmove"] for r in rs}) > 1}
    base = {r["idx"]: r for r in det if r["threads"] == 1 and r["rep"] == 0}
    print(f"Threads 4 bestmove unstable on {len(unstable)}/{len(per)} positions; "
          f"measuring gaps on each distinct move pair")

    e = Engine(exe, {"Hash": 64, "Threads": 1}, timeout=300.0)
    rows = []
    try:
        for idx, rs in sorted(unstable.items()):
            fen = rs[0]["fen"]
            moves = sorted({r["sig"]["bestmove"] for r in rs})
            ref = base[idx]["sig"]["bestmove"] if idx in base else moves[0]
            cand = [m for m in moves if m != ref]
            if not cand:
                continue
            other = cand[0]
            s_ref = pinned_score(e, fen, ref, depth)
            s_oth = pinned_score(e, fen, other, depth)
            s_ref_deep = pinned_score(e, fen, ref, depth + 4)
            s_oth_deep = pinned_score(e, fen, other, depth + 4)
            if None in (s_ref, s_oth, s_ref_deep, s_oth_deep):
                continue
            gap = s_oth - s_ref            # negative => the alternates are worse than T1's move
            gap_deep = s_oth_deep - s_ref_deep
            rows.append({"idx": idx, "fen": fen, "ref": ref, "other": other,
                         "score_ref": s_ref, "score_other": s_oth, "gap": gap,
                         "gap_deep": gap_deep})
            print(f"  pos {idx:>2} ref={ref} ({s_ref:+d})  other={other} ({s_oth:+d})  "
                  f"gap={gap:+d}  gap@d{depth+4}={gap_deep:+d}", flush=True)
    finally:
        e.close()

    if not rows:
        print("no measurable pairs")
        return 1
    gaps = [r["gap"] for r in rows]
    deep = [r["gap_deep"] for r in rows]
    tie = sum(1 for g in gaps if g == 0)
    within10 = sum(1 for g in gaps if abs(g) <= 10)
    within50 = sum(1 for g in gaps if abs(g) <= 50)
    worse = sum(1 for g in gaps if g < -10)
    print()
    print(f"pairs: {len(rows)}")
    print(f"gap == 0 (exact tie):        {tie}/{len(rows)}")
    print(f"|gap| <= 10 cp:              {within10}/{len(rows)}")
    print(f"|gap| <= 50 cp:              {within50}/{len(rows)}")
    print(f"alternate worse by > 10 cp:  {worse}/{len(rows)}")
    print(f"median gap {statistics.median(gaps):+.0f} cp   mean {statistics.mean(gaps):+.1f} cp")
    print(f"median gap at depth+4 {statistics.median(deep):+.0f} cp   mean {statistics.mean(deep):+.1f} cp")
    out = {"depth": depth, "rows": rows, "n": len(rows), "tie": tie,
           "within10": within10, "within50": within50, "worse10": worse,
           "median_gap": statistics.median(gaps), "mean_gap": statistics.mean(gaps),
           "median_gap_deep": statistics.median(deep), "mean_gap_deep": statistics.mean(deep),
           "exe": exe, "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
