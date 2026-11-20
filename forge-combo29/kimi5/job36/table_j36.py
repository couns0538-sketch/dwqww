#!/usr/bin/env python3
"""kimi5 job 36 step 4: tables T1-T4 from committed .rows and .ledger files.
Usage: table_j36.py <runs_dir> <set>   (set = O or G; files tagged <TAG>_<STATE>.{rows,ledger})
Prints T1, T2, T3, T4. Pure stdlib. Every count is printed with what it counted.
Ledger line format (after the position-number prefix):
  info string ITER depth D elapsed E target T rule R effort1000 X falling1000 Y floor Z factor1000 F basis B
  info string LEDGER kind K soft S hard H elapsed E nodes N depth D
  info string TmFinishIteration hold depth D prev P last L remaining R
"""
import sys, os, math
from collections import Counter, defaultdict

RUNS = sys.argv[1]
SET = sys.argv[2] if len(sys.argv) > 2 else "G"

STATES = ["A", "B", "C"]
GO = {"A": ("wtime 6000 btime 6000 winc 60 binc 60", 317, 1585),
      "B": ("wtime 2000 btime 2000 winc 60 binc 60", 135, 675),
      "C": ("wtime 300 btime 300 winc 60 binc 60", 58, 174)}

def load(tag):
    rows, ledger = [], []
    rp = os.path.join(RUNS, tag + ".rows")
    lp = os.path.join(RUNS, tag + ".ledger")
    if os.path.exists(rp):
        rows = [l.split() for l in open(rp) if l.strip()]
    if os.path.exists(lp):
        for l in open(lp):
            l = l.strip()
            if l:
                ledger.append(l.split())
    return rows, ledger

def parse_led(ledger):
    """-> per position: dict iters=[(depth,elapsed,target,rule,eff,fall,floor,factor,basis)], hold=(depth,...), led=(kind,soft,hard,elapsed,nodes,depth)"""
    per = defaultdict(lambda: {"iters": [], "hold": None, "led": None})
    for f in ledger:
        pos = int(f[0])
        if f[1] == "info" and f[3] == "ITER":
            kv = {f[i]: f[i+1] for i in range(4, len(f)-1, 2)}
            per[pos]["iters"].append({k: (int(v) if k not in ("rule",) else v) for k, v in kv.items()})
        elif f[1] == "info" and f[3] == "LEDGER":
            kv = {f[i]: f[i+1] for i in range(4, len(f)-1, 2)}
            per[pos]["led"] = {k: (int(v) if k != "kind" else v) for k, v in kv.items()}
        elif f[1] == "info" and f[3] == "TmFinishIteration":
            kv = {f[i]: f[i+1] for i in range(5, len(f)-1, 2)}
            per[pos]["hold"] = {k: int(v) for k, v in kv.items()}
    return per

