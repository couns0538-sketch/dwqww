#!/usr/bin/env python3
"""Prove the refactor did not change a single recorded answer.

Rebuilds the first two games contiguously, from a cold process, in the same game order the
session arm used, and compares every per-ply record against the committed
evidence/session.jsonl.gz.

WHOLE GAMES, not a sample of plies. A spot-check that jumps between plies of one process is
NOT a reproduction check: warm-state answers depend on the path that led to them (measured:
41% of plies differ under a reversed game order). My first version of this check did exactly
that and reported 5/16, which is the harness being wrong, not the engine -- it is recorded here
because it is the same trap the headline finding is about.
"""
import sys, os, json, gzip

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
from replay import run_search, pos_cmd
from evio import EVID
from checks import require

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")
GAMES = ("g000", "g001")


def main():
    corpus = {g["id"]: g
              for g in json.load(open(os.path.join(EVID, "games.json"), encoding="utf-8"))["games"]}
    committed = {}
    with gzip.open(os.path.join(EVID, "session.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            committed[(r["g"], r["p"])] = r

    eng = Engine(ENG)
    eng.uci(); eng.sync()
    n = same = 0
    bad = []
    for gid in GAMES:
        g = corpus[gid]
        for k in range(1, len(g["moves"]) + 1):   # whole game, in order, one process
            r = run_search(eng, pos_cmd(g, k))
            n += 1
            w = committed[(gid, k)]
            if (r["bm"], r["nodes"], r["score"]) == (w["m"], w["n"], w["s"]):
                same += 1
            else:
                bad.append({"game": gid, "ply": k, "now": [r["bm"], r["nodes"], r["score"]],
                            "committed": [w["m"], w["n"], w["s"]]})
    eng.quit()

    out = {"games": list(GAMES), "plies": n, "reproduced": same,
           "identical": same == n, "mismatches": bad[:20]}
    json.dump(out, open(os.path.join(EVID, "reproduction_check.json"), "w", encoding="utf-8"),
              indent=0)
    print(f"{same}/{n} plies reproduce the committed session record exactly "
          f"({len(GAMES)} whole games, contiguous, cold process)")
    for b in bad[:5]:
        print("  MISMATCH", b)
    require(same == n, "refactor changed a recorded answer")


if __name__ == "__main__":
    main()
