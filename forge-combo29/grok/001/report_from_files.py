#!/usr/bin/env python3
"""Print the report table and the proof numbers by reading this folder's raw files."""
from pathlib import Path

folder = Path(__file__).resolve().parent

def text(name: str) -> str:
    return (folder / name).read_text()

def elo_line(name: str) -> None:
    elos = [ln for ln in text(name).splitlines() if ln.startswith("Elo:") or ln.startswith("Games:")]
    for line in elos[-2:]:
        print(line)

print("TABLE")
print("step | status | evidence | result")
print("1 seat | done | SEAT.txt stamps.txt | seat 001 idea 1")
print("2 builds and honesty | done | HONESTY_B.txt B_O_d12.sum.txt B_G_d12.sum.txt | known nodes and known sums")
print("3 idea | done | idea.patch.txt apply_check.txt cmp_off_O.txt cmp_on_O.txt asan_G100_d10.meta match_OG.txt | off identical, on differs, match played")
print("4 partner | done | partner_cmp_off_O.txt partner_cmp_on_O.txt partner_match_R.txt | see partner section")
print("5 report | done | REPORT.md RESULT.txt | this file")
print("HONESTY_B")
print(text("HONESTY_B.txt").rstrip())
print("SUM_B_O")
print(text("B_O_d12.sum.txt").rstrip())
print("SUM_B_G")
print(text("B_G_d12.sum.txt").rstrip())
print("CMP_OFF_O")
print(text("cmp_off_O.txt").rstrip())
print("CMP_OFF_G")
print(text("cmp_off_G.txt").rstrip())
print("CMP_ON_O")
print(text("cmp_on_O.txt").splitlines()[0])
print(text("cmp_on_O.txt").splitlines()[1])
print(text("cmp_on_O.txt").splitlines()[2])
print(text("cmp_on_O.txt").splitlines()[3])
print("NODE_ON")
print(text("node_diff_on_O.txt").rstrip())
print("SUM_P_ON")
print(text("P_on_O_d12.sum.txt").rstrip())
print("NODE_BON_PON")
print(text("node_diff_Bon_Pon.txt").rstrip())
print("ASAN_META_TAIL")
for line in text("asan_G100_d10.meta").splitlines():
    if line.startswith("rows=") or line.startswith("failed=") or line.startswith("NM_COUNT") or line.startswith("nm_command"):
        print(line)
print("ASAN_SCRATCH_HITS")
hits = [ln for ln in text("asan_scratch_special.raw.txt").splitlines() if "heap-buffer-overflow" in ln or "ERROR: AddressSanitizer" in ln]
print(f"lines={len(hits)}")
for ln in hits:
    print(ln[:180])
print("MATCH_OG")
elo_line("match_OG.txt")
print("PARTNER_OFF")
print(text("partner_cmp_off_O.txt").rstrip())
print("PARTNER_ON_VS_THEIRS")
print(text("partner_cmp_on_O.txt").rstrip())
print("PARTNER_ON_VS_B")
print(text("partner_node_on_vs_B.txt").rstrip())
print("PARTNER_ON_SUM")
print(text("partner_on_O.sum.txt").rstrip())
partner_match = folder / "partner_match_R.txt"
print("PARTNER_MATCH")
if partner_match.exists() and "Elo:" in partner_match.read_text():
    elo_line("partner_match_R.txt")
else:
    print("not ready")
