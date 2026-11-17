#!/usr/bin/env python3
"""kimi5 job 18 step 1: known answers (sums + first three, job file 18) and the
position-by-position identity against the job-17 rows that job 17 proved equal
to Opus's own port (nodes AND best move). Run from tests_kimi5_job18/.
"""
import json

def load(tag, d="rows"):
    with open(f"{d}/{tag}.json") as f: return json.load(f)

exp = {
    ("O", "arr0"): (8315168, [21812, 26844, 35173]),
    ("O", "arr1"): (5299861, [14068, 11388, 24787]),
    ("O", "arr2"): (3744289, [7097, 8942, 17837]),
    ("G", "arr0"): (17611204, [31779, 46086, 84457]),
    ("G", "arr1"): (12340273, [25279, 30081, 45847]),
    ("G", "arr2"): (9116305, [17682, 27721, 42553]),
}
print("Step 1 known answers (job file 18, written before this report):")
allok = True
for (s, a), (esum, ef3) in sorted(exp.items()):
    d = load(f"{s}_{a}_d12")
    ok = d["nodes_sum"] == esum and d["nodes_first3"] == ef3
    allok &= ok
    print(f"  {s} {a}: sum {d['nodes_sum']} vs {esum}, first3 {d['nodes_first3']} vs {ef3} -> {'OK' if ok else 'MISMATCH'}")
print(f"  all six: {'OK' if allok else 'MISMATCH'}")

print("\nPosition-by-position vs job 17 rows (proved equal to Opus's port there):")
pairs = [("O", "arr0", "p2_base_O", 200), ("O", "arr1", "p2_aq1_O", 200),
         ("G", "arr0", "p2_base_G", 353), ("G", "arr1", "p2_aq1_G", 353)]
for s, a, ref, n in pairs:
    mine, r = load(f"{s}_{a}_d12"), load(ref, "../tests_kimi5_job17/rows")
    eq = sum(1 for x, y, bm1, bm2 in zip(mine["per_position"], r["per_position"],
                                         mine["bestmove"], r["bestmove"]) if x == y and bm1 == bm2)
    diffs = [i for i, (x, y, bm1, bm2) in enumerate(zip(mine["per_position"], r["per_position"],
                                                        mine["bestmove"], r["bestmove"])) if x != y or bm1 != bm2]
    print(f"  {s} {a} vs {ref}: equal {eq}/{n} (sums {mine['nodes_sum']}/{r['nodes_sum']})"
          + (f" DIFF at {diffs[:10]}" if diffs else ""))
