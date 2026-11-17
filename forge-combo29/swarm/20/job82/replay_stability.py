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
res={}
for n in (11,12,13):
    e=Engine(EXE,[("NNUEArchFile",NET),("NNUEArch","true")]+PC20)
    try:
        e.isready(); k=e.mark(); e.send(f"bench {n}"); e.expect("info string bench",300)
        bl=[l for l in e.since(k) if l.startswith("info string bench")][-1]
        nodes=int(re.search(r"nodes (\d+)",bl).group(1))
        e.isready(); k2=e.mark(); e.send("quit"); got,_=e.expect("info string diag",30)
        d=[l for l in got if "diag" in l][-1]
        g=lambda x:int(re.search(x+r" (\d+)",d).group(1))
        rc,rep,pf,cols=g("refresh_calls"),g("replays"),g("pairfail"),g("refresh_columns")
        row={"nodes":nodes,"refresh_calls":rc,"replays":rep,"pairfail":pf,"refresh_columns":cols,
             "pairfail_pct_of_replays":round(100.0*pf/rep,2),
             "cols_per_refresh":round(cols/rc,3),
             "refreshes_per_1000_nodes":round(1000.0*rc/nodes,2)}
        res[f"bench{n}"]=row
        print(f"bench {n}: nodes={nodes:8d} refreshes={rc:7d} ({row['refreshes_per_1000_nodes']:6.1f}/1k) "
              f"pairfail={pf:7d} = {row['pairfail_pct_of_replays']:5.2f}% of {rep} replays "
              f"cols/refresh={row['cols_per_refresh']}")
    finally:
        pass
json.dump(res,open("job82/replay_stability.json","w"),indent=1)
