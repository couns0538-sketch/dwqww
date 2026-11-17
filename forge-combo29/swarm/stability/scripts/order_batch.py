"""Measurement 4: does the answer depend on the ORDER of a batch?

Design is ABA, not AB. Three arms over the same 200 positions:

  A    one process, positions in corpus order
  B    one process, positions in a shuffled order
  A2   one process, corpus order AGAIN (fresh process, same order as A)

Why A2 and not just A vs B: A vs B alone confounds "warm state matters at all"
with "the order matters". Two arms cannot separate them. A == A2 is the control
that says the batch result is deterministic given the order; then A != B is a
genuine state leak keyed on what preceded a position, not noise.

The fresh-process column comes from corpus_twice.py, so a fourth comparison
(batch vs fresh) attributes any warm-state drift separately from order.

Usage: order_batch.py <forge> <corpus.json> <fresh.json> <out.json>
"""
import argparse
import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import Uci, score_key

OPTS = ["setoption name OwnBook value false",
        "setoption name Threads value 1",
        "setoption name Hash value 32",
        "setoption name MultiPV value 1"]


def run_batch(forge, corpus, order, depth):
    """One process, one search per position, in `order`. Returns {id: result}."""
    u = Uci(forge, timeout=600)
    out = {}
    try:
        u.handshake()
        for o in OPTS:
            u.send(o)
        u.send("isready")
        while u.readline() != "readyok":
            pass
        for idx in order:
            pos = corpus[idx]
            poscmd = "position startpos moves " + " ".join(pos["moves"])
            r = u.search(poscmd, f"go depth {depth}")
            out[pos["id"]] = {
                "score": list(score_key(r)),
                "depth": r["depth"],
                "bestmove": r["bestmove"],
                "nodes": r["nodes"],
                "n_info_depth": r["n_info_depth"],
                "bail": r["bail"],
                "refused": r["pos_refused"],
            }
    finally:
        u.close()
    return out


def diff_fields(x, y):
    moved = []
    if x["score"] != y["score"]:
        moved.append("score")
    if x["depth"] != y["depth"]:
        moved.append("depth")
    if x["bestmove"] != y["bestmove"]:
        moved.append("bestmove")
    return moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forge")
    ap.add_argument("corpus")
    ap.add_argument("fresh", help="corpus_twice.py output, T1 arm")
    ap.add_argument("out")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--seed", type=int, default=424242)
    a = ap.parse_args()

    corpus = json.load(open(a.corpus))
    n = len(corpus)
    order_a = list(range(n))
    order_b = list(range(n))
    random.Random(a.seed).shuffle(order_b)

    print(f"running arm A (corpus order) ...", file=sys.stderr, flush=True)
    A = run_batch(a.forge, corpus, order_a, a.depth)
    print(f"running arm B (shuffled) ...", file=sys.stderr, flush=True)
    B = run_batch(a.forge, corpus, order_b, a.depth)
    print(f"running arm A2 (corpus order again, fresh process) ...", file=sys.stderr, flush=True)
    A2 = run_batch(a.forge, corpus, order_a, a.depth)

    # fresh-process arm: rep 0 of the twice measurement
    fresh_raw = json.load(open(a.fresh))
    F = {}
    for rec in fresh_raw["rows"]:
        r = rec["runs"][0]
        F[rec["id"]] = {"score": list(score_key(r)), "depth": r["depth"],
                        "bestmove": r["bestmove"], "nodes": r["nodes"],
                        "n_info_depth": r["n_info_depth"], "bail": r["bail"],
                        "refused": r["pos_refused"]}

    ids = [p["id"] for p in corpus]

    def compare(left, right, tag):
        rows = []
        for i in ids:
            m = diff_fields(left[i], right[i])
            rows.append({"id": i, "fields_moved": m, "a": left[i], "b": right[i]})
        cnt = Counter(",".join(r["fields_moved"]) if r["fields_moved"] else "none" for r in rows)
        return {
            "comparison": tag,
            "n": len(ids),
            "diff_any": sum(1 for r in rows if r["fields_moved"]),
            "diff_score": sum(1 for r in rows if "score" in r["fields_moved"]),
            "diff_depth": sum(1 for r in rows if "depth" in r["fields_moved"]),
            "diff_bestmove": sum(1 for r in rows if "bestmove" in r["fields_moved"]),
            "field_combos": dict(cnt),
            "diff_ids": [r["id"] for r in rows if r["fields_moved"]],
            "rows": rows,
        }

    arms = [compare(A, A2, "A vs A2 (same order, fresh process = reproducibility control)"),
            compare(A, B, "A vs B (corpus order vs shuffled = ORDER DEPENDENCE)"),
            compare(A, F, "A vs fresh (batch vs one-process-per-position = warm state)"),
            compare(B, F, "B vs fresh (shuffled batch vs fresh)")]

    summary = {"depth": a.depth, "n": n, "seed": a.seed, "arms": arms}
    with open(a.out, "w") as f:
        json.dump(summary, f, indent=1)
    for arm in arms:
        print(json.dumps({k: arm[k] for k in arm if k not in ("rows", "diff_ids")}, indent=1))


if __name__ == "__main__":
    main()
