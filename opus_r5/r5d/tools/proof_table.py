#!/usr/bin/env python3
"""R5D: markdown tables for MATEFIX_REPORT.md section 4 from r5d_proof.py's proof.tsv.
usage: proof_table.py <proof.tsv>"""
import sys
from collections import defaultdict

rows = []
with open(sys.argv[1], encoding="utf-8") as f:
    header = f.readline().rstrip("\n").split("\t")
    for line in f:
        if line.strip():
            rows.append(dict(zip(header, line.rstrip("\n").split("\t"))))


def pct(fail, runs):
    return f"{100.0 * fail / runs:.2f} %" if runs else "-"


def cell(r):
    runs, fail = int(r["runs"]), int(r["failures"])
    exact = int(r["exact"])
    tail = f", exact {exact}" if exact >= 0 else ""
    return f"{fail} / {runs} ({pct(fail, runs)}){tail}"


def by(step):
    return [r for r in rows if r["step"] == step]


print("KRK mate in 3, fresh Searcher per run, go depth 14 (misses / runs; exact = runs reporting exactly mate in 3):\n")
print("| Threads | SmpV2 | base 5eabdb7 | fix BKM |")
print("|---|---|---|---|")
table = defaultdict(dict)
for r in by("krk"):
    table[(r["threads"], r["smpv2"])][r["tree"]] = cell(r)
for key in sorted(table):
    print(f"| {key[0]} | {'on' if key[1] == '1' else 'off'} | {table[key].get('base', '-')} | **{table[key].get('fix', '-')}** |")
fix_total = sum(int(r["runs"]) for r in by("krk") if r["tree"] == "fix")
fix_fail = sum(int(r["failures"]) for r in by("krk") if r["tree"] == "fix")
print(f"\nfix total: {fix_fail} misses in {fix_total} runs\n")

if by("best"):
    print("SmpBestThread (SmpV2 off), depth 14:\n")
    print("| Threads | base | fix |")
    print("|---|---|---|")
    t = defaultdict(dict)
    for r in by("best"):
        t[r["threads"]][r["tree"]] = cell(r)
    for k in sorted(t):
        print(f"| {k} | {t[k].get('base', '-')} | **{t[k].get('fix', '-')}** |")
    print()

if by("sweep"):
    print("Depth sweep, fix only (misses / runs per depth; all four Threads 2/4 x SmpV2 configurations):\n")
    print("| depth | Threads 2 off | Threads 2 on | Threads 4 off | Threads 4 on |")
    print("|---|---|---|---|---|")
    t = defaultdict(dict)
    for r in by("sweep"):
        t[int(r["depth"])][(r["threads"], r["smpv2"])] = f"{r['failures']} / {r['runs']} (exact {r['exact']})"
    for d in sorted(t):
        print(f"| {d} | " + " | ".join(t[d].get(k, "-") for k in (("2", "0"), ("2", "1"), ("4", "0"), ("4", "1"))) + " |")
    s_runs = sum(int(r["runs"]) for r in by("sweep"))
    s_fail = sum(int(r["failures"]) for r in by("sweep"))
    print(f"\nsweep total: {s_fail} misses in {s_runs} runs\n")

if by("warm"):
    print("Warm TT: an unrelated depth-9 search first (prefill40 openings), then KRK depth 14 on the same Searcher:\n")
    print("| tree | Threads | SmpV2 | misses / runs | note |")
    print("|---|---|---|---|---|")
    for r in by("warm"):
        print(f"| {r['tree']} | {r['threads']} | {'on' if r['smpv2'] == '1' else 'off'} | {cell(r)} | {r['extra']} |")
    print()

if by("tt"):
    print("forge_tt_mate_tb_tests runs (a run fails when the test exits non-zero; its Threads block via FORGE_TT_MATE_*):\n")
    print("| Threads | SmpV2 | base: failed runs | fix: failed runs |")
    print("|---|---|---|---|")
    t = defaultdict(dict)
    for r in by("tt"):
        t[(r["threads"], r["smpv2"])][r["tree"]] = f"{r['failures']} / {r['runs']} ({r['extra']})"
    for k in sorted(t):
        print(f"| {k[0]} | {'on' if k[1] == '1' else 'off'} | {t[k].get('base', '-')} | **{t[k].get('fix', '-')}** |")
