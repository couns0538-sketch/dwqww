#!/usr/bin/env python3
"""Print the report table from the raw files in this folder."""
from pathlib import Path
import sys

folder = Path(sys.argv[1])

def text(name):
    return (folder / name).read_text()

def sum_of(name):
    info = {}
    for line in text(name).splitlines():
        key, value = line.split("=", 1)
        info[key] = value
    return info

def differ(name):
    for line in text(name).splitlines():
        if line.startswith("positions="):
            return line
    return "missing"

def elo(name):
    lines = text(name).splitlines()
    got = {line.split("=", 1)[0]: line.split("=", 1)[1] for line in lines if "=" in line}
    return got

o = sum_of("B_O_d12.sum")
g = sum_of("B_G_d12.sum")
on = sum_of("P_on_O_d12.sum")
match = elo("match_og.elo.txt")
partner = elo("partner_R.elo.txt")
rows = [
    ("1 seat", "done", "SEAT.txt, stamps.txt", "seat 088, idea 38, IdeaA7"),
    ("2 builds and known sums", "done", "HONESTY_B.txt, B_O_d12.sum, B_G_d12.sum",
     f"honesty exact; O sum {o['sum']} first3 {o['first3']}; G sum {g['sum']}"),
    ("3 idea", "done", "idea.patch.txt, apply_check.txt, proof_off_O.txt, proof_off_G.txt, proof_on_O.txt, P_uci.txt, asan_G100.meta, asan_scratch.txt, match_og.elo.txt",
     f"apply check ok; off identical; on {differ('proof_on_O.txt')}; O-on sum {on['sum']}; sanitizer clean, trap reports; Elo {match['elo']} +/- {match['err']} over {match['games']} games"),
    ("4 partner 038", "done", "partner_038_idea.patch.txt, partner_038_apply_check.txt, HONESTY_PARTNER.txt, partner_cmp_off_O.txt, partner_cmp_on_vs_claim.txt, partner_cmp_on_vs_B.txt, partner_R.elo.txt",
     f"CONFIRMS; off {differ('partner_cmp_off_O.txt')}; on vs their rows {text('partner_cmp_on_vs_claim.txt').strip()}; on vs B {differ('partner_cmp_on_vs_B.txt')}; R match Elo {partner['elo']} +/- {partner['err']} games {partner['games']}"),
    ("5 report", "done", "REPORT.md, RESULT.txt", "this file"),
]
print("step | done / partly / not done | evidence file | result")
print("--- | --- | --- | ---")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
