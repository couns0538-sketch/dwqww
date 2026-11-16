#!/usr/bin/env python3
"""job26 part A: job 24's k-cell table, read with the indices in the order the code writes them
([step][MARGIN class][DEPTH class]), by a command over the committed job-24 rows.
Prints, per step and depth class, the five margin cells with n, FULL and FULL per 1,000 of the
cell's own n; under each step the identity line: the sums over the margin index against n by depth."""
import json
import sys
D = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job24"
STEPS = ["2 futility", "3 history", "4 quietSEE", "6 noisySEE"]
DL = ["d1", "d2", "d3", "d4-6", "d7+"]
KC = ["k1", "k1.5", "k2", "k3", "k5"]
sets = {"O-probe": "RegretTop+true_set_O.epd_d12.rows", "G-probe": "RegretTop+true_set_G.epd_d12.rows"}
if len(sys.argv) > 1:
    sets = {sys.argv[1]: sys.argv[2]}
out = {}
for tag, fn in sets.items():
    # the cells: kn[step][depth][margin] and kf likewise, per the code's index order
    kn = [[[0]*5 for _ in range(5)] for _ in range(4)]
    kf = [[[0]*5 for _ in range(5)] for _ in range(4)]
    nd = [[0]*5 for _ in range(4)]   # n by depth class
    full = [0]*5
    for ln in open(f"{D}/{fn}"):
        p = ln.strip().split("|")
        if len(p) < 4 or not p[0].isdigit():
            continue
        d = json.loads(p[3])
        for s in range(4):
            for dd in range(5):
                # the print's outer loop was the margin index in the code's order: kn[s][dd] here
                # is [s][margin][depth]; the file's layout is [step][margin][depth][?no - [step][depth]...]
                # DECIDED BY THE DATA: try both readings and print the identity for each.
                pass
        # read both interpretations
        for s in range(4):
            for dd in range(5):
                for kc in range(5):
                    # reading A (the code's order: [step][margin][depth])
                    kn[0][0][0] = kn[0][0][0]  # placeholder, real sums below
    # real sums: the file's k_n = [4][5][5]; interpretation A: [step][margin][depth]
    knA = [[[0]*5 for _ in range(5)] for _ in range(4)]
    kfA = [[[0]*5 for _ in range(5)] for _ in range(4)]
    knB = [[[0]*5 for _ in range(5)] for _ in range(4)]
    kfB = [[[0]*5 for _ in range(5)] for _ in range(4)]
    ndA = [[0]*5 for _ in range(4)]
    ndB = [[0]*5 for _ in range(4)]
    full = [0]*5
    for ln in open(f"{D}/{fn}"):
        p = ln.strip().split("|")
        if len(p) < 4 or not p[0].isdigit():
            continue
        d = json.loads(p[3])
        for s in range(4):
            for i in range(5):
                for j in range(5):
                    v = d["k_n"][s][i][j]
                    f = d["k_full"][s][i][j]
                    knA[s][i][j] += v; kfA[s][i][j] += f   # A: i = margin, j = depth
                    knB[s][j][i] += v; kfB[s][j][i] += f   # B: i = depth, j = margin
        for k in range(5):
            full[k] += d.get("full", [0]*5)[k]
    for tagI, knX, kfX, ndX in [("A(margin,depth)", knA, kfA, None), ("B(depth,margin)", knB, kfB, None)]:
        # the identity: the sums over the MARGIN index must equal n by depth class
        # n by depth class: from the interpretation where the depth index's sums match the known
        # n-by-depth (job 22's exact numbers for the count run; for the probe run use A's own)
        pass
    # decide by the known anchor: O probe, the margin-index sums by depth = 94,548 / 58,530 / 12,390 / 6,549 / 570 (Fable's)
    sumsA = [sum(sum(knA[s][dd][kc] for kc in range(5)) for s in range(4)) for dd in range(5)]
    sumsB = [sum(sum(knB[s][dd][kc] for kc in range(5)) for s in range(4)) for dd in range(5)]
    print(f"== {tag}: the depth-index sums over all steps — reading A {sumsA} vs reading B {sumsB}")
    known = [94548, 58530, 12390, 6549, 570]
    if tag == "O-probe":
        pick = "A(margin,depth)" if abs(sumsA[0] - known[0]) < abs(sumsB[0] - known[0]) else "B(depth,margin)"
        print(f"   the reading that matches the known n-by-depth {known}: {pick}")
    out[tag] = {"A": {"kn": knA, "kf": kfA}, "B": {"kn": knB, "kf": kfB}, "full": full}
json.dump(out, open("/agent/repos/dwqww/forge-combo29/tests_deepseek5_job26/partA_both_readings.json", "w"), indent=1)
# the final table with the picked reading, printed for both sets
for tag, fn in sets.items():
    knA = out[tag]["A"]["kn"]; kfA = out[tag]["A"]["kf"]
    n_by_depth = [[sum(knA[s][dd][kc] for kc in range(5)) for dd in range(5)] for s in range(4)]
    print(f"== {tag}: the table (FULL per 1,000 of the cell's own n; cells with n < 200 left out)")
    for s in range(4):
        for dd in range(5):
            n_dd = n_by_depth[s][dd]
            if n_dd < 200:
                continue
            cells = []
            for kc in range(5):
                n_c = knA[s][dd][kc]
                f_c = kfA[s][dd][kc]
                if n_c < 200:
                    cells.append(f"{KC[kc]}:-")
                else:
                    cells.append(f"{KC[kc]}:{f_c*1000/n_c:.1f}(n{n_c},F{f_c})")
            print(f"   {STEPS[s]} {DL[dd]}(n{n_dd}): " + " ".join(cells))
        ident = [sum(knA[s][dd][kc] for dd in range(5) for kc in range(5)) for s in range(4)]
        byd = [n_by_depth[s][dd] for dd in range(5)]
        print(f"   IDENTITY {STEPS[s]}: the sums over the margin index {sum(knA[s][dd][kc] for dd in range(5) for kc in range(5))} per step vs n per step by depth {byd} (the per-depth sums: {[sum(knA[s][dd][kc] for kc in range(5)) for dd in range(5)]})")
PYEOF