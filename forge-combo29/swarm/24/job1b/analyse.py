#!/usr/bin/env python3
"""Reads the raw job-1 files and prints the report table.  Every number in the report comes from here.

Usage: analyse.py [dir]   (default: the directory this script is in)
"""
import os
import re
import sys
import glob

d = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

TSAN = "WARNING: ThreadSanitizer"
rows = []
total = {"positions": 0, "bestmove": 0, "illegal": 0, "nolegal": 0, "crashes": 0,
         "timeouts": 0, "tsan": 0, "stops": 0, "answers": 0, "ms": 0}
for pre in ("r2", "r4"):
    raw = os.path.join(d, pre + ".raw")
    res = os.path.join(d, pre + ".results")
    meta = os.path.join(d, pre + ".meta")
    if not os.path.exists(res):
        rows.append((pre, "MISSING", 0, 0, 0, 0, 0, 0))
        continue
    lines = [l.rstrip("\n") for l in open(res) if not l.startswith("#")]
    bestmoves = [l for l in lines if l.count("|") >= 5]
    illegal = [l for l in bestmoves if "ILLEGAL" in l.split("|")[3]]
    nolegal = [l for l in bestmoves if l.split("|")[3] == "nolegal-ok"]
    crashes = [l for l in lines if "|CRASH|" in l]
    timeouts = [l for l in lines if "|TIMEOUT|" in l]
    stops = [l for l in lines if "STOP" in l.split("|")[2]]
    ntsan = 0
    nans = 0
    if os.path.exists(raw):
        txt = open(raw, errors="replace").read()
        ntsan = txt.count(TSAN)
        nans = len([l for l in txt.splitlines() if l.startswith("info depth")])
    exitcode = "?"
    for l in lines:
        if l.startswith("# engine_exit"):
            exitcode = l.split("\t")[1].strip()
    mseta = ""
    if os.path.exists(meta):
        for l in open(meta):
            if l.startswith("nm_tsan"):
                mseta = l.split("\t")[1].strip()
    rows.append((pre, exitcode, len(bestmoves), len(illegal), len(nolegal), len(crashes),
                 len(timeouts), ntsan, mseta))
    total["positions"] += len(bestmoves)
    total["bestmove"] += len([l for l in bestmoves if l.split("|")[2] not in ("-",)])
    total["illegal"] += len(illegal)
    total["nolegal"] += len(nolegal)
    total["crashes"] += len(crashes)
    total["timeouts"] += len(timeouts)
    total["tsan"] += ntsan
    total["stops"] += len(stops)
    total["answers"] += nans

print("| run | exit | bestmoves | illegal bestmoves | bestmove 0000 on no-legal pos | crashes | timeouts | "
      "TSan reports | nm __tsan_ |")
print("|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print("| " + " | ".join(str(x) for x in r[:9]) + " |")
print()
print(f"TOTAL positions searched      : {total['positions']}")
print(f"TOTAL bestmove lines          : {total['bestmove']}")
print(f"TOTAL illegal bestmoves       : {total['illegal']}")
print(f"TOTAL bestmove 0000 (no legal): {total['nolegal']}")
print(f"TOTAL crashes                 : {total['crashes']}")
print(f"TOTAL hangs/timeouts          : {total['timeouts']}")
print(f"TOTAL TSan report blocks      : {total['tsan']}")
print(f"TOTAL runs stopped on a UCI error: {total['stops']}")
print(f"TOTAL info depth lines        : {total['answers']}")
