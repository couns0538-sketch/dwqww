#!/usr/bin/env python3
"""job27 part C: the calib cell/term tables under S14, by a command over the committed rows."""
import json
D = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job27"
RUNS = [("O S14", "cO_calib_set_O.epd_d12.rows"), ("O +LmrNotImproving 0", "cOni_calib_set_O.epd_d12.rows"),
        ("O +LmrCutoffAdd 0", "cOca_calib_set_O.epd_d12.rows"), ("O +LmrTtPv 0", "cOtp_calib_set_O.epd_d12.rows"),
        ("G S14", "cG_calib_set_G.epd_d12.rows"), ("G +LmrNotImproving 0", "cGni_calib_set_G.epd_d12.rows"),
        ("G +LmrCutoffAdd 0", "cGca_calib_set_G.epd_d12.rows"), ("G +LmrTtPv 0", "cGtp_calib_set_G.epd_d12.rows")]
TERMS = ["t1 LmrTtPv", "t2 LmrNotImproving", "t3 LmrCutNode", "t4 LmrTtCapture", "t5 LmrGiveCheck",
         "t6 LmrInCheck", "t7 LmrCutoffAdd"]
out = {}
for tag, fn in RUNS:
    kinds = {k: {"n": 0, "fh": 0, "fh1": 0, "conf1": 0, "rn": 0, "re": 0, "an": 0} for k in range(3)}
    by_a_n = [0]*6; by_a_fh = [0]*6
    terms = {t: {0: {"n": 0, "fh": 0, "conf": 0}, 1: {"n": 0, "fh": 0, "conf": 0}} for t in range(7)}
    rows = 0; cells = 0; k2_passes = 0; fhge1 = 0
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
                    kinds[k]["n"] += n; kinds[k]["fh"] += fh
                    if a >= 1:
                        kinds[k]["fh1"] += fh; kinds[k]["conf1"] += conf
                    kinds[k]["rn"] += rn; kinds[k]["re"] += re; kinds[k]["an"] += a * n
                by_a_n[min(a, 5)] += n; by_a_fh[min(a, 5)] += fh
            if "LMRTERM" in seg:
                parts = seg.split()
                try:
                    t = int([x for x in parts if x.startswith("t")][0][1:]) - 1
                    a = int([x for x in parts if x.startswith("a")][0][1:])
                    f = int([x for x in parts if x.startswith("f")][0][1:])
                    n = int(parts[parts.index("n") + 1])
                    fh = int(parts[parts.index("fh") + 1])
                    conf = int(parts[parts.index("conf") + 1])
                except (ValueError, IndexError):
                    continue
                if t in terms and f in (0, 1):
                    terms[t][f]["n"] += n; terms[t][f]["fh"] += fh; terms[t][f]["conf"] += conf
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
    n_sum = sum(kinds[k]["n"] for k in range(3))
    fh1_sum = sum(kinds[k]["fh1"] for k in range(3))
    print(f"== {tag}: rows {rows}, LMRCELL lines {cells}")
    for kind, name in [(0, "kind 0 (tt_pv)"), (1, "kind 1 (cut node)"), (2, "kind 2 (neither)")]:
        d = kinds[kind]
        print(f"   {name}: passes {d['n']}  fh {d['fh']}  fh1+ {d['fh1']}  conf1+ {d['conf1']}  rn {d['rn']}  re {d['re']}  mean a {d['an']/d['n'] if d['n'] else 0:.3f}")
    print(f"   IDENTITY 1: the cells' n {n_sum} vs the LMRK2 passes {k2_passes} -> {'EQUAL' if n_sum == k2_passes else 'DIFFERENT'}")
    print(f"   IDENTITY 2: the fh1+ {fh1_sum} vs the fhge1 {fhge1} -> {'EQUAL' if fh1_sum == fhge1 else 'DIFFERENT'}")
    print(f"   by applied reduction: n {by_a_n}")
    print(f"   by applied reduction: fh {by_a_fh}")
    for t in range(7):
        f0, f1 = terms[t][0], terms[t][1]
        print(f"   {TERMS[t]}: not-fired n {f0['n']} fh/1000 {f0['fh']*1000/f0['n'] if f0['n'] else 0:.1f} conf% {f0['conf']*100/f0['fh'] if f0['fh'] else 0:.1f} | "
              f"fired n {f1['n']} fh/1000 {f1['fh']*1000/f1['n'] if f1['n'] else 0:.1f} conf% {f1['conf']*100/f1['fh'] if f1['fh'] else 0:.1f}")
    out[tag] = {"kinds": kinds, "by_a_n": by_a_n, "by_a_fh": by_a_fh, "terms": {t: terms[t] for t in terms}}
json.dump(out, open(f"{D}/partC_tables.json", "w"), indent=1)
