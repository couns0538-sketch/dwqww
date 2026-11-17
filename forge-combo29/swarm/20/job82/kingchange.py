import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','AUDIT'))
from hardened import Engine, exe_identity
EXE='/agent/repos/build-v3diag/forge'
NET=os.path.abspath(os.path.join(os.path.dirname(__file__),'testnet.fnn3'))
S14=[("Threads",1),("Hash",16),("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
 ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),
 ("HistoryBonusLinear",54),("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
ident=exe_identity(EXE); print("EXE", ident['sha256'])
e=Engine(EXE,[("NNUEArchFile",NET),("NNUEArch","true")]+PC20)
try:
    e.isready(); k=e.mark(); e.send("bench 13"); e.expect("info string bench",300)
    bl=[l for l in e.since(k) if l.startswith("info string bench")][-1]
    nodes=int(re.search(r"nodes (\d+)",bl).group(1))
    e.isready(); k2=e.mark(); e.send("quit"); got,_=e.expect("info string diag",30)
    d=[l for l in got if "diag" in l][-1]; print(d)
    g=lambda n:int(re.search(n+r" (\d+)",d).group(1))
    rc, kc, inc, undo, cols = g("refresh_calls"), g("kingchange"), g("incremental"), g("undo_plies"), g("refresh_columns")
    tot=kc+inc
    out={"nodes":nodes,"bench":bl,"refresh_calls":rc,"kingchange_refreshes":kc,"incremental_applies":inc,
         "undo_plies_total":undo,"refresh_columns":cols,
         "kingchange_share_of_perspective_updates_pct":round(100.0*kc/tot,2),
         "columns_per_refresh":round(cols/rc,3),
         "undo_plies_per_kingchange":round(undo/kc,2)}
    print(json.dumps(out,indent=1))
    json.dump(out,open("job82/kingchange.json","w"),indent=1)
finally:
    pass
