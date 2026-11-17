#!/usr/bin/env python3
"""Analysis of the cost rows: move change, cost distribution, and clustering.

THE REFERENCE ARM'S VALIDITY VARIES BY REASON, and pooling the reasons would mix
populations with different measurement quality:

  threefold roots          -- the reference search is clean; a threefold at mid-game
                              halfmove counts is an ordinary searched position.
  halfmove >= 100 roots    -- findings section 2 records that the LEAF rule already
                              adjudicates a draw one ply down at this boundary, so the
                              reference arm's own search is truncated near the horizon.
                              These rows are reported separately and are the weaker
                              measurement.
  insufficient roots       -- the game is over by rule; no move matters. They are
                              counted (they are firing positions) but excluded from the
                              cost distribution, because "cost of a wrong move" is not
                              defined in a dead position.
"""
from __future__ import annotations

import collections
import json
import statistics
import sys
import os

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import glob_under_root, load_json, open_json_out


def group_of(row: dict) -> str:
    if "insufficient" in row["reason"]:
        return "insufficient"
    if "threefold" in row["reason"]:
        return "threefold"
    if "halfmove" in row["reason"]:
        return "halfmove_only"
    return "other"


def stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    s = sorted(values)
    return {
        "n": len(s),
        "median": statistics.median(s),
        "mean": round(statistics.mean(s), 1),
        "min": min(s), "max": max(s),
        "p25": s[len(s) // 4], "p75": s[(3 * len(s)) // 4],
        "n_gt_0": sum(1 for v in s if v > 0),
        "n_ge_100": sum(1 for v in s if v >= 100),
        "n_ge_300": sum(1 for v in s if v >= 300),
        "n_lt_0": sum(1 for v in s if v < 0),
        "n_zero": sum(1 for v in s if v == 0),
    }


def main() -> int:
    path = sys.argv[1]
    d = load_json(path)
    rows = [r for r in d["rows"] if "error" not in r]
    errs = [r for r in d["rows"] if "error" in r]

    out = {"source": path, "depth": d["depth"], "rows": len(rows), "errors": len(errs)}
    out["base_bailed"] = sum(r["base_bailed"] for r in rows)
    out["patched_changes_move"] = sum(r["patched_changes_move"] for r in rows)
    out["search_changes_move"] = sum(r["search_changes_move"] for r in rows)
    out["roots_with_mate_in_1"] = sum(1 for r in rows if r["mating_moves"])
    out["base_forfeits_mate"] = sum(1 for r in rows if r["base_forfeits_mate"])

    # Cost, split by group. Insufficient-material roots are excluded from the cost
    # distribution (see module docstring) but kept in the firing counts.
    groups = collections.defaultdict(list)
    for r in rows:
        groups[group_of(r)].append(r)

    out["groups"] = {}
    for name, grows in sorted(groups.items()):
        costs = [r["cost_cp"] for r in grows if r["cost_cp"] is not None]
        movable = [r for r in grows if name != "insufficient"]
        out["groups"][name] = {
            "n_rows": len(grows),
            "n_unique_positions": len({r["fen"] for r in grows}),
            "n_unique_games": len({r["game"] for r in grows}),
            "patched_changes_move": sum(r["patched_changes_move"] for r in grows),
            "search_changes_move": sum(r["search_changes_move"] for r in grows),
            "mate_in_1_available": sum(1 for r in grows if r["mating_moves"]),
            "cost_cp": stats(costs),
            "mobility_median": statistics.median([r["legal"] for r in grows]) if grows else None,
            "halfmove_values": sorted({r["halfmove"] for r in grows})[:10],
        }
        if name == "insufficient":
            out["groups"][name]["note"] = "dead position: cost of a move is not defined"

    # Unique positions only: the same firing repeats on consecutive plies, so a count of
    # ROWS over-weights a position that fires for several plies in a row.
    uniq = {}
    for r in rows:
        uniq.setdefault(r["fen"], r)
    out["unique_positions"] = len(uniq)
    out["unique_positions_search_changes_move"] = sum(
        1 for r in uniq.values() if r["search_changes_move"])
    out["unique_positions_patched_changes_move"] = sum(
        1 for r in uniq.values() if r["patched_changes_move"])
    uc = [r["cost_cp"] for r in uniq.values()
          if r["cost_cp"] is not None and group_of(r) != "insufficient"]
    out["unique_positions_cost_cp"] = stats(uc)

    # Clustering: material signature at the firing.
    out["endgame_types"] = collections.Counter(
        r["endgame_type"] for r in rows).most_common(12)
    out["mobility_histogram"] = collections.Counter(
        min(r["legal"], 40) // 5 * 5 for r in rows).most_common()

    print(json.dumps(out, indent=2))
    with open_json_out(path.replace(".json", "_analysis.json")) as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
