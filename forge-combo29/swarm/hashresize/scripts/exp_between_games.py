"""Experiment J - the between-games resize, which is where a runner's option block
actually lands if the runner does NOT send `ucinewgame`.

Three game-start states, each measured on a game's FIRST search with a different
position searched before it, so a populated table from a real previous game is
present:

  J_fresh       fresh process, search the game position.
                The reference.
  J_newgame     search prev position; ucinewgame; search the game position.
                Should equal J_fresh (ucinewgame is the documented cold reset).
  J_resize      search prev position; setoption Hash <same value>; search.
                The runner pattern with no ucinewgame.
  J_clear       search prev position; Clear Hash; search.
                The known non-cold reset, as a control pair for J_resize.

The question is not only "does J_resize equal J_fresh" (A and F already answer
no) but "what does it cost on a REAL game start", i.e. is the third state closer
to cold or to warm, and how many nodes does the difference amount to.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE
from corpus import select
from exp_resize_state import compare


def run(engine, hash_mb, prev_pos, pos, go, action):
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        e.newgame()
        warm = {"bestmove": None, "nodes": 0}
        if action != "fresh":
            r = e.search(prev_pos, go)
            warm = {"bestmove": r["bestmove"], "nodes": r["nodes"]}
            if action == "newgame":
                e.newgame()
            elif action == "resize":
                e.setoption("Hash", hash_mb)
            elif action == "clear":
                e.setoption("Clear Hash")
        r = e.search(pos, go)
        return warm, {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
                      "depth": r["depth"], "hashfull": r["hashfull"]}
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chosen, _ = select(args.count + args.count, args.depth, engine=args.engine)
    prevs = chosen[: args.count]
    games = chosen[args.count:]
    go = "go depth %d" % args.depth
    print("pairs %d, %s, Hash %d" % (len(games), go, args.hash), flush=True)

    rows = []
    for i, g in enumerate(games):
        prev_pos = "position fen " + prevs[i]["fen"]
        pos = "position fen " + g["fen"]
        rec = {"i": i, "fen": g["fen"], "prev": prevs[i]["fen"]}
        rec["fresh"] = run(args.engine, args.hash, prev_pos, pos, go, "fresh")
        rec["newgame"] = run(args.engine, args.hash, prev_pos, pos, go, "newgame")
        rec["resize"] = run(args.engine, args.hash, prev_pos, pos, go, "resize")
        rec["clear"] = run(args.engine, args.hash, prev_pos, pos, go, "clear")
        rows.append(rec)
        if (i + 1) % 10 == 0:
            print("  %d/%d" % (i + 1, len(rows)), flush=True)

    checks = {
        "J_newgame vs fresh (expect 0)": lambda r: compare(r["fresh"][1], r["newgame"][1]),
        "J_resize  vs fresh (question)": lambda r: compare(r["fresh"][1], r["resize"][1]),
        "J_clear   vs fresh (known)": lambda r: compare(r["fresh"][1], r["clear"][1]),
        "J_resize  vs Clear Hash": lambda r: compare(r["clear"][1], r["resize"][1]),
    }
    n = len(rows)
    print("\n== J over %d pairs ==" % n)
    summary = {}
    for name, fn in checks.items():
        differing = [(r["i"], fn(r)) for r in rows if fn(r)]
        moves = [i for i, d in differing if "bestmove" in d]
        summary[name] = {"differing": len(differing), "of": n, "moves": len(moves)}
        print("  %-32s differ %2d/%d  move %2d" % (name, len(differing), n, len(moves)))

    fresh_nodes = sum(r["fresh"][1]["nodes"] for r in rows)
    resize_nodes = sum(r["resize"][1]["nodes"] for r in rows)
    print("\n  total nodes: fresh %d, after same-value resize %d, delta %+d (%.1f%%)" % (
        fresh_nodes, resize_nodes, resize_nodes - fresh_nodes,
        100.0 * (resize_nodes - fresh_nodes) / fresh_nodes))

    out = {"args": vars(args), "summary": summary,
           "total": {"fresh": fresh_nodes, "resize": resize_nodes},
           "rows": rows}
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
