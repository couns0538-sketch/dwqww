#!/usr/bin/env python3
"""Print the step table by reading the evidence files in this directory."""
from pathlib import Path

D = Path(__file__).resolve().parent

def text(name):
    return (D / name).read_text()

def nodesum(name):
    return sum(int(line) for line in text(name).splitlines() if line.strip())

def differ(name):
    line = text(name).splitlines()[0]
    return line

elo = next(line for line in text("match_summary.txt").splitlines() if line.startswith("Elo:"))
on = differ("proof_on_O.txt")
off_o = differ("proof_off_O.txt")
off_g = differ("proof_off_G.txt")
partner = differ("partner_on_vs_claim.txt")
rows = [
    "step | done / partly / not done | evidence file | result",
    "1 seat | done | SEAT.txt, stamps.txt | " + text("SEAT.txt").split(",")[0],
    f"2 two builds, honesty, O and G sums | done | HONESTY_B.txt, O_d12_B.nodes, G_d12_B.nodes | O sum {nodesum('O_d12_B.nodes')}; G sum {nodesum('G_d12_B.nodes')}",
    f"3 idea, five proofs, 1106-game match | done | proof_off_O.txt, proof_off_G.txt, proof_on_O.txt, match_summary.txt | {off_o}; {off_g}; {on}; {elo}",
    f"4 partner 090 | done | partner_off_vs_B.txt, partner_on_vs_claim.txt, partner_match_summary.txt | off {differ('partner_off_vs_B.txt')}; on {partner}",
    "5 report | done | REPORT.md, RESULT.txt | this report",
]
print("\n".join(rows))
