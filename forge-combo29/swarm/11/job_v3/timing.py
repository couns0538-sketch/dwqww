#!/usr/bin/env python3
"""timing.py — FABLE_TO_swarm_7 Step 3: alternating runs of bench 13, ratio of medians + bootstrap CI.

    *** A 95% CI THAT EXCLUDES 1.0 PROVES AN EFFECT EXISTS. IT DOES NOT PROVE THE PATCH IS FASTER.
        CHECK WHICH SIDE OF 1.0 THE INTERVAL IS ON. ***

    A ratio of 0.9954 with CI [0.9913, 0.9989] excludes 1.0 and means the patch is reliably
    SLOWER by 0.1-0.9 %. Read the verdict line, not just the interval: this script prints
    "PATCH IS FASTER" only when the LOWER bound is above 1.0, and "PATCH IS SLOWER" when the
    UPPER bound is below 1.0. Anything else is "NOT PROVEN".

Two builds per side (file 7: one source spreads 4.2% between two builds)."""
import subprocess, sys, statistics, random, re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from pc20 import PC20
BASE=["/tmp/v3build/forge","/tmp/v3b2/forge"]
PATCH=["/tmp/v3p3b/forge","/tmp/v3p3c/forge"]
NET="/tmp/v3test.fnn3"
RUNS=int(sys.argv[1]) if len(sys.argv)>1 else 20
def nps(exe):
    opts=PC20+[f"NNUEArchFile {NET}","NNUEArch true"]
    inp="uci\n"+"".join(f"setoption name {o.partition(' ')[0]} value {o.partition(' ')[2]}\n" for o in opts)+"bench 13\nquit\n"
    out=subprocess.run([exe],input=inp,capture_output=True,text=True,timeout=300).stdout
    m=re.search(r"nps (\d+)",out)
    return int(m.group(1)) if m else None
b=[];p=[]
print(f"{RUNS} alternating runs of bench 13 under PC20 + test net, two builds per side\n")
for i in range(RUNS):
    eb=BASE[i%2]; ep=PATCH[i%2]
    nb=nps(eb); np_=nps(ep)
    if nb: b.append(nb)
    if np_: p.append(np_)
    if (i+1)%5==0: print(f"  after {i+1} rounds: base mean {statistics.mean(b):.0f}, patch mean {statistics.mean(p):.0f}")
mb,mp=statistics.median(b),statistics.median(p)
ratio=mp/mb
print(f"\n  base  nps: median {mb:.0f} (n={len(b)}), min {min(b)}, max {max(b)}")
print(f"  patch nps: median {mp:.0f} (n={len(p)}), min {min(p)}, max {max(p)}")
print(f"  RATIO of medians: {ratio:.4f}  ({(ratio-1)*100:+.2f}%)")
print(f"  two-build spread base: {abs(max(b)-min(b))/mb*100:.2f}%, patch: {abs(max(p)-min(p))/mp*100:.2f}%")
# bootstrap on the ratio
rng=random.Random(1101); rs=[]
for _ in range(4000):
    bs=[rng.choice(b) for _ in b]; ps=[rng.choice(p) for _ in p]
    rs.append(statistics.median(ps)/statistics.median(bs))
rs.sort()
print(f"  bootstrap 95% CI of the ratio: [{rs[int(0.025*len(rs))]:.4f}, {rs[int(0.975*len(rs))]:.4f}]")
lo, hi = rs[int(0.025*len(rs))], rs[int(0.975*len(rs))]
if lo > 1.0:
    verdict = f"PATCH IS FASTER (CI lower bound {lo:.4f} > 1.0)"
elif hi < 1.0:
    verdict = f"*** PATCH IS SLOWER *** (CI upper bound {hi:.4f} < 1.0) -- DO NOT SHIP"
else:
    verdict = f"NOT PROVEN (CI [{lo:.4f}, {hi:.4f}] contains 1.0)"
print(f"  => {verdict}")
