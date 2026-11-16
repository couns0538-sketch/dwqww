#!/usr/bin/env python3
"""vacuity_audit.py : one pass over every number in my reports that came from a PARSED LINE.

The rule being applied (learned from my own 08-F9 attempt 1, which passed vacuously on a NaN comparison):
a number is only a number if the line it was parsed from was ACTUALLY FOUND in the raw file. A parser that
returns None / 0 / NaN on a missing line, followed by a comparison that cannot fail, produces a silent pass.

This script re-parses the raw files from my own committed job/check folders and reports, for each number in
my reports, whether the source line exists. It does not recompute the science; it checks the parsing step.
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = "/agent/repos/dwqww/forge-combo29/swarm/19"
rows = []


def note(name, source, found, value, verdict, why=""):
    rows.append((name, source, found, value, verdict, why))


def text(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None


# ---- 1. honesty numbers: bench lines must EXIST with the exact node count ----
for tag, d in [("honesty (base)", "honesty"),
               ("honesty (job2 patch)", "job2/honesty_patched"),
               ("honesty (job3 patch)", "job3/honesty_patched")]:
    base = os.path.join(ROOT, d)
    for depth, want in [(11, 312866), (13, 862329), (16, 3024920)]:
        p = os.path.join(base, "bench_%d.raw.txt" % depth)
        body = text(p)
        if body is None:
            note("bench %d nodes (%s)" % (depth, tag), p, False, "file MISSING", "FAIL")
            continue
        m = re.search(r"bench depth %d nodes (\d+)" % depth, body)
        if not m:
            note("bench %d nodes (%s)" % (depth, tag), p, False, "line NOT FOUND", "FAIL")
            continue
        got = int(m.group(1))
        note("bench %d nodes (%s)" % (depth, tag), p, True, got,
             "PASS" if got == want else "MISMATCH", "expected %d" % want)
    p = os.path.join(base, "perft5.raw.txt")
    body = text(p)
    m = re.search(r"^nodes (\d+)$", body or "", re.M)
    note("perft 5 nodes (%s)" % tag, p, m is not None,
         int(m.group(1)) if m else "line NOT FOUND",
         "PASS" if (m and int(m.group(1)) == 4865609) else "FAIL", "expected 4865609")

# ---- 2. job1 / job1b profile sample counts ----
for label, p, pat in [
    ("job1 samples", "job1/profile/perf_symbols_all.txt", r"^# Samples: (\d+)K?"),
    ("job1b samples (profD)", "job1b/profD/perf_symbols_all.txt", r"^# Samples: (\d+)K?"),
    ("job2 cg samples", "job1/profile_cg/perf_children.txt", r"^# Samples: (\d+)K?"),
]:
    body = text(os.path.join(ROOT, p))
    m = re.search(pat, body or "", re.M)
    note(label, p, m is not None, m.group(1) if m else "line NOT FOUND",
         "PASS" if m else "FAIL")

# ---- 3. job1b: the driver results my report quotes (nodes, zero-count, refusals) ----
p = os.path.join(ROOT, "job1b/profD/drive/results.txt")
body = text(p)
for label, pat, want in [
    ("job1b positions driven", r"positions: (\d+)", "200"),
    ("job1b refusal lines", r"refusal lines: (\d+)", "0"),
    ("job1b zero-node searches", r"searches reporting 0 nodes: (\d+) of (\d+)", "0 200"),
    ("job1b total nodes", r"total nodes: (\d+)", "14077298"),
]:
    m = re.search(pat, body or "")
    got = None
    if m:
        got = " ".join(m.groups()) if len(m.groups()) > 1 else m.group(1)
    note(label, p, m is not None, got,
         "PASS" if (m and got == want) else "FAIL", "expected %s" % want)

# ---- 4. job2 ratio CI numbers ----
for label, p, want in [
    ("job2 pair ratio", "job2/pairs/ratio_ci.txt", "1.0059"),
    ("job2 control ratio", "job2/pairs_control/ratio_ci.txt", "1.0002"),
]:
    body = text(os.path.join(ROOT, p))
    m = re.search(r"ratio of mean nps \(patch/base\): ([0-9.]+)", body or "")
    note(label, p, m is not None, m.group(1) if m else "line NOT FOUND",
         "PASS" if (m and m.group(1) == want) else "FAIL", "expected %s" % want)

# ---- 5. job3 ratios ----
for label, p, want in [
    ("job3 full prefetch ratio", "job3/pairs/ratio_ci.txt", "0.9190"),
    ("job3 lite ratio", "job3/pairs_lite/ratio_ci.txt", "1.0021"),
    ("job3 control ratio", "job3/pairs_control/ratio_ci.txt", "0.9889"),
]:
    body = text(os.path.join(ROOT, p))
    m = re.search(r"ratio of mean nps \(patch/base\): ([0-9.]+)", body or "")
    note(label, p, m is not None, m.group(1) if m else "line NOT FOUND",
         "PASS" if (m and m.group(1) == want) else "FAIL", "expected %s" % want)

# ---- 6. the check verdicts: the VERDICT line must exist and say what I claim ----
for label, p, want in [
    ("21-F1 verdict", "check21F1/raw/RESULT.txt", "CONFIRMS 21-F1"),
    ("28-C2 verdict", "check28C2/raw/RESULT.txt", "VERDICT CONFIRMS"),
    ("29-F3 verdict", "check29F3/raw/RESULT.txt", "CONFIRMS 29-F3"),
    ("08-F9 verdict (multi)", "check08F9/raw3/RESULT.txt", "CONFIRMS 08-F9"),
]:
    body = text(os.path.join(ROOT, p))
    ok = bool(body) and want in body
    note(label, p, bool(body), want, "PASS" if ok else "FAIL")

# ---- 7. the 19-F12 numbers (quit_abort + plant_control) ----
p = os.path.join(ROOT, "job1b/quitabort/RESULT.txt")
body = text(p)
for label, pat, want in [
    ("19-F12 aborted case nodes", r"A_quit_immediately \| 0 \| `bestmove a2a3` \| (\d+)", "0"),
    ("19-F12 searched case nodes", r"B_quit_after_2s \| 12 \| `bestmove e2e4` \| (\d+)", "56720"),
]:
    m = re.search(pat, body or "")
    note(label, p, m is not None, m.group(1) if m else "line NOT FOUND",
         "PASS" if (m and m.group(1) == want) else "FAIL", "expected %s" % want)
p = os.path.join(ROOT, "job1b/plant/RESULT.txt")
body = text(p)
m = re.search(r"the harness distinguishes the two: (\w+)", body or "")
note("19-F12 plant/control", p, m is not None, m.group(1) if m else "line NOT FOUND",
     "PASS" if (m and m.group(1) == "YES") else "FAIL")

# ---- 8. 19-F14 / 19-F13 ----
p = os.path.join(ROOT, "job1b/isready_mid/RESULT.txt")
body = text(p)
m = re.search(r"cases where the search produced nothing: *(.*)$", body or "", re.M)
note("19-F14 all four cases searched", p, m is not None,
     (("(empty)" if m.group(1).strip() == "" else m.group(1).strip()) if m else "line NOT FOUND"),
     "PASS" if (m and m.group(1).strip() == "") else "FAIL", "expected an empty list")
p = os.path.join(ROOT, "job1b/summary2.txt")
body = text(p)
m = re.search(r"MovePicker::pick_best\(\)` \| ([0-9.]+) %", body or "")
note("19-F13 pick_best share", p, m is not None, m.group(1) if m else "line NOT FOUND",
     "PASS" if (m and m.group(1) == "7.93") else "FAIL", "expected 7.93")

out = os.path.join(ROOT, "vacuity_audit")
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "RESULT.txt"), "w") as fh:
    fh.write("# vacuity audit: was the line each number came from actually FOUND?\n\n")
    fh.write("| number | source file | line found | value parsed | verdict | note |\n")
    fh.write("|---|---|---|---|---|---|\n")
    for name, src, found, val, verdict, why in rows:
        fh.write("| %s | `%s` | %s | %s | **%s** | %s |\n"
                 % (name, os.path.relpath(src, ROOT), "yes" if found else "NO", val, verdict, why))
    bad = [r for r in rows if r[4] != "PASS"]
    fh.write("\n%d numbers audited, %d failed.\n" % (len(rows), len(bad)))
    if bad:
        fh.write("\n## failures\n")
        for r in bad:
            fh.write("- %s: line found=%s, parsed=%r, verdict %s (%s)\n" % (r[0], r[2], r[3], r[4], r[5]))
print(open(os.path.join(out, "RESULT.txt")).read())
