#!/usr/bin/env python3
"""step4_timing.py OUT — seat 08 Step 4: the output_sum AVX-512 horizontal-reduction patch.

Same protocol as Step 3 so the two results are comparable: two builds per side, alternating, 20 runs each,
ratio of pooled medians with a bootstrap interval, and the build-to-build spread reported beside the effect.

Arms:
  B1 = v3       (file-5 tree + v3, unpatched)
  B2 = v3base2  (same source, second build)
  P1 = v3p2     (patched: in-register reduction)
  P2 = v3p2b    (same source, second build)

Every build must report 4,151,906 nodes on bench 13 with the test net and no PC20 options; a different count
means the build is not the engine it claims and the run stops.

PREDICTION RECORDED BEFORE THE RUN (ANALYSIS_other_hot_functions.md): ~1.2 % if the scalar tail costs what it
looks like, and a REJECTION if the bench moves under 0.5 %, because that would mean the compiler was already
vectorising the sum loop.

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
          "P1": "/home/ubuntu/builds/v3p2/forge",
          "P2": "/home/ubuntu/builds/v3p2b/forge"}
RUNS = 20
EXPECT_NODES = 4151906   # bench 13, test net, Threads 1, Hash 16, no PC20 options


def bench(exe):
    script = "uci\nsetoption name NNUEArchFile value " + NET + "\nsetoption name NNUEArch value true\n"
    script += "setoption name Threads value 1\nsetoption name Hash value 16\nisready\nucinewgame\nisready\nbench 13\n"
    r = subprocess.run([exe], input=script + "quit\n", capture_output=True, text=True, timeout=300)
    nodes = ms = None
    for line in r.stdout.splitlines():
        if "info string bench" in line:
            t = line.split()
            try:
                n = int(t[t.index("nodes") + 1])
                m = int(t[t.index("time") + 1])
            except (IndexError, ValueError):
                continue
            if n == EXPECT_NODES:
                nodes, ms = n, m
    return nodes, ms


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Seat 08 Step 4 — output_sum in-register reduction, two builds per side, %d alternating runs each" % RUNS)
emit("")
emit("Order per round is B1 P1 B2 P2, so machine drift hits both sides equally.")
emit("")
emit("| round | B1 ms | P1 ms | B2 ms | P2 ms | nodes all equal? |")
emit("|---|---|---|---|---|---|")
data = {k: [] for k in BUILDS}
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
emit("## Build-to-build spread (the confound the brief warns about)")
emit("")
b_spread = med["B2"] / med["B1"]
p_spread = med["P2"] / med["P1"]
emit("| comparison | ratio | meaning |")
emit("|---|---|---|")
emit("| B2 / B1 (same source, two builds) | **%.4f** | %.2f %% apart |" % (b_spread, 100 * abs(1 - b_spread)))
emit("| P2 / P1 (same source, two builds) | **%.4f** | %.2f %% apart |" % (p_spread, 100 * abs(1 - p_spread)))

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

random.seed(804)
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
effect = 100 * abs(1 - med_patch / med_base)
spread = 100 * max(abs(1 - b_spread), abs(1 - p_spread))
emit("| question | answer |")
emit("|---|---|")
emit("| is the interval entirely below 1.0 (patch faster)? | **%s** |" % ("YES" if hi < 1.0 else "NO"))
emit("| is the effect larger than the build-to-build spread? | **%s** (effect %.2f %%, spread %.2f %%) |" %
     ("YES" if effect > spread else "NO", effect, spread))
emit("| does it clear the pre-registered 0.5 %% bar? | **%s** |" % ("YES" if effect >= 0.5 else "NO"))
emit("")
if hi < 1.0 and effect >= 0.5:
    emit("**Step 4 verdict: the patch is faster, the interval excludes 1.0, and it clears the 0.5 %% bar** —")
    emit("%.2f %% pooled over 40 runs per side across two builds each." % (100 * (med_base - med_patch) / med_base))
elif effect < 0.5:
    emit("**Step 4 verdict: REJECTED on the pre-registered bar** — the bench moved %+.2f %%, under the 0.5 %% bar."
         % (100 * (med_base - med_patch) / med_base))
    emit("")
    emit("The stated reason for the bar was that a sub-0.5 %% move would mean the compiler was already vectorising")
    emit("the sum loop. **That stated reason is wrong and I am correcting it rather than inheriting it:** the base")
    emit("build has no `vpaddd` in the sum tail (checked in the disassembly), so the compiler was not vectorising it.")
    emit("The tail is simply too small to see. See the cost-model section of the report.")
else:
    emit("**Step 4 verdict: the interval includes 1.0** — not recommendable from this machine.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
