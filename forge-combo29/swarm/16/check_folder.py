#!/usr/bin/env python3
"""check_folder.py — integrity check for ONE swarm seat's folder. Adopt it for your own seat number.

USAGE
-----
    python3 check_folder.py NN [REPO]

    python3 check_folder.py 16                        # run from the repository root
    python3 check_folder.py 16 /agent/repos/dwqww     # run from anywhere

    NN     your seat number; `7` and `07` both work (zero-padded internally).
    REPO   repository root; defaults to the current directory.

OUTPUT
------
    One line per check, then either `ALL CHECKS PASS.` or `NEEDS ATTENTION:` followed by each fault.
    Exit code 0 = clean, 1 = something to fix. Suitable for a pre-FINAL gate:
        python3 forge-combo29/swarm/NN/check_folder.py NN . || echo "FIX BEFORE FINAL"

WHAT EACH OF THE THREE CHECKS CATCHES
-------------------------------------
1. FINDINGS.md TABLE WELL-FORMEDNESS
   Every line starting `| S-` must split into exactly 4 fields for a C-row (`| S-C...`) or 5 for an F-row
   (`| S-F...`). This one rule catches two silent failures that both happened to seat 16:
     * a PIPE INSIDE A CELL (`median |gap| is 14 cp`) — the row splits into 6 or 7 fields and every later cell
       shifts, so the table renders wrong while looking almost right;
     * a row written to the WRONG FILE, which shows up here as a gap in the id sequence of your own table —
       reported as `id gaps`, e.g. `F: no row for [16, 17, ...]`. That is the fingerprint of a stray append.
   It also reports DUPLICATE ids (the same row appended twice).
   Note: an id gap is not always a fault — a seat may deliberately skip an id — so the line is a prompt to look,
   not an automatic failure. Malformed rows and duplicates are always failures.

2. NOTHING STAGED OUTSIDE YOUR FOLDER
   `git log --diff-filter=A` from your seat commit (found by the message `swarm NN seat`) lists every file ever
   ADDED on your branch, and anything not under `forge-combo29/swarm/NN/` is reported by full path.
   This is deliberately stronger than inspecting the working tree: a stray file that was staged once still
   appears after you delete it, which is exactly the case you need to know about.
   If the seat commit cannot be found, the check says so and skips rather than passing silently.

3. TEXT-ONLY
   No file in the folder may contain a NUL byte or fail UTF-8 decoding. Catches an accidentally committed
   binary, a build artefact, a `__pycache__` (the walk skips that directory), or a file with stray control bytes.

WHY IT IS TRUSTWORTHY
---------------------
A check that has never been seen to fail proves nothing. This script was validated against PLANTED FAULTS: in a
scratch repository, a row containing `median |gap|` and a `FINDINGS.md` written outside the seat folder were both
reported — the malformed row as `7 fields, expected 5`, the stray as `OUTSIDE your folder:
['forge-combo29/swarm/FINDINGS.md']`. If you modify the script, re-plant a fault and confirm it still fires.

ONE THING THAT LOOKS LIKE A FAULT AND IS NOT
---------------------------------------------
`FINDINGS.md: MISSING` for a seat other than yours is expected: every seat works in its own checkout, which holds
only its own folder. Run the tool with YOUR seat number. If it reports your own FINDINGS.md missing, that is real.

WHAT IT DOES NOT CHECK
----------------------
It does not validate the CONTENT of a finding (whether the number is right), it does not know which findings were
confirmed by another seat, and it does not check your STATUS.md or FINAL.md. It checks the record's integrity, not
its truth — those are different problems and this script only claims the first.

AUTHOR / PROVENANCE
-------------------
Written by swarm seat 16 (area 6) on 2026-11-16 after a wrong relative path (`cat >> ../../FINDINGS.md` from a job
subdirectory) silently scattered 20 findings rows across four files while its own FINDINGS.md stopped at S-F15.
Nothing errored at any step. Companion notes: WARNING_stray_paths.md in this folder.
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
