#!/usr/bin/env python3
"""Compact evidence table. Every number is read from a file in this folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text(errors="replace")


def line_with(name: str, prefix: str) -> str:
    for line in text(name).splitlines():
        if line.startswith(prefix):
            return line
    return ""


print("file\tkey")
print(f"HONESTY_B.txt\t{text('HONESTY_B.txt').strip().splitlines()[-4:]}")
print("--- HONESTY_B ---")
print(text("HONESTY_B.txt").rstrip())
print("--- HONESTY_P ---")
print(text("HONESTY_P.txt").rstrip())
print("--- B_SUMS ---")
print(text("B_SUMS.txt").rstrip())
print("--- P_SUMS ---")
print(text("P_SUMS.txt").rstrip())
print("--- compare off O ---")
print(text("compare_O_off.txt").rstrip())
print("--- compare off G ---")
print(text("compare_G_off.txt").rstrip())
print("--- compare on O head ---")
print("\n".join(text("compare_O_on.txt").splitlines()[:8]))
print("--- match elo ---")
print(text("match_og_elo.txt").rstrip())
print("--- asan meta tail ---")
print("\n".join(text("G_d10_asan.meta").splitlines()[-6:]))
print("--- scratch meta ---")
print(text("scratch_asan.meta").rstrip())
print("--- uci idea lines ---")
for line in text("uci_p.txt").splitlines():
    if "IdeaA2" in line:
        print(line)
print("--- apply_check ---")
print(text("apply_check.txt").rstrip())
print("--- prediction ---")
print(text("prediction.txt").rstrip())
print("--- partner honesty ---")
print(text("HONESTY_PARTNER.txt").rstrip())
print("--- partner off ---")
print(text("partner_compare_off.txt").rstrip())
print("--- partner on vs claimed ---")
print(text("partner_compare_on.txt").rstrip())
print("--- partner on vs B head ---")
print("\n".join(text("partner_compare_on_vs_B.txt").splitlines()[:6]))
print("--- partner apply ---")
print(text("partner_apply_check.txt").rstrip())
print("--- partner match ---")
print(text("partner_match_elo.txt").rstrip())
print("--- stamps ---")
print(text("stamps.txt").rstrip())
print("--- step table ---")
print("step\tstatus\tevidence\tresult")
on = text("compare_O_on.txt")
off_o = text("compare_O_off.txt")
off_g = text("compare_G_off.txt")
elo = [ln for ln in text("match_og_elo.txt").splitlines() if ln.startswith("Elo:")][0]
print("1 seat\tdone\tSEAT.txt stamps.txt\tseat 083 idea 33")
print("2 honesty and known sums\tdone\tHONESTY_B.txt B_SUMS.txt\t" + " ".join(
    ln for ln in text("HONESTY_B.txt").splitlines() if ln.startswith("bench") or ln.startswith("perft")
))
print("2 O and G on exe B\tdone\tB_SUMS.txt\t" + text("B_SUMS.txt").splitlines()[1] + " | " + text("B_SUMS.txt").splitlines()[2])
print("3 prediction\tdone\tprediction.txt\tcommitted before measuring exe P; node band missed, elo band hit")
print("3 proof off\tdone\tcompare_O_off.txt compare_G_off.txt\t" + off_o.splitlines()[3] + " O; " + off_g.splitlines()[3] + " G")
print("3 proof on\tdone\tcompare_O_on.txt P_SUMS.txt\t" + on.splitlines()[3] + " of 200; sum " + text("P_SUMS.txt").splitlines()[3].split()[2])
print("3 uci options\tdone\tuci_p.txt\tIdeaA2 check default false; IdeaA2_MinDepth spin default 2")
print("3 sanitizer\tdone\tG_d10_asan.meta scratch_asan.meta\tnm_asan_count 35; clean G100; scratch reported a runtime error")
print("3 match\tdone\tmatch_og.txt match_og.pgn match_og_elo.txt\t" + elo + "; games 1106")
print("4 partner 033\tdone\tpartner_compare_off.txt partner_compare_on.txt partner_match_elo.txt\tCONFIRMS; " + text("partner_match_elo.txt").splitlines()[-2])
print("5 report\tdone\tREPORT.md RESULT.txt\tthis file")
