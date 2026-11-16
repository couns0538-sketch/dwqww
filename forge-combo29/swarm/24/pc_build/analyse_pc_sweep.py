#!/usr/bin/env python3
"""Reads the PC-build Threads-sweep raw files and prints the table. No score is read or compared."""
import os, sys
d = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
print("| Threads | positions answered | illegal bestmoves | crashes | timeouts | TSan blocks | nm __tsan_ |")
print("|---|---|---|---|---|---|---|")
tot = [0,0,0,0,0]
for t in ("2","4","8","16"):
    pre = os.path.join(d, "pcT"+t)
    res = pre+".results"; raw = pre+".raw"; meta = pre+".meta"
    if not os.path.exists(res):
        print(f"| {t} | MISSING | - | - | - | - | - |"); continue
    lines=[l.rstrip("\n") for l in open(res)]
    data=[l for l in lines if l and not l.startswith("#") and "TIMEOUT" not in l and "CRASH" not in l and "STOP" not in l]
    ill=[l for l in data if "ILLEGAL" in l.split("|")[3]]
    to=len([l for l in lines if "TIMEOUT" in l]); cr=len([l for l in lines if "CRASH" in l])
    ntsan = open(raw,errors="replace").read().count("WARNING: ThreadSanitizer") if os.path.exists(raw) else "?"
    nm="?"; ex="?"
    if os.path.exists(meta):
        for l in open(meta):
            if l.startswith("nm_tsan"): nm=l.split("\t")[1].strip()
            if l.startswith("engine_exit_code"): ex=l.split("\t")[1].strip()
    print(f"| {t} | {len(data)} | {len(ill)} | {cr} | {to} | {ntsan} | {nm} |")
    tot=[tot[0]+len(data),tot[1]+len(ill),tot[2]+cr,tot[3]+to,tot[4]+(ntsan if isinstance(ntsan,int) else 0)]
print()
print(f"TOTAL answered {tot[0]}, illegal {tot[1]}, crashes {tot[2]}, timeouts {tot[3]}, TSan blocks {tot[4]}")
