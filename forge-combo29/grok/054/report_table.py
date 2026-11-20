#!/usr/bin/env python3
"""Print the step table and the proof numbers from the raw files in this folder."""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8", errors="replace").rstrip()


def main() -> None:
    rows = [
        ("STEP 1 seat", "done", "SEAT.txt", "seat 054 idea 4"),
        ("STEP 2 honesty B", "done", "HONESTY_B.txt", "bench 11/13/16 and perft 5 match"),
        ("STEP 2 O and G", "done", "B_O_d12.meta B_G_d12.meta", "O 9500069 G 18466239"),
        ("3a read", "done", "decision.txt", "EXISTS search.cpp:2010"),
        ("3b prediction", "done", "prediction.txt", "10200000 and Elo +5, committed before measuring"),
        ("3c patch", "done", "idea.patch.txt apply_check.txt", "git apply --check ok"),
        ("3d (1) honesty P", "done", "HONESTY_P.txt", "same four node counts, no setoption"),
        ("3d (2) switch off", "done", "cmp_off_O.txt cmp_off_G.txt", "0 of 200 and 0 of 353"),
        ("3d (3) switch on", "done", "cmp_on_O.txt", "200 of 200 differ, sum 9722581"),
        ("3d (4) uci", "done", "HONESTY_P_uci.txt", "IdeaS35_Index 7, IdeaS35_Replies 4"),
        ("3d (5) sanitizer", "done", "asan_G100.meta asan_scratch_lines.txt", "nm __asan_ 35, clean, trap reports"),
        ("3e match", "done", "match_result.txt match_on_off.pgn", "1106 games, Elo -0.00 +/- 10.81"),
        ("STEP 4 partner 104", "done", "partner104_cmp_off_O.txt partner104_cmp_on_O.txt partner104_match_result.txt", "CONFIRMS"),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {evidence} | {result}")
    print()
    print("--- HONESTY_B ---")
    print(text("HONESTY_B.txt"))
    print("--- HONESTY_P ---")
    print(text("HONESTY_P.txt"))
    print("--- cmp_off_O ---")
    print(text("cmp_off_O.txt"))
    print("--- cmp_off_G ---")
    print(text("cmp_off_G.txt"))
    print("--- cmp_on_O ---")
    print(text("cmp_on_O.txt"))
    print("--- asan clean ---")
    print(text("asan_G100_lines.txt"))
    print("--- asan trap ---")
    print(text("asan_scratch_lines.txt"))
    print("--- match ---")
    print(text("match_result.txt"))
    print("--- partner off vs B ---")
    print(text("partner104_cmp_off_O.txt"))
    print("--- partner on vs their rows ---")
    print(text("partner104_cmp_on_O.txt"))
    print("--- partner on vs B ---")
    print(text("partner104_cmp_on_vs_B.txt"))
    print("--- partner honesty ---")
    print(text("partner104_HONESTY.txt"))
    print("--- partner match ---")
    print(text("partner104_match_result.txt"))
    print("--- apply ---")
    print(text("apply_check.txt"))
    print("--- stamps ---")
    print(text("stamps.txt"))


if __name__ == "__main__":
    main()
