#!/usr/bin/env python3
"""kimi5 job 10: sums every per-search QSTEPS line of one or more *_full.txt
runner outputs, checks identities I1-I5 per search, prints the Part-2 tables.
Usage: agg_j10.py <full.txt> [more_full.txt] [--k2]
Under every table the identity line ties it to a total. The last line says how
many searches were summed and their node sum. --k2 compares the totals with
Fable's known answers (set O, defaults).
"""
import sys

QCLASS = ["q1", "q2", "q3", "q4-5", "q6+"]
PV = ["nonPV", "PV"]
CHK = ["notchk", "chk"]
VC = ["<25", "<50", "<100", "<200", "<400", ">=400"]
PC = ["P", "N", "B", "R", "Q", "none"]
SITES = ["C_leaf", "C_razor", "C_probcut", "C_self", "C_hind"]

# Fable's known answers, set O, defaults (file 10, K2)
K2 = {
    "q0": 5643723,
    "cs": [2964914, 41581, 22111, 2615117, 0],
    "exits": {"xd": 144, "xm": 0, "xmb": 0, "xtt": 504203, "xsp": 2133567, "xmt": 2909, "xe": 3002900},
    "m_notchk": (4566204, 1967735, 773269, 1825200),  # legal, searched, fut, see
    "m_chk": 647382,
    "spm": [538493, 429099, 523647, 332905, 196482, 112941],
}


def parse(path):
    searches = []
    with open(path) as f:
        for line in f:
            if "QSTEPS v1" not in line:
                continue
            t = line.split()
            i = t.index("v1")
            d = {}
            j = i + 1
            while j < len(t):
                name = t[j]
                if name in ("nodes", "xab", "m0", "hdec"):
                    d[name] = int(t[j + 1]); j += 2
                else:
                    n = {"q0": 20, "cs": 50, "xd": 10, "xm": 10, "xmb": 10, "xtt": 30,
                         "xsp": 10, "xmt": 10, "xe": 10, "spm": 60, "stta": 10, "stts": 10,
                         "spq": 20, "ml": 20, "ms": 20, "pf": 300, "ps": 360, "cut": 30}[name]
                    d[name] = [int(x) for x in t[j + 1:j + 1 + n]]; j += 1 + n
            searches.append(d)
    return searches


def idx3(a, i, n2, n3):
    # flat index helpers matching the C++ layout order
    return a[i * n2 * n3:(i + 1) * n2 * n3]


