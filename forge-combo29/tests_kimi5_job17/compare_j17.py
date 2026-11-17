#!/usr/bin/env python3
"""kimi5 job 17 step 1 comparison: per-position nodes AND best move against the
plain-tree rows of the job that made each patch. Prints one line per pair and
lists every differing position (1-based index, piece count, both node counts).
"""
import json, os

J = "/agent/repos/dwqww/forge-combo29"

def load(p):
    with open(p) as f: return json.load(f)

def pieces(fen):
    return sum(c.isalpha() for c in fen.split()[0])

def cmp(mine_p, ref_p, fens_p, label, mask=None):
    m, r = load(mine_p), load(ref_p)
    mp, rp = m["per_position"], r["per_position"]
    mb, rb = m["bestmove"], r["bestmove"]
    fens = [l.strip() for l in open(fens_p) if l.strip()]
    assert len(mp) == len(rp) == len(mb) == len(rb), (label, len(mp), len(rp))
    diffs = []
    for i in range(len(mp)):
        if mask is not None and not mask[i]:
            continue
        if mp[i] != rp[i] or mb[i] != rb[i]:
            diffs.append((i + 1, pieces(fens[i]) if i < len(fens) else -1, rp[i], mp[i], rb[i], mb[i]))
    n = len(mp) if mask is None else sum(mask)
    print(f"{label}: equal {n - len(diffs)} of {n}  (sums ref {r['nodes_sum']} / mine {m['nodes_sum']})")
    for d in diffs:
        print(f"  DIFF pos {d[0]} pieces {d[1]} nodes ref {d[2]} mine {d[3]} bm ref {d[4]} mine {d[5]}")
    return set(i for i in range(len(mp)) if mp[i] == rp[i] and mb[i] == rb[i])

os.chdir(os.path.dirname(os.path.abspath(__file__)))
maskO = sorted(cmp("rows/a0_O.json", f"{J}/tests_kimi5_job15/rows/i2_s14_O_d12.json", "O.epd", "a0_O vs job15 I2"))
maskG = sorted(cmp("rows/a0_G.json", f"{J}/tests_kimi5_job15/rows/i2_s14_G_d12.json", "G.epd", "a0_G vs job15 I2"))
mO = [i in set(maskO) for i in range(200)]
mG = [i in set(maskG) for i in range(353)]
print(f"a0-equal mask: O {sum(mO)} G {sum(mG)}")
pairs = [
    ("rfp_O", f"{J}/tests_kimi5_job14/rows/tallf_O_d12.json", "O.epd", "RfpGuards(tallf) O", mO),
    ("rfp_G", f"{J}/tests_kimi5_job14/rows/tallf_G_d12.json", "G.epd", "RfpGuards(tallf) G", mG),
    ("fhb_O", f"{J}/tests_kimi5_job12/rows/c_fhb7_s14_O_d12.json", "O.epd", "FailHighBlend(fhb7) O", mO),
    ("lmr_O", f"{J}/tests_kimi5_job11/rows/i4_s14fine_O_d12.json", "O.epd", "LmrFine(i4) O", mO),
    ("lmr_G", f"{J}/tests_kimi5_job11/rows/i4_s14fine_G_d12.json", "G.epd", "LmrFine(i4) G", mG),
    ("aq1_O", f"{J}/tests_kimi5_job15/rows/t_a1_O_d12.json", "O.epd", "AlphaQs(a1) O", mO),
    ("aq1_G", f"{J}/tests_kimi5_job15/rows/t_a1_G_d12.json", "G.epd", "AlphaQs(a1) G", mG),
    ("aq2_O", f"{J}/tests_kimi5_job15/rows/t_a2_O_d12.json", "O.epd", "AlphaQs(a2) O", mO),
    ("aq2_G", f"{J}/tests_kimi5_job15/rows/t_a2_G_d12.json", "G.epd", "AlphaQs(a2) G", mG),
    ("mal_O", f"{J}/tests_kimi5_job16/rows/t_m4_O_d12.json", "O.epd", "MalusE(m4) O", mO),
    ("mal_G", f"{J}/tests_kimi5_job16/rows/t_m4_G_d12.json", "G.epd", "MalusE(m4) G", mG),
]
for mine, ref, fens, label, mask in pairs:
    cmp(f"rows/{mine}.json", ref, fens, label, mask)
