#!/usr/bin/env python3
"""kimi5 job 9 Part 4: ONE command that prints every table of the report.
Reads run_j9.py JSON rows from a directory. Checks K1/K2 identities, then prints
per setting and set: node sum, factor vs the S14 base, bootstrap 95% CI over
POSITIONS (10,000 resamples, seed 9), factor of each half of the set, and the
number of positions whose best move changes. Every table ends with an identity
line tying it to the totals. Prints how many rows files it read and positions.
Usage: agg_j9.py <rows_dir>
"""
import glob
import json
import random
import sys

D = sys.argv[1]
rows = {}
for p in sorted(glob.glob(f"{D}/*.json")):
    with open(p) as f:
        r = json.load(f)
    rows[r["tag"]] = r

EXPECTED = [
    ("k1_def_O", 12573318, [18407, 25756, 64000]),
    ("k1_def_G", 22128265, None),
    ("k1_s14_O", 9500069, [41311, 24872, 28574]),
    ("k1_s14_G", 18466239, None),
]
OPTS = ["NullStaticSlope", "NullStaticBase", "NullEvalRedMax", "NullVerifyDepth",
        "ProbcutImproving", "ProbcutReduction", "ProbcutTtSlack", "ProbcutStoreReduction"]
DEFAULTS = {"NullStaticSlope": 24, "NullStaticBase": 180, "NullEvalRedMax": 3,
            "NullVerifyDepth": 14, "ProbcutImproving": 50, "ProbcutReduction": 4,
            "ProbcutTtSlack": 3, "ProbcutStoreReduction": 3}
SETTINGS = [("NullStaticSlope", 0), ("NullStaticSlope", 48), ("NullStaticBase", 0),
            ("NullStaticBase", 400), ("NullEvalRedMax", 0), ("NullEvalRedMax", 6),
            ("NullVerifyDepth", 8), ("ProbcutImproving", 0), ("ProbcutImproving", 100),
            ("ProbcutReduction", 3), ("ProbcutReduction", 5), ("ProbcutTtSlack", 0),
            ("ProbcutStoreReduction", 0)]

print(f"rows files read: {len(rows)}")
for tag in sorted(rows):
    r = rows[tag]
    print(f"  {tag}: positions={r['n_positions']} nodes_sum={r['nodes_sum']}")

print("\n== K1 known sums (patched build, no option / S14) ==")
ok = True
for tag, want, first3 in EXPECTED:
    r = rows.get(tag)
    if r is None:
        print(f"  {tag}: MISSING"); ok = False; continue
    good = r["nodes_sum"] == want and (first3 is None or r["nodes_first3"] == first3)
    ok = ok and good
    print(f"  {tag}: sum={r['nodes_sum']} want={want} first3={r['nodes_first3']} want={first3} -> {'OK' if good else 'MISMATCH'}")
print(f"K1 sums: {'ALL OK' if ok else 'FAILED'}")
print(f"identity: the 4 sums above = the nodes_sum fields of the 4 rows files named.")

def cmp_per_position(a, b):
    """positions where nodes or bestmove differ"""
    dn = sum(1 for x, y in zip(a["per_position"], b["per_position"]) if x != y)
    db = sum(1 for x, y in zip(a["bestmove"], b["bestmove"]) if x != y)
    anydiff = sum(1 for x, y, u, v in zip(a["per_position"], b["per_position"], a["bestmove"], b["bestmove"]) if x != y or u != v)
    return dn, db, anydiff

print("\n== K1 identity: each option AT ITS DEFAULT vs the no-option run, per position ==")
tot_mismatch = 0
for pre, base in (("k1def", "k1_def"), ("k1s14", "k1_s14")):
    for N in OPTS:
        for s in ("O", "G"):
            tag, btag = f"{pre}_{s}_{N}", f"{base}_{s}"
            if tag not in rows or btag not in rows:
                print(f"  {tag}: MISSING"); tot_mismatch += 1; continue
            dn, db, _ = cmp_per_position(rows[tag], rows[btag])
            tot_mismatch += dn + db
            flag = "OK" if dn == 0 and db == 0 else f"DIFF nodes:{dn} bm:{db}"
            print(f"  {tag} vs {btag}: {flag}")
print(f"identity: 32 comparisons, mismatch total {tot_mismatch} -> K1 identity {'MET (200/200 and 353/353 everywhere)' if tot_mismatch == 0 else 'BROKEN'}")

