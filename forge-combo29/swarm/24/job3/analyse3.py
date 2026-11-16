#!/usr/bin/env python3
"""Reads the raw job-3 files and prints the report table.  Every number in REPORT_job3.md comes from here.

Usage: analyse3.py [dir] [prefix]
"""
import os
import sys

d = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
pre = sys.argv[2] if len(sys.argv) > 2 else "inf8"
TSAN = "WARNING: ThreadSanitizer"

p = os.path.join(d, pre + ".rounds")
if not os.path.exists(p):
    print(f"{p} not written yet")
    sys.exit(0)
lines = [l.rstrip("\n") for l in open(p)]
data = [l for l in lines if l and not l.startswith("#") and "|HANG" not in l and "|CRASH" not in l
        and "|STOP" not in l]
hangs = [l for l in lines if "|HANG" in l]
crashes = [l for l in lines if "|CRASH" in l]
stops = [l for l in lines if "|STOP" in l]
rawp = os.path.join(d, pre + ".raw")
raw = open(rawp, errors="replace").read() if os.path.exists(rawp) else ""
ntsan = raw.count(TSAN)
meta = {}
mp = os.path.join(d, pre + ".meta")
if os.path.exists(mp):
    for l in open(mp):
        k, _, v = l.rstrip("\n").partition("\t")
        meta.setdefault(k, []).append(v)

multi = [l for l in data if int(l.split("|")[3]) > 1]
illegal = [l for l in data if l.split("|")[5].startswith("ILLEGAL")]
zeros = [l for l in data if l.split("|")[5] == "0000"]
delays = [int(l.split("|")[2]) for l in data]
ms_after = [float(l.split("|")[6]) for l in data]
exitcodes = [l.split("\t")[1].strip() for l in lines if l.startswith("# engine_exit")]

print("| measure | value |")
print("|---|---|")
print(f"| rounds attempted | {len(data) + len(hangs) + len(crashes) + len(stops)} |")
print(f"| rounds with a bestmove | {len(data)} |")
print(f"| rounds with MORE than one bestmove line | {len(multi)} |")
print(f"| rounds with bestmove 0000 | {len(zeros)} |")
print(f"| illegal bestmoves | {len(illegal)} |")
print(f"| crashes | {len(crashes)} |")
print(f"| hangs (no bestmove in 60 s after stop) | {len(hangs)} |")
print(f"| aborted on a UCI error line | {len(stops)} |")
print(f"| TSan report blocks | {ntsan} |")
print(f"| nm __tsan_ in .meta | {meta.get('nm_tsan', ['?'])[0]} |")
print(f"| threads / hash | {meta.get('threads', ['?'])[0]} / {meta.get('hash', ['?'])[0]} |")
print(f"| engine exit code | {exitcodes[0] if exitcodes else '?'} |")
if delays:
    print(f"| stop delay ms: min / mean / max | {min(delays)} / {sum(delays)/len(delays):.0f} / {max(delays)} |")
if ms_after:
    ms_sorted = sorted(ms_after)
    print(f"| ms from `stop` to bestmove: median / 99th / max | "
          f"{ms_sorted[len(ms_sorted)//2]:.1f} / {ms_sorted[min(len(ms_sorted)-1, int(len(ms_sorted)*0.99))]:.1f} / "
          f"{ms_sorted[-1]:.1f} |")
for l in illegal[:10]:
    print("ILLEGAL: " + l[:200])
for l in multi[:10]:
    print("MULTI: " + l[:200])
