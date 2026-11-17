"""Measurement 3: 200 corpus positions, twice each, in FRESH process pairs.

This is the "can I label with this" number. A fresh process per run means the
only variable is the launch itself; warm-state drift (trap 3) is excluded by
construction, so a disagreement here is launch-to-launch instability.

Disagreements are broken out BY FIELD -- score, depth, bestmove -- because a
count of "differing positions" that does not say which field moved is not a
result, and because the fields have different consequences: a score-only
disagreement corrupts a label, a bestmove disagreement corrupts a target move.

Usage: corpus_twice.py <forge> <corpus.json> <out.json> [--depth 12] [--threads 1]
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import run_one, score_key

BASE_OPTS = ["setoption name OwnBook value false"]


def opts_for(threads, hash_mb):
    return list(BASE_OPTS) + [
        f"setoption name Threads value {threads}",
        f"setoption name Hash value {hash_mb}",
        "setoption name MultiPV value 1",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forge")
    ap.add_argument("corpus")
    ap.add_argument("out")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=32)
    a = ap.parse_args()

    corpus = json.load(open(a.corpus))
    opts = opts_for(a.threads, a.hash)
    rows = []
    for idx, pos in enumerate(corpus):
        poscmd = "position startpos moves " + " ".join(pos["moves"])
        pair = []
        for rep in (0, 1):
            r = run_one(a.forge, poscmd, f"go depth {a.depth}", options=opts)
            r["rep"] = rep
            pair.append(r)
        rec = {"id": pos["id"], "ply": pos["ply"], "phase": pos["phase"],
               "pieces": pos["pieces"], "runs": pair}
        sa, sb = score_key(pair[0]), score_key(pair[1])
        rec["diff_score"] = sa != sb
        rec["diff_depth"] = pair[0]["depth"] != pair[1]["depth"]
        rec["diff_bestmove"] = pair[0]["bestmove"] != pair[1]["bestmove"]
        rec["diff_nodes"] = pair[0]["nodes"] != pair[1]["nodes"]
        rec["any_diff"] = rec["diff_score"] or rec["diff_depth"] or rec["diff_bestmove"]
        rec["score_a"] = list(sa)
        rec["score_b"] = list(sb)
        rec["bail"] = pair[0]["bail"] or pair[1]["bail"]
        rec["refused"] = pair[0]["pos_refused"] or pair[1]["pos_refused"]
        # the field that moved, named explicitly
        moved = []
        if rec["diff_score"]:
            moved.append("score")
        if rec["diff_depth"]:
            moved.append("depth")
        if rec["diff_bestmove"]:
            moved.append("bestmove")
        rec["fields_moved"] = moved
        rows.append(rec)
        if (idx + 1) % 25 == 0:
            print(f"  {idx+1}/{len(corpus)}", file=sys.stderr, flush=True)

    n = len(rows)
    cp_gaps = [abs(r["score_a"][1] - r["score_b"][1]) for r in rows
               if r["diff_score"] and r["score_a"][0] == "cp" and r["score_b"][0] == "cp"]
    summary = {
        "depth": a.depth, "threads": a.threads, "hash_mb": a.hash,
        "n_positions": n,
        "n_pairs": 2 * n,
        "diff_any": sum(1 for r in rows if r["any_diff"]),
        "diff_score": sum(1 for r in rows if r["diff_score"]),
        "diff_depth": sum(1 for r in rows if r["diff_depth"]),
        "diff_bestmove": sum(1 for r in rows if r["diff_bestmove"]),
        "diff_nodes": sum(1 for r in rows if r["diff_nodes"]),
        "diff_score_only": sum(1 for r in rows
                               if r["diff_score"] and not r["diff_depth"] and not r["diff_bestmove"]),
        "diff_bestmove_only": sum(1 for r in rows
                                  if r["diff_bestmove"] and not r["diff_score"] and not r["diff_depth"]),
        "field_combo_counts": {",".join(k) if k else "none": v
                               for k, v in Counter(tuple(r["fields_moved"]) for r in rows).items()},
        "cp_gap_max": max(cp_gaps) if cp_gaps else 0,
        "cp_gap_mean": (sum(cp_gaps) / len(cp_gaps)) if cp_gaps else 0,
        "cp_gaps": sorted(cp_gaps, reverse=True)[:20],
        "bail_positions": sum(1 for r in rows if r["bail"]),
        "refused_positions": sum(1 for r in rows if r["refused"]),
        "phase_counts": dict(Counter(r["phase"] for r in rows)),
        "diffs_by_phase": {p: sum(1 for r in rows if r["phase"] == p and r["any_diff"])
                           for p in sorted({r["phase"] for r in rows})},
        "rows": rows,
    }
    with open(a.out, "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({k: summary[k] for k in summary if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
