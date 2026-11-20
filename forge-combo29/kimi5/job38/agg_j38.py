#!/usr/bin/env python3
"""kimi5 job 38 Step 2: K1 (node sums), row equality (count vs plain), K2 (the 35 cells x 3 sets)
and the identities, from the s2 jsonl and prc.log files. Prints how many lines it read.
Usage: agg_j38.py <s2dir>
"""
import json
import os
import sys

D = sys.argv[1]

FIELDS = ["B", "T", "QP", "QPc", "Q", "Q1", "FE", "F", "Fc", "SR", "S", "Sc", "Spv",
          "NR", "NRc", "NRq", "NRp", "CF", "NS", "N", "Nc", "Nq", "Npv", "L", "Lc", "Lpv",
          "X", "WL", "WF", "HL", "HF", "HLc", "HFc", "HP", "HC", "W0"]

K1 = {"R": 4294263, "O": 8315168, "G": 17611204}

K2 = {
    "B":  (3668713, 6021602, 12617464), "T": (0, 0, 0),
    "QP": (2775719, 4872518, 9358852), "QPc": (56052, 103331, 471211),
    "Q":  (58893, 96907, 252660), "Q1": (53224, 84149, 228028),
    "FE": (2401588, 4019125, 7236370), "F": (11633, 11208, 43280), "Fc": (5521, 4336, 18556),
    "SR": (2705193, 4764403, 9062912), "S": (757864, 927429, 1952176),
    "Sc": (8013, 17555, 37882), "Spv": (260849, 141872, 295930),
    "NR": (892994, 1149084, 3258612), "NRc": (709419, 963916, 1607185),
    "NRq": (180201, 185084, 1512145), "NRp": (3374, 84, 139282),
    "CF": (0, 0, 0), "NS": (105268, 194763, 376414),
    "N":  (472754, 527247, 1392796), "Nc": (378267, 472767, 807129),
    "Nq": (94487, 54480, 585667), "Npv": (80132, 37232, 99407),
    "L":  (296281, 553415, 960105), "Lc": (1894, 5177, 16799), "Lpv": (61393, 52267, 82200),
    "X":  (398050, 685988, 1639230), "WL": (290972, 545710, 937915), "WF": (53213, 84146, 227933),
    "HL": (7366196, 14353354, 18448670), "HF": (1513969, 2448656, 5328298),
    "HLc": (16715, 11518, 308276), "HFc": (10363, 12941, 173396),
    "HP": (0, 0, 0), "HC": (0, 0, 0),
}

def read_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

def read_prc(path):
    sums = {k: 0 for k in FIELDS}
    n = 0
    with open(path) as f:
        for line in f:
            parts = line.split()
            vals = parts[parts.index("PRC") + 1:]
            assert len(vals) == 36, f"bad PRC line: {line}"
            for k, v in zip(FIELDS, vals):
                sums[k] += int(v)
            n += 1
    return sums, n

total_lines = 0
print("== row equality (count vs plain: depth, nodes, bestmove) ==")
for s, n in (("R", 1200), ("O", 200), ("G", 353)):
    a = read_rows(os.path.join(D, f"cnt_{s}.jsonl"))
    b = read_rows(os.path.join(D, f"pln_{s}.jsonl"))
    total_lines += len(a) + len(b)
    diff = sum(1 for x, y in zip(a, b) if (x["depth"], x["nodes"], x["bestmove"]) != (y["depth"], y["nodes"], y["bestmove"]))
    print(f"{s}: rows {len(a)} vs {len(b)}, differing {diff}")

print("== K1 node sums (count build) ==")
for s in ("R", "O", "G"):
    a = read_rows(os.path.join(D, f"cnt_{s}.jsonl"))
    total = sum(r["nodes"] for r in a)
    print(f"{s}: {total} vs K1 {K1[s]} {'OK' if total == K1[s] else 'DIFFER'}")

print("== K2 cells (sum of PRC lines) ==")
sums = {}
nprc = {}
for i, s in enumerate(("R", "O", "G")):
    sums[s], nprc[s] = read_prc(os.path.join(D, f"cnt_{s}.prc.log"))
    total_lines += nprc[s]
print(f"PRC lines read: R {nprc['R']}, O {nprc['O']}, G {nprc['G']}")
eq = 0
neq = 0
for k in K2:
    mine = (sums["R"][k], sums["O"][k], sums["G"][k])
    if mine == K2[k]:
        eq += 3
    else:
        neq += 1
        print(f"DIFFER {k}: mine {mine} vs known {K2[k]}")
print(f"cells equal: {eq} of {3 * len(K2)} ({len(K2) - neq} of {len(K2)} rows)")

print("== identities ==")
for s in ("R", "O", "G"):
    m = sums[s]
    print(f"{s}: B=T+QP+NR {m['B'] == m['T'] + m['QP'] + m['NR']} "
          f"SR=QP-Q-F {m['SR'] == m['QP'] - m['Q'] - m['F']} "
          f"NR=NRc+NRq+NRp {m['NR'] == m['NRc'] + m['NRq'] + m['NRp']} "
          f"N=Nc+Nq {m['N'] == m['Nc'] + m['Nq']}")

print("== own count: WL/WF nodes of R with no hidden quiet ==")
print(f"W0 on R: {sums['R']['W0']}  (WL {sums['R']['WL']} + WF {sums['R']['WF']} nodes)")
print(f"total lines read: {total_lines}")
