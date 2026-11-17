import sys, os, re, json, statistics
sys.path.insert(0, os.path.join(os.getcwd(),'AUDIT'))
from hardened import Engine, exe_identity
EXE='/agent/repos/build-v3/forge'
NET=os.path.abspath('job82/testnet.fnn3')
S14=[("Threads",1),("Hash",16),("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
 ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),
 ("HistoryBonusLinear",54),("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
FEN='r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3'
GO='go nodes 2000000'
print("EXE", exe_identity(EXE)['sha256'])
print("pos", FEN, "|", GO, "| PC20, Threads 1, Hash 16, fresh process each run")
arms={"builtin":[], "v3net":[]}
for rep in range(10):
    for name in ("builtin","v3net"):
        pre=[("NNUEArchFile",NET),("NNUEArch","true")] if name=="v3net" else []
        e=Engine(EXE, pre+PC20)
        try:
            e.send("ucinewgame"); e.isready(); e.position(FEN)
            r=e.search(GO, 300.0)
            arms[name].append((r["nodes"], r["wall"]))
        finally:
            e.close()
for name,v in arms.items():
    ns=[x[0] for x in v]; ts=[x[1] for x in v]
    print(f"{name:8s} nodes={sorted(set(ns))} wall median={statistics.median(ts)*1000:.1f} ms  "
          f"min={min(ts)*1000:.1f} max={max(ts)*1000:.1f}")
b=statistics.median([x[1] for x in arms["builtin"]]); v=statistics.median([x[1] for x in arms["v3net"]])
print(f"\nv3/builtin wall ratio = {v/b:.4f}  ({(v/b-1)*100:+.1f}%)")
print(f"per-node: builtin {b/2e6*1e9:.1f} ns, v3 {v/2e6*1e9:.1f} ns")
json.dump({"exe":exe_identity(EXE),"fen":FEN,"go":GO,"arms":{k:[list(map(float,x)) for x in vs] for k,vs in arms.items()},
           "ratio":v/b},open('job82/net_cost.json','w'),indent=1)
