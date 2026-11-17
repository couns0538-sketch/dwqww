#!/usr/bin/env python3
"""Count the overclaim class and confirm the mechanism that produces it.

The class: a `go mate N` request that reports `score mate M` with M > N. Such a
score cannot be a proved mate — the search only reaches 2N-1 plies, so it cannot
see a mate that needs 2M-1 > 2N-1 plies. It is a BOUND wearing a claim's syntax.

The mechanism, as arithmetic a reader can check:

  * `qsearch` clamps `alpha = max(alpha, mated_in(ply))` and
    `beta = min(beta, mate_in(ply+1))` (search.cpp:1431-1433).
  * The iteration loop breaks when `score >= mate_in(mate_moves*2 - 1)`
    (search.cpp:2552).
  * With `mate_in(p) = 32000 - p`, the break condition for `go mate N` is
    `score >= 32000 - (2N - 1)`.
  * A score of `mate M` is encoded as `32000 - (2M - 1)`.
  * So the break fires exactly when `2M - 1 <= 2N - 1`, i.e. `M <= N` — and ALSO
    fires on any bound that happens to reach that encoding, including one the
    search never proved.

This script prints the count per corpus, and re-derives the encoding so the
arithmetic is checked rather than asserted.

Usage: check_overclaim_class.py --dir evidence --out overclaim_class.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os

MATE = 32000
MAXPLY = 128


def encode(mate_moves: int) -> int:
    return MATE - (2 * mate_moves - 1)


def decode(score: int) -> int:
    """Signed distance in moves: `mate M` is encoded as MATE-(2M-1), and a score
    of `mate -M` as -MATE+(2M-1). Abs first, then re-apply the sign."""
    mag = (MATE - abs(score) + 1) // 2
    return mag if score > 0 else -mag


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="evidence")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # Control on the arithmetic itself: encode/decode must round-trip.
    for m in range(1, 12):
        assert decode(encode(m)) == m, f"encode/decode disagree at mate {m}"
        assert decode(-encode(m)) == -m
    print("encode/decode round-trip: OK for mate 1..11 (positive and negative)")
    print(f"break condition for go mate N: score >= {encode(1)} - ... -> "
          f"mate_in(2N-1) = {MATE} - (2N-1)")
    for n in (1, 2, 3, 4, 5, 6):
        print(f"  go mate {n}: break when score >= {MATE - (2*n-1)} "
              f"(= a mate {n} score). A score of mate {n+1} is {MATE - (2*(n+1)-1)} "
              f"which is {'<' if MATE-(2*(n+1)-1) < MATE-(2*n-1) else '>='} the threshold")

    # The clamp can never empty: it needs 2*ply >= 2*MATE-1.
    print(f"\nwindow-empty branch needs 2*ply >= {2*MATE-1}; MaxPly is {MAXPLY}, "
          f"so `if (alpha >= beta) return alpha;` at search.cpp:1434 is UNREACHABLE.")

    rows = []
    for name in ("compare_real.json", "compare_mate.json"):
        path = os.path.join(args.dir, name)
        if not os.path.exists(path):
            continue
        for r in json.load(open(path)):
            s = r["mate"]
            if s["score_kind"] == "mate" and s["score_value"] is not None:
                rows.append({
                    "source": name, "id": r["id"], "N": r["N"],
                    "mate": s["score_value"], "overclaims": s["score_value"] > r["N"],
                    "pv_len": len(s["pv"]), "implied_plies": 2 * abs(s["score_value"]) - 1,
                    "nodes": s["nodes"], "bestmove": s["bestmove"],
                })
    # raw_modes: the proven-DTM corpus, where the TRUE distance is known.
    path = os.path.join(args.dir, "raw_modes.json")
    if os.path.exists(path):
        for r in json.load(open(path)):
            for n in (1, 2, 3, 4):
                s = r["searches"][f"mate {n}"]
                if s["score_kind"] == "mate" and s["score_value"] is not None:
                    rows.append({
                        "source": "raw_modes", "id": r["id"], "N": n,
                        "mate": s["score_value"],
                        "overclaims": s["score_value"] > n,
                        "pv_len": len(s["pv"]),
                        "implied_plies": 2 * abs(s["score_value"]) - 1,
                        "nodes": s["nodes"], "bestmove": s["bestmove"],
                        "true_moves": r.get("oracle_mate_moves"),
                    })
    # overclaim.json: the characterised single case.
    path = os.path.join(args.dir, "overclaim.json")
    if os.path.exists(path):
        for run in json.load(open(path))["runs"]:
            if run["score_kind"] == "mate" and run["score_value"] is not None:
                rows.append({
                    "source": "overclaim", "id": "overclaim-board", "N": run["n"],
                    "mate": run["score_value"],
                    "overclaims": run["score_value"] > run["n"],
                    "pv_len": run["pv_len"],
                    "implied_plies": 2 * abs(run["score_value"]) - 1,
                    "nodes": run["nodes"], "bestmove": run["bestmove"],
                })

    over = [r for r in rows if r["overclaims"]]
    print(f"\nmate-scored cells examined: {len(rows)}")
    print(f"cells where reported M > requested N (unprovable at that depth): {len(over)}")
    for r in over:
        print(f"  {r['source']:16s} {r['id']:16s} N={r['N']} -> mate {r['mate']} "
              f"(implies {r['implied_plies']} plies, PV {r['pv_len']} plies"
              + (f", truth {2*r['true_moves']-1} plies" if r.get("true_moves") else "") + ")")

    # The consistent-with-truth subset: proven-DTM corpus, mate N >= truth.
    exact = [r for r in rows if r["source"] == "raw_modes" and r.get("true_moves")]
    right = [r for r in exact if r["mate"] == r["true_moves"]]
    print(f"\nproven-DTM corpus, mate-scored cells: {len(exact)}; distance correct: {len(right)}")
    wrong = [r for r in exact if r["mate"] != r["true_moves"]]
    for r in wrong:
        print(f"  WRONG DISTANCE: {r['id']} N={r['N']} says mate {r['mate']}, truth {r['true_moves']}")

    json.dump({"examined": len(rows), "overclaims": over, "arithmetic": {
        "mate_value": MATE, "maxply": MAXPLY,
        "break_threshold_by_n": {n: MATE - (2 * n - 1) for n in range(1, 7)},
        "window_empty_unreachable": True,
    }}, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
