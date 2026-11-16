#!/usr/bin/env python3
"""agg_qs.py -- aggregate QSTEPS v1 lines and emit kimi5's job-10 agg layout EXACTLY.
Usage: agg_qs.py QST_CAPTURE_FILE ENGINE_NODE_SUM [KIMI5_AGG_FOR_K2_TARGETS]"""
import sys

SHAPE = {"q0": 20, "cs": 50, "xd": 10, "xm": 10, "xmb": 10, "xtt": 30, "xsp": 10, "xmt": 10,
         "xe": 10, "spm": 60, "stta": 10, "stts": 10, "spq": 20, "ml": 20, "ms": 20,
         "pf": 300, "ps": 360, "cut": 30}
acc = {k: [0] * n for k, n in SHAPE.items()}
xab = m0 = hdec = 0
searches = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("info string QSTEPS v1 "):
        continue
    searches += 1
    toks = line[len("info string QSTEPS v1 "):].split()
    i = 0
    cur = None
    got = 0
    while i < len(toks):
        t = toks[i]
        if t in SHAPE:
            cur = t; got = 0; i += 1; continue
        if t in ("xab", "m0", "hdec", "nodes"):
            v = int(toks[i + 1])
            if t == "xab": xab += v
            if t == "m0": m0 += v
            if t == "hdec": hdec += v
            i += 2; continue
        if cur is not None and got < SHAPE[cur] and t.lstrip("-").isdigit():
            acc[cur][got] += int(t); got += 1; i += 1; continue
        i += 1

def A(k): return acc[k]
q0_tot = sum(A("q0")); cs_tot = sum(A("cs"))
nodes_engine = int(sys.argv[2])
i1 = int(q0_tot != cs_tot)
ml_nc = sum(A("ml")[i] for i in range(0, 20, 2)); ms_nc = sum(A("ms")[i] for i in range(0, 20, 2))
ml_c = sum(A("ml")[i] for i in range(1, 20, 2)); ms_c = sum(A("ms")[i] for i in range(1, 20, 2))
fut = sum(A("pf")); see = sum(A("ps"))
i4 = int(not (ml_nc == ms_nc + fut + see and ml_c == ms_c))
exits = sum(sum(A(k)) for k in ("xd", "xm", "xmb", "xtt", "xsp", "xmt", "xe"))
i3 = int(q0_tot != exits)
i5 = int(q0_tot + m0 - hdec != nodes_engine)
sp_tot = sum(A("xsp"))
spm_sum = sum(A("spm"))
i2 = int(spm_sum != sp_tot)
sites = ["C_leaf", "C_razor", "C_probcut", "C_self", "C_hind"]
ssum = [sum(A("cs")[s * 10 + p * 5 + q] for p in range(2) for q in range(5)) for s in range(5)]
out = []
out.append(f"IDENTITY VIOLATIONS: I1={i1} I2={i2} I3={i3} I4={i4} I5={i5} XAB={xab} (searches {searches})")
out.append("")
out.append(f"TOTALS searches={searches} nodes(engine)={nodes_engine} q0={q0_tot} m0={m0} hdec={hdec}")
out.append(f"identity I5 total: q0+m0-hdec = {q0_tot + m0 - hdec} vs engine nodes {nodes_engine}")
out.append(f"QSEARCH SHARE of all nodes: {q0_tot / nodes_engine * 100:.4f}%")
out.append("")
out.append(f"CALL SITES total C_leaf={ssum[0]} C_razor={ssum[1]} C_probcut={ssum[2]} C_self={ssum[3]} C_hind={ssum[4]}")
out.append(f"identity I1: q0 {q0_tot} = cs {cs_tot} -> {'OK' if i1 == 0 else 'FAIL'}")
out.append("  by site x qclass (pv summed):")
for s, nm in enumerate(sites):
    vals = [sum(A("cs")[s * 10 + p * 5 + q] for p in range(2)) for q in range(5)]
    out.append(f"  {nm:10s} q1={vals[0]} q2={vals[1]} q3={vals[2]} q4-5={vals[3]} q6+={vals[4]}")
out.append("")
xd, xm, xmb, x_tt, xsp, xmt, xe = (sum(A(k)) for k in ("xd", "xm", "xmb", "xtt", "xsp", "xmt", "xe"))
out.append(f"EXITS X_draw={xd} X_maxply={xm} X_matebound={xmb} X_tt={x_tt} X_standpat={xsp} X_mated={xmt} X_end={xe}")
out.append(f"identity I3: q0 {q0_tot} = exits {exits} -> {'OK' if i3 == 0 else 'FAIL'} ; X_abort total {xab}")
out.append(f"  X_tt by bound exact/lower/upper: {sum(A('xtt')[i] for i in range(0, 30, 3))} {sum(A('xtt')[i] for i in range(1, 30, 3))} {sum(A('xtt')[i] for i in range(2, 30, 3))}")
out.append("")
out.append("STAND PAT by (best_score-beta) class " + " ".join(
    f"<{[25,50,100,200,400][i]}={sum(A('spm')[q*6+i] for q in range(10))}" for i in range(5)) +
    f" >=400={sum(A('spm')[q*6+5] for q in range(10))}")
