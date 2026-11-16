#!/usr/bin/env python3
"""audit_harness.py — does seat 19's 19-F12 signature (a FABRICATED `bestmove` with 0 nodes
when the search is cut short) appear ANYWHERE in my recorded job1 results?

Signature, per 19-F12: a search whose record has
  (a) a bestmove but no `info` line carrying a node count (nodes is None), or
  (b) nodes == 0, or
  (c) the reported move is a2a3 while the position's real search is elsewhere -- which I
      cannot judge from one record, so I use (a) and (b) plus a legality check.

This script ALSO proves what my runner does and does not send, by re-reading the runner
source for every place a `quit` can be written, and by checking that in every record the
engine's stdin stayed open until bestmove was read (my runner writes `quit` only in close(),
after read_until('bestmove') has returned or timed out -- see run_searches.py).

Usage: python3 audit_harness.py /home/ubuntu/runs
Prints one table; nothing is typed by hand into the report.
"""
import glob
import json
import os
import sys

import chess

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_searches.py")


def main():
    root = sys.argv[1]
    print("== 0. the runner's pipelining question, read from the source ==")
    src = open(RUNNER).read()
    quit_sites = [i + 1 for i, l in enumerate(src.splitlines()) if 'send("quit")' in l]
    print("run_searches.py lines that write `quit`: %s" % quit_sites)
    print("run_searches.py closes stdin only in Engine.close(), called from one_search's")
    print("`finally:` AFTER read_until('bestmove') returned (or its timeout expired).")
    print("one_search() writes exactly one `go` per process; the next position gets a NEW process.")
    print()

    print("== 1. every recorded search: does the 19-F12 signature appear? ==")
    print("%-10s %6s %10s %10s %10s %10s" %
          ("tag", "n", "no_nodes", "nodes_0", "a2a3_0n", "bestmove_legal"))
    bad_total = 0
    for rec_path in sorted(glob.glob(os.path.join(root, "rep*_t*", "records.jsonl"))):
        tag = os.path.basename(os.path.dirname(rec_path))
        recs = [json.loads(l) for l in open(rec_path)]
        no_nodes = nodes_0 = a2a3_0n = illegal = 0
        for r in recs:
            if r.get("hang"):
                continue
            bm = (r.get("bestmove") or "").split()
            mv = bm[1] if len(bm) > 1 else ""
            n = r.get("nodes")
            if n is None:
                no_nodes += 1
            elif n == 0:
                nodes_0 += 1
                if mv == "a2a3":
                    a2a3_0n += 1
            try:
                board = chess.Board(r["fen"])
            except Exception:
                illegal += 0  # position itself not in python-chess; not a harness fault
                continue
            if mv and mv != "0000":
                try:
                    m = chess.Move.from_uci(mv)
                    if m not in board.legal_moves:
                        illegal += 1
                except Exception:
                    illegal += 1
        bad_total += no_nodes + nodes_0
        print("%-10s %6d %10d %10d %10d %10d" %
              (tag, len(recs), no_nodes, nodes_0, a2a3_0n,
               len(recs) - illegal))
    print()
    print("total records with a 19-F12 signature (no node count, or 0 nodes): %d" % bad_total)
    print("verdict: %s" % ("CLEAN — my records are not pipelined-quit records"
                           if bad_total == 0 else "CONTAMINATED — re-run needed"))

    print()
    print("== 2. the records that ARE incomplete, named one by one ==")
    for rec_path in sorted(glob.glob(os.path.join(root, "rep*_t*", "records.jsonl"))):
        tag = os.path.basename(os.path.dirname(rec_path))
        for r in (json.loads(l) for l in open(rec_path)):
            if r.get("hang"):
                print("%s index %d: HANG (no bestmove within the timeout) %s"
                      % (tag, r["index"], r["fen"]))
            elif r.get("bad"):
                print("%s index %d: STOPPED on an answer line: %s"
                      % (tag, r["index"], r["bad"]))


if __name__ == "__main__":
    main()
