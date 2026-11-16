#!/usr/bin/env python3
"""job1_mdtable.py -- emit the report's markdown table from part1/part2 tables."""
import sys
out = sys.argv[1]
cs = {}
for line in open(f"{out}/table.txt"):
    p = line.split()
    if len(p) == 3:
        cs[p[0]] = (int(p[1]) if False else p[1], p[2])
# c values from the job file
C = {"LmrQuietBase":8,"LmrQuietDivisor":12,"LmrNoisyBase":6,"LmrNoisyDivisor":20,
     "NullMoveBase":1,"NullMoveDepthDivisor":1,"NullMoveEvalDivisor":20,"RfpDepth":1,
     "RfpMargin":6,"RfpImproving":6,"RazorBase":20,"RazorMultiplier":25,"FutilityDepth":1,
     "FutilityBase":12,"FutilityMultiplier":10,"LmpBase":1,"HistoryPruneMultiplier":200,
     "SeeQuietMultiplier":3,"SeeNoisyMultiplier":12,"SingularDepth":1,"SingularMargin":1,
     "IirDepth":1,"ProbcutDepth":1,"ProbcutMargin":15,"QsFutilityMargin":14,"QsSeeMargin":6,
     "AspirationDelta":2,"HistoryBonusQuadratic":3,"HistoryBonusLinear":6,"HistoryBonusMax":180,
     "LmrHistoryDivisor":500,"LmrCutoffThreshold":1,"MaterialCorrectionWeight":10,
     "CaptureFutilityMultiplier":25,"CaptureFutilityDepth":1}
VAL = {"LmrQuietBase":93,"LmrQuietDivisor":205,"LmrNoisyBase":13,"LmrNoisyDivisor":333,
       "NullMoveBase":5,"NullMoveDepthDivisor":3,"NullMoveEvalDivisor":200,"RfpDepth":8,
       "RfpMargin":72,"RfpImproving":40,"RazorBase":150,"RazorMultiplier":350,"FutilityDepth":7,
       "FutilityBase":100,"FutilityMultiplier":110,"LmpBase":8,"HistoryPruneMultiplier":2220,
       "SeeQuietMultiplier":24,"SeeNoisyMultiplier":150,"SingularDepth":6,"SingularMargin":2,
       "IirDepth":2,"ProbcutDepth":5,"ProbcutMargin":180,"QsFutilityMargin":160,"QsSeeMargin":40,
       "AspirationDelta":18,"HistoryBonusQuadratic":24,"HistoryBonusLinear":54,"HistoryBonusMax":2212,
       "LmrHistoryDivisor":5643,"LmrCutoffThreshold":3,"MaterialCorrectionWeight":100,
       "CaptureFutilityMultiplier":250,"CaptureFutilityDepth":6}
def load(pfx):
    d = {}
    for line in open(f"{out}/part{'1' if pfx=='p1' else '2'}_table.txt"):
        f = line.strip().split("|")
        if len(f) != 7 or f[0] == "setting":
            continue
        d[(f[0], f[2])] = (f[3], f[4], f[5])
    return d
o, g = load("p1"), load("p2")
order = list(C.keys())
print("| setting | value | c | O -c sum | O -c nodes-eq | O +c sum | O +c nodes-eq | G -c sum | G -c nodes-eq | G +c sum | G +c nodes-eq | bm-eq O -c/+c | bm-eq G -c/+c |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for n in order:
    v, c = VAL[n], C[n]
    om, op = o[(n, "m")], o[(n, "p")]
    gm, gp = g[(n, "m")], g[(n, "p")]
    print(f"| {n} | {v} | {c} | {om[0]} | {om[1]}/200 | {op[0]} | {op[1]}/200 | {gm[0]} | {gm[1]}/353 | {gp[0]} | {gp[1]}/353 | {om[2]}/{op[2]} | {gm[2]}/{gp[2]} |")
