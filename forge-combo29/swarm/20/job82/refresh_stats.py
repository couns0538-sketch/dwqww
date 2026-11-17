import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AUDIT'))
from hardened import Engine, exe_identity
EXE = '/agent/repos/build-v3diag/forge'
NET = os.path.abspath(os.path.join(os.path.dirname(__file__), 'testnet.fnn3'))
S14 = [("Threads",1),("Hash",16),("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
    ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),
    ("HistoryBonusLinear",54),("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
ident = exe_identity(EXE)
print("EXE", ident['sha256'])
out = {}
for label, opts in [("no net (builtin)", []), ("PC20 + test net", PC20)]:
    pre = [("NNUEArchFile", NET), ("NNUEArch", "true")] if "net" in label and "no net" not in label else []
    e = Engine(EXE, pre + opts)
    try:
        e.isready(); k = e.mark(); e.send("bench 13"); e.expect("info string bench", 300)
        benchline = [l for l in e.since(k) if l.startswith("info string bench")][-1]
        nodes = int(re.search(r"nodes (\d+)", benchline).group(1))
        e.isready(); k2 = e.mark(); e.send("quit")
        got, _ = e.expect("info string diag", 30)
        diag = [l for l in got if "diag" in l]
        d = diag[-1] if diag else "(none)"
        m = re.search(r"refresh_calls (\d+) refresh_columns (\d+) columns_per_refresh (\S+)", d)
        rec = {"regime": label, "nodes": nodes, "bench": benchline}
        if m:
            calls, cols, cpr = int(m.group(1)), int(m.group(2)), m.group(3)
            rec.update({"refresh_calls": calls, "refresh_columns": cols, "columns_per_refresh": cpr,
                        "refresh_per_1k_nodes": round(1000.0*calls/nodes, 2)})
            print(f"{label:20s} nodes={nodes:9d} refresh_calls={calls:7d} cols={cols:9d} "
                  f"cols/refresh={cpr:>7s} refresh/1k nodes={rec['refresh_per_1k_nodes']}")
        else:
            rec["diag"] = d; print(label, "NO DIAG:", d)
        out[label] = rec
    finally:
        pass
json.dump(out, open("job82/refresh_stats.json","w"), indent=1)
