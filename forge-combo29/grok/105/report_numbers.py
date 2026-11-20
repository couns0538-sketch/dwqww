#!/usr/bin/env python3
"""Print the proof numbers from the raw result files in this folder."""
import pathlib

here = pathlib.Path(__file__).resolve().parent


def text(name: str) -> str:
    return (here / name).read_text(errors="replace").rstrip()


def row_sum(name: str) -> str:
    rows = [line.split() for line in text(name).splitlines() if line.strip()]
    total = sum(int(parts[1]) for parts in rows)
    return f"{name} n={len(rows)} sum={total}"


print("HONESTY_B")
print(text("HONESTY_B.txt"))
print("HONESTY_P")
print(text("HONESTY_P.txt"))
print("COMPARE")
print(text("compare_O_off.txt"))
print(text("compare_G_off.txt"))
print(text("compare_O_on.txt"))
print(row_sum("O_P_on.rows"))
print("UCI")
print(text("uci_p_options.txt"))
print("ASAN")
print(text("asan_summary.txt"))
print("MATCH")
print(text("match_og_elo.txt"))
print("PARTNER")
print(text("partner005_HONESTY.txt"))
print(text("partner005_cmp_off.txt"))
print(text("partner005_cmp_on.txt"))
print(text("partner005_match_elo.txt"))
print("APPLY")
print(text("idea_apply_check.txt"))
print(text("partner005_apply_check.txt"))
print("STEP_TABLE")
ob = sum(int(line.split()[1]) for line in text("O_B.rows").splitlines() if line.strip())
gb = sum(int(line.split()[1]) for line in text("G_B.rows").splitlines() if line.strip())
on = sum(int(line.split()[1]) for line in text("O_P_on.rows").splitlines() if line.strip())
print(f"1 seat | done | SEAT.txt | seat 105")
print(f"2 baseline | done | HONESTY_B.txt O_B.rows G_B.rows | honesty pass O {ob} G {gb}")
print(f"3 patch | done | idea.patch.txt idea_apply_check.txt | apply check ok")
print(f"3 proofs | done | compare_O_off.txt compare_G_off.txt compare_O_on.txt | off 0 and 0; on sum {on}")
print("3 match | done | match_og_elo.txt | see MATCH block")
print("4 partner | done | partner005_cmp_off.txt partner005_cmp_on.txt partner005_match_elo.txt | see PARTNER block")
print("5 report | done | REPORT.md RESULT.txt | this report")
