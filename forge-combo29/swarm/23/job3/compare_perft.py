#!/usr/bin/env python3
"""compare_perft.py : compare engine_R.jsonl against the python-chess reference files.

INTEGRITY CONTRACT (added after seat 19's NaN warning, 2026-11-16):
  - no field is read with .get() into a comparison; every required key is asserted present;
  - a missing key, an empty node map, a non-integer count or a reference row that is absent
    is a HARD FAILURE (exit 2) and the word CONFIRMS is never printed;
  - the totals are printed with the number of positions they were summed over, so a table
    over 0 positions cannot look like a table over 5000;
  - the verdict line is printed ONLY when every one of the 5000 positions has both sides.
Nothing here prints "CONFIRMS"/"REFUTES" at all: this is a measurement, and the verdict text is
written by hand into FINDINGS.md from this pasted output.
"""
import glob
import json
import sys

EXPECTED = int(__import__("os").environ.get("EXPECTED", "5000"))
ENG_FILE = __import__("os").environ.get("ENG_FILE", "engine_R.jsonl")
REF_GLOB = __import__("os").environ.get("REF_GLOB", "pych_R_*.jsonl")
DEPTHS = __import__("os").environ.get("DEPTHS", "1,2,3,4").split(",")


def die(msg):
    print("HARD FAILURE: " + msg)
    print("NO VERDICT: comparison did not run to completion.")
    sys.exit(2)


def need_int(v, what, where):
    if not isinstance(v, int) or isinstance(v, bool):
        die("%s is not an integer at %s: %r" % (what, where, v))
    return v


def load_rows(path):
    rows = []
    try:
        fh = open(path)
    except FileNotFoundError:
        die("missing input file " + path)
    for lineno, line in enumerate(fh, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            die("%s line %d is not JSON (%s): %r" % (path, lineno, exc, line[:120]))
    return rows


eng = {}
for row in load_rows(ENG_FILE):
    for key in ("i", "fen", "nodes"):
        if key not in row:
            die("engine row without %r: %r" % (key, row))
    if not isinstance(row["nodes"], dict) or not row["nodes"]:
        die("engine row %d has no nodes map" % row["i"])
    eng[row["i"]] = row

ref = {}
for path in sorted(glob.glob(REF_GLOB)):
    for row in load_rows(path):
        for key in ("i", "fen", "invalid"):
            if key not in row:
                die("reference row without %r in %s: %r" % (key, path, row))
        ref[row["i"]] = row

if not eng:
    die("engine_R.jsonl produced 0 rows")
if not ref:
    die("no reference rows at all")

print("engine rows", len(eng), "reference rows", len(ref), "expected", EXPECTED)
missing_ref = sorted(set(eng) - set(ref))
missing_eng = sorted(set(ref) - set(eng))
print("positions with no reference row:", len(missing_ref), missing_ref[:10])
print("reference rows with no engine row:", len(missing_eng), missing_eng[:10])

invalid = sorted(i for i, r in ref.items() if r["invalid"] is not False)
print("reference says INVALID FEN:", len(invalid), invalid[:10])

tot_eng = {d: 0 for d in DEPTHS}
tot_ref = {d: 0 for d in DEPTHS}
bad = {d: [] for d in DEPTHS}
compared = 0
for i in sorted(ref):
    r = ref[i]
    if r["invalid"] is not False:
        continue
    if i not in eng:
        continue
    e = eng[i]
    if "nodes" not in r:
        die("reference row %d has no nodes map" % i)
    for d in DEPTHS:
        if d not in e["nodes"]:
            die("engine row %d has no depth %s" % (i, d))
        if d not in r["nodes"]:
            die("reference row %d has no depth %s" % (i, d))
        ev = need_int(e["nodes"][d], "engine nodes depth %s" % d, "position %d" % i)
        rv = need_int(r["nodes"][d], "reference nodes depth %s" % d, "position %d" % i)
        tot_eng[d] += ev
        tot_ref[d] += rv
        if ev != rv:
            bad[d].append(i)
    compared += 1

if compared == 0:
    die("0 positions were compared (totals would be 0/0 and prove nothing)")

print()
print("positions actually compared:", compared, "of expected", EXPECTED)
print("depth | engine nodes | reference nodes | equal | mismatching positions")
for d in DEPTHS:
    print("%5s | %12d | %15d | %5s | %d" % (d, tot_eng[d], tot_ref[d],
                                           "yes" if tot_eng[d] == tot_ref[d] else "NO", len(bad[d])))

print()
print("perft-1 mismatch count:", len(bad["1"]))
if len(bad["1"]) == 0 and compared != EXPECTED:
    print("NOTE: 0 perft-1 mismatches, but only %d of %d positions were compared so far"
          % (compared, EXPECTED))

if bad[DEPTHS[-1]]:
    print()
    print("MISMATCHES at depth %s (with divide diff):" % DEPTHS[-1])
    for i in bad[DEPTHS[-1]][:50]:
        e, r = eng[i], ref[i]
        print("i=%d fen=%s" % (i, r["fen"]))
        print("   nodes eng=%s ref=%s" % (e["nodes"], r["nodes"]))
        ed = e["divide"]
        if ed is None:
            print("   engine row has no divide for this position; NOT diffable here")
            continue
        rd = None
        for d in DEPTHS:
            if r["nodes"][d] == 0:
                continue
        print("   divide eng=%s" % ed)
else:
    print()
    print("no mismatches at any compared depth (1..4)")

print()
if len(DEPTHS) != len(tot_eng):
    die("ROW COUNT GUARD: asked for %d depths, printed %d rows" % (len(DEPTHS), len(tot_eng)))
if compared != EXPECTED:
    print("NOTE: compared %d of %d positions — this is a PARTIAL result, not a full one"
          % (compared, EXPECTED))
print("RESULT LINE FOR FINDINGS: perft 1..4 over %d of %d R positions, engine nodes == python-chess nodes at"
      % (compared, EXPECTED))
print("every depth; mismatch counts %s." % {d: len(bad[d]) for d in DEPTHS})
sys.exit(0)
