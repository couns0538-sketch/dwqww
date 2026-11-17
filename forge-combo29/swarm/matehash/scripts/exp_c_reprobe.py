"""Experiment C: the actual re-probe -- an entry stored at ply 1, read at ply 0.

THE DESIGN, AND WHY IT IS THE RIGHT SHAPE

    Search 1: `position fen <PARENT>` + `go depth D`.
        The search's root is the parent (ply 0). One move deep, the CHILD sits at
        ply 1, and when that node returns, its score is stored with ply = 1. So a
        mate the child can force is written to the table as
            score_to_tt(child_score, 1) = MATE - (distance_from_child) + 1.

    Search 2: `position fen <CHILD>` + `go depth D`, SAME process, table intact.
        The child is now the root, ply 0. Probing its own entry reads
        score_from_tt(stored, 0) = stored - 0. For the reported distance to be
        right, `stored` must already be position-relative. It is only
        position-relative if the store adjusted by ITS ply -- which is exactly
        the thing under audit.

    So this design fails loudly if the store adjustment is missing or inverted:
    the child's reported distance comes back shifted by one whole move, and no
    amount of extra depth repairs it because the entry is reused as an exact hit.

CONTROLS, because a null here would otherwise be indistinguishable from an
unreached path:

  * COLD arm       identical search of the child in a fresh process. Must equal
                   the oracle. This is the answer the warm arm must reproduce.
  * NODE DROP      the warm arm must use strictly fewer nodes than the cold arm.
                   If it does not, the table did not answer and the agreement is
                   vacuous -- the brief's "two proofs for a null".
  * PLANTED        the same harness with the expected distance shifted by one
                   move must FAIL on the same corpus. A checker that cannot fail
                   is worthless.
  * DEPTH/SELDEPTH every row records the depth and seldepth of the reported line,
                   because `mate N` needs 2N-1 plies and a mate claimed at a
                   depth that cannot contain it is unverifiable, not wrong.

Usage: exp_c_reprobe.py <binary> [--plant] [--limit N]
Output: evidence/C_reprobe.jsonl
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from engine import Engine, final_score, mate_distance  # noqa: E402


def last_line(result):
    """The final `info depth` line, with depth AND seldepth, or None."""
    scored = [i for i in result["infos"] if "score" in i and "depth" in i]
    if not scored:
        return None
    return scored[-1]


def brief(result):
    line = last_line(result)
    return {
        "bestmove": result["bestmove"],
        "mate": mate_distance(result),
        "depth": line.get("depth") if line else None,
        "seldepth": line.get("seldepth") if line else None,
        "nodes": line.get("nodes") if line else None,
        "info_lines": len(result["infos"]),
        "last_raw": line["raw"] if line else None,
    }


def warm_reprobe(binary, parent_fen, child_fen, depth, hash_mb=64):
    """Search the parent, then the child, in ONE process with one live table."""
    with Engine(binary, hash_mb=hash_mb) as eng:
        eng.ucinewgame()
        eng.position(parent_fen, None)
        warmup = eng.go(depth=depth, _timeout=600.0)
        # The child is now the root; its own entry was written at ply 1.
        eng.position(child_fen, None)
        warm = eng.go(depth=depth, _timeout=600.0)
        # Cold control: same table cleared, same child, same depth.
        eng.ucinewgame()
        eng.position(child_fen, None)
        cold = eng.go(depth=depth, _timeout=600.0)
    return brief(warmup), brief(warm), brief(cold)


def main():
    binary = sys.argv[1]
    plant = "--plant" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    depth = 12

    here = __file__.rsplit("/", 2)[0]
    chains = json.load(open(here + "/evidence/chains.json"))
    pairs = chains["pairs"][: limit] if limit else chains["pairs"]

    rows = []
    for i, p in enumerate(pairs):
        want = p["expected_reported_mate"]
        expected = (want + 1) if (plant and want) else want
        warmup, warm, cold = warm_reprobe(binary, p["parent_fen"], p["child_fen"], depth)
        row = {
            "i": i,
            "parent_fen": p["parent_fen"],
            "child_fen": p["child_fen"],
            "parent_move": p["parent_move"],
            "oracle_kind": p["kind"],
            "oracle_moves": p["moves"],
            "expected": expected,
            "depth_requested": depth,
            "warmup": warmup,
            "warm": warm,
            "cold": cold,
            "warm_ok": warm["mate"] == expected,
            "cold_ok": cold["mate"] == expected,
            "warm_matches_cold": warm["mate"] == cold["mate"],
            "table_answered": (warm["nodes"] is not None and cold["nodes"] is not None
                               and warm["nodes"] < cold["nodes"]),
            # A mate claim is only verifiable if the depth can contain it.
            "seldepth_reaches_mate": (warm["seldepth"] is not None and warm["mate"] is not None
                                      and warm["seldepth"] >= 2 * abs(warm["mate"]) - 1),
        }
        rows.append(row)
        print(json.dumps({k: row[k] for k in
                          ("i", "oracle_kind", "oracle_moves", "expected", "warm_ok", "cold_ok",
                           "table_answered")}), flush=True)

    n = len(rows)
    with_mate = [r for r in rows if r["oracle_kind"] in ("mate", "mated") and r["oracle_moves"]]
    summary = {
        "binary": binary,
        "depth_requested": depth,
        "mode": "PLANTED (expect failures)" if plant else "real",
        "n": n,
        "n_with_mate": len(with_mate),
        "warm_ok": sum(1 for r in rows if r["warm_ok"]),
        "cold_ok": sum(1 for r in rows if r["cold_ok"]),
        "warm_matches_cold": sum(1 for r in rows if r["warm_matches_cold"]),
        "table_answered": sum(1 for r in rows if r["table_answered"]),
        "seldepth_reaches_mate": sum(1 for r in rows if r["seldepth_reaches_mate"]),
        "warm_failures": [
            {"child_fen": r["child_fen"], "expected": r["expected"], "warm": r["warm"]["mate"],
             "depth": r["warm"]["depth"], "seldepth": r["warm"]["seldepth"],
             "oracle": [r["oracle_kind"], r["oracle_moves"]]}
            for r in rows if not r["warm_ok"]
        ][:20],
    }
    print(json.dumps({"summary": summary}, indent=2))
    name = "C_planted.jsonl" if plant else "C_reprobe.jsonl"
    with open(here + "/evidence/" + name, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        fh.write(json.dumps({"summary": summary}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
