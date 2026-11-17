#!/usr/bin/env python3
"""kimi5 job 19 Step 1 checker: sums, first-three, and (for the control) row-by-row equality."""
import json, sys

KA = {
 "base":  {"O": (8315168,  [21812, 26844, 35173]), "G": (17611204, [31779, 46086, 84457])},
 "snc1":  {"O": (8346403,  [13000, 18714, 34252]), "G": (16793551, [32463, 34259, 69385])},
 "tem100":{"O": (8436458,  [21812, 26844, 41637]), "G": (19117129, [31779, 35829, 103522])},
 "both":  {"O": (8254805,  [13000, 18714, 34055]), "G": (18241549, [32463, 32453, 69937])},
}

def rows(tag):
    with open(f"rows/{tag}.json") as f:
        d = json.load(f)
    return d["per_position"], d["bestmove"]

ok = True
for cfg, sets in KA.items():
    for s, (ksum, kfirst) in sets.items():
        nodes, bm = rows(f"{cfg}_{s}_d12")
        first3 = nodes[:3]
        tot = sum(nodes)
        good = tot == ksum and first3 == kfirst
        ok &= good
        print(f"{cfg:8s} {s}: sum {tot} vs {ksum} {'OK' if tot==ksum else 'MISMATCH'}; "
              f"first3 {first3} vs {kfirst} {'OK' if first3==kfirst else 'MISMATCH'}; n={len(nodes)}")

# control: allsd20 vs sd20 on O, row by row (nodes AND bestmove)
a, abm = rows("allsd20_O_d12")
b, bbm = rows("sd20_O_d12")
same = sum(1 for i in range(len(a)) if a[i] == b[i] and abm[i] == bbm[i])
print(f"control O: allsd20 == sd20 on {same} of {len(a)} (nodes AND bestmove)")
ok &= same == len(a)

# changed-position counts vs base (file 20's rule: an ON state changing < half is no test)
for cfg in ("snc1", "tem100", "both"):
    for s in ("O", "G"):
        x, _ = rows(f"{cfg}_{s}_d12")
        y, _ = rows(f"base_{s}_d12")
        ch = sum(1 for p, q in zip(x, y) if p != q)
        print(f"changed vs base {cfg:8s} {s}: {ch} of {len(x)}")
print("ALL OK" if ok else "FAILURES PRESENT")