def T_of(rows):
    return sum(int(r[2]) // 1000 for r in rows)

def kinds_of(per):
    return Counter(v["led"]["kind"] for v in per.values() if v["led"])

def t1(tags):
    print("== T1: how the searches end ==")
    print("run | n | SOFT HOLD HARDEND ABORTKEPT ABORTNEW CAP OTHER | T | W_kept W_new (x10000 of T)")
    for tag in tags:
        rows, ledger = load(tag)
        per = parse_led(ledger)
        c = kinds_of(per)
        T = T_of(rows)
        wk = wn = 0
        for pos, v in per.items():
            if v["led"] and v["led"]["kind"] in ("ABORTKEPT", "ABORTNEW") and v["iters"]:
                over = v["led"]["elapsed"] - v["iters"][-1]["elapsed"]
                if v["led"]["kind"] == "ABORTKEPT": wk += over
                else: wn += over
        print(f"{tag} | {len(rows)} | {c.get('SOFT',0)} {c.get('HOLD',0)} {c.get('HARDEND',0)} {c.get('ABORTKEPT',0)} {c.get('ABORTNEW',0)} {c.get('CAP',0)} {sum(v for k,v in c.items() if k.startswith('OTHER'))} | {T} | {10000*wk//max(T,1)} {10000*wn//max(T,1)}")
    print()

def t2(tags):
    print("== T2: how late (elapsed/soft classes; SOFT-stop lateness) ==")
    print("run | <=0.5 <=1 <=2 <=4 >4 | SOFT: sum(elapsed)/sum(target), n(elapsed>1.5*target)")
    for tag in tags:
        rows, ledger = load(tag)
        per = parse_led(ledger)
        cls = [0]*5
        se = st = n15 = 0
        for pos, v in per.items():
            if not v["led"]: continue
            e, s = v["led"]["elapsed"], v["led"]["soft"]
            r = e / s if s else 0
            cls[0 if r <= 0.5 else 1 if r <= 1 else 2 if r <= 2 else 3 if r <= 4 else 4] += 1
            if v["led"]["kind"] == "SOFT" and v["iters"]:
                se += e; st += v["iters"][-1]["target"]
                if e * 2 > 3 * v["iters"][-1]["target"]: n15 += 1
        ratio = f"{se/st:.4f}" if st else "-"
        print(f"{tag} | {cls[0]} {cls[1]} {cls[2]} {cls[3]} {cls[4]} | {ratio} {n15}")
    print()

def t3(tags):
    print("== T3: which rule (base runs; LAST ITER per search | all ITER with depth>=6) ==")
    for tag in tags:
        rows, ledger = load(tag)
        per = parse_led(ledger)
        for label, sel in (("LAST", None), ("D6+", "all6")):
            rules = Counter(); eff = []; fall = 0; flr = 0; fac = []; n = 0
            for pos, v in per.items():
                its = v["iters"]
                if not its: continue
                use = [its[-1]] if sel is None else [i for i in its if i["depth"] >= 6]
                for i in use:
                    n += 1; rules[i["rule"]] += 1; eff.append(i["effort1000"]); fac.append(i["factor1000"])
                    if i["falling1000"] > 1000: fall += 1
                    if i["floor"] == 1: flr += 1
            if n == 0: continue
            print(f"{tag} {label} | n={n} | S6 {rules.get('S6',0)} S3 {rules.get('S3',0)} U {rules.get('U',0)} N {rules.get('N',0)} | mean effort1000 {sum(eff)/n:.0f} | falling>1000 {100*fall/n:.1f}% | floor1 {100*flr/n:.1f}% | mean factor1000 {sum(fac)/n:.0f}")
    print()

def t4(base_tags, fin_tags):
    print("== T4: the hold's own claim (base vs TmFinishIteration) ==")
    for btag, ftag in zip(base_tags, fin_tags):
        brows, bledger = load(btag)
        frows, fledgetag = load(ftag)
        base, fin = parse_led(bledger), parse_led(fledgetag)
        bbase_iters = {p: {i["depth"]: i for i in v["iters"]} for p, v in base.items()}
        holds = right = wrong = nonext = missed = 0
        nonext_ends = Counter()
        t_base, t_fin = T_of(brows), T_of(frows)
        saved_right = saved_wrong = 0
        diff_right, diff_wrong, diff_nonext = [], [], []
        for p, v in fin.items():
            if v["hold"] and v["led"] and v["led"]["kind"] == "HOLD":
                holds += 1
                d = v["hold"]["depth"]
                t = v["iters"][-1]["target"] if v["iters"] else None
                nxt = bbase_iters.get(p, {}).get(d + 1)
                base_led = base.get(p, {}).get("led")
                fin_bm = [r[3] for r in frows if int(r[0]) == p][0]
                base_bm = [r[3] for r in brows if int(r[0]) == p][0]
                saved = (base_led["elapsed"] - v["led"]["elapsed"]) if base_led else 0
                if nxt is None:
                    nonext += 1
                    nonext_ends[base_led["kind"] if base_led else "?"] += 1
                    if fin_bm != base_bm: diff_nonext.append(p)
                elif t is not None and nxt["elapsed"] > t:
                    right += 1; saved_right += saved
                    if fin_bm != base_bm: diff_right.append(p)
                else:
                    wrong += 1; saved_wrong += saved
                    if fin_bm != base_bm: diff_wrong.append(p)
        # MISSED: in the FIN run itself, every (search, depth d) the search went on from
        # (no hold after d), whose own ITER line at d+1 has elapsed above the target of d.
        for p, v in fin.items():
            by_depth = {i["depth"]: i for i in v["iters"]}
            for d, i in by_depth.items():
                if v["hold"] and v["led"] and v["led"]["kind"] == "HOLD" and d >= v["hold"]["depth"]:
                    continue
                nxt = by_depth.get(d + 1)
                if nxt is not None and nxt["elapsed"] > i["target"]:
                    missed += 1
        print(f"{ftag} vs {btag}: holds {holds} RIGHT {right} WRONG {wrong} NO_NEXT_LINE {nonext} (base ended: {dict(nonext_ends)}) MISSED {missed}")
        print(f"  T base {t_base} fin {t_fin} saved {t_base - t_fin} (right part {saved_right}, wrong part {saved_wrong}); bestmove differs vs base: right {diff_right} wrong {diff_wrong} nonext {diff_nonext}")
    print()

if __name__ == "__main__":
    base = [f"{SET}_{s}" for s in STATES]
    t1(base + [f"{SET}_A_chard", f"{SET}_A_cfloor", f"{SET}_{s}_fin" for s in STATES])
    t2(base + [f"{SET}_A_chard", f"{SET}_A_cfloor", f"{SET}_{s}_fin" for s in STATES])
    t3(base)
    t4(base, [f"{SET}_{s}_fin" for s in STATES])
