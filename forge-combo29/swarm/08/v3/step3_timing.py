#!/usr/bin/env python3
"""step3_timing.py OUT — FABLE file 7 Step 3: two builds per side, alternating, 20 runs, ratio of medians
with a bootstrap interval, and the BUILD-TO-BUILD spread shown (19-F7: one source spreads 4.2 % between builds).

Arms:
  B1 = v3build  (file-5 tree, unpatched)
  B2 = v3base2  (file-5 tree, unpatched, second build)
  P1 = v3patch1 (patched)
  P2 = v3patch2 (patched, second build)

Every build must report the same node count (4,151,906 on bench 13 with PC20+net); a different count means the build
is not the engine it claims and the run stops.

ARGUMENT ORDER: OUT first.
"""
import random
import statistics
import subprocess
import sys

OUT = sys.argv[1]
NET = "/agent/repos/dwqww/forge-combo29/swarm/08/v3/test_v3.fnn3"
BUILDS = {"B1": "/home/ubuntu/builds/v3/forge",
          "B2": "/home/ubuntu/builds/v3base2/forge",
          "P1": "/home/ubuntu/builds/v3patch1/forge",
          "P2": "/home/ubuntu/builds/v3patch2/forge"}
RUNS = 20
EXPECT_NODES = 3652372   # PC20 + test net (4,151,906 is the net-ONLY row; the guard caught my mix-up)
OPT = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def bench(exe):
    script = "uci\nsetoption name NNUEArchFile value " + NET + "\nsetoption name NNUEArch value true\n"
    for k, v in OPT:
        script += "setoption name %s value %s\n" % (k, v)
    script += "setoption name Threads value 1\nsetoption name Hash value 16\nisready\nucinewgame\nisready\nbench 13\n"
    r = subprocess.run([exe], input=script + "quit\n", capture_output=True, text=True, timeout=300)
    nodes = ms = None
    for line in r.stdout.splitlines():
        if "info string bench" in line:
            t = line.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
                ms = int(t[t.index("time") + 1])
            except (IndexError, ValueError):
                pass
    return nodes, ms


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## FABLE file 7 Step 3 — two builds per side, %d alternating runs each" % RUNS)
emit("")
emit("Order per round is B1 P1 B2 P2, so machine drift hits both sides equally.")
emit("")
emit("| round | B1 ms | P1 ms | B2 ms | P2 ms | nodes all equal? |")
emit("|---|---|---|---|---|---|")
data = {k: [] for k in BUILDS}
nodes_ok = True
for r in range(1, RUNS + 1):
    row = {}
    for k in ("B1", "P1", "B2", "P2"):
        n, t = bench(BUILDS[k])
        if n != EXPECT_NODES:
            raise SystemExit("STOP: %s reported %r nodes, expected %d — this is not the engine it claims"
                             % (k, n, EXPECT_NODES))
        data[k].append(t)
        row[k] = t
    emit("| %d | %d | %d | %d | %d | yes |" % (r, row["B1"], row["P1"], row["B2"], row["P2"]))

med = {k: statistics.median(v) for k, v in data.items()}
emit("")
emit("## The four builds")
emit("")
emit("| build | median ms | min | max | runs |")
emit("|---|---|---|---|---|")
for k in ("B1", "B2", "P1", "P2"):
    emit("| %s | **%d** | %d | %d | %d |" % (k, med[k], min(data[k]), max(data[k]), len(data[k])))

emit("")
emit("## The build-to-build spread the brief warns about (19-F7: 4.2 %)")
emit("")
emit("| comparison | ratio | meaning |")
emit("|---|---|---|")
b_spread = med["B2"] / med["B1"]
p_spread = med["P2"] / med["P1"]
emit("| B2 / B1 (same source, two builds) | **%.4f** | %.1f %% apart |" % (b_spread, 100 * abs(1 - b_spread)))
emit("| P2 / P1 (same source, two builds) | **%.4f** | %.1f %% apart |" % (p_spread, 100 * abs(1 - p_spread)))

# pooled base and pooled patch medians
base_all = data["B1"] + data["B2"]
patch_all = data["P1"] + data["P2"]
med_base = statistics.median(base_all)
med_patch = statistics.median(patch_all)
emit("")
emit("## The effect, pooled over both builds per side")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| base median ms (40 runs) | %d |" % med_base)
emit("| patch median ms (40 runs) | %d |" % med_patch)
emit("| **ratio patch/base** | **%.4f** |" % (med_patch / med_base))
emit("| speed change | **%+.2f %%** |" % (100 * (med_base - med_patch) / med_base))

# bootstrap over the pooled runs
random.seed(801)
boots = []
for _ in range(4000):
    b = statistics.median([random.choice(base_all) for _ in base_all])
    p = statistics.median([random.choice(patch_all) for _ in patch_all])
    boots.append(p / b)
boots.sort()
lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]
emit("| bootstrap 95 %% interval of the ratio | **%.4f .. %.4f** |" % (lo, hi))
emit("| as a speed gain | %+.2f %% .. %+.2f %% |" % (100 * (1 - hi), 100 * (1 - lo)))
emit("")
emit("| question | answer |")
emit("|---|---|")
emit("| is the interval entirely below 1.0 (patch faster)? | **%s** |" % ("YES" if hi < 1.0 else "NO"))
emit("| is the effect larger than the build-to-build spread? | **%s** (effect %.2f %%, spread %.2f %%) |" %
     ("YES" if abs(1 - med_patch / med_base) > max(abs(1 - b_spread), abs(1 - p_spread)) else "NO",
      100 * abs(1 - med_patch / med_base), 100 * max(abs(1 - b_spread), abs(1 - p_spread))))
emit("")
if hi < 1.0:
    emit("**Step 3 verdict: the patch is faster, and the interval excludes 1.0** — %.2f %% pooled, over 40 runs per"
         % (100 * (med_base - med_patch) / med_base))
    emit("side across two builds each, with the build-to-build spread reported beside it.")
else:
    emit("**Step 3 verdict: the interval includes 1.0** — the effect does not survive the build-to-build spread on")
    emit("this machine, so the patch is not recommendable from here even though the paired test favoured it.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
