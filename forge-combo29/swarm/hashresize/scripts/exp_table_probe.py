"""Experiment B - does the TABLE survive a resize? (question 1, table half)

Comparing a resized run against a fresh process cannot answer this, because the
warm search also warms the per-worker history tables and those are not cleared
by a resize.  This experiment isolates the table with an instrument that does
not search:

    `go wtime 0` on a WARM table answers 0 nodes with NO `info depth` line,
    because the root is a TT hit.  On a COLD table it answers ~26-45 nodes with
    exactly one `info depth 1` line.  (forge-findings.md S7 item 2d0.)

So the probe is a binary read of "is the root in the table", independent of
node budgets, depths and search shape.

Arms, all from one warm-up search at `warm` then one probe:

  none            no reset                  expect 0 nodes  (probe sees warmth)
  resize_same     setoption Hash warm       ?                (question 5)
  resize_up       setoption Hash big        ?                (question 1 up)
  resize_down     setoption Hash small      ?                (question 1 down)
  clear           setoption name Clear Hash ?                (known control)
  newgame         ucinewgame                expect >0 nodes (known cold control)
  fresh           fresh process, no warm-up expect >0 nodes (known cold control)

Two controls make the zero/positive readings meaningful: `none` must read warm
and `fresh` must read cold.  If either control flips, the probe is not reading
what it claims and the run is void.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE
from corpus import select

PROBE = "go wtime 0"


def warm_then_probe(engine, position, go, warm_hash, action, target_hash=None):
    e = Engine(engine)
    rec = {}
    try:
        e.handshake()
        e.setoption("Hash", warm_hash)
        e.newgame()
        warm = e.search(position, go)
        rec["warm"] = {"bestmove": warm["bestmove"], "nodes": warm["nodes"], "hashfull": warm["hashfull"]}
        if action == "resize_same":
            e.setoption("Hash", warm_hash)
        elif action == "resize_up":
            e.setoption("Hash", target_hash)
        elif action == "resize_down":
            e.setoption("Hash", target_hash)
        elif action == "clear":
            e.setoption("Clear Hash")
        elif action == "newgame":
            e.newgame()
        elif action == "none":
            pass
        probe = e.search(position, PROBE, timeout=60)
        rec["probe"] = {
            "bestmove": probe["bestmove"],
            "nodes": probe["nodes"],
            "depth": probe["depth"],
            "info_depth_lines": probe["info_depth_lines"],
            "ok": probe["ok"],
            "raw": probe["lines"][:4],
        }
        return rec
    finally:
        e.close()


def fresh_probe(engine, position, hash_mb):
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        e.newgame()
        probe = e.search(position, PROBE, timeout=60)
        return {
            "bestmove": probe["bestmove"],
            "nodes": probe["nodes"],
            "depth": probe["depth"],
            "info_depth_lines": probe["info_depth_lines"],
            "ok": probe["ok"],
            "raw": probe["lines"][:4],
        }
    finally:
        e.close()


def is_warm(probe):
    """The binary reading.  `0 nodes` with no iteration = the root was in the table."""
    return (probe["nodes"] in (0, None)) and probe["info_depth_lines"] == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--small", type=int, default=16)
    ap.add_argument("--large", type=int, default=256)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    go = "go depth %d" % args.depth
    chosen, rejected = select(args.count, args.depth, engine=args.engine)
    print("positions %d (rejected %d)" % (len(chosen), len(rejected)), flush=True)

    rows = []
    for idx, entry in enumerate(chosen):
        fen = entry["fen"]
        pos = "position fen " + fen
        S, L = args.small, args.large
        row = {
            "i": idx,
            "fen": fen,
            "fresh_small": fresh_probe(args.engine, pos, S),
            "fresh_large": fresh_probe(args.engine, pos, L),
            "warm_small": {
                "none": warm_then_probe(args.engine, pos, go, S, "none"),
                "resize_same": warm_then_probe(args.engine, pos, go, S, "resize_same"),
                "resize_up": warm_then_probe(args.engine, pos, go, S, "resize_up", L),
                "clear": warm_then_probe(args.engine, pos, go, S, "clear"),
                "newgame": warm_then_probe(args.engine, pos, go, S, "newgame"),
            },
            "warm_large": {
                "none": warm_then_probe(args.engine, pos, go, L, "none"),
                "resize_same": warm_then_probe(args.engine, pos, go, L, "resize_same"),
                "resize_down": warm_then_probe(args.engine, pos, go, L, "resize_down", S),
                "clear": warm_then_probe(args.engine, pos, go, L, "clear"),
                "newgame": warm_then_probe(args.engine, pos, go, L, "newgame"),
            },
        }
        rows.append(row)
        with open(args.out, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print("  [%d/%d]" % (idx + 1, len(rows)), flush=True)

    summarise(rows, args)


def summarise(rows, args):
    n = len(rows)
    arms = [
        ("warm_small", "none"),
        ("warm_small", "resize_same"),
        ("warm_small", "resize_up"),
        ("warm_small", "clear"),
        ("warm_small", "newgame"),
        ("warm_large", "none"),
        ("warm_large", "resize_same"),
        ("warm_large", "resize_down"),
        ("warm_large", "clear"),
        ("warm_large", "newgame"),
    ]
    summary = {}
    print("\n== table probe (warm = 0 nodes and no info depth line) ==")
    for group, arm in arms:
        warm = 0
        for r in rows:
            if is_warm(r[group][arm]["probe"]):
                warm += 1
        summary["%s.%s" % (group, arm)] = {"reads_warm": warm, "of": n}
        print("  %-12s %-12s reads warm %2d/%d" % (group, arm, warm, n))
    fresh_warm = {
        "fresh_small": sum(1 for r in rows if is_warm(r["fresh_small"])),
        "fresh_large": sum(1 for r in rows if is_warm(r["fresh_large"])),
    }
    summary["fresh"] = fresh_warm
    print("  %-12s %-12s reads warm %2d/%d" % ("fresh", "small", fresh_warm["fresh_small"], n))
    print("  %-12s %-12s reads warm %2d/%d" % ("fresh", "large", fresh_warm["fresh_large"], n))

    # Node-count detail for the arms that are meant to be cold: shows the probe
    # is a real search, not a constant.
    print("\n== probe node counts (cold arms) ==")
    for group, arm in (("warm_small", "resize_up"), ("warm_large", "resize_down"), ("warm_small", "newgame")):
        vals = [r[group][arm]["probe"]["nodes"] for r in rows]
        print("  %-12s %-12s nodes %s" % (group, arm, vals[:10]))
    summary["void"] = fresh_warm["fresh_small"] != 0 or fresh_warm["fresh_large"] != 0

    with open(args.out + ".summary.json", "w") as fh:
        json.dump({"args": vars(args), "summary": summary}, fh, indent=2)
    print("\nVOID" if summary["void"] else "\nprobe controls hold")


if __name__ == "__main__":
    main()
