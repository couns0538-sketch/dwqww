#!/usr/bin/env python3
"""job27 part A: the LMRCELL cell table of job 25's calib rows, by a command over the committed files.
Per kind (0 = tt_pv, 1 = cut node, 2 = neither - the patch's 'e.kind = tt_pv ? 0 : (cut_node ? 1 : 2)'):
passes (n), fail-highs (fh), fail-highs at applied reduction >= 1, confirmed at >= 1, rn, re, mean a.
Identities: the cells' n sum vs the LMRK2 'passes' sum; the fh at >= 1 vs the 'fhge1' sum."""
import json
import sys
D = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job25"
SETS = {
    ("O", "CutNode 0"): "LmrCutNode+0_calib_set_O.epd_d12.rows",
    ("O", "CutNode 1"): "LmrCutNode+1_calib_set_O.epd_d12.rows",
    ("O", "CutNode 2 (no option)"): "none_calib_set_O.epd_d12.rows",
    ("O", "CutNode 3"): "LmrCutNode+3_calib_set_O.epd_d12.rows",
    ("G", "CutNode 0"): "LmrCutNode+0_calib_set_G.epd_d12.rows",
    ("G", "CutNode 1"): "LmrCutNode+1_calib_set_G.epd_d12.rows",
    ("G", "CutNode 2 (no option)"): "none_calib_set_G.epd_d12.rows",
    ("G", "CutNode 3"): "LmrCutNode+3_calib_set_G.epd_d12.rows",
}
for (tag, setting), fn in SETS.items():
    kinds = {k: {"n": 0, "fh": 0, "fh1": 0, "conf1": 0, "rn": 0, "re": 0, "an": 0} for k in range(3)}
    rows = 0
    cells = 0
    k2_passes = 0
    fhge1 = 0
    for ln in open(f"{D}/{fn}"):
        parts0 = ln.strip().split("|", 3)
        if len(parts0) < 4 or not parts0[0].isdigit():
            continue
        rows += 1
        for seg in parts0[3].split(" || "):
            seg = seg.strip()
            if "LMRCELL" in seg:
                parts = seg.split()
                try:
                    a = int([x for x in parts if x.startswith("a")][0][1:])
                    k = int([x for x in parts if x.startswith("k")][0][1:])
                    n = int(parts[parts.index("n") + 1])
                    fh = int(parts[parts.index("fh") + 1])
                    conf = int(parts[parts.index("conf") + 1])
                    rn = int(parts[parts.index("rn") + 1])
                    re = int(parts[parts.index("re") + 1])
                except (ValueError, IndexError):
                    continue
                cells += 1
                if k in kinds:
                    kinds[k]["n"] += n
                    kinds[k]["fh"] += fh
                    if a >= 1:
                        kinds[k]["fh1"] += fh
                        kinds[k]["conf1"] += conf
                    kinds[k]["rn"] += rn
                    kinds[k]["re"] += re
                    kinds[k]["an"] += a * n
            if "LMRK2" in seg and "passes" in seg:
                parts = seg.split()
                try:
                    k2_passes += int(parts[parts.index("passes") + 1])
                except (ValueError, IndexError):
                    pass
            if "LMRK2" in seg and "fhge1" in seg:
                parts = seg.split()
                try:
                    fhge1 += int(parts[parts.index("fhge1") + 1])
                except (ValueError, IndexError):
                    pass
    print(f"== {tag} / {setting}: rows {rows}, LMRCELL lines {cells}")
    n_sum = 0
    fh1_sum = 0
    for kind, name in [(0, "kind 0 (tt_pv)"), (1, "kind 1 (cut node)"), (2, "kind 2 (neither)")]:
        d = kinds[kind]
        mean_a = d["an"] / d["n"] if d["n"] else 0
        n_sum += d["n"]
        fh1_sum += d["fh1"]
        print(f"   {name}: passes {d['n']}  fh {d['fh']}  fh at 1+ {d['fh1']}  conf at 1+ {d['conf1']}  "
              f"rn {d['rn']}  re {d['re']}  mean a {mean_a:.3f}")
    print(f"   IDENTITY 1: the cells' n sum {n_sum} vs the LMRK2 passes sum {k2_passes} -> "
          f"{'EQUAL' if n_sum == k2_passes else 'DIFFERENT'}")
    print(f"   IDENTITY 2: the fh at 1+ sum {fh1_sum} vs the LMRK2 fhge1 sum {fhge1} -> "
          f"{'EQUAL' if fh1_sum == fhge1 else 'DIFFERENT'}")
