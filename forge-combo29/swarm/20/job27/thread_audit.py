#!/usr/bin/env python3
"""thread_audit.py — seat 20: which other seats' findings were measured above Threads 1?

Swarm rule (22:19Z): any score must be from Threads 1 unless the job is about threading. Seat 04 found the PC build
at Threads 4 gives four distinct scores on one position (+2576, mate 13, mate 18, mate 16; nodes 5.0M-31.4M) while
Threads 1 gives +2207 four times with identical nodes.

This scans every seat's FINDINGS.md on the remote for a thread count, and classifies each finding line:
  SAFE       - states Threads 1, or explicitly a threading job, or reports only moves/nodes/legality
  AT_RISK    - reports a SCORE (cp/mate) and mentions Threads >1 or says nothing about threads while naming a
               multi-thread run
  UNSTATED   - reports a score and never says which thread count  -> cannot be confirmed as-is, needs a re-run
  THREAD_JOB - area 4 (threads under TSAN) or an explicitly threading case

Prints one line per seat with counts, and lists every AT_RISK/UNSTATED line that reports a score.

usage: thread_audit.py <outdir>
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

score_re = re.compile(r"\b(cp|mate)\s*[-+]?\d+", re.I)
thread_re = re.compile(r"threads?\s*[:=]?\s*(\d+)", re.I)
out = []


def say(s=""):
    out.append(s)
    print(s)


branch = "for-fable-and-opus/swarm-"
seats = []
for n in range(1, 61):
    s = f"{n:02d}"
    r = subprocess.run(["git", "ls-remote", "origin", f"refs/heads/{branch}{s}"],
                       capture_output=True, text=True)
    if r.stdout.strip():
        seats.append(s)

say(f"seats with a branch: {len(seats)}")
say()
say(f"{'seat':5s} {'lines':>6s} {'scored':>7s} {'t1':>4s} {'risk':>5s} {'unstated':>9s}")
risk_rows = []
for s in seats:
    br = f"{branch}{s}"
    f = subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", br],
                       capture_output=True, text=True)
    if f.returncode != 0:
        continue
    show = subprocess.run(["git", "show", f"FETCH_HEAD:forge-combo29/swarm/{s}/FINDINGS.md"],
                          capture_output=True, text=True)
    if show.returncode != 0:
        continue
    lines = [l for l in show.stdout.split("\n") if l.strip().startswith("|")]
    scored = t1 = risk = unstated = 0
    for l in lines:
        if not score_re.search(l):
            continue
        scored += 1
        tm = [int(x) for x in thread_re.findall(l)]
        low = l.lower()
        is_thread_job = (s == "04") or ("tsan" in low) or ("threadsanitizer" in low) or \
                        ("planted race" in low) or ("race" in low and "threads" in low)
        if 1 in tm or "threads 1" in low:
            t1 += 1
        elif any(t > 1 for t in tm):
            risk += 1
            risk_rows.append((s, "AT_RISK", l.strip()[:200]))
        elif is_thread_job:
            t1 += 0
        else:
            unstated += 1
            risk_rows.append((s, "UNSTATED", l.strip()[:200]))
    say(f"{s:5s} {len(lines):6d} {scored:7d} {t1:4d} {risk:5d} {unstated:9d}")

say()
say("== findings that report a score and either name Threads >1 or never state a thread count")
say("   (a confirmation of these must be a re-run at Threads 1, stating the thread count)")
seen = set()
for s, kind, txt in risk_rows:
    key = (s, txt[:80])
    if key in seen:
        continue
    seen.add(key)
    say(f"  seat {s} [{kind}] {txt}")

open(os.path.join(OUT, "thread_audit.txt"), "w").write("\n".join(out) + "\n")
print(f"\nwrote thread_audit.txt ({len(risk_rows)} flagged lines)")
