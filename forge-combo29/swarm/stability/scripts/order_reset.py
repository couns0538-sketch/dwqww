"""Measurement 4b: does `ucinewgame` per position remove the ORDER dependence too?

Measurement 4 showed 194 of 200 positions answer differently depending on what
preceded them in the batch, and A == A2 showed that is deterministic, not noise.
This asks the operational question a labeling harness actually needs: if I reset
between positions, does the batch order stop mattering?

Arms (all in one process each, corpus order vs the SAME shuffle seed as
order_batch.py, so the two experiments are comparable):
  U  ucinewgame before each position
  N  no reset (the leak, re-measured here as the positive control)

The no-reset arm is the control that proves this script can detect order
dependence at all. Without it a clean U result would be a control that never
fires.
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


def run_batch(forge, corpus, order, depth, resets):
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
            for c in resets:
                u.send(c)
            r = u.search("position startpos moves " + " ".join(pos["moves"]), f"go depth {depth}")
            out[pos["id"]] = {"score": list(score_key(r)), "depth": r["depth"],
                              "bestmove": r["bestmove"], "nodes": r["nodes"]}
    finally:
        u.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forge"); ap.add_argument("corpus"); ap.add_argument("out")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--seed", type=int, default=424242)
    a = ap.parse_args()

    corpus = json.load(open(a.corpus))
    n = len(corpus)
    order_a = list(range(n))
    order_b = list(range(n))
    random.Random(a.seed).shuffle(order_b)
    ids = [p["id"] for p in corpus]

    arms = {}
    for tag, resets in (("N", []), ("U", ["ucinewgame"])):
        for oname, order in (("a", order_a), ("b", order_b)):
            key = f"{tag}{oname}"
            print(f"arm {key} ...", file=sys.stderr, flush=True)
            arms[key] = run_batch(a.forge, corpus, order, a.depth, resets)

    def cmp(left, right, tag):
        rows = []
        for i in ids:
            moved = []
            if left[i]["score"] != right[i]["score"]:
                moved.append("score")
            if left[i]["depth"] != right[i]["depth"]:
                moved.append("depth")
            if left[i]["bestmove"] != right[i]["bestmove"]:
                moved.append("bestmove")
            rows.append({"id": i, "fields_moved": moved,
                         "a": left[i]["score"], "b": right[i]["score"]})
        cp = [abs(r["a"][1] - r["b"][1]) for r in rows
              if r["fields_moved"] and r["a"][0] == "cp" and r["b"][0] == "cp"]
        return {"comparison": tag, "n": len(ids),
                "diff_any": sum(1 for r in rows if r["fields_moved"]),
                "diff_score": sum(1 for r in rows if "score" in r["fields_moved"]),
                "diff_depth": sum(1 for r in rows if "depth" in r["fields_moved"]),
                "diff_bestmove": sum(1 for r in rows if "bestmove" in r["fields_moved"]),
                "cp_gap_max": max(cp) if cp else 0,
                "cp_gap_mean": round(sum(cp) / len(cp), 1) if cp else 0.0,
                "field_combos": dict(Counter(",".join(r["fields_moved"]) if r["fields_moved"] else "none" for r in rows)),
                "diff_ids": [r["id"] for r in rows if r["fields_moved"]]}

    out_arms = [
        cmp(arms["Na"], arms["Nb"], "NO reset: corpus order vs shuffled (order dependence)"),
        cmp(arms["Ua"], arms["Ub"], "ucinewgame per position: corpus order vs shuffled"),
        cmp(arms["Na"], arms["Ua"], "corpus order: no reset vs ucinewgame"),
    ]
    summary = {"depth": a.depth, "n": n, "seed": a.seed, "arms": out_arms}
    with open(a.out, "w") as f:
        json.dump(summary, f, indent=1)
    for arm in out_arms:
        print(json.dumps({k: arm[k] for k in arm if k != "diff_ids"}))


if __name__ == "__main__":
    main()
