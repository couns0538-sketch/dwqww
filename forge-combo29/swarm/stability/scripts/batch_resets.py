"""Measurement 5: does `ucinewgame` per position make a batch match fresh processes?

Trap 3 says `ucinewgame` IS a cold reset (0 of 25 differ from a fresh process).
That was measured one-search-at-a-time. This asks the operational version: can a
labeling harness loop positions in ONE process with `ucinewgame` between them and
get the fresh-process answer? If yes, the order leak has a documented fix and the
answer is "label in a batch with ucinewgame"; if no, the only safe harness is one
process per position.

Arms, all against the fresh-process reference (corpus_twice rep 0):
  A     no reset between positions (the leaky arm, measured again here)
  U     ucinewgame before each position
  UC    ucinewgame + Clear Hash before each position
  UH    ucinewgame + re-send Hash (the same-value resize, which is a table WIPE)
  A2    no reset, corpus order again (reproducibility control)

Usage: batch_resets.py <forge> <corpus.json> <fresh.json> <out.json>
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import Uci, score_key

OPTS = ["setoption name OwnBook value false",
        "setoption name Threads value 1",
        "setoption name Hash value 32",
        "setoption name MultiPV value 1"]

RESETS = {
    "A":  [],
    "U":  ["ucinewgame"],
    "UC": ["ucinewgame", "setoption name Clear Hash"],
    "UH": ["ucinewgame", "setoption name Hash value 32"],
}


def run_batch(forge, corpus, depth, reset_cmds):
    u = Uci(forge, timeout=600)
    out = {}
    try:
        u.handshake()
        for o in OPTS:
            u.send(o)
        u.send("isready")
        while u.readline() != "readyok":
            pass
        for pos in corpus:
            for c in reset_cmds:
                u.send(c)
            poscmd = "position startpos moves " + " ".join(pos["moves"])
            r = u.search(poscmd, f"go depth {depth}")
            out[pos["id"]] = {"score": list(score_key(r)), "depth": r["depth"],
                              "bestmove": r["bestmove"], "nodes": r["nodes"],
                              "n_info_depth": r["n_info_depth"]}
    finally:
        u.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forge"); ap.add_argument("corpus"); ap.add_argument("fresh"); ap.add_argument("out")
    ap.add_argument("--depth", type=int, default=12)
    a = ap.parse_args()

    corpus = json.load(open(a.corpus))
    ids = [p["id"] for p in corpus]
    fresh_raw = json.load(open(a.fresh))
    F = {}
    for rec in fresh_raw["rows"]:
        r = rec["runs"][0]
        F[rec["id"]] = {"score": list(score_key(r)), "depth": r["depth"],
                        "bestmove": r["bestmove"], "nodes": r["nodes"],
                        "n_info_depth": r["n_info_depth"]}

    arms = {}
    for name, cmds in RESETS.items():
        print(f"arm {name} ...", file=sys.stderr, flush=True)
        arms[name] = run_batch(a.forge, corpus, a.depth, cmds)
    print("arm A2 ...", file=sys.stderr, flush=True)
    arms["A2"] = run_batch(a.forge, corpus, a.depth, [])

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
            rows.append({"id": i, "fields_moved": moved})
        return {"comparison": tag, "n": len(ids),
                "diff_any": sum(1 for r in rows if r["fields_moved"]),
                "diff_score": sum(1 for r in rows if "score" in r["fields_moved"]),
                "diff_depth": sum(1 for r in rows if "depth" in r["fields_moved"]),
                "diff_bestmove": sum(1 for r in rows if "bestmove" in r["fields_moved"]),
                "field_combos": dict(Counter(",".join(r["fields_moved"]) if r["fields_moved"] else "none" for r in rows)),
                "diff_ids": [r["id"] for r in rows if r["fields_moved"]]}

    out_arms = [
        cmp(F, arms["A"],  "fresh vs batch-no-reset (the leak)"),
        cmp(F, arms["U"],  "fresh vs batch with ucinewgame per position"),
        cmp(F, arms["UC"], "fresh vs batch with ucinewgame + Clear Hash per position"),
        cmp(F, arms["UH"], "fresh vs batch with ucinewgame + Hash resend per position"),
        cmp(arms["A"], arms["A2"], "A vs A2 (same order twice: reproducibility control)"),
    ]
    summary = {"depth": a.depth, "n": len(ids), "arms": out_arms}
    with open(a.out, "w") as f:
        json.dump(summary, f, indent=1)
    for arm in out_arms:
        print(json.dumps(arm))


if __name__ == "__main__":
    main()
