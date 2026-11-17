import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AUDIT'))
from hardened import Engine
EXE = '/agent/repos/build-v3/forge'
NET = os.path.abspath(os.path.join(os.path.dirname(__file__), 'testnet.fnn3'))
S14 = [("Threads",1),("Hash",16),
    ("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
    ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),
    ("HistoryPruneMultiplier",2220),("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),
    ("HistoryBonusMax",2212),("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true")]
POS = [("startpos", "startpos"),
       ("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
       ("8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40", "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40")]
PUB = {"startpos": (968,968), "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": (1176,1176),
       "8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40": (31,31)}
e = Engine(EXE, [("NNUEArchFile", NET), ("NNUEArch", "true")] + PC20)
res = []
try:
    for name, pos in POS:
        e.isready(); k = e.mark(); e.send(f"position {pos}"); e.isready()
        e.send("eval")
        got, ok = e.expect("info string eval", 30.0)
        line = [l for l in got if l.startswith("info string eval")][-1]
        m = re.search(r"nnue (-?\d+) total (-?\d+)", line)
        got_pub = (int(m.group(1)), int(m.group(2)))
        print(f"{name[:44]:46s} nnue={got_pub[0]:5d} total={got_pub[1]:5d} published={PUB[name]} "
              f"{'MATCH' if got_pub==PUB[name] else 'DIFF'}")
        res.append({"pos": name, "nnue": got_pub[0], "total": got_pub[1], "published": list(PUB[name]),
                    "match": got_pub==PUB[name], "raw": line})
finally:
    e.close()
json.dump(res, open("job82/step0_eval.json","w"), indent=1)
print("\nload line:"); print([l for l in e.lines if "NNUE v3 loaded" in l or "NNUE v3 active" in l][:2])
