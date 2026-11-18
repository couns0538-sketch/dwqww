import re, sys
# (name, pc_value, lo, hi) from the job-26 table; the 5 untuned have no range check, defaults only
tuned = [("DrawJitter",0,0,8),("LmrQuietBase",93,0,300),("LmrQuietDivisor",205,100,500),
("LmrNoisyBase",13,0,300),("LmrNoisyDivisor",333,100,800),("NullMoveMinDepth",3,1,10),
("NullMoveBase",5,1,6),("NullMoveDepthDivisor",3,1,10),("NullMoveEvalDivisor",200,50,1000),
("RfpDepth",8,0,15),("RfpMargin",72,10,300),("RfpImproving",40,0,200),("RazorDepth",2,0,6),
("RazorBase",150,0,1000),("RazorMultiplier",350,0,1000),("FutilityDepth",7,0,15),
("FutilityBase",100,0,500),("FutilityMultiplier",110,0,500),("LmpBase",8,0,20),
("HistoryPruneDepth",3,0,10),("HistoryPruneMultiplier",2220,0,20000),("SeeQuietMultiplier",24,0,200),
("SeeNoisyMultiplier",150,0,1000),("SingularDepth",6,2,20),("SingularMargin",2,0,10),
("IirDepth",2,1,20),("ProbcutDepth",5,1,20),("ProbcutMargin",180,0,1000),("QsFutilityMargin",160,0,1000),
("AspirationDelta",18,4,200),("HistoryBonusQuadratic",24,0,100),("HistoryBonusLinear",54,0,500),
("HistoryBonusMax",2212,100,10000),("LmrHistoryDivisor",5643,1000,30000),("CheckExtensionDepth",2,1,30),
("LmrCutoffThreshold",3,0,20),("MaterialCorrectionWeight",100,0,300),("CaptureFutilityBase",0,0,1000),
("FailLowContinuationBonus",0,0,300),("EvalSwingMult",0,0,64)]
untuned = [("QsSeeMargin",40),("CaptureFutilityMultiplier",250),("CaptureFutilityDepth",6),
("AspFailHighMaxReduce",3),("EvalSwingMax",200)]
text = open("step0/uci_list.txt").read()
found = {}
for m in re.finditer(r"option name (\S+) type spin default (-?\d+) min (-?\d+) max (-?\d+)", text):
    found[m.group(1)] = (int(m.group(2)), int(m.group(3)), int(m.group(4)))
diffs, missing = [], []
print(f"{'name':26s} {'table(def,lo,hi)':22s} {'exe(def,lo,hi)':22s} verdict")
for name, pcv, lo, hi in tuned:
    if name not in found: missing.append(name); print(f"{name:26s} MISSING from uci list"); continue
    d,l,h = found[name]
    ok = (l,h)==(lo,hi)
    if not ok: diffs.append(name)
    print(f"{name:26s} ({pcv},{lo},{hi}){'':5s} ({d},{l},{h}){'':5s} {'range OK' if ok else 'RANGE DIFFERS'}")
for name, pcv in untuned:
    if name not in found: missing.append(name); print(f"{name:26s} MISSING"); continue
    d,l,h = found[name]
    print(f"{name:26s} untuned pc={pcv} exe default={d} range=[{l},{h}] {'default==pc' if d==pcv else 'DEFAULT DIFFERS'}")
print(f"\n45 names covered: {len([n for n,_,_,_ in tuned])+len(untuned)}, found {len([1 for n,_,_,_ in tuned if n in found])+len([1 for n,_ in untuned if n in found])}, missing {missing}")
print(f"range diffs: {diffs}")
