#!/usr/bin/env python3
"""Drawn-root bail under threading: does it still fire, and is the MOVE stable?

The bail (search.cpp:2244-2272 on the base) tests the root for repetition /
halfmove>=100 / insufficient material and returns WITHOUT searching: an `info depth`
line per depth with `nodes 0` and an EMPTY pv, then `bestmove root_candidates.front()`.

Two things are measured, and they are different claims:
  (a) does the bail still FIRE at Threads 2/4/8?  Fingerprint: `nodes 0` and a pv
      of zero moves in every depth line. (The findings warn that a 0-node reply also
      comes from a piped EOF abort -- trap 2d0 -- so this script never pipes: it
      drives an interactive process and reads to `bestmove`.)
  (b) is the MOVE the same on every repeat? The bail publishes
      `root_candidates.front()`, which is a move-list order, so a threaded run cannot
      change it unless the root-drawn predicate itself became thread-dependent.

Controls, both required:
  - a NON-drawn twin of each fixture must NOT bail (nodes > 0), or "bails" is just
    "answers with no info";
  - the drawn fixtures reached BY MOVE LIST must bail where the same board reached by
    FEN does not (findings trap 2d: a FEN cannot carry repetition history).

Usage: python3 drawn_root.py <exe> <out.json> [reps]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

THREADS = (1, 2, 4, 8)

# The repetition fixture MUST be delivered by move list: a FEN with the same board
# has no history, and the bail's repetition test would be false. The other two
# fixtures are position properties that a FEN can carry.
REP_MOVES = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2

FIXTURES = [
    # name, kind, payload
    ("repetition_bylist", "moves", REP_MOVES),
    ("repetition_byfen", "fen", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5"),
    ("fifty_move", "fen", "8/8/8/4k3/8/4K3/8/7R w - - 100 60"),
    ("insufficient_KvK", "fen", "8/8/8/4k3/8/4K3/8/8 w - - 0 1"),
    ("insufficient_KBvK", "fen", "8/8/8/4k3/8/4K3/8/5B2 w - - 0 1"),
    ("insufficient_KNvK", "fen", "8/8/8/4k3/8/4K3/8/5N2 w - - 0 1"),
    # controls: near-twins that must NOT bail
    ("ctrl_fifty_99", "fen", "8/8/8/4k3/8/4K3/8/7R w - - 99 60"),
    ("ctrl_repetition_1rep", "moves", ["g1f3", "g8f6", "f3g1", "f6g8"]),
    ("ctrl_KRvK", "fen", "8/8/8/4k3/8/4K3/8/7R w - - 0 1"),
]


def classify(info, best):
    infos = [l for l in info if l.startswith("info depth")]
    d = last_depth_info(info)
    if d is None:
        return {"kind": "NO_INFO", "bestmove": best.split()[-1] if best else None,
                "n_info": len(infos)}
    pv_len = len(d["pv"])
    bail = d["nodes"] == 0 and pv_len == 0
    return {"kind": "BAIL" if bail else "SEARCH", "nodes": d["nodes"], "pv_len": pv_len,
            "score_kind": d.get("score_kind"), "score": d.get("score"),
            "bestmove": best.split()[-1] if best else None, "n_info": len(infos)}


def main():
    exe = os.path.abspath(sys.argv[1])
    out_path = sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    rows = []
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=300.0)
        for name, kind, payload in FIXTURES:
            results = []
            for _ in range(reps):
                e.ucinewgame()
                if kind == "moves":
                    e.position(None, payload)
                else:
                    e.position(payload)
                info, best, wall = e.go("depth 10")
                results.append(classify(info, best))
            kinds = {r["kind"] for r in results}
            moves = {r.get("bestmove") for r in results}
            scores = {(r.get("score_kind"), r.get("score")) for r in results}
            rows.append({"threads": th, "fixture": name, "kind_in": kind,
                         "reps": results, "kinds": sorted(kinds),
                         "distinct_moves": sorted(m for m in moves if m),
                         "distinct_scores": sorted(str(s) for s in scores)})
            print(f"T{th} {name:<22} kinds={sorted(kinds)} moves={sorted(m for m in moves if m)} "
                  f"scores={sorted(str(s) for s in scores)}", flush=True)
        e.close()
        print(flush=True)
    with open(out_path, "w") as fh:
        json.dump({"rows": rows, "reps": reps, "exe": exe,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