print("\n== K2: NullVerifyDepth 15 and 64 on O at defaults (cannot act at depth 12) ==")
k2ok = True
for v in (15, 64):
    tag = f"k2_v{v}_O"
    dn, db, _ = cmp_per_position(rows[tag], rows["k1_def_O"])
    k2ok = k2ok and dn == 0 and db == 0
    print(f"  {tag} vs k1_def_O: nodes differ in {dn}, bestmoves in {db} -> {'OK' if dn == 0 and db == 0 else 'DIFFERS'}")
print(f"K2: {'MET on 200 of 200 both values' if k2ok else 'FAILED'}")
print("identity: the two comparisons above are the K2 rows files against the default base rows file.")

print("\n== base AGAIN under S14 (runner carries no state) ==")
for s in ("O", "G"):
    dn, db, _ = cmp_per_position(rows[f"r2_s14_{s}"], rows[f"k1_s14_{s}"])
    print(f"  r2_s14_{s} vs k1_s14_{s}: nodes differ in {dn}, bestmoves in {db}")
print("identity: base-again sums " +
      " ".join(f"{rows[f'r2_s14_{s}']['nodes_sum']} vs {rows[f'k1_s14_{s}']['nodes_sum']}" for s in ("O", "G")))

def bootstrap_ci(setting_nodes, base_nodes, resamples=10000, seed=9):
    rng = random.Random(seed)
    n = len(setting_nodes)
    ratios = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        sb = sum(base_nodes[i] for i in idx)
        ss = sum(setting_nodes[i] for i in idx)
        ratios.append(ss / sb)
    ratios.sort()
    return ratios[250], ratios[9750]

print("\n== Part 4 table: each setting alone under S14 vs the S14 base, depth 12 ==")
print(f"bootstrap: 10000 resamples over positions, seed 9")
grand = {}
for s in ("O", "G"):
    base = rows[f"k1_s14_{s}"]
    print(f"\n-- set {s} (base {base['nodes_sum']} nodes, {base['n_positions']} positions) --")
    print(f"{'setting':<28} {'sum':>10} {'factor':>7} {'95% CI':>17} {'half1':>7} {'half2':>7} {'bm chg':>7} {'any chg':>7}")
    for N, V in SETTINGS:
        r = rows.get(f"s_{N}_{V}_{s}")
        if r is None:
            print(f"  {N} {V}: MISSING"); continue
        f = r["nodes_sum"] / base["nodes_sum"]
        lo, hi = bootstrap_ci(r["per_position"], base["per_position"])
        h = base["n_positions"] // 2
        f1 = sum(r["per_position"][:h]) / sum(base["per_position"][:h])
        f2 = sum(r["per_position"][h:]) / sum(base["per_position"][h:])
        dn, db, anyd = cmp_per_position(r, base)
        grand[(N, V, s)] = (f, lo, hi, db, anyd)
        print(f"{N+'='+str(V):<28} {r['nodes_sum']:>10} {f:>7.4f} [{lo:.4f},{hi:.4f}] {f1:>7.4f} {f2:>7.4f} {db:>4}/{base['n_positions']} {anyd:>4}/{base['n_positions']}")
    tot_settings = sum(1 for N, V in SETTINGS if f"s_{N}_{V}_{s}" in rows)
    print(f"identity: {tot_settings} setting rows + base row read for set {s}; each sum = the nodes_sum field "
          f"of its rows file; factor = sum/base_sum = {base['nodes_sum']} as denominator throughout.")

print("\n== sentence material ==")
print("per-unit move on G (|factor-1| / |value-default|):")
for N, V in SETTINGS:
    if (N, V, "G") in grand:
        f = grand[(N, V, "G")][0]
        per_unit = abs(f - 1) / abs(V - DEFAULTS[N])
        print(f"  {N} {V}: factor {f:.4f}, per unit {per_unit:.6f}")
print("settings with bm changes > 10% of positions while |tree factor-1| < 0.05:")
for (N, V, s), (f, lo, hi, db, anyd) in sorted(grand.items()):
    n = 200 if s == "O" else 353
    if db / n > 0.10 and abs(f - 1) < 0.05:
        print(f"  {N}={V} on {s}: factor {f:.4f}, bm changed {db}/{n} ({100*db/n:.1f}%)")
print("NullVerifyDepth 8 vs base, searches changed at all (nodes or bestmove):")
for s in ("O", "G"):
    if ("NullVerifyDepth", 8, s) in grand:
        print(f"  on {s}: {grand[('NullVerifyDepth', 8, s)][4]} of {200 if s == 'O' else 353}")
