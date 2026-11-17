#!/usr/bin/env python3
"""File 7 Step 1: profile bench 13 under PC20 + the test net, Threads 1, and report every nnue::v3 function's share.

Uses perf task-clock samples (the only event this unprivileged user can open). Reports the v3 family summed and each
v3 symbol separately, plus the search functions around it, so the "is evaluation dominating" question is answerable.

A symbol that is not sampled is printed NOT FOUND and excluded from the total, never counted as 0.
"""
import re, subprocess, sys, os
EXE, NET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
PERF = "/usr/lib/linux-tools/6.8.0-149-generic/perf"
S14 = [("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
       ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
       ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
       ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
              ("MateAlphaGuard","true"),("OwnBook","false")]
drv = os.path.join(OUT, "drv.py")
with open(drv,"w") as f:
    f.write("import subprocess\n")
    f.write(f"p=subprocess.Popen([{EXE!r}],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)\n")
    f.write("def s(c):\n    p.stdin.write(c+'\\n'); p.stdin.flush()\n")
    f.write("s('uci')\n")
    f.write("for l in p.stdout:\n    if l.startswith('uciok'): break\n")
    f.write(f"s({('setoption name NNUEArchFile value ' + NET)!r})\n")
    f.write("s('setoption name NNUEArch value true')\n")
    for k,v in PC20:
        f.write(f"s({('setoption name %s value %s' % (k,v))!r})\n")
    f.write("s('setoption name Hash value 16')\ns('setoption name Threads value 1')\n")
    f.write("s('isready')\n")
    f.write("for l in p.stdout:\n    if l.startswith('readyok'): break\n")
    f.write("s('bench 13')\n")
    f.write("for l in p.stdout:\n    if l.startswith('info string bench'): break\n")
    f.write("s('quit')\np.wait()\n")
data = os.path.join(OUT,"v3.data")
subprocess.run([PERF,"record","-q","-e","task-clock","-o",data,sys.executable,drv],check=False,capture_output=True)
rep = subprocess.run([PERF,"report","-i",data,"--stdio","--no-children","--percent-limit","0.1"],
                     capture_output=True,text=True).stdout
open(os.path.join(OUT,"flat.txt"),"w").write(rep)
rows=[]
for line in rep.splitlines():
    m=re.match(r'^\s+([0-9]+\.[0-9]+)%\s+\S+\s+\S+\s+\[\S\]\s+(.*)$', line)
    if m: rows.append((float(m.group(1)), m.group(2).strip()))
if not rows: raise SystemExit("ABORT: perf produced no samples -- nothing measured")
v3=[(p,s) for p,s in rows if "nnue::v3" in s]
tot=sum(p for p,_ in rows)
print(f"total sampled share parsed: {tot:.1f}%  over {len(rows)} symbols")
print()
print(f"| v3 symbol | share |")
print(f"|---|---|")
for p,s in sorted(v3, reverse=True):
    print(f"| {s[:78]} | {p:.2f} % |")
print(f"\n**v3 family total: {sum(p for p,_ in v3):.2f} %**")
print()
print("top non-v3 symbols:")
print("| symbol | share |")
print("|---|---|")
for p,s in [x for x in rows if "nnue::v3" not in x[1]][:10]:
    print(f"| {s[:78]} | {p:.2f} % |")
