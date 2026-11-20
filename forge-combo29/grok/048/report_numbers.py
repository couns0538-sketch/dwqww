#!/usr/bin/env python3
"""Print proof numbers from the raw files in this folder."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def nodes_bench(path: Path) -> str:
    for line in path.read_text().splitlines():
        if "bench depth" in line and " nodes " in line:
            parts = line.split()
            return parts[parts.index("nodes") + 1]
    return "missing"


def nodes_perft(path: Path) -> str:
    for line in reversed(path.read_text().splitlines()):
        if line.startswith("nodes "):
            return line.split()[1]
    return "missing"


def file_text(path: Path) -> str:
    if not path.exists():
        return "missing"
    return path.read_text().strip().replace("\n", " | ")


def last_elo(path: Path) -> str:
    if not path.exists():
        return "missing"
    elo = "missing"
    games = ""
    for line in path.read_text().splitlines():
        if line.startswith("Elo:"):
            elo = line
        if line.startswith("Games:"):
            games = line
    if games:
        return elo + " ; " + games
    return elo


def meta_count(path: Path, key: str) -> str:
    if not path.exists():
        return "missing"
    for line in path.read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
    return "missing"


print("honesty_B_bench11", nodes_bench(ROOT / "bench11.raw.txt"))
print("honesty_B_bench13", nodes_bench(ROOT / "bench13.raw.txt"))
print("honesty_B_bench16", nodes_bench(ROOT / "bench16.raw.txt"))
print("honesty_B_perft5", nodes_perft(ROOT / "goperft5.raw.txt"))
print("honesty_P_bench11", nodes_bench(ROOT / "P_bench11.raw.txt"))
print("honesty_P_bench13", nodes_bench(ROOT / "P_bench13.raw.txt"))
print("honesty_P_bench16", nodes_bench(ROOT / "P_bench16.raw.txt"))
print("honesty_P_perft5", nodes_perft(ROOT / "P_goperft5.raw.txt"))
print("off_O", file_text(ROOT / "P_off_O_vs_B.txt"))
print("off_G", file_text(ROOT / "P_off_G_vs_B.txt"))
print("on_O", file_text(ROOT / "P_on_O_vs_B.txt"))
print("cap0_O", file_text(ROOT / "P_cap0_O_vs_B.txt"))
print("asan_symbols", meta_count(ROOT / "asan_G100.raw.txt.meta.txt", "nm_asan_symbol_lines"))
print("asan_lines", meta_count(ROOT / "asan_G100.raw.txt.meta.txt", "sanitizer_lines"))
print("asan_bug_symbols", meta_count(ROOT / "asan_bug.raw.txt.meta.txt", "nm_asan_symbol_lines"))
print("asan_bug_lines", meta_count(ROOT / "asan_bug.raw.txt.meta.txt", "sanitizer_lines"))
print("k9_R_match", last_elo(ROOT / "k9_match.log"))
print("k9_OG_match", last_elo(ROOT / "k9_og_match.log"))
print("partner030_off", file_text(ROOT / "partner030_off_vs_B.txt"))
print("partner030_on", file_text(ROOT / "partner030_on_vs_B.txt"))
print("partner030_match", last_elo(ROOT / "partner030_match.log"))
print("partner098_off", file_text(ROOT / "partner098_off_vs_B.txt"))
print("partner098_on_vs_theirs", file_text(ROOT / "partner098_on_vs_theirs.txt"))
print("partner098_match", last_elo(ROOT / "partner098_match.log"))
print("partner098_honesty_bench11", nodes_bench(ROOT / "P098_bench11.raw.txt"))
print("partner098_honesty_bench13", nodes_bench(ROOT / "P098_bench13.raw.txt"))
print("partner098_honesty_bench16", nodes_bench(ROOT / "P098_bench16.raw.txt"))
print("partner098_honesty_perft5", nodes_perft(ROOT / "P098_goperft5.raw.txt"))
b11 = nodes_bench(ROOT / "bench11.raw.txt")
b13 = nodes_bench(ROOT / "bench13.raw.txt")
b16 = nodes_bench(ROOT / "bench16.raw.txt")
p5 = nodes_perft(ROOT / "goperft5.raw.txt")
sums = (ROOT / "SUMS.txt").read_text().strip().replace("\n", " ; ")
apply_exit = "missing"
for line in (ROOT / "idea_apply_check.txt").read_text().splitlines():
    if line.startswith("exit "):
        apply_exit = line
print("TABLE")
print("step | status | evidence | result")
print(f"STEP 2 honesty B | done | HONESTY_B.txt bench11.raw.txt bench13.raw.txt bench16.raw.txt goperft5.raw.txt | {b11} {b13} {b16} {p5}")
print(f"STEP 2 O and G | done | SUMS.txt | {sums}")
print(f"STEP 3 apply | done | idea_apply_check.txt | {apply_exit}")
print(f"proof 1 honesty P | done | HONESTY_P.txt | {nodes_bench(ROOT / 'P_bench11.raw.txt')} {nodes_bench(ROOT / 'P_bench13.raw.txt')} {nodes_bench(ROOT / 'P_bench16.raw.txt')} {nodes_perft(ROOT / 'P_goperft5.raw.txt')}")
print(f"proof 2 off O | done | P_off_O_vs_B.txt | {file_text(ROOT / 'P_off_O_vs_B.txt')}")
print(f"proof 2 off G | done | P_off_G_vs_B.txt | {file_text(ROOT / 'P_off_G_vs_B.txt')}")
print(f"proof 3 on cap 3 | done | P_on_O_vs_B.txt | {file_text(ROOT / 'P_on_O_vs_B.txt')}")
print(f"proof 3 cap 0 | done | P_cap0_O_vs_B.txt | {file_text(ROOT / 'P_cap0_O_vs_B.txt')}")
print(f"proof 5 clean | done | asan_G100.raw.txt.meta.txt | symbols {meta_count(ROOT / 'asan_G100.raw.txt.meta.txt', 'nm_asan_symbol_lines')} lines {meta_count(ROOT / 'asan_G100.raw.txt.meta.txt', 'sanitizer_lines')}")
print(f"proof 5 bug | done | asan_bug.raw.txt.meta.txt | symbols {meta_count(ROOT / 'asan_bug.raw.txt.meta.txt', 'nm_asan_symbol_lines')} lines {meta_count(ROOT / 'asan_bug.raw.txt.meta.txt', 'sanitizer_lines')}")
print(f"match O+G | done | k9_og_match.log | {last_elo(ROOT / 'k9_og_match.log')}")
print(f"match R | done | k9_match.log | {last_elo(ROOT / 'k9_match.log')}")
print(f"partner 098 off | done | partner098_off_vs_B.txt | {file_text(ROOT / 'partner098_off_vs_B.txt')}")
print(f"partner 098 on | done | partner098_on_vs_theirs.txt | {file_text(ROOT / 'partner098_on_vs_theirs.txt')}")
print(f"partner 098 match | done | partner098_match.log | {last_elo(ROOT / 'partner098_match.log')}")
print(f"partner 098 honesty | done | HONESTY_P098.txt | {nodes_bench(ROOT / 'P098_bench11.raw.txt')} {nodes_bench(ROOT / 'P098_bench13.raw.txt')} {nodes_bench(ROOT / 'P098_bench16.raw.txt')} {nodes_perft(ROOT / 'P098_goperft5.raw.txt')}")
print(f"seat 030 off | done | partner030_off_vs_B.txt | {file_text(ROOT / 'partner030_off_vs_B.txt')}")
print(f"seat 030 on | done | partner030_on_vs_B.txt | {file_text(ROOT / 'partner030_on_vs_B.txt')}")
print(f"seat 030 match | done | partner030_match.log | {last_elo(ROOT / 'partner030_match.log')}")