out.append(f"identity: sum {spm_sum} = X_standpat {sp_tot} -> {'OK' if i2 == 0 else 'FAIL'}")
out.append(f"  S_tt: eval replaced {sum(A('stta'))}, of them stand-pat {sum(A('stts'))}")
spq = A("spq"); hasq = sum(spq[i] for i in range(0, 20, 2)); noq = sum(spq[i] for i in range(1, 20, 2))
out.append(f"  stand pat by legal quiet move: has-quiet {hasq}, no-quiet {noq} (no-quiet per 1000 stand pat: {noq/max(sp_tot,1)*1000:.2f})")
out.append(f"identity: spq sum {hasq + noq} = X_standpat {sp_tot} -> {'OK' if hasq + noq == sp_tot else 'FAIL'}")
out.append("")
out.append(f"MOVES not in check: legal {ml_nc} = searched {ms_nc} + fut {fut} + see {see} -> {'OK (I4)' if i4 == 0 else 'FAIL (I4)'}")
out.append(f"MOVES in check:     legal {ml_c} = searched {ms_c} -> {'OK (I4)' if ml_c == ms_c else 'FAIL (I4)'}")
out.append("")
pf = A("pf")
out.append("P_fut by margin class " + " ".join(
    f"<{[25,50,100,200,400][i]}={sum(pf[q*30 + i*5 + p] for q in range(10) for p in range(5))}" for i in range(5)) +
    f" >=400={sum(pf[q*30 + 25 + p] for q in range(10) for p in range(5))}")
out.append("P_fut by captured piece " + " ".join(
    f"{['P','N','B','R','Q'][p]}={sum(pf[q*30 + c*5 + p] for q in range(10) for c in range(6))}" for p in range(5)))
out.append(f"identity: splits sum to P_fut {fut}")
ps = A("ps")
def PSEE(gc=None, k=None, p=None):
    t = 0
    for pv in range(2):
        for q in range(5):
            for g2 in range(2):
                for k2 in range(3):
                    for p2 in range(6):
                        if gc is not None and g2 != gc: continue
                        if k is not None and k2 != k: continue
                        if p is not None and p2 != p: continue
                        t += ps[pv*180 + q*36 + g2*18 + k2*6 + p2]
    return t
out.append("P_see by gives_check no/yes " + str([PSEE(gc=g) for g in range(2)]) +
           " ; by kind cap/promo/cap+promo " + str([PSEE(k=k) for k in range(3)]) +
           " ; by captured " + str([PSEE(p=p) for p in range(6)]))
out.append(f"identity: splits sum to P_see {see}")
out.append("")
cut = A("cut")
c1 = sum(cut[i*3] for i in range(10)); c2 = sum(cut[i*3+1] for i in range(10)); c3 = sum(cut[i*3+2] for i in range(10))
out.append(f"CUT by searched-move index 1st/2nd/3rd+: [{c1}, {c2}, {c3}] (sum {c1+c2+c3})")
out.append("")
qq = [sum(A("q0")[p*10 + q*2 + c] for p in range(2) for c in range(2)) for q in range(5)]
out.append("Q0 by q class " + f"q1={qq[0]} q2={qq[1]} q3={qq[2]} q4-5={qq[3]} q6+={qq[4]}")
out.append(f"Q0 by pv nonPV={sum(A('q0')[q*2+c] for q in range(5) for c in range(2))} PV={sum(A('q0')[10+q*2+c] for q in range(5) for c in range(2))}")
out.append(f"Q0 by in_check notchk={sum(A('q0')[p*10 + q*2] for p in range(2) for q in range(5))} chk={sum(A('q0')[p*10 + q*2 + 1] for p in range(2) for q in range(5))}")
out.append(f"identity: every split sums to Q0 {q0_tot}")
out.append("")
if len(sys.argv) > 3 and "K2 COMPARISON" in open(sys.argv[3]).read():
    tgt = {}
    for l in open(sys.argv[3]):
        if " vs " in l and l.startswith("  "):
            left, rest = l.split(" vs ", 1)
            words = left.strip().split()
            key = " ".join(words[:2]) if words[0] == "moves" else words[0]
            tgt[key] = rest.split("->")[0].strip()
    out.append("K2 COMPARISON (set O, defaults):")
    out.append(f"  q0 {q0_tot} vs {tgt.get('q0','?')} -> {'OK' if str(q0_tot) == tgt.get('q0','?') else 'DIFF'}")
    cs_mine = str([ssum[i] for i in range(5)])
    out.append(f"  cs {cs_mine} vs {tgt.get('cs','?')} -> {'OK' if cs_mine == tgt.get('cs','?') else 'DIFF'}")
    ex_mine = str({'xd': xd, 'xm': xm, 'xmb': xmb, 'xtt': x_tt, 'xsp': xsp, 'xmt': xmt, 'xe': xe})
    out.append(f"  exits {ex_mine} vs {tgt.get('exits','?')} -> {'OK' if ex_mine == tgt.get('exits','?') else 'DIFF'}")
    mv_mine = str((ml_nc, ms_nc, fut, see))
    out.append(f"  moves notchk {mv_mine} vs {tgt.get('moves notchk','?')} -> {'OK' if mv_mine == tgt.get('moves notchk','?') else 'DIFF'}")
    out.append(f"  moves chk legal {ml_c} vs {tgt.get('moves chk','?')} -> {'OK' if str(ml_c) == tgt.get('moves chk','?') else 'DIFF'}")
    spm_mine = str([sum(A('spm')[q*6+i] for q in range(10)) for i in range(6)])
    out.append(f"  spm {spm_mine} vs {tgt.get('spm','?')} -> {'OK' if spm_mine == tgt.get('spm','?') else 'DIFF'}")
    out.append("")
out.append(f"SUMMED {searches} searches from ['my captured QSTEPS lines']; node sum {nodes_engine}")
print("\n".join(out))
