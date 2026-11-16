#!/usr/bin/env python3
"""Reads the raw job-2 files and prints the table.  Every number in REPORT_job2.md comes from here."""
import os
import sys

d = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
pre = "churn"
TSAN = "WARNING: ThreadSanitizer"

steps = [l.rstrip("\n") for l in open(os.path.join(d, pre + ".steps"))]
bad_kinds = ("STOP", "TIMEOUT", "CRASH", "STOP_AFTER_RESTART", "STOP_AT_HANDSHAKE")
data = [l for l in steps if l and not l.startswith("#") and not any(k in l for k in bad_kinds)]
bad = [l for l in steps if any(k in l for k in bad_kinds)]
raw = open(os.path.join(d, pre + ".raw"), errors="replace").read()
ntsan = raw.count(TSAN)
meta = {}
for l in open(os.path.join(d, pre + ".meta")):
    k, _, v = l.rstrip("\n").partition("\t")
    meta.setdefault(k, []).append(v)

threads_used = {}
hash_used = {}
illegal = []
for l in data:
    p = l.split("|")
    threads_used[p[1]] = threads_used.get(p[1], 0) + 1
    hash_used[p[2]] = hash_used.get(p[2], 0) + 1
    if p[7].startswith("ILLEGAL"):
        illegal.append(l)
newgames = len([l for l in data if l.split("|")[3] == "1"])
exitcodes = [l.split("\t")[1].strip() for l in steps if l.startswith("# engine_exit")]

print("| measure | value |")
print("|---|---|")
print(f"| steps attempted | {len(data) + len(bad)} |")
print(f"| steps completed | {len(data)} |")
print(f"| steps with ucinewgame | {newgames} |")
print(f"| aborted steps (STOP/TIMEOUT/CRASH) | {len(bad)} |")
print(f"| illegal bestmoves | {len(illegal)} |")
print(f"| engine exit code | {exitcodes[0] if exitcodes else '?'} |")
print(f"| TSan report blocks | {ntsan} |")
print(f"| nm __tsan_ in .meta | {meta.get('nm_tsan', ['?'])[0]} |")
print()
print("Threads values used (value: steps):", dict(sorted(threads_used.items(), key=lambda x: int(x[0]))))
print("Hash values used   (value: steps):", dict(sorted(hash_used.items(), key=lambda x: int(x[0]))))
print()
if bad:
    print("Aborted-step lines:")
    for l in bad:
        print("  " + l[:200])
print()
tot_ms = sum(float(l.split("|")[8]) for l in data)
print(f"sum of per-search wall times: {tot_ms/1000:.1f} s over {len(data)} searches")
for l in illegal:
    print("ILLEGAL: " + l[:200])
