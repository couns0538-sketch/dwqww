#!/usr/bin/env python3
"""l50_driver.py -- for each scaled S14 setting, find the smallest change from the S14 value that
moves the O tree (depth 12) by at least 2 percent in either direction. Starts at the tuner's step
(file 8), then halves (if the step already crosses) or doubles (if not), at most 6 runs a setting.
The c-level ratios already measured in long 27/28 are reused, not re-run."""
import json
import subprocess
import sys

L1 = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long1"
J = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long50"
EXE = "/tmp/glmflash5_base/build/forge"
S14 = open(L1 + "/s14.txt").read().strip()
O = L1 + "/first200.fens"
BASE = 9500069

# (setting, s14 value, tuner c, min, max) -- min/max from the uci list
SET = [("LmrQuietBase", 93, 8, 0, 1000), ("LmrQuietDivisor", 205, 12, 1, 4000),
       ("LmrNoisyBase", 13, 6, 0, 1000), ("LmrNoisyDivisor", 333, 20, 1, 4000),
       ("LmrHistoryDivisor", 5643, 500, 100, 30000), ("HistoryPruneMultiplier", 2220, 200, 0, 6000),
       ("HistoryBonusQuadratic", 24, 3, 0, 100), ("HistoryBonusLinear", 54, 6, 0, 200),
       ("HistoryBonusMax", 2212, 180, 0, 8000)]
# the c-level ratios already known from long 27 (O): {setting: {end: ratio}}
KNOWN = {
    "LmrQuietBase": {"m": 1.0612, "p": 0.9804}, "LmrQuietDivisor": {"m": 0.9511, "p": 1.1272},
    "LmrNoisyBase": {"m": 1.0134, "p": 1.0121}, "LmrNoisyDivisor": {"m": 1.0181, "p": 1.0020},
    "LmrHistoryDivisor": {"m": 1.0139, "p": 1.0260}, "HistoryPruneMultiplier": {"m": 1.0032, "p": 1.0084},
    "HistoryBonusQuadratic": {"m": 0.9851, "p": 1.0003}, "HistoryBonusLinear": {"m": 1.0184, "p": 1.0026},
    "HistoryBonusMax": {"m": 1.0023, "p": 1.0258}}

def run_vals(setting, val):
    out = f"{J}/runs/{setting}_{val}.rows"
    import os
    if os.path.exists(out):
        r = [l.strip().split("|") for l in open(out) if l.strip()]
        return sum(int(x[1]) for x in r)
    subprocess.run(["python3", L1 + "/rows.py", "--exe", EXE, "--set", O, "--out", out,
                    "--depth", "12", "--opts", f"{S14};{setting}={val}",
                    "--meta", out + ".meta"], capture_output=True, text=True)
    r = [l.strip().split("|") for l in open(out) if l.strip()]
    return sum(int(x[1]) for x in r)

def ratio(setting, val):
    return run_vals(setting, val) / BASE

results = []
for name, v, c, lo, hi in SET:
    km = KNOWN[name]["m"]; kp = KNOWN[name]["p"]
    if abs(km - 1) >= 0.02 or abs(kp - 1) >= 0.02:
        # the tuner step already crosses: halve while the half still crosses (int check)
        step = c
        runs = 0
        best = (abs(km - 1) >= 0.02 and km or (abs(kp - 1) >= 0.02 and kp))
        while runs < 4:
            half = step / 2
            vlo, vhi = round(v - half), round(v + half)
            if vlo < lo and vhi > hi:
                break
            r_lo = ratio(name, vlo) if vlo >= lo else None
            r_hi = ratio(name, vhi) if vhi <= hi else None
            runs += 1
            cross = any(r is not None and abs(r - 1) >= 0.02 for r in (r_lo, r_hi))
            if not cross:
                break
            step = half
            best = max((abs(r - 1), r) for r in (r_lo, r_hi) if r is not None)[1]
        results.append((name, c, step, best, runs))
        print(f"{name}: tuner c {c} -> 2% step {step} (ratio {best:.4f}; {runs} new level(s))")
        continue
    # the step is too small: double
    step = c
    runs = 0
    best = None
    while runs < 5:
        step *= 2
        vlo, vhi = v - step, v + step
        r_lo = ratio(name, vlo) if vlo >= lo else None
        r_hi = ratio(name, vhi) if vhi <= hi else None
        runs += 1
        cross = any(r is not None and abs(r - 1) >= 0.02 for r in (r_lo, r_hi))
        if cross:
            best = max((abs(r - 1), r) for r in (r_lo, r_hi) if r is not None)[1]
            break
    results.append((name, c, step if best else None, best, runs))
    print(f"{name}: tuner c {c} -> 2% step {step} (ratio {best if best else 'NOT FOUND within budget'}; {runs} new level(s))")
json.dump([{"setting": n, "tuner_c": c, "step_for_2pct": s, "ratio_at_step": r, "new_levels": k}
           for n, c, s, r, k in results], open(f"{J}/results.json", "w"), indent=1)
print("wrote results.json")
