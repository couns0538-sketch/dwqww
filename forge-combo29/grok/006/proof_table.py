#!/usr/bin/env python3
"""Print the proof table from committed raw files. No hand-typed numbers."""
from pathlib import Path

root = Path(__file__).resolve().parent

def grab(path, needle):
    text = (root / path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if needle in line:
            return line
    return "MISSING " + needle

def file_line(path, key):
    for line in (root / path).read_text(encoding="utf-8").splitlines():
        if line.startswith(key):
            return line.split("=", 1)[1]
    raise SystemExit(f"missing {key} in {path}")

print("honesty_B_bench11", grab("HONESTY_B.txt", "bench11="))
print("honesty_B_bench13", grab("HONESTY_B.txt", "bench13="))
print("honesty_B_bench16", grab("HONESTY_B.txt", "bench16="))
print("honesty_B_perft5", grab("HONESTY_B.txt", "perft5="))
print("honesty_P_bench11", grab("HONESTY_P.txt", "bench11="))
print("honesty_P_bench13", grab("HONESTY_P.txt", "bench13="))
print("honesty_P_bench16", grab("HONESTY_P.txt", "bench16="))
print("honesty_P_perft5", grab("HONESTY_P.txt", "perft5="))
print("B_O", (root / "B_O_d12.sum").read_text().strip().replace("\n", " | "))
print("B_G", (root / "B_G_d12.sum").read_text().strip().replace("\n", " | "))
print("P_off_O", (root / "P_off_O_d12.sum").read_text().strip().replace("\n", " | "))
print("P_off_G", (root / "P_off_G_d12.sum").read_text().strip().replace("\n", " | "))
print("P_on_O", (root / "P_on_O_d12.sum").read_text().strip().replace("\n", " | "))
print("compare_off_O", (root / "compare_B_Poff_O.txt").read_text().strip().replace("\n", " | "))
print("compare_off_G", (root / "compare_B_Poff_G.txt").read_text().strip().replace("\n", " | "))
print("compare_on_O", (root / "compare_B_Pon_O.txt").read_text().strip().replace("\n", " | "))
print("uci_options")
print((root / "uci_options_idea.txt").read_text().rstrip())
print("asan_clean", (root / "asan_g100.san").read_text().strip().replace("\n", " | "))
print("asan_nm", (root / "asan_nm_count.txt").read_text().strip())
print("asan_bug", (root / "asan_bug.san").read_text().strip().replace("\n", " | "))
print("apply_check", (root / "apply_check.txt").read_text().strip())
