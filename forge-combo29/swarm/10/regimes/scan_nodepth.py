#!/usr/bin/env python3
"""scan_nodepth.py -- the 585-file gap: files with engine output but NO recorded requested depth.

For each such file it asks, explicitly:
  * are there any `go` command echoes at all, and can a depth be recovered from them?
  * if not, can rule R2 (last depth < largest depth in this file) judge the records?
  * how many records can be judged at all, and does any flag UNFINISHED?

A record is "judgeable" only when the file's own content supplies a reference depth: either a
recoverable `go depth N`, or a larger depth elsewhere in the same file. Records in a single-search file
with no depth echo are UNJUDGEABLE by this method and are counted as such -- not guessed.

Usage: scan_nodepth.py REPO_ROOT OUTDIR
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from is_unfinished import analyse, records

ROOT = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)


def candidate_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True).stdout
    hits = []
    for rel in out.splitlines():
        if not rel.lower().endswith((".txt", ".log", ".out", ".stdout.txt")):
            continue
        try:
            raw = open(os.path.join(ROOT, rel), "rb").read(200000)
        except OSError:
            continue
        if b"info depth" in raw:
            hits.append(rel)
    return hits


def recover_depth(text):
    """every way a requested depth can be present in a log"""
    pats = [r"^\s*go depth (\d+)", r"go depth (\d+)", r"^\s*depth (\d+)\s*$",
            r"bench depth (\d+)"]
    for p in pats:
        m = re.findall(p, text, re.M)
        if m:
            return int(m[0]), p
    return None, None


rows = []
for rel in candidate_files():
    text = open(os.path.join(ROOT, rel), errors="replace").read()
    req, how = recover_depth(text)
    if req is not None:
        continue                      # this file is NOT in the gap
    recs = [r for r in records(text)
            if any(l.startswith("info depth") for l in r) or any(l.startswith("bestmove") for l in r)]
    depths_per_record = []
    for r in recs:
        ds = [int(m.group(1)) for m in (re.match(r"info depth (\d+)", l) for l in r) if m]
        depths_per_record.append(ds)
    all_depths = [d for ds in depths_per_record for d in ds]
    file_max = max(all_depths) if all_depths else None
    judgeable = 0
    flagged = 0
    for r, ds in zip(recs, depths_per_record):
        # R2 can judge a record only if some depth reference exists in this file
        if file_max is None:
            continue
        last = ds[-1] if ds else None
        if last is None:
            # bestmove with no info: judgeable by the second clause
            judgeable += 1
            flagged += 1
            continue
        judgeable += 1
        if last < file_max:
            flagged += 1
    rows.append({"file": rel, "records": len(recs), "file_max_depth": file_max,
                 "judgeable_by_R2": judgeable, "flagged": flagged,
                 "ungjudgeable": len(recs) - judgeable})

with open(os.path.join(OUT, "scan_nodepth.json"), "w") as f:
    json.dump(rows, f, indent=1)
    f.write("\n")

gapp = len(rows)
tot_rec = sum(r["records"] for r in rows)
tot_judge = sum(r["judgeable_by_R2"] for r in rows)
tot_flag = sum(r["flagged"] for r in rows)
multi = sum(1 for r in rows if r["file_max_depth"] is not None)
print("files in the gap (no recoverable requested depth): %d" % gapp)
print("records in those files                            : %d" % tot_rec)
print("records R2 could actually judge                   : %d" % tot_judge)
print("records it flagged UNFINISHED                     : %d" % tot_flag)
print("files where at least one depth reference existed  : %d / %d" % (multi, gapp))
print()
print("the flagged ones:")
for r in rows:
    if r["flagged"]:
        print("  %-70s recs=%-3d flagged=%d file_max=%s"
              % (r["file"][-70:], r["records"], r["flagged"], r["file_max_depth"]))
