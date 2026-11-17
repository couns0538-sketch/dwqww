"""Experiment E - a SHARP prediction, in the window where the two sizes AGREE.

The audit established (forge-findings.md S3): at `go nodes 50000`, Hash 16 and
Hash 64 are indistinguishable -- 0 of 24 cells differ.  Above ~200k they diverge.

That gives a falsifiable prediction for this seat.  If the post-resize divergence
measured in experiment A were a property of the TABLE SIZE, it would vanish in
the window where the two sizes are equivalent.  If it is a property of the
UNCLEARED SEARCH HISTORIES, it must persist there, because a resize does not
touch histories at any size.

  E1  fresh(64) vs fresh(16)            control: must be 0 differing, or the
                                        window is not the window the audit says
  E2  [warm16 -> resize 64] vs fresh(64)  prediction: DIFFERS, while E1 is 0
  E3  [warm16 -> newgame]    vs fresh(16) control: must be 0 (ucinewgame is cold)
  E4  [warm16 -> resize 64 -> newgame] vs fresh(64) control: must be 0

E2 against E1 is the sharpest statement in this seat: same endpoint size, same
budget, same table size at the end, and the ONLY difference is whether the
process reached that table by allocation or by resize.  E1 says the table size
is not the explanation.  So a non-zero E2 with a zero E1 names the histories.

E4 against E2 says the residual is removable by a history reset, which is the
other half of the same claim.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE
from corpus import select
from exp_resize_state import compare, order_arm


def run_two(engine, position, go, first_hash, ops):
    """Warm at first_hash, apply ops, then measure."""
    e = Engine(engine)
    rec = {}
    try:
        e.handshake()
        e.setoption("Hash", first_hash)
        e.newgame()
        warm = e.search(position, go)
        rec["warm"] = {"bestmove": warm["bestmove"], "nodes": warm["nodes"]}
        for op, arg in ops:
            if op == "hash":
                e.setoption("Hash", arg)
            elif op == "newgame":
                e.newgame()
        r = e.search(position, go)
        rec["after"] = {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
                        "depth": r["depth"], "hashfull": r["hashfull"]}
        return rec
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--nodes", type=int, default=50000)
    ap.add_argument("--small", type=int, default=16)
    ap.add_argument("--large", type=int, default=64)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", type=int, default=0)
    args = ap.parse_args()

    go = "go nodes %d" % args.nodes
    # Eligibility uses a fixed depth search so the sample does not depend on the
    # budget under test.
    chosen, rejected = select(args.count + args.skip, 18, engine=args.engine)
    if args.skip:
        chosen = chosen[args.skip:]
    chosen = chosen[: args.count]
    print("positions %d (rejected %d), budget %s" % (len(chosen), len(rejected), go), flush=True)

    rows = []
    for idx, entry in enumerate(chosen):
        fen = entry["fen"]
        pos = "position fen " + fen
        S, L = args.small, args.large
        fresh_S = order_arm(args.engine, pos, go, [("hash", S), ("newgame", None)])
        fresh_L = order_arm(args.engine, pos, go, [("hash", L), ("newgame", None)])
        row = {
            "i": idx, "fen": fen,
            "fresh_small": fresh_S,
            "fresh_large": fresh_L,
            "resize_only": run_two(args.engine, pos, go, S, [("hash", L)]),
            "newgame_only": run_two(args.engine, pos, go, S, [("newgame", None)]),
            "resize_then_newgame": run_two(args.engine, pos, go, S, [("hash", L), ("newgame", None)]),
        }
        rows.append(row)
        with open(args.out, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print("  [%d/%d]" % (idx + 1, len(rows)), flush=True)

    checks = {
        "E1 fresh64 vs fresh16 (expect 0)": lambda r: compare(r["fresh_large"], r["fresh_small"]),
        "E2 resize->64 vs fresh64 (predict >0)": lambda r: compare(r["fresh_large"], r["resize_only"]["after"]),
        "E3 newgame vs fresh16 (expect 0)": lambda r: compare(r["fresh_small"], r["newgame_only"]["after"]),
        "E4 resize->64->newgame vs fresh64 (expect 0)": lambda r: compare(r["fresh_large"], r["resize_then_newgame"]["after"]),
    }
    n = len(rows)
    print("\n== experiment E over %d positions, %s, Hash %d vs %d ==" % (n, go, args.small, args.large))
    summary = {}
    for name, fn in checks.items():
        differing = [(r["i"], fn(r)) for r in rows if fn(r)]
        moves = [i for i, d in differing if "bestmove" in d]
        summary[name] = {"differing": len(differing), "of": n, "moves": len(moves)}
        print("  %-46s differ %2d/%d  move %2d" % (name, len(differing), n, len(moves)))
    with open(args.out + ".summary.json", "w") as fh:
        json.dump({"args": vars(args), "summary": summary}, fh, indent=2)


if __name__ == "__main__":
    main()
