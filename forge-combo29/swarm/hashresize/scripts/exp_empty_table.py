"""Experiment L - item 1 at width: does a same-value resize matter on an EMPTY table?

Experiment F asked this on one position.  A null on one position is weak, and the
audit's rule is that a null needs the same two proofs as a defect: a control that
shows the instrument can see a difference, and enough positions that the null is
not a coincidence.

Per position, five arms from a FRESH process each:

  L_silent     Hash 32, ucinewgame, search              (baseline)
  L_resend     Hash 32, Hash 32, ucinewgame, search     (the same-value re-send, cold)
  L_resend2    Hash 32, Hash 32, Hash 32, ucinewgame, search
  L_default    no Hash at all, ucinewgame, search       (default is 32; must match)
  L_warm_none  Hash 32, ucinewgame, search, search       (warm control)
  L_warm_resend Hash 32, ucinewgame, search, Hash 32, search
                                                        (the positive control)

The verdict is only admissible if, on the same positions, `L_warm_resend` differs
from `L_warm_none` at least once.  Otherwise the null above it is a probe that
cannot see anything.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE
from corpus import select

CORE = ("bestmove", "nodes", "score", "depth")


def one(engine, pos, go, ops, warm_search=False, resend_after_warm=False, hash_mb=32):
    e = Engine(engine)
    try:
        e.handshake()
        if hash_mb is not None:
            e.setoption("Hash", hash_mb)
        for op in ops:
            if op == "resend":
                e.setoption("Hash", hash_mb)
            elif op == "newgame":
                e.newgame()
        r = e.search(pos, go)
        warm = {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"], "depth": r["depth"]}
        if not warm_search:
            return warm, None
        if resend_after_warm:
            e.setoption("Hash", hash_mb)
        r2 = e.search(pos, go)
        return warm, {"bestmove": r2["bestmove"], "nodes": r2["nodes"],
                      "score": r2["score"], "depth": r2["depth"]}
    finally:
        e.close()


def same(a, b):
    return all(a[k] == b[k] for k in CORE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chosen, _ = select(args.count, 18, engine=args.engine)
    go = "go depth %d" % args.depth
    print("positions %d, %s, Hash %d" % (len(chosen), go, args.hash), flush=True)

    rows = []
    for i, entry in enumerate(chosen):
        pos = "position fen " + entry["fen"]
        r = {"i": i, "fen": entry["fen"]}
        r["silent"], _ = one(args.engine, pos, go, ["newgame"], hash_mb=args.hash)
        r["resend"], _ = one(args.engine, pos, go, ["resend", "newgame"], hash_mb=args.hash)
        r["resend2"], _ = one(args.engine, pos, go, ["resend", "resend", "newgame"], hash_mb=args.hash)
        r["default"], _ = one(args.engine, pos, go, ["newgame"], hash_mb=None)
        r["warm_none"], r["warm_none_2"] = one(args.engine, pos, go, ["newgame"], warm_search=True, hash_mb=args.hash)
        r["warm_resend"], r["warm_resend_2"] = one(
            args.engine, pos, go, ["newgame"], warm_search=True, resend_after_warm=True, hash_mb=args.hash)
        rows.append(r)
        if (i + 1) % 4 == 0:
            print("  %d/%d" % (i + 1, len(rows)), flush=True)

    n = len(rows)
    checks = {
        "cold resend  == cold silent": lambda r: same(r["resend"], r["silent"]),
        "cold 2xresend== cold silent": lambda r: same(r["resend2"], r["silent"]),
        "cold default == cold silent": lambda r: same(r["default"], r["silent"]),
        "POSITIVE: warm+resend != warm": lambda r: not same(r["warm_resend_2"], r["warm_none_2"]),
        "CONTROL:  warm warm == warm warm (repeat)": None,
    }
    print("\n== item 1 at width, %d positions ==" % n)
    summary = {}
    for name, fn in checks.items():
        if fn is None:
            continue
        hits = sum(1 for r in rows if fn(r))
        summary[name] = {"holds": hits, "of": n}
        print("  %-42s %2d/%d" % (name, hits, n))

    # The null is only admissible if the positive control fired.
    positive_fired = summary["POSITIVE: warm+resend != warm"]["holds"]
    admissible = positive_fired > 0
    print("\n  positive control fired %d/%d -> null is %s" % (
        positive_fired, n, "ADMISSIBLE" if admissible else "VOID"))

    # Worked example, so the numbers are inspectable rather than summarised.
    r0 = rows[0]
    print("\n  example position 0 (%s):" % r0["fen"][:40])
    for k in ("silent", "resend", "resend2", "warm_none_2", "warm_resend_2"):
        v = r0[k]
        print("    %-14s %s nodes %s score %s" % (k, v["bestmove"], v["nodes"], v["score"]))

    with open(args.out, "w") as fh:
        json.dump({"args": vars(args), "summary": summary,
                   "positive_fired": positive_fired, "admissible": admissible,
                   "rows": rows}, fh, indent=2)
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
