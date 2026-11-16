#!/usr/bin/env python3
"""check_folder.py NN [REPO] : the two integrity checks for a swarm folder, as one runnable script.

usage:  python3 check_folder.py 16
        python3 check_folder.py 16 /agent/repos/dwqww

Checks, in order of importance:
  1. FINDINGS.md table well-formedness. Every line starting `| S-` must split into exactly 4 fields if it is a
     C-row (`| S-C...`) or 5 fields if it is an F-row (`| S-F...`). This catches BOTH of the silent failures
     this folder has actually suffered:
       * a row that landed in the wrong file (so an id is missing from your own table), and
       * a pipe character inside a cell (which splits the row into 6 or 7 fields and shifts every later cell).
     It also reports duplicate ids and ids that skip a number.
  2. Nothing outside your folder was ever staged on your branch. Uses `git log --diff-filter=A` from your seat
     commit, which is stronger than looking at the working tree: a stray file that was staged once shows up even
     if it is gone now.
  3. Text-only: no file in the folder contains a NUL byte or fails UTF-8.
Exit code 0 = all checks pass, 1 = something needs attention.
"""
import os
import re
import subprocess
import sys

SEAT = sys.argv[1].zfill(2)
REPO = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
FOLDER = f"forge-combo29/swarm/{SEAT}"
fails = []

print(f"=== checking seat {SEAT} in {REPO}")
print(f"    folder {FOLDER}")

# ---------- 1. findings table ----------
findings = os.path.join(REPO, FOLDER, "FINDINGS.md")
if not os.path.exists(findings):
    fails.append("FINDINGS.md missing")
    print("1. FINDINGS.md: MISSING")
else:
    rows = [l.rstrip("\n") for l in open(findings) if l.startswith("| S-")]
    malformed = []
    ids = []
    for i, l in enumerate(rows, 1):
        want = 4 if re.match(r"\| S-C", l) else 5
        got = len(l.strip().strip("|").split("|"))
        m = re.match(r"\| (S-[FC]\d+)", l)
        if m:
            ids.append(m.group(1))
        if got != want:
            malformed.append(f"row {i} ({m.group(1) if m else '?'}): {got} fields, expected {want}")
    dupes = sorted({k for k in ids if ids.count(k) > 1})
    nums = {}
    for k in ids:
        kind, n = k.split("-")[1][0], int(k.split("-")[1][1:])
        nums.setdefault(kind, set()).add(n)
    gaps = []
    for kind, s in nums.items():
        if s:
            missing = sorted(set(range(min(s), max(s) + 1)) - s)
            if missing:
                gaps.append(f"{kind}: no row for {missing}")
    print(f"1. FINDINGS.md: {len(rows)} rows, {len(ids)} ids")
    print(f"   malformed rows: {malformed or 'none'}")
    print(f"   duplicate ids : {dupes or 'none'}")
    print(f"   id gaps       : {gaps or 'none'}  (a gap is not always wrong -- but a stray row often looks like one)")
    if malformed:
        fails.append(f"malformed findings rows: {len(malformed)}")

# ---------- 2. nothing outside the folder was staged ----------
try:
    seat_commits = subprocess.run(
        ["git", "-C", REPO, "log", "--reverse", "--format=%h", "--grep", f"swarm {SEAT} seat"],
        capture_output=True, text=True).stdout.split()
    seat_base = seat_commits[0] if seat_commits else None
    if seat_base is None:
        print("2. stray files: could not find the seat commit (skipped)")
    else:
        out = subprocess.run(
            ["git", "-C", REPO, "log", "--diff-filter=A", "--name-only",
             "--pretty=format:", f"{seat_base}..HEAD"],
            capture_output=True, text=True).stdout
        # split on newlines AND drop any stray NUL/empty tokens, so a separator can never look like a path
        added = [p.strip("\x00\r") for p in out.replace("\x00", "\n").split("\n")]
        added = [p for p in added if p and not re.fullmatch(r"[0-9a-f]{7,}", p)]
        outside = sorted({p for p in added if not p.startswith(FOLDER + "/")})
        print(f"2. files added since seat commit {seat_base}: {len(set(added))}")
        print(f"   OUTSIDE your folder: {outside or 'none'}")
        if outside:
            fails.append(f"{len(outside)} files added outside the folder")
except Exception as exc:  # noqa: BLE001
    print(f"2. stray files: check failed to run: {exc}")

# ---------- 3. text only ----------
print("3. text-only check:")
n_bad = 0
n_files = 0
for root, dirs, files in os.walk(os.path.join(REPO, FOLDER)):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        p = os.path.join(root, f)
        n_files += 1
        data = open(p, "rb").read()
        if b"\x00" in data:
            print(f"   BINARY: {p}")
            n_bad += 1
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            print(f"   NOT UTF-8: {p}")
            n_bad += 1
print(f"   files {n_files}, non-text {n_bad}")
if n_bad:
    fails.append(f"{n_bad} non-text files")

print()
if fails:
    print("NEEDS ATTENTION:")
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL CHECKS PASS.")
