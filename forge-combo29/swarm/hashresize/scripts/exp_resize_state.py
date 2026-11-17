"""Experiment A - what a Hash resize leaves behind (questions 1, 4, 5).

Every arm starts in its own process and is compared against a fresh process at
the size the arm ENDS at.  The arm set is chosen so the resize can be
decomposed rather than merely observed:

  A_fresh(S)   fresh process, Hash S, ucinewgame, search.
               The reference: "what an allocation gives you".
  B_resize     Hash S_start, ucinewgame, search; setoption Hash S_end; search.
               The thing under test.
  C_samesize   Hash S_end, ucinewgame, search; setoption Hash S_end; search.
               Same warmth, same endpoint size, same re-set path, but the two
               sizes are equal.  Question 5 lives here.
  D_clear      Hash S_end, ucinewgame, search; setoption name Clear Hash; search.
               The audit's known non-cold reset, as a control.
  E_none       Hash S_end, ucinewgame, search; search again with no reset.
               The warm baseline: proves the endpoint can be reached without a
               reset at all.
  F_orderA     setoption Hash S_end; ucinewgame; search.   (resize before newgame)
  G_orderB     ucinewgame; setoption Hash S_end; search.   (resize after newgame)
               Question 4: both orders should be fully cold if a resize is an
               allocation, because ucinewgame clears the histories the resize
               does not.

Comparisons are exact on (bestmove, nodes, score, depth).  Node counts are
integers from a deterministic engine (proved by the repeat control below), so
"equal" means equal, not "within tolerance".
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE
from corpus import select


def cell(engine, position, go, hash_mb=None, newgame=False, settle=True):
    e = Engine(engine)
    try:
        e.handshake()
        if hash_mb is not None:
            e.setoption("Hash", hash_mb)
        if newgame:
            e.newgame()
        r = e.search(position, go)
        return {
            "bestmove": r["bestmove"],
            "nodes": r["nodes"],
            "score": r["score"],
            "depth": r["depth"],
            "seldepth": r["seldepth"],
            "hashfull": r["hashfull"],
            "pv": r["pv"],
            "info_depth_lines": r["info_depth_lines"],
            "ok": r["ok"],
        }
    finally:
        e.close()


def arm_chain(engine, position, go, first_hash, reset, second_hash=None, newgame=False):
    """One process, two searches: warm-up then the measured one."""
    e = Engine(engine)
    rec = {"warm": None, "after": None}
    try:
        e.handshake()
        e.setoption("Hash", first_hash)
        if newgame:
            # resize-before-newgame order handled by caller via reset="none"
            e.newgame()
        r = e.search(position, go)
        rec["warm"] = {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"]}
        if reset == "resize":
            e.setoption("Hash", second_hash)
        elif reset == "clear":
            e.setoption("Clear Hash")
        elif reset == "newgame_then_resize":
            e.newgame()
            e.setoption("Hash", second_hash)
        elif reset == "resize_then_newgame":
            e.setoption("Hash", second_hash)
            e.newgame()
        elif reset == "none":
            pass
        r = e.search(position, go)
        rec["after"] = {
            "bestmove": r["bestmove"],
            "nodes": r["nodes"],
            "score": r["score"],
            "depth": r["depth"],
            "seldepth": r["seldepth"],
            "hashfull": r["hashfull"],
            "pv": r["pv"],
            "info_depth_lines": r["info_depth_lines"],
            "ok": r["ok"],
        }
    finally:
        e.close()
    return rec


def key(c):
    return (c["bestmove"], c["nodes"], c["score"], c["depth"])


def order_arm(engine, position, go, ops):
    """Fresh process, then apply `ops` in order, then search once.

    ops is a list like [("hash", 256), ("newgame", None)]; this is the only way
    to state an ordering question without a warm-up search confusing it.
    """
    e = Engine(engine)
    try:
        e.handshake()
        for op, arg in ops:
            if op == "hash":
                e.setoption("Hash", arg)
            elif op == "newgame":
                e.newgame()
            elif op == "clear":
                e.setoption("Clear Hash")
        r = e.search(position, go)
        return {
            "bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"],
            "depth": r["depth"], "seldepth": r["seldepth"], "hashfull": r["hashfull"],
            "pv": r["pv"], "info_depth_lines": r["info_depth_lines"], "ok": r["ok"],
        }
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--small", type=int, default=16)
    ap.add_argument("--large", type=int, default=256)
    ap.add_argument("--out", required=True)
    ap.add_argument("--replication", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    args = ap.parse_args()

    go = "go depth %d" % args.depth
    chosen, rejected = select(args.count + args.skip, args.depth, engine=args.engine)
    if args.skip:
        chosen = chosen[args.skip:]
    chosen = chosen[: args.count]
    print("positions %d (rejected %d) depth %d" % (len(chosen), len(rejected), args.depth), flush=True)

    rows = []
    for idx, entry in enumerate(chosen):
        fen = entry["fen"]
        position = "position fen " + fen
        A = {args.small: cell(args.engine, position, go, args.small, True),
             args.large: cell(args.engine, position, go, args.large, True)}
        B_ab = arm_chain(args.engine, position, go, args.small, "resize", args.large)
        B_ba = arm_chain(args.engine, position, go, args.large, "resize", args.small)
        C_sm = arm_chain(args.engine, position, go, args.small, "resize", args.small)
        C_lg = arm_chain(args.engine, position, go, args.large, "resize", args.large)
        D_sm = arm_chain(args.engine, position, go, args.small, "clear")
        D_lg = arm_chain(args.engine, position, go, args.large, "clear")
        E_sm = arm_chain(args.engine, position, go, args.small, "none")
        E_lg = arm_chain(args.engine, position, go, args.large, "none")
        # Question 4, asked without a warm-up search so only ORDER differs:
        #   F: resize first, then ucinewgame, then search
        #   G: ucinewgame first, then resize, then search
        F = order_arm(args.engine, position, go, [("hash", args.large), ("newgame", None)])
        G = order_arm(args.engine, position, go, [("newgame", None), ("hash", args.large)])
        # Repeat control: a second fresh process at the large size. Proves the
        # comparison CAN fail (it fails on the arms above), and that a
        # fresh-vs-fresh comparison is not failing by itself.
        A2 = cell(args.engine, position, go, args.large, True)
        A3 = cell(args.engine, position, go, args.small, True)
        row = {
            "i": idx,
            "fen": fen,
            "depth": args.depth,
            "A_fresh": {str(k): v for k, v in A.items()},
            "A2_fresh_repeat": A2,
            "A3_fresh_small_repeat": A3,
            "B_ab": B_ab, "B_ba": B_ba,
            "C_sm": C_sm, "C_lg": C_lg,
            "D_sm": D_sm, "D_lg": D_lg,
            "E_sm": E_sm, "E_lg": E_lg,
            "F_resize_then_newgame": {"after": F},
            "G_newgame_then_resize": {"after": G},
        }
        rows.append(row)
        with open(args.out, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print("  [%d/%d] %s" % (idx + 1, len(rows), fen.split()[0]), flush=True)

    report(rows, args)


CORE = ("bestmove", "nodes", "score", "depth")


def compare(a, b):
    """b against a, on the fields that describe the SEARCH.

    `hashfull` is deliberately excluded: it is reported as a fraction of the
    table's own cluster count, so two runs with identical contents report
    different values at different table sizes.  Including it would make the
    fresh-Hash-16-vs-64 control "differ" on a field the audit's equivalence
    claim was never about, and the control has to be the control the audit
    established.  `hashfull` is compared separately, below.
    """
    diffs = {}
    for f in CORE:
        if a.get(f) != b.get(f):
            diffs[f] = (a.get(f), b.get(f))
    return diffs


def report(rows, args):
    S, L = str(args.small), str(args.large)
    checks = {
        "Q1 16->256 vs fresh256": lambda r: compare(r["A_fresh"][L], r["B_ab"]["after"]),
        "Q1 256->16 vs fresh16": lambda r: compare(r["A_fresh"][S], r["B_ba"]["after"]),
        "DIAG 16->256 vs fresh16": lambda r: compare(r["A_fresh"][S], r["B_ab"]["after"]),
        "DIAG 256->16 vs fresh256": lambda r: compare(r["A_fresh"][L], r["B_ba"]["after"]),
        "ABL resize-only vs resize+newgame": lambda r: compare(r["B_ab"]["after"], r["F_resize_then_newgame"]["after"]),
        "Q5 same 16 vs fresh16": lambda r: compare(r["A_fresh"][S], r["C_sm"]["after"]),
        "Q5 same 256 vs fresh256": lambda r: compare(r["A_fresh"][L], r["C_lg"]["after"]),
        "CTRL ClearHash16 vs fresh16": lambda r: compare(r["A_fresh"][S], r["D_sm"]["after"]),
        "CTRL ClearHash256 vs fresh256": lambda r: compare(r["A_fresh"][L], r["D_lg"]["after"]),
        "CTRL warm16 vs fresh16": lambda r: compare(r["A_fresh"][S], r["E_sm"]["after"]),
        "CTRL warm256 vs fresh256": lambda r: compare(r["A_fresh"][L], r["E_lg"]["after"]),
        "Q4 resize-then-newgame vs fresh256": lambda r: compare(r["A_fresh"][L], r["F_resize_then_newgame"]["after"]),
        "Q4 newgame-then-resize vs fresh256": lambda r: compare(r["A_fresh"][L], r["G_newgame_then_resize"]["after"]),
        "DECOMP resize256 vs samesize256": lambda r: compare(r["C_lg"]["after"], r["B_ab"]["after"]),
        "DECOMP resize16 vs samesize16": lambda r: compare(r["C_sm"]["after"], r["B_ba"]["after"]),
        "PRED  samesize256 == ClearHash256": lambda r: compare(r["D_lg"]["after"], r["C_lg"]["after"]),
        "PRED  samesize16 == ClearHash16": lambda r: compare(r["D_sm"]["after"], r["C_sm"]["after"]),
        "POSCTRL fresh16 vs fresh256": lambda r: compare(r["A_fresh"][S], r["A_fresh"][L]),
        "POSCTRL fresh256 vs fresh256 repeat": lambda r: compare(r["A_fresh"][L], r["A2_fresh_repeat"]),
        "POSCTRL fresh16 vs fresh16 repeat": lambda r: compare(r["A_fresh"][S], r["A3_fresh_small_repeat"]),
    }
    n = len(rows)
    print("\n== summary over %d positions ==" % n)
    summary = {}
    for name, fn in checks.items():
        hits = [(r["i"], fn(r)) for r in rows]
        differing = [(i, d) for i, d in hits if d]
        move_changed = [i for i, d in differing if "bestmove" in d]
        node_changed = [i for i, d in differing if "nodes" in d]
        summary[name] = {
            "cells": n,
            "differing": len(differing),
            "move_changed": len(move_changed),
            "nodes_changed": len(node_changed),
            "indices_differing": [i for i, _ in differing],
        }
        print("%-38s differ %2d/%d  move %2d  nodes %2d%s" % (
            name, len(differing), n, len(move_changed), len(node_changed),
            "" if not differing else "  first=%d %s" % (differing[0][0], differing[0][1])))
    with open(args.out + ".summary.json", "w") as fh:
        json.dump({"args": vars(args), "summary": summary}, fh, indent=2)


if __name__ == "__main__":
    main()
