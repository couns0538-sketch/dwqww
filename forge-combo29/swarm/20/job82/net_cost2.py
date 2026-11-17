import sys, os, re, json, statistics
sys.path.insert(0, os.path.join(os.getcwd(),'AUDIT'))
from hardened import Engine, exe_identity
EXE='/agent/repos/build-v3/forge'
NET=os.path.abspath('job82/testnet.fnn3')
S14=[("Threads",1),("Hash",16),("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
 ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),
 ("HistoryBonusLinear",54),("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
print("EXE", exe_identity(EXE)['sha256'])
# bench 13: fixed depth sequence -> fixed WORK, node count determined by the eval. Compare ns/node.
res={}
for name in ("builtin","v3net"):
    runs=[]
    for rep in range(8):
        pre=[("NNUEArchFile",NET),("NNUEArch","true")] if name=="v3net" else []
        e=Engine(EXE, pre+PC20)
        try:
            e.isready(); k=e.mark(); e.send("bench 13"); e.expect("info string bench",400)
            line=[l for l in e.since(k) if l.startswith("info string bench")][-1]
            n=int(re.search(r"nodes (\d+)",line).group(1)); t=int(re.search(r"time (\d+)",line).group(1))
            runs.append((n,t))
        finally:
            e.close()
    ns=sorted(set(x[0] for x in runs)); ts=[x[1] for x in runs]
    med=statistics.median(ts)
    n=ns[0]
    res[name]={"node_counts":ns,"times_ms":ts,"median_ms":med,"ns_per_node":round(med*1e6/n,2)}
    print(f"{name:8s} nodes={ns} time median={med} ms (spread {min(ts)}-{max(ts)})  ns/node={med*1e6/n:.2f}")
r=res["v3net"]["ns_per_node"]/res["builtin"]["ns_per_node"]
print(f"\nPER-NODE ratio v3/builtin = {r:.4f} ({(r-1)*100:+.1f}%)  <-- normalised, so the 6x node gap is removed")
res["per_node_ratio"]=round(r,4); res["exe"]=exe_identity(EXE)
json.dump(res,open('job82/net_cost2.json','w'),indent=1)
