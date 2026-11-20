#!/usr/bin/env python3
"""Read seat 026 evidence files and print the report table and the proof numbers."""

from pathlib import Path

folder = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (folder / name).read_text(encoding="utf-8", errors="replace")


def nodes_of(name: str, marker: str) -> str:
    for line in text(name).splitlines():
        if marker in line and "nodes " in line:
            parts = line.split()
            return parts[parts.index("nodes") + 1]
    return "MISSING"


print("honesty_B_bench11", nodes_of("honesty_b_bench11.txt", "bench depth 11"))
print("honesty_B_bench13", nodes_of("honesty_b_bench13.txt", "bench depth 13"))
print("honesty_B_bench16", nodes_of("honesty_b_bench16.txt", "bench depth 16"))
print("honesty_B_perft5", nodes_of("honesty_b_perft5.txt", "nodes "))
print("honesty_P_bench11", nodes_of("honesty_p_bench11.txt", "bench depth 11"))
print("honesty_P_bench13", nodes_of("honesty_p_bench13.txt", "bench depth 13"))
print("honesty_P_bench16", nodes_of("honesty_p_bench16.txt", "bench depth 16"))
print("honesty_P_perft5", nodes_of("honesty_p_perft5.txt", "nodes "))
print("--- sums ---")
for name in ("sum_B_O.txt", "sum_B_G.txt", "sum_P_on_O.txt", "partner076_on_sum.txt"):
    print(name)
    print(text(name).rstrip())
print("--- compares ---")
for name in (
    "compare_off_O.txt",
    "compare_off_G.txt",
    "compare_on_O.txt",
    "partner076_off_vs_B.txt",
    "partner076_on_vs_claim.txt",
    "partner076_on_vs_B.txt",
):
    print(name)
    print(text(name).rstrip())
print("--- asan ---")
print(text("asan_summary.txt").rstrip())
print("--- uci options ---")
print(text("uci_options_p.txt").rstrip())
print("--- apply ---")
print("own", text("apply_check.txt").rstrip())
print("partner", text("partner076_apply.txt").rstrip())
print("--- matches ---")
for name in ("match_og.txt", "partner076_match.txt"):
    lines = text(name).splitlines()
    keep = [line for line in lines if line.startswith("Elo:") or line.startswith("Games:") or line.startswith("Results ") or line == "exit 0"]
    print(name)
    print("\n".join(keep))
