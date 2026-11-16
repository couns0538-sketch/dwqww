#!/usr/bin/env python3
"""scan_repo.py -- run the is_unfinished checker over every engine-output file in the repository.

It finds files that contain `info depth` lines and runs the R1 depth rule on them. The requested depth is
inferred per file from the `=== commands:` header that my own harnesses write (`go depth N`), and from
`go depth N` lines inside the file itself (soak logs echo their commands). When neither is available the
rule is reported as INAPPLICABLE for that file rather than guessed.

Usage: scan_repo.py REPO_ROOT OUTDIR
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


def files_with_search_output():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True).stdout
    hits = []
    for rel in out.splitlines():
        if not rel.lower().endswith((".txt", ".log", ".out", ".stdout.txt")):
            continue
        p = os.path.join(ROOT, rel)
        try:
            with open(p, "rb") as f:
                head = f.read(200000)
        except OSError:
            continue
        if b"info depth" in head:
            hits.append(rel)
    return hits


def requested_depth(text):
    """a `go depth N` in the file's own command echo, or the harness header"""
    m = re.findall(r"^\s*(?:go )?depth (\d+)", text, re.M)
    if m:
        return int(m[0])
    m = re.search(r"go depth (\d+)", text)
    if m:
        return int(m.group(1))
    return None


rows = []
for rel in files_with_search_output():
    p = os.path.join(ROOT, rel)
    text = open(p, errors="replace").read()
    req = requested_depth(text)
    recs = records(text)
    # only count records that actually contain a bestmove or an info line
    verdicts = []
    for r in recs:
        if not any(l.startswith("info depth") for l in r) and not any(l.startswith("bestmove") for l in r):
            continue
        all_depths = [int(m.group(1)) for m in
                      (re.match(r"info depth (\d+)", l) for l in r) if m]
        fmax = max(all_depths) if all_depths else None
        verdicts.append(analyse(r, requested=req, file_max=fmax))
    n_unf = sum(1 for v in verdicts if v["verdict"] == "UNFINISHED")
    rows.append({"file": rel, "requested_depth": req, "records": len(verdicts),
                 "unfinished": n_unf,
                 "applicable": req is not None,
                 "verdicts": verdicts})

with open(os.path.join(OUT, "scan_repo.json"), "w") as f:
    json.dump(rows, f, indent=1)
    f.write("\n")

tot_rec = sum(r["records"] for r in rows)
tot_unf = sum(r["unfinished"] for r in rows)
print("files with engine search output: %d" % len(rows))
print("records examined               : %d" % tot_rec)
print("records flagged UNFINISHED     : %d" % tot_unf)
print()
for r in sorted(rows, key=lambda x: -x["records"])[:25]:
    print("  %-72s req=%-4s recs=%-3d unfinished=%d%s"
          % (r["file"][-72:], r["requested_depth"], r["records"], r["unfinished"],
             "" if r["applicable"] else "   [depth not recorded]"))