def main():
    paths = [p for p in sys.argv[1:] if p != "--k2"]
    use_k2 = "--k2" in sys.argv
    S = []
    for p in paths:
        S.extend(parse(p))
    if not S:
        sys.exit("no QSTEPS lines found")

    # ---- per-search identity checks (I1-I5); a failure prints the search number
    viol = {"I1": 0, "I2": 0, "I3": 0, "I4": 0, "I5": 0, "XAB": 0}
    for n, d in enumerate(S):
        q0 = sum(d["q0"])
        cs = sum(d["cs"])
        if q0 != cs:
            viol["I1"] += 1; print(f"I1 FAIL search {n}: q0 {q0} != cs {cs}")
        q0_q1 = sum(d["q0"][qc * 2:(qc + 1) * 2] for qc in [0]) if False else 0
        # q0 layout [pv][qc][chk]: index pv*10 + qc*2 + chk
        q0_q1 = sum(d["q0"][pv * 10 + 0 * 2 + c] for pv in (0, 1) for c in (0, 1))
        cs_q1 = sum(d["cs"][s * 10 + pv * 5 + 0] for s in (0, 1, 2, 4) for pv in (0, 1))
        if q0_q1 != cs_q1:
            viol["I2"] += 1; print(f"I2 FAIL search {n}: q0@q1 {q0_q1} != sites {cs_q1}")
        exits = sum(d[k][i] for k in ("xd", "xm", "xmb", "xsp", "xmt", "xe") for i in range(10)) + sum(d["xtt"])
        if q0 != exits:
            viol["I3"] += 1; print(f"I3 FAIL search {n}: q0 {q0} != exits {exits}")
        # I4 layout ml/ms [pv][qc][chk]: pv*10+qc*2+chk ; pf [pv][qc][v][p] ; ps [pv][qc][g][k][p]
        for chk in (0, 1):
            ml = sum(d["ml"][pv * 10 + qc * 2 + chk] for pv in (0, 1) for qc in range(5))
            ms = sum(d["ms"][pv * 10 + qc * 2 + chk] for pv in (0, 1) for qc in range(5))
            if chk == 1:
                if ml != ms:
                    viol["I4"] += 1; print(f"I4 FAIL search {n} in check: ml {ml} != ms {ms}")
            else:
                pf, ps = sum(d["pf"]), sum(d["ps"])
                if ml != ms + pf + ps:
                    viol["I4"] += 1; print(f"I4 FAIL search {n}: ml {ml} != ms {ms} + pf {pf} + ps {ps}")
        if q0 + d["m0"] - d["hdec"] != d["nodes"]:
            viol["I5"] += 1; print(f"I5 FAIL search {n}: {q0}+{d['m0']}-{d['hdec']} != {d['nodes']}")
        if d["xab"] != 0:
            viol["XAB"] += 1; print(f"XAB search {n}: {d['xab']} aborts")
    print("IDENTITY VIOLATIONS:", " ".join(f"{k}={v}" for k, v in viol.items()),
          f"(searches {len(S)})")

    # ---- totals
    def tot(name):
        return [sum(x) for x in zip(*(d[name] for d in S))]
    q0, cs = tot("q0"), tot("cs")
    xd, xm, xmb, xtt = tot("xd"), tot("xm"), tot("xmb"), tot("xtt")
    xsp, xmt, xe = tot("xsp"), tot("xmt"), tot("xe")
    spm, stta, stts, spq = tot("spm"), tot("stta"), tot("stts"), tot("spq")
    ml, ms, pf, ps, cut = tot("ml"), tot("ms"), tot("pf"), tot("ps"), tot("cut")
    m0 = sum(d["m0"] for d in S); hdec = sum(d["hdec"] for d in S)
    nodes = sum(d["nodes"] for d in S)
    q0s, css = sum(q0), sum(cs)
    print(f"\nTOTALS searches={len(S)} nodes(engine)={nodes} q0={q0s} m0={m0} hdec={hdec}")
    print(f"identity I5 total: q0+m0-hdec = {q0s + m0 - hdec} vs engine nodes {nodes}")
    share = q0s / (q0s + m0 - hdec) if q0s + m0 - hdec else 0
    print(f"QSEARCH SHARE of all nodes: {share:.4%}")

    print("\nCALL SITES total " + " ".join(f"{SITES[s]}={sum(cs[s*10:(s+1)*10])}" for s in range(5)))
    print(f"identity I1: q0 {q0s} = cs {css} -> {'OK' if q0s == css else 'FAIL'}")
    print("  by site x qclass (pv summed):")
    for s in range(5):
        row = [sum(cs[s * 10 + pv * 5 + qc] for pv in (0, 1)) for qc in range(5)]
        print(f"  {SITES[s]:10s} " + " ".join(f"{QCLASS[q]}={row[q]}" for q in range(5)))

    exits = [sum(xd), sum(xm), sum(xmb), sum(xtt), sum(xsp), sum(xmt), sum(xe)]
    print("\nEXITS " + " ".join(f"{n}={v}" for n, v in
          zip(["X_draw", "X_maxply", "X_matebound", "X_tt", "X_standpat", "X_mated", "X_end"], exits)))
    print(f"identity I3: q0 {q0s} = exits {sum(exits)} -> {'OK' if q0s == sum(exits) else 'FAIL'}"
          f" ; X_abort total {sum(d['xab'] for d in S)}")
    print(f"  X_tt by bound exact/lower/upper: "
          + " ".join(str(sum(xtt[pv * 15 + qc * 3 + b] for pv in (0, 1) for qc in range(5))) for b in range(3)))

    print("\nSTAND PAT by (best_score-beta) class " + " ".join(
        f"{VC[v]}={sum(spm[pv*30+qc*6+v] for pv in (0,1) for qc in range(5))}" for v in range(6)))
    print(f"identity: sum {sum(spm)} = X_standpat {sum(xsp)} -> {'OK' if sum(spm) == sum(xsp) else 'FAIL'}")
    print(f"  S_tt: eval replaced {sum(stta)}, of them stand-pat {sum(stts)}")
    nq = [sum(spq[pv * 10 + qc * 2 + w] for pv in (0, 1) for qc in range(5)) for w in (0, 1)]
    print(f"  stand pat by legal quiet move: has-quiet {nq[0]}, no-quiet {nq[1]}"
          f" (no-quiet per 1000 stand pat: {1000*nq[1]/max(1,sum(nq)):.2f})")
    print(f"identity: spq sum {sum(spq)} = X_standpat {sum(xsp)} -> {'OK' if sum(spq) == sum(xsp) else 'FAIL'}")

    ml_n = [sum(ml[pv * 10 + qc * 2 + c] for pv in (0, 1) for qc in range(5)) for c in (0, 1)]
    ms_n = [sum(ms[pv * 10 + qc * 2 + c] for pv in (0, 1) for qc in range(5)) for c in (0, 1)]
    print(f"\nMOVES not in check: legal {ml_n[0]} = searched {ms_n[0]} + fut {sum(pf)} + see {sum(ps)}"
          f" -> {'OK' if ml_n[0] == ms_n[0] + sum(pf) + sum(ps) else 'FAIL'} (I4)")
    print(f"MOVES in check:     legal {ml_n[1]} = searched {ms_n[1]} -> {'OK' if ml_n[1] == ms_n[1] else 'FAIL'} (I4)")

    print("\nP_fut by margin class " + " ".join(
        f"{VC[v]}={sum(pf[pv*150+qc*30+v*5+p] for pv in (0,1) for qc in range(5) for p in range(5))}"
        for v in range(6)))
    print("P_fut by captured piece " + " ".join(
        f"{PC[p]}={sum(pf[pv*150+qc*30+v*5+p] for pv in (0,1) for qc in range(5) for v in range(6))}"
        for p in range(5)))
    print(f"identity: splits sum to P_fut {sum(pf)}")
    ps_g = [sum(ps[pv*180+qc*36+g*18+k*6+p] for pv in (0,1) for qc in range(5) for k in range(3) for p in range(6))
            for g in (0, 1)]
    ps_k = [sum(ps[pv*180+qc*36+g*18+k*6+p] for pv in (0,1) for qc in range(5) for g in (0,1) for p in range(6))
            for k in range(3)]
    ps_p = [sum(ps[pv*180+qc*36+g*18+k*6+p] for pv in (0,1) for qc in range(5) for g in (0,1) for k in range(3))
            for p in range(6)]
    print(f"P_see by gives_check no/yes {ps_g} ; by kind cap/promo/cap+promo {ps_k} ; by captured {ps_p}")
    print(f"identity: splits sum to P_see {sum(ps)}")

    cut_i = [sum(cut[pv * 15 + qc * 3 + i] for pv in (0, 1) for qc in range(5)) for i in range(3)]
    print(f"\nCUT by searched-move index 1st/2nd/3rd+: {cut_i} (sum {sum(cut)})")

    print("\nQ0 by q class " + " ".join(
        f"{QCLASS[q]}={sum(q0[pv*10+q*2+c] for pv in (0,1) for c in (0,1))}" for q in range(5)))
    print("Q0 by pv " + " ".join(
        f"{PV[p]}={sum(q0[p*10+qc*2+c] for qc in range(5) for c in (0,1))}" for p in (0, 1)))
    print("Q0 by in_check " + " ".join(
        f"{CHK[c]}={sum(q0[pv*10+qc*2+c] for pv in (0,1) for qc in range(5))}" for c in (0, 1)))
    print(f"identity: every split sums to Q0 {q0s}")

    if use_k2:
        print("\nK2 COMPARISON (set O, defaults):")
        print(f"  q0 {q0s} vs {K2['q0']} -> {'OK' if q0s == K2['q0'] else 'DIFF'}")
        cs_s = [sum(cs[s * 10:(s + 1) * 10]) for s in range(5)]
        print(f"  cs {cs_s} vs {K2['cs']} -> {'OK' if cs_s == K2['cs'] else 'DIFF'}")
        ex = dict(zip(["xd", "xm", "xmb", "xtt", "xsp", "xmt", "xe"], exits))
        print(f"  exits {ex} vs {K2['exits']} -> {'OK' if ex == K2['exits'] else 'DIFF'}")
        mn = (ml_n[0], ms_n[0], sum(pf), sum(ps))
        print(f"  moves notchk {mn} vs {K2['m_notchk']} -> {'OK' if mn == K2['m_notchk'] else 'DIFF'}")
        print(f"  moves chk legal {ml_n[1]} vs {K2['m_chk']} -> {'OK' if ml_n[1] == K2['m_chk'] else 'DIFF'}")
        spm_s = [sum(spm[pv * 30 + qc * 6 + v] for pv in (0, 1) for qc in range(5)) for v in range(6)]
        print(f"  spm {spm_s} vs {K2['spm']} -> {'OK' if spm_s == K2['spm'] else 'DIFF'}")

    print(f"\nSUMMED {len(S)} searches from {paths}; node sum {nodes}")


if __name__ == "__main__":
    main()
