#!/usr/bin/env python3
"""Compare the two columns of pc20_rerun.py output (self vs colour mirror).

Rules: the colour mirror flips boards AND side to move, so a side-to-move-relative number must be EQUAL.
  eval mode  : hce, nnue, total compared for exact equality.
  search mode: bestmove compared after mirroring every square; score compared with the EQUAL rule;
               node counts compared for information only (S-F22 says totals are not a symmetry test).

usage: pc20_compare.py eval|search FILE.jsonl [FILE.jsonl ...]
"""
import json
import sys

import chess


def mir(u):
    return (chess.square_name(chess.parse_square(u[0:2]) ^ 56) +
            chess.square_name(chess.parse_square(u[2:4]) ^ 56) + (u[4:] or ""))


def main():
    mode = sys.argv[1]
    paths = sys.argv[2:]
    n = bad = 0
    node_eq = 0
    diffs = []
    for path in paths:
        for line in open(path):
            r = json.loads(line)
            n += 1
            a, b = r["self"], r["mirror"]
            if mode == "eval":
                keys = ("hce", "nnue", "total")
                if any(a.get(k) != b.get(k) for k in keys):
                    bad += 1
                    diffs.append((r["index"], {k: (a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)}))
            else:
                if a["nodes"] == b["nodes"]:
                    node_eq += 1
                bm_ok = b["bm"] == mir(a["bm"])
                sc_ok = a["kind"] == b["kind"] and a["score"] == b["score"]
                if not (bm_ok and sc_ok):
                    bad += 1
                    diffs.append((r["index"], a["bm"], b["bm"], mir(a["bm"]), a["score"], b["score"]))
    print("pairs compared: %d" % n)
    if mode == "eval":
        print("pairs with ANY hce/nnue/total difference: %d" % bad)
    else:
        print("pairs with a differing bestmove or score: %d (%.1f%%)" % (bad, 100.0 * bad / max(n, 1)))
        print("pairs whose NODE COUNTS are equal: %d (%.1f%%) - informational only, see S-F22" % (node_eq, 100.0 * node_eq / max(n, 1)))
    for d in diffs[:25]:
        print("  " + "\t".join(str(x) for x in d))
    if len(diffs) > 25:
        print("  ... %d more" % (len(diffs) - 25))


if __name__ == "__main__":
    main()
