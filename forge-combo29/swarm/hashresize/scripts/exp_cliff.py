"""Experiment K - does the same-value transient MOVE the memory cliff?

forge-findings.md S7 item 3c bisected the memory cliff exactly: "Hash 16 needs
60 MB (dies at 56), Hash 256 needs 300 MB (dies at 290)" under `ulimit -v`.
Those numbers were measured with a resize to the FINAL size, i.e. one
allocation.

`TranspositionTable::resize` holds the new block while the old one is still
owned, so a same-value resize at size S needs S for the new table PLUS S still
resident for the old.  If the transient is real and page-backed (experiment H
measured exactly one table size above the post-resize RSS, 7 of 7 at every
size), then a process that reached Hash S by a same-value resize needs about
TWICE the address space a fresh process at Hash S needs.

That is a falsifiable prediction against the audit's own published cliff:

  K1  fresh at Hash S under a cap just above the published cliff   -> survives
  K2  fresh at Hash S, then a same-value resize, same cap          -> ?

If K2 dies where K1 survives, the transient is not a curiosity: it changes the
engine's memory requirement, and it does so for every runner that re-sends its
option block.

The cap is applied with RLIMIT_AS on the child so the reading is exact, and each
cell is run at two caps so the boundary is bracketed rather than assumed.
"""

import argparse
import json
import os
import resource
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine


def limited_child(limit_mb):
    """preexec_fn that sets RLIMIT_AS for the engine."""
    def apply():
        bytes_ = limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (bytes_, bytes_))
    return apply


def cell(engine, limit_mb, hash_mb, mode, go):
    """Return (survived, nodes_or_error).

    mode is one of:
      fresh    - Hash S, then search.                      (one allocation)
      warmonly - Hash S, newgame, search, search.          (the resize cell's
                 sequence WITHOUT a resize -- the control that separates "the
                 resize" from "a second search happened")
      resize   - Hash S, newgame, search, Hash S again, search.
    """
    proc_holder = {}
    real_popen = subprocess.Popen

    def patched(*args, **kwargs):
        kwargs["preexec_fn"] = limited_child(limit_mb)
        p = real_popen(*args, **kwargs)
        proc_holder["p"] = p
        return p

    subprocess.Popen = patched
    try:
        e = Engine(engine)
    finally:
        subprocess.Popen = real_popen

    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        if mode in ("warmonly", "resize"):
            e.newgame()
            e.search("position startpos", "go depth 6", timeout=60)
        if mode == "resize":
            e.setoption("Hash", hash_mb)
        r = e.search("position startpos", go, timeout=120)
        survived = bool(r["ok"] and r["bestmove"])
        return survived, r["nodes"], None
    except Exception as exc:  # noqa: BLE001
        return False, None, "%s: %s" % (type(exc).__name__, exc)
    finally:
        try:
            e.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--caps", default=None,
                    help="comma-separated caps; overrides the default plan")
    ap.add_argument("--hash", type=int, default=None)
    args = ap.parse_args()

    go = "go depth %d" % args.depth
    out = {"engine": args.engine, "go": go, "cells": []}

    if args.caps:
        plan = [(args.hash or 256, [int(c) for c in args.caps.split(",")])]
    else:
        plan = [
            (16, [56, 60, 64, 76, 90, 120]),
            (256, [290, 300, 320, 560, 600]),
        ]
    print("%-6s %-7s %-7s %-9s %-9s %s" % ("Hash", "capMB", "warm", "fresh", "resized", "note"))
    for hash_mb, caps in plan:
        for cap in caps:
            ok_w, nodes_w, err_w = cell(args.engine, cap, hash_mb, "warmonly", go)
            ok_f, nodes_f, err_f = cell(args.engine, cap, hash_mb, "fresh", go)
            ok_r, nodes_r, err_r = cell(args.engine, cap, hash_mb, "resize", go)
            note = ""
            if ok_w and not ok_r:
                note = "RESIZE DIES; the no-resize control survives -> the resize is the cause"
            elif not ok_w and ok_r:
                note = "unexpected: control died, resize survived"
            elif ok_f and not ok_r and not ok_w:
                note = "both warm arms die; the second search is what needs the memory"
            out["cells"].append({
                "hash_mb": hash_mb, "cap_mb": cap,
                "warmonly_ok": ok_w, "warmonly_nodes": nodes_w, "warmonly_err": err_w,
                "fresh_ok": ok_f, "fresh_nodes": nodes_f, "fresh_err": err_f,
                "resized_ok": ok_r, "resized_nodes": nodes_r, "resized_err": err_r,
                "note": note,
            })
            print("%-6d %-7d %-7s %-9s %-9s %s" % (hash_mb, cap, ok_w, ok_f, ok_r, note))
            sys.stdout.flush()

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
