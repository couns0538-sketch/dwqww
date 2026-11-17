import sys, os, re, json, time
sys.path.insert(0, os.path.join(os.getcwd(),'AUDIT'))
from hardened import Engine, exe_identity
EXE='/agent/repos/build-v3diag/forge'
NET=os.path.abspath('job82/testnet.fnn3')
S14=[("Threads",1),("Hash",16),("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
 ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),
 ("HistoryBonusLinear",54),("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
fens=[l.strip() for l in open('job24/G_353.fens') if l.strip()][:200]
print("EXE", exe_identity(EXE)['sha256'], "positions", len(fens))
tot={"nodes":0,"rc":0,"rep":0,"pf":0,"cols":0,"kc":0,"undo":0}
rows=[]
e=Engine(EXE,[("NNUEArchFile",NET),("NNUEArch","true")]+PC20)
try:
    for i,fen in enumerate(fens):
        e.send("ucinewgame"); e.isready()
        e.position(fen)
        r=e.search("go depth 12")
        e.isready()
        # read counters by asking; counters are process-wide so diff them
        k=e.mark(); e.send("isready"); e.expect("readyok",20)
        rows.append((i,fen,r.get("nodes"),r.get("bestmove"),r.get("score")))
    # one final counter dump via quit
    e.isready(); k=e.mark(); e.send("quit"); got,_=e.expect("info string diag",30)
    d=[l for l in got if "diag" in l][-1]; print(d)
    g=lambda n:int(re.search(n+r" (\d+)",d).group(1))
    rc,rep,pf,cols,kc,undo=g("refresh_calls"),g("replays"),g("pairfail"),g("refresh_columns"),g("kingchange"),g("undo_plies")
    nodes=sum(r[2] or 0 for r in rows)
    out={"positions":len(rows),"nodes":nodes,"refresh_calls":rc,"replays":rep,"pairfail":pf,
         "refresh_columns":cols,"kingchange":kc,"undo_plies":undo,
         "pairfail_pct_of_replays":round(100.0*pf/rep,2),
         "refreshes_per_1000_nodes":round(1000.0*rc/nodes,2),
         "cols_per_refresh":round(cols/rc,3)}
    print(json.dumps(out,indent=1)); json.dump(out,open("job82/openings_rate.json","w"),indent=1)
    json.dump(rows,open("job82/openings_rows.json","w"),indent=1)
finally:
    pass
