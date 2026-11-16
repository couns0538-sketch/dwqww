#!/usr/bin/env bash
# planted_mismatch.sh : THE CONTROL for every perft zero in this seat (FABLE_TO_swarm_2, Rule 1).
# Rule: a result "0 differences" counts only when the SAME harness, unchanged, counted one planted case.
# So: take the real reference rows, change ONE node count by one node, and require compare_perft.py to
# report that position as a mismatch and to exit with the mismatch table. If the plant is not caught, every
# "0 mismatches" in jobs 1, 2, 3 and 4 is "not shown".
set -u
J=/agent/repos/dwqww/forge-combo29/swarm/23/job4
T=$(mktemp -d); cd "$T" || exit 1

echo "== build a 200-position subset of the REAL reference rows"
python3 - "$J" "$T" <<'PY'
import json, sys, glob, os
J, T = sys.argv[1], sys.argv[2]
rows = []
for path in sorted(glob.glob(os.path.join(J, "..", "job1", "pych_R_*.jsonl"))):
    for line in open(path):
        rows.append(json.loads(line))
rows.sort(key=lambda r: r["i"])
rows = rows[:200]
open(os.path.join(T, "pych_PLANT_0.jsonl"), "w").write("".join(json.dumps(r) + "\n" for r in rows))
# engine side: the REAL PC20 rows, matching indices
eng = {}
for line in open(os.path.join(J, "engine_pc20.jsonl")):
    r = json.loads(line)
    eng[r["i"]] = r
sel = [eng[r["i"]] for r in rows]
open(os.path.join(T, "engine_R.jsonl"), "w").write("".join(json.dumps(r) + "\n" for r in sel))
print("real rows:", len(rows))
PY

echo
echo "== case A: the real data UNCHANGED (must show 0 mismatches)"
EXPECTED=200 DEPTHS=1,2,3,4 ENG_FILE=engine_R.jsonl REF_GLOB='pych_PLANT_*.jsonl' \
  python3 "$J/compare_perft.py" > A_clean.out 2>&1
echo "   exit=$?"; grep -E "^    4 |perft-1 mismatch" A_clean.out

echo
echo "== case B: ONE node count planted +1 at depth 4 (must be caught)"
python3 - <<'PY'
import json
rows = [json.loads(l) for l in open("pych_PLANT_0.jsonl")]
# pick a position with a non-zero depth-4 count and add exactly one node
for r in rows:
    if r["nodes"]["4"] > 0:
        r["nodes"]["4"] += 1
        print("planted +1 node at depth 4 on i=%d fen=%s" % (r["i"], r["fen"]))
        break
open("pych_PLANT_0.jsonl", "w").write("".join(json.dumps(r) + "\n" for r in rows))
PY
EXPECTED=200 DEPTHS=1,2,3,4 ENG_FILE=engine_R.jsonl REF_GLOB='pych_PLANT_*.jsonl' \
  python3 "$J/compare_perft.py" > B_planted.out 2>&1
echo "   exit=$?"
grep -E "^    4 |perft-1 mismatch" B_planted.out

echo
echo "== case C: a whole depth key deleted (must be a HARD FAILURE, not a silent skip)"
python3 - <<'PY'
import json
rows = [json.loads(l) for l in open("pych_PLANT_0.jsonl")]
for r in rows:
    r["nodes"]["4"] -= 1   # undo the previous plant
    break
del rows[0]["nodes"]["4"]
open("pych_PLANT_0.jsonl", "w").write("".join(json.dumps(r) + "\n" for r in rows))
PY
EXPECTED=200 DEPTHS=1,2,3,4 ENG_FILE=engine_R.jsonl REF_GLOB='pych_PLANT_*.jsonl' \
  python3 "$J/compare_perft.py" > C_missing.out 2>&1
echo "   exit=$?"; grep -E "HARD FAILURE|NO VERDICT" C_missing.out | head -2

cd /agent/repos/dwqww/forge-combo29/swarm/23/job4
cp "$T"/A_clean.out "$T"/B_planted.out "$T"/C_missing.out .
echo
echo "== verdict"
echo "A (clean)   : $(grep -c 'mismatching positions' A_clean.out) table lines, depth-4 mismatches=$(grep -E '^    4 ' A_clean.out | awk -F'|' '{print $5}')"
echo "B (planted) : depth-4 mismatches=$(grep -E '^    4 ' B_planted.out | awk -F'|' '{print $5}')  <-- must be >= 1"
echo "C (missing) : $(grep -c 'HARD FAILURE' C_missing.out) HARD FAILURE line(s)  <-- must be 1"
rm -rf "$T"
