#!/usr/bin/env python3
"""kimi5 job 20 Step 4 checker (the owed LmrFine run of file 20's Step 4).
T1 = S14 + LmrFine 1 + LmrFineHistory 1; C1 = S14 + LmrFine 1 + LmrFineHistory 0
+ LmrRoundF 0 + LmrTtPvF 1025. My rows: rows_lmr/{t1_O,t1_G,c1_O}_d12.json on the
LmrFine-alone PC build. References: job 11 rows (same .opt states, plain-build era
known answers) and job 17 a0 rows. The G mask = positions where job 17's a0_G
equaled job 11's I2 G rows (recomputed here; job 17 counted 341 of 353).
usage: check_s4.py
"""
import json

R = "rows_lmr"

def load(p):
    with open(p) as f:
        return json.load(f)

t1o, t1g, c1o = load(f"{R}/t1_O_d12.json"), load(f"{R}/t1_G_d12.json"), load(f"{R}/c1_O_d12.json")
r_t1o, r_t1g, r_c1o = load(f"{R}/t1_s14fh_O_d12.json"), load(f"{R}/t1_s14fh_G_d12.json"), load(f"{R}/c1_s14fine_tt1025_O_d12.json")
a0o, a0g = load(f"{R}/a0_O.json"), load(f"{R}/a0_G.json")
i2o, i2g = load(f"{R}/i2_s14_O_d12.json"), load(f"{R}/i2_s14_G_d12.json")

def eq_count(a, b, idx):
    n = sum(1 for i in idx if a["per_position"][i] == b["per_position"][i])
    m = sum(1 for i in idx if a["bestmove"][i] == b["bestmove"][i])
    return n, m

maskO = [i for i in range(200) if a0o["per_position"][i] == i2o["per_position"][i]]
maskG = [i for i in range(353) if a0g["per_position"][i] == i2g["per_position"][i]]
print(f"a0==I2 mask recomputed: O {len(maskO)}/200, G {len(maskG)}/353 (job 17 counted 200 and 341)")
diffG = [i + 1 for i in range(353) if i not in set(maskG)]
print(f"G positions outside the mask (1-indexed): {diffG}")

print()
n, m = eq_count(t1o, r_t1o, range(200))
print(f"T1 O vs job11 t1_s14fh_O: nodes equal {n}/200, best moves {m}/200; "
      f"sum {t1o['nodes_sum']} (known 10170054), first3 {t1o['nodes_first3']} (known [42893, 29118, 29414])")
n, m = eq_count(t1g, r_t1g, maskG)
nA, mA = eq_count(t1g, r_t1g, range(353))
print(f"T1 G vs job11 t1_s14fh_G on the 341 mask: nodes equal {n}/{len(maskG)}, best moves {m}/{len(maskG)} "
      f"(on all 353: nodes {nA}/353, bm {mA}/353); sum {t1g['nodes_sum']}, first3 {t1g['nodes_first3']}")
n, m = eq_count(c1o, r_c1o, range(200))
print(f"C1 O vs job11 c1_s14fine_tt1025_O: nodes equal {n}/200, best moves {m}/200; "
      f"sum {c1o['nodes_sum']} (known 13036988), first3 {c1o['nodes_first3']} (known [22466, 44041, 47235])")

print()
chO = sum(1 for i in range(200) if t1o["per_position"][i] != a0o["per_position"][i])
chG = sum(1 for i in maskG if t1g["per_position"][i] != a0g["per_position"][i])
chGA = sum(1 for i in range(353) if t1g["per_position"][i] != a0g["per_position"][i])
print(f"T1 changes node count vs a0: O {chO}/200, G {chG}/{len(maskG)} (all-353: {chGA}/353)")
chO = sum(1 for i in range(200) if c1o["per_position"][i] != a0o["per_position"][i])
print(f"C1 changes node count vs a0: O {chO}/200")
