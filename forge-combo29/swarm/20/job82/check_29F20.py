import sys, os, re, json
sys.path.insert(0, os.path.join(os.getcwd(),'AUDIT'))
from hardened import Engine, exe_identity
EXE='/agent/repos/build-v3diag/forge'
NET=os.path.abspath('job82/testnet.fnn3')
S14=[("Threads",1),("Hash",16),("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
 ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),
 ("HistoryBonusLinear",54),("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
print("EXE", exe_identity(EXE)['sha256'])
ARMS=[
 ("A) NNUEArch OFF (built-in net, no v3)", []),
 ("B) NNUEArch TRUE, no net file (29-F20's arm)", [("NNUEArch","true")]),
 ("C) test net LOADED (the PC's state, untestable before)", [("NNUEArchFile",NET),("NNUEArch","true")]),
]
res={}
for label,pre in ARMS:
    e=Engine(EXE, pre+PC20)
    try:
        e.isready(); k=e.mark(); e.send("bench 13"); e.expect("info string bench",300)
        bl=[l for l in e.since(k) if l.startswith("info string bench")][-1]
        nodes=int(re.search(r"nodes (\d+)",bl).group(1))
        e.isready(); k2=e.mark(); e.send("quit"); got,_=e.expect("info string diag",30)
        d=[l for l in got if "diag" in l][-1]
        m=re.search(r"eval_runtime_calls (\d+)",d); rc=re.search(r"refresh_calls (\d+)",d)
        er=int(m.group(1)) if m else None
        v3ref=int(rc.group(1)) if rc else None
        res[label]={"nodes":nodes,"evaluate_runtime_calls":er,"v3_refresh_calls":v3ref,"bench":bl}
        print(f"{label:52s} nodes={nodes:8d} evaluate_runtime={er!s:>9s} v3_refresh={v3ref!s:>8s}")
    finally:
        pass
json.dump(res,open("job82/check_29F20.json","w"),indent=1)
