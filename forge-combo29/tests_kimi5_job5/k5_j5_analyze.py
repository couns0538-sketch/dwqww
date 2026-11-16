#!/usr/bin/env python3
"""kimi5 job5 analysis: sums, tree factors with bootstrap intervals over positions,
piece-class splits, and the regret tables. Resamples named in every line.
Usage:
  k5_j5_analyze.py sums <run.json> [kpos]        -> nodes of pos 1/2/3 and the total sum
  k5_j5_analyze.py factor <base.json> <run.json> [index.txt]
                                                   -> sum ratio + 95% bootstrap CI over positions
                                                      (with index: also by piece class)
  k5_j5_analyze.py regret <run.json> [index.txt]   -> 4 cases x 6 steps: drops, regrets and
                                                      mate regrets per 1000 drops; then the
                                                      four cases (all steps) by piece class
Piece counts come from the FENs; an index file (set_G_index.txt) is only cross-checked.
Bootstrap: 2000 resamples with replacement over positions, seed 20261116, percentile 95%.
"""
import chess
import json
import random
import sys

SEED = 20261116
RESAMPLES = 2000
CLASSES = [(27, 32), (21, 26), (15, 20), (9, 14), (3, 8)]
CNAMES = ["ordinary", "pv", "in_check", "mate_alpha"]


def load(path):
    with open(path) as f:
        return json.load(f)


def nodes_of(run):
    return [r.get("nodes", 0) for r in run["records"]]


def pcount(fen):
    return chess.Board(fen).occupied.bit_count()


def sums_cmd(path, kpos):
    run = load(path)
    ns = nodes_of(run)
    first = " / ".join(f"{ns[i]:,}" for i in range(min(3, len(ns))))
    print(f"{path}: pos1/2/3 = {first}   sum = {sum(ns):,}   n = {len(ns)}")
    if kpos:
        exp = [int(x) for x in kpos.split(",")]
        ok = all(ns[i] == exp[i] for i in range(len(exp)))
        print(f"  expected pos1/2/3 = {' / '.join(f'{e:,}' for e in exp)}  -> {'MATCH' if ok else 'MISMATCH'}")


def boot_ci(base_ns, run_ns):
    rng = random.Random(SEED)
    n = len(base_ns)
    ratios = []
    for _ in range(RESAMPLES):
        idx = [rng.randrange(n) for _ in range(n)]
        b = sum(base_ns[i] for i in idx)
        r = sum(run_ns[i] for i in idx)
        if b > 0:
            ratios.append(r / b)
    ratios.sort()
    return ratios[int(0.025 * len(ratios))], ratios[int(0.975 * len(ratios))]


def factor_cmd(base_path, run_path, fens_path):
    base, run = load(base_path), load(run_path)
    bn, rn = nodes_of(base), nodes_of(run)
    assert len(bn) == len(rn), "run lengths differ"
    fens = [l.strip() for l in open(fens_path) if l.strip()][:len(bn)]
    lo, hi = boot_ci(bn, rn)
    print(f"factor {run['config']} vs {base['config']} on {fens_path} d{run['depth']}: "
          f"{sum(rn)/sum(bn):.4f} [{lo:.4f}, {hi:.4f}]  sums {sum(rn):,}/{sum(bn):,} "
          f"(seed {SEED}, {RESAMPLES} resamples)")
    for clo, chi in CLASSES:
        idx = [i for i, f in enumerate(fens) if clo <= pcount(f) <= chi]
        if not idx:
            print(f"  pieces {clo}-{chi}: n=0")
            continue
        b = sum(bn[i] for i in idx)
        r = sum(rn[i] for i in idx)
        print(f"  pieces {clo}-{chi}: n={len(idx)}  factor {r/b:.4f}  sums {r:,}/{b:,}")


def regret_cmd(run_path, fens_path):
    run = load(run_path)
    fens = [l.strip().split("|")[0].strip() for l in open(fens_path) if l.strip()][:len(run["records"])]
    drops = [[0] * 6 for _ in range(4)]
    regrets = [[0] * 6 for _ in range(4)]
    mates = [[0] * 6 for _ in range(4)]
    dt = co = pn = 0
    cls_drops = {c: {cl: 0 for cl in CLASSES} for c in range(4)}
    cls_reg = {c: {cl: 0 for cl in CLASSES} for c in range(4)}
    cls_mate = {c: {cl: 0 for cl in CLASSES} for c in range(4)}
    for i, rec in enumerate(run["records"]):
        ctr = rec.get("ctr") or {}
        pc = pcount(fens[i]) if i < len(fens) else 0
        cl = next((c for c in CLASSES if c[0] <= pc <= c[1]), None)
        for c in range(4):
            for s in range(6):
                d = ctr.get(f"d{c}{s}", 0)
                r = ctr.get(f"r{c}{s}", 0)
                m = ctr.get(f"m{c}{s}", 0)
                drops[c][s] += d
                regrets[c][s] += r
                mates[c][s] += m
                if cl:
                    cls_drops[c][cl] += d
                    cls_reg[c][cl] += r
                    cls_mate[c][cl] += m
        dt += ctr.get("dt", 0)
        co += ctr.get("co", 0)
        pn += ctr.get("pn", 0)
    print(f"regret table {run_path} (drops; regrets/1000 drops; mate/1000 drops)  dt={dt:,} co={co:,} pn={pn:,}")
    for c in range(4):
        row = []
        for s in range(6):
            d = drops[c][s]
            rr = f"{1000.0 * regrets[c][s] / d:.1f}" if d else "-"
            mm = f"{1000.0 * mates[c][s] / d:.1f}" if d else "-"
            row.append(f"s{s+1}: {d:,}; {rr}; {mm}")
        print(f"  {CNAMES[c]:<10} " + " | ".join(row))
    print("  by piece class (all steps): class n-pos drops regrets/1000 mate/1000")
    for c in range(4):
        for cl in CLASSES:
            d = cls_drops[c][cl]
            rr = f"{1000.0 * cls_reg[c][cl] / d:.1f}" if d else "-"
            mm = f"{1000.0 * cls_mate[c][cl] / d:.1f}" if d else "-"
            print(f"  {CNAMES[c]:<10} {cl[0]}-{cl[1]}: {d:,} {rr} {mm}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "sums":
        sums_cmd(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "factor":
        factor_cmd(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "regret":
        regret_cmd(sys.argv[2], sys.argv[3])
