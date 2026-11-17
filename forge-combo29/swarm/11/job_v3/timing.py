#!/usr/bin/env python3
"""timing.py — FABLE_TO_swarm_7 Step 3: alternating runs of bench 13, ratio of medians + bootstrap CI.
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
print(f"  => {'PATCH IS FASTER' if rs[int(0.025*len(rs))] > 1.0 else 'NOT PROVEN faster (CI includes 1.0)'}")
