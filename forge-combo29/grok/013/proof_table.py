#!/usr/bin/env python3
"""Print the report table from the raw evidence files."""
from pathlib import Path
D = Path("/agent/repos/dwqww/forge-combo29/grok/013")

def text(name):
    return (D / name).read_text(encoding="utf-8", errors="replace")

def last_elo(name):
    elo = err = games = ""
    for line in text(name).splitlines():
        if line.startswith("Elo:"):
            # Elo: -12.26 +/- 10.25, nElo: ...
            parts = line.split()
            elo = parts[1]
            err = parts[3].rstrip(",")
        if line.startswith("Games:"):
            games = line.split()[1].rstrip(",")
    return elo, err, games

print("HONESTY_B")
print(text("HONESTY_B.txt"), end="")
print("HONESTY_P")
print(text("HONESTY_P.txt"), end="")
print("SUMS")
for name in ["B_O_d12.sum.txt", "B_G_d12.sum.txt", "P_off_O_d12.sum.txt", "P_off_G_d12.sum.txt", "P_on_O_d12.sum.txt", "asan_on_G_d10.sum.txt", "partner_off_O.sum.txt", "partner_on_O.sum.txt"]:
    print(text(name), end="")
print("COMPARES")
for name in ["compare_off_O.txt", "compare_off_G.txt", "compare_on_O.txt", "partner_compare_off.txt", "partner_compare_on.txt", "partner_compare_on_vs_B.txt"]:
    print(name)
    print(text(name), end="")
print("ASAN_META")
for line in text("asan_on_G_d10.meta").splitlines():
    if "asan_symbol_count" in line or line.startswith("exe"):
        print(line)
print("scratch_sanitizer_lines", sum(1 for line in text("asan_scratch.raw.txt").splitlines() if "AddressSanitizer" in line))
print("g100_sanitizer_lines", sum(1 for line in text("asan_on_G_d10.raw.txt").splitlines() if "AddressSanitizer" in line or "runtime error" in line))
print("MATCH", *last_elo("match_on_off.log"))
print("PARTNER_MATCH", *last_elo("partner_match.log"))
print("APPLY")
print("mine", text("apply_check.txt"), end="")
print("partner", text("partner_apply_check.txt"), end="")
print("STEP_TABLE")
rows = [
    ("1 seat", "done", "SEAT.txt stamps.txt", "seat 013 idea 13"),
    ("2 honesty B", "done", "HONESTY_B.txt", "312866 862329 3024920 4865609"),
    ("2 O and G", "done", "B_O_d12.sum.txt B_G_d12.sum.txt", "9500069 and 18466239"),
    ("3 prediction", "done", "prediction.txt", "9200000 and Elo 8, committed before measuring"),
    ("3 patch", "done", "idea.patch.txt apply_check.txt", "apply exit 0"),
    ("3 proof off", "done", "compare_off_O.txt compare_off_G.txt", "0 of 200 and 0 of 353"),
    ("3 proof on", "done", "compare_on_O.txt P_on_O_d12.sum.txt", "200 of 200, sum 9796924"),
    ("3 uci", "done", "uci_options.txt", "IdeaS13 false, Lag 4, Bonus 160, Divisor 48, Shave 1"),
    ("3 sanitizer", "done", "asan_on_G_d10.meta asan_scratch.raw.txt", "symbols 35, G lines 0, scratch heap-buffer-overflow"),
    ("3 match", "done", "match_on_off.log match_on_off.pgn", "Elo -12.26 +/- 10.25, 1106 games"),
    ("4 partner", "done", "partner_compare_off.txt partner_compare_on.txt partner_match.log", "CONFIRMS, R match Elo -2.90 +/- 4.67, 600 games"),
]
print("step | done | evidence | result")
for step, done, evidence, result in rows:
    print(f"{step} | {done} | {evidence} | {result}")
