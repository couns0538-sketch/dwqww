#!/usr/bin/env python3
"""analyse.py — read the raw records of area-4 job 1 and print the report tables.

Every table printed here is the output of this script over the committed raw
files; nothing is typed by hand. Usage: python3 analyse.py RUNDIR
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

import chess

TSAN_HDR = "WARNING: ThreadSanitizer"


def load(run):
    recs = []
    p = os.path.join(run, "records.jsonl")
    if not os.path.exists(p):
        return recs
    for line in open(p):
        recs.append(json.loads(line))
    return recs


def race_key(block):
    """Collapse a TSan report to (top frame of first access, kind)."""
    lines = block.splitlines()
    kind = ""
    tops = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("Read of size") or s.startswith("Write of size") or \
           s.startswith("Atomic read") or s.startswith("Atomic write"):
            kind = s.split(" at ")[0]
        if s.startswith("#0 "):
            tops.append(re.sub(r" \(forge\+0x[0-9a-f]+.*", "", s[3:]))
    return (kind, tops[0] if tops else "?", tuple(tops[1:2]))


def blocks(stderr):
    out = []
    cur = None
    for ln in stderr.splitlines():
        if ln.startswith("==="):
            continue
        if ln.strip().startswith(TSAN_HDR):
            if cur:
                out.append(cur)
            cur = ln
        elif cur is not None:
            cur += "\n" + ln
    if cur:
        out.append(cur)
    return out


def main():
    runroot = sys.argv[1]
    tags = sorted(glob.glob(os.path.join(runroot, "rep*_t*")))
    tags = [t for t in tags if os.path.isdir(t)]
    sets = {}
    for t in tags:
        sets[os.path.basename(t)] = load(t)

    print("== A. per tag: searches, race reports (blocks), hangs, bad-answer stops, illegal bestmoves ==")
    print("%-10s %6s %8s %10s %10s %6s %8s %10s" %
          ("tag", "n", "races", "distinct", "hangs", "stops", "illegal", "median_s"))
    per_tag_keys = {}
    for tag, recs in sets.items():
        races = 0
        keys = Counter()
        hangs = 0
        stops = 0
        illegal = 0
        walls = []
        for r in recs:
            bs = blocks(r.get("stderr", ""))
            races += len(bs)
            for b in bs:
                keys[race_key(b)] += 1
            if r.get("hang"):
                hangs += 1
                continue
            if r.get("bad"):
                stops += 1
            walls.append(r.get("wall", 0.0))
            bm = (r.get("bestmove") or "").split()
            mv = bm[1] if len(bm) > 1 else ""
            try:
                board = chess.Board(r["fen"])
            except Exception:
                continue
            legal = board.legal_moves.count()
            if mv == "0000":
                if legal:
                    illegal += 1
                    print("  ILLEGAL 0000 with %d legal moves: %s" % (legal, r["fen"]))
            elif mv:
                try:
                    m = chess.Move.from_uci(mv)
                except Exception:
                    illegal += 1
                    print("  UNPARSEABLE bestmove %r for %s" % (mv, r["fen"]))
                    continue
                if m not in board.legal_moves:
                    illegal += 1
                    print("  ILLEGAL bestmove %s for %s" % (mv, r["fen"]))
        walls.sort()
        med = walls[len(walls) // 2] if walls else 0.0
        per_tag_keys[tag] = keys
        print("%-10s %6d %8d %10d %10d %6d %8d %10.2f" %
              (tag, len(recs), races, len(keys), hangs, stops, illegal, med))

    print()
    print("== B. distinct TSan report kinds over ALL tags, with the number of tags that showed each ==")
    allkeys = defaultdict(set)
    total = Counter()
    for tag, keys in per_tag_keys.items():
        for k, n in keys.items():
            allkeys[k].add(tag)
            total[k] += n
    for k, n in total.most_common():
        print("%6d occurrences in %2d tags  %-12s %s" % (n, len(allkeys[k]), k[0], k[1]))
        if k[2]:
            print("        via %s" % (k[2],))

    print()
    print("== C. node counts and bestmoves: rep1 vs rep2, per threads count ==")
    print("%-8s %12s %12s %12s %12s" % ("threads", "nodes_same", "nodes_diff", "bm_same", "bm_diff"))
    for t in (1, 2, 4, 8, 16):
        a = {r["index"]: r for r in sets.get("rep1_t%d" % t, [])}
        b = {r["index"]: r for r in sets.get("rep2_t%d" % t, [])}
        if not a or not b:
            continue
        nsame = ndiff = bsame = bdiff = 0
        for i in a:
            if i not in b:
                continue
            if a[i].get("nodes") == b[i].get("nodes"):
                nsame += 1
            else:
                ndiff += 1
            if a[i].get("bestmove") == b[i].get("bestmove"):
                bsame += 1
            else:
                bdiff += 1
        print("%-8d %12d %12d %12d %12d" % (t, nsame, ndiff, bsame, bdiff))

    print()
    print("== D. race reports at Threads 1 (control) ==")
    for t in ("rep1_t1", "rep2_t1"):
        print("%s: %d reports" % (t, sum(len(blocks(r.get("stderr", ""))) for r in sets.get(t, []))))

    print()
    print("== E. first 40 lines of one report per distinct kind ==")
    shown = set()
    for tag, recs in sets.items():
        for r in recs:
            for b in blocks(r.get("stderr", "")):
                k = race_key(b)
                if k in shown:
                    continue
                shown.add(k)
                print("---- kind %s %s from %s index %d" % (k[0], k[1], tag, r["index"]))
                print("\n".join(b.splitlines()[:40]))
                print()


if __name__ == "__main__":
    main()
