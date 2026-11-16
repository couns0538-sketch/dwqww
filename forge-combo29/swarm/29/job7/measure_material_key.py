#!/usr/bin/env python3
"""CHECK of 19-F6, measured EMPIRICALLY instead of by line attribution.

19-F6 says the material key is re-derived 750,427 times per `bench 13` and is 2.71 % of total self time, and that
19-F9's patch caching it in Board was neutral (ratio 1.0059, CI [0.9680, 1.0454]).

Line attribution of an INLINED function is unreliable (my build attributes the whole
`(*material_correction_)[side][material_key(board) & mask] * w / 100` statement to one line, 0.153 %, and the
function symbol itself does not appear at all). So I measure the COST directly by toggling the feature off at
runtime: `setoption name MaterialCorrectionWeight value 0` disables exactly the material-correction lookup and
nothing else (src/search.cpp:1218 guards the read and :1237 the write with `if (tune::MaterialCorrectionWeight > 0)`).

If removing that lookup entirely does not change the node count, `bench 13` gives a direct bound on what the
material key costs per search: the difference between weight-100 and weight-0 runs is an UPPER bound on the whole
material-correction path, of which the key derivation is a part.

Node counts are asserted identical; a run whose count differs is reported and never silently averaged.
"""
import statistics, subprocess, sys

EXE = sys.argv[1]
ROUNDS = 10
EXPECT = 862329


def run(weight):
    cmd = ("uci\nsetoption name Hash value 16\nsetoption name Threads value 1\n"
           f"setoption name MaterialCorrectionWeight value {weight}\nisready\nbench 13\nquit\n")
    out = subprocess.run([EXE], input=cmd, capture_output=True, text=True).stdout
    ms = nodes = None
    for line in out.splitlines():
        if line.startswith("info string bench depth 13"):
            f = line.split()
            ms = int(f[f.index("time") + 1])
            nodes = int(f[f.index("nodes") + 1])
    if ms is None:
        raise SystemExit(f"ABORT: no bench line for weight {weight} -- nothing measured")
    return ms, nodes


rows = {100: [], 0: []}
for r in range(ROUNDS):
    order = (100, 0) if r % 2 == 0 else (0, 100)
    for w in order:
        ms, nodes = run(w)
        flag = "OK" if nodes == EXPECT else f"NODE COUNT CHANGED ({nodes})"
        rows[w].append((ms, nodes))
        print(f"round {r+1:2d} weight {w:3d}: {ms:4d} ms  nodes {nodes}  {flag}")

for w in (100, 0):
    ms = [x[0] for x in rows[w]]
    ns = {x[1] for x in rows[w]}
    print(f"\nweight {w:3d}: median {statistics.median(ms):.1f} ms  mean {statistics.mean(ms):.1f}  "
          f"node counts seen: {sorted(ns)}")
print()
same_nodes = {x[1] for w in (100, 0) for x in rows[w]} == {EXPECT}
print(f"node count identical across both settings: {same_nodes}")
if not same_nodes:
    print("=> the two settings search DIFFERENT trees, so a time difference cannot be attributed to the key alone.")
else:
    d = statistics.mean([x[0] for x in rows[100]]) - statistics.mean([x[0] for x in rows[0]])
    print(f"=> turning the whole material-correction path OFF changes bench 13 by {d:+.1f} ms "
          f"({100*d/statistics.mean([x[0] for x in rows[100]]):+.2f} %), and the node count does not move.")
    print("   That difference is an UPPER BOUND on what the material key can cost, since it removes the lookup,")
    print("   the multiply and the correction term together, not only the key derivation.")
