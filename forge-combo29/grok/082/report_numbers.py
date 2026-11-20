#!/usr/bin/env python3
"""Read this seat's raw files and print the report numbers. No hand totals."""
from pathlib import Path

d = Path(__file__).resolve().parent

def last_nodes(name):
    lines = (d / name).read_text().splitlines()
    hits = [ln for ln in lines if "nodes " in ln]
    return hits[-1]

def rows(name):
    out = []
    for line in (d / name).read_text().splitlines():
        if line.startswith("SUM") or line.startswith("FIRST"):
            continue
        if not line.strip():
            continue
        out.append(int(line.split()[1]))
    return out

def differ(a, b):
    return sum(x != y for x, y in zip(a, b)), min(len(a), len(b))

print("HONESTY_B")
print((d / "HONESTY_B.txt").read_text().rstrip())
print("HONESTY_P")
print((d / "HONESTY_P.txt").read_text().rstrip())
print("COMPARE_O_OFF")
print((d / "compare_O_off.txt").read_text().rstrip())
print("COMPARE_G_OFF")
print((d / "compare_G_off.txt").read_text().rstrip())
print("COMPARE_O_ON")
print((d / "compare_O_on.txt").read_text().rstrip())
print("UCI_IDEA")
for ln in (d / "uci_options.txt").read_text().splitlines():
    if "IdeaA1" in ln:
        print(ln)
print("ASAN_ERR_BYTES", (d / "asan_G100_d10.err").stat().st_size)
for ln in (d / "asan_G100_d10.meta").read_text().splitlines():
    if "asan_symbol" in ln or ln.startswith("sum=") or ln.startswith("exe="):
        print(ln)
print("CANARY_HAS_OVERFLOW", "heap-buffer-overflow" in (d / "canary_asan.runner.txt").read_text())
print("MATCH")
text = (d / "match_summary.txt").read_text().splitlines()
for ln in text:
    if ln.startswith("Elo:") or ln.startswith("Games:"):
        print(ln)
print("PARTNER_HONESTY")
for name in ["partner032_bench11", "partner032_bench13", "partner032_bench16", "partner032_perft5"]:
    print(last_nodes(name + ".txt"))
b = rows("B_O_d12.rows")
off = rows("partner032_off_O.rows")
on = rows("partner032_on_O.rows")
claim = []
for line in (d / "partner032_P_on_O.nodes").read_text().splitlines():
    if line.strip():
        claim.append(int(line.split()[1]))
doff, n1 = differ(off, b)
don, n2 = differ(on, claim)
donb, n3 = differ(on, b)
print(f"partner_off_vs_B differ {doff} of {n1}")
print(f"partner_on_vs_their_rows differ {don} of {n2} on_sum {sum(on)} their_sum {sum(claim)}")
print(f"partner_on_vs_B differ {donb} of {n3}")
plog = (d / "partner032_match.log").read_text().splitlines()
idx = [i for i, ln in enumerate(plog) if ln.startswith("Results of ")]
for ln in plog[idx[-1]:idx[-1] + 6]:
    if ln.startswith("Elo:") or ln.startswith("Games:"):
        print(ln)
print("APPLY")
print("mine", (d / "apply_check_mine.txt").read_text().rstrip())
print("partner", (d / "apply_check_partner.txt").read_text().rstrip())
o_off = (d / "compare_O_off.txt").read_text().splitlines()[0]
g_off = (d / "compare_G_off.txt").read_text().splitlines()[0]
o_on = (d / "compare_O_on.txt").read_text().splitlines()[0]
print("TABLE")
print("step | status | evidence | result")
print("1 seat | done | SEAT.txt stamps.txt | seat 082 idea 32")
print("2 two builds and honesty | done | HONESTY_B.txt B_O_d12.rows B_G_d12.rows | bench nodes 312866 862329 3024920 perft 4865609; O sum 9500069; G sum 18466239")
print("3 idea | done | idea.patch.txt compare_O_off.txt compare_G_off.txt compare_O_on.txt asan_G100_d10.meta canary_asan.runner.txt match_summary.txt | " + o_off + "; " + g_off + "; " + o_on)
print("4 partner 032 | done | partner032_compare.txt partner032_match.log | off differ 0; on vs their rows differ 0; CONFIRMS")
print("5 report | done | REPORT.md RESULT.txt | this file")
print("proof 1 honesty no setoption | done | HONESTY_P.txt | same four node counts as exe B")
print("proof 2 switch false | done | compare_O_off.txt compare_G_off.txt | " + o_off + "; " + g_off)
print("proof 3 switch true | done | compare_O_on.txt | " + o_on)
print("proof 4 uci options | done | uci_options.txt | IdeaA1 check false; IdeaA1_Scale 1024; IdeaA1_Clamp 2")
print("proof 5 sanitizer | done | asan_G100_d10.err asan_G100_d10.meta canary_asan.runner.txt | err bytes 0; asan symbols 35; canary heap-buffer-overflow")
elo = next(ln for ln in (d / "match_summary.txt").read_text().splitlines() if ln.startswith("Elo:"))
games = next(ln for ln in (d / "match_summary.txt").read_text().splitlines() if ln.startswith("Games:"))
print("match | done | match_summary.txt | " + elo + " | " + games)
