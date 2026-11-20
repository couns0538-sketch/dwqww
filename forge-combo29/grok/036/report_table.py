#!/usr/bin/env python3
"""Print the report table from the raw evidence files in this folder."""
from pathlib import Path

d = Path(__file__).resolve().parent

def last_nodes(name: str) -> str:
    lines = [ln for ln in (d / name).read_text().splitlines() if "nodes " in ln]
    parts = lines[-1].split()
    return parts[parts.index("nodes") + 1]

def rows(name: str) -> list[int]:
    out = []
    for line in (d / name).read_text().splitlines():
        line = line.strip()
        if line:
            out.append(int(line.split()[-1]))
    return out

def differ(a: str, b: str) -> tuple[int, int, int, int]:
    A, B = rows(a), rows(b)
    n = min(len(A), len(B))
    return n, sum(x != y for x, y in zip(A, B)), sum(A), sum(B)

def elo_line(name: str) -> str:
    lines = (d / name).read_text().splitlines()
    idxs = [i for i, ln in enumerate(lines) if ln.startswith("Elo:") or ln.startswith("Results of ")]
    # prefer the last Results block's Elo
    blocks = [i for i, ln in enumerate(lines) if ln.startswith("Results of ")]
    elo = ""
    games = ""
    for ln in lines[blocks[-1]:blocks[-1] + 6]:
        if ln.startswith("Elo:"):
            elo = ln
        if ln.startswith("Games:"):
            games = ln
    return elo + " | " + games

n, diff, sa, sb = differ("o_p_on_d12.txt", "o_b_d12.txt")
off_o = differ("o_p_off_d12.txt", "o_b_d12.txt")
off_g = differ("g_p_off_d12.txt", "g_b_d12.txt")
pon = differ("partner_on.txt", "partner_claimed_on_O.nodes")
poff = differ("partner_off.txt", "o_b_d12.txt")
clean = [ln for ln in (d / "asan_g100_d10.meta").read_text().splitlines() if "sanitizer_lines" in ln or "nm_asan" in ln]
bad = [ln for ln in (d / "asan_deliberate.meta").read_text().splitlines() if "sanitizer_lines" in ln or "nm_asan" in ln]
rows_out = [
    ("1 seat", "done", "SEAT.txt", "seat 036, script printed IDEA 36"),
    ("2 honesty and baseline", "done", "HONESTY_B.txt SUMS_B.txt",
     f"bench 11/13/16 {last_nodes('honesty_b_bench11.txt')}/{last_nodes('honesty_b_bench13.txt')}/{last_nodes('honesty_b_bench16.txt')} perft5 {last_nodes('honesty_b_perft5.txt')} O {sum(rows('o_b_d12.txt'))} G {sum(rows('g_b_d12.txt'))}"),
    ("3 patch and proofs", "done", "idea.patch.txt PROOFS.txt asan_g100_d10.meta",
     f"off O differ {off_o[1]} of {off_o[0]}; off G differ {off_g[1]} of {off_g[0]}; on O differ {diff} of {n} sum {sa}"),
    ("3e match", "done", "MATCH_RESULT.txt match_og.log", elo_line("match_og.log")),
    ("4 partner", "done", "partner_compare.txt partner_match_result.txt",
     f"off vs B differ {poff[1]} of {poff[0]}; on vs claimed differ {pon[1]} of {pon[0]} sum {pon[2]}; {elo_line('match_partner_R.log')}"),
    ("5 report", "done", "REPORT.md RESULT.txt", "this report"),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows_out:
    print(f"{step} | {status} | {evidence} | {result}")
print("asan_clean " + " ".join(clean))
print("asan_bad " + " ".join(bad))
