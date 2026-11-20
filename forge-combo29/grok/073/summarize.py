#!/usr/bin/env python3
"""Print the step table from the raw files in this folder. Numbers are read, not typed."""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name):
    return (HERE / name).read_text(encoding="utf-8")


def honesty(name):
    return "; ".join(text(name).splitlines()[1:])


def compare(name):
    data = {}
    for line in text(name).splitlines():
        key, value = line.split(" ", 1)
        data[key] = value
    return data


def match_final(name):
    lines = text(name).splitlines()
    last = max(i for i, line in enumerate(lines) if line.startswith("Results of "))
    return " | ".join(lines[last : last + 4])


def main():
    off_o = compare("compare_off_O.txt")
    off_g = compare("compare_off_G.txt")
    on_o = compare("compare_on_O.txt")
    p_off = compare("partner023_compare_off.txt")
    print("step | status | evidence | result")
    print("1 seat | done | SEAT.txt stamps.txt | " + text("SEAT.txt").strip())
    print("2 honesty B | done | HONESTY_B.txt | " + honesty("HONESTY_B.txt"))
    print("2 O and G baseline | done | compare not needed; B_O_d12.rows.txt B_G_d12.rows.txt | O sum is the left sum in compare_off_O.txt " + off_o["sum_left"] + "; G sum is the left sum in compare_off_G.txt " + off_g["sum_left"])
    print("3 prediction | done | prediction.txt | committed before the patched measurements")
    print("3 apply | done | apply_check.txt idea.patch.txt | " + text("apply_check.txt").strip())
    print("3 honesty P | done | HONESTY_P.txt | " + honesty("HONESTY_P.txt"))
    print("3 off O | done | compare_off_O.txt | nodes_differ " + off_o["nodes_differ"] + " sum " + off_o["sum_right"])
    print("3 off G | done | compare_off_G.txt | nodes_differ " + off_g["nodes_differ"] + " sum " + off_g["sum_right"])
    print("3 on O | done | compare_on_O.txt | nodes_differ " + on_o["nodes_differ"] + " sum " + on_o["sum_right"])
    uci = [line for line in text("P_uci.txt").splitlines() if "IdeaS29" in line]
    print("3 uci options | done | P_uci.txt | " + " ; ".join(uci))
    print("3 sanitizer | done | P_asan_G100.meta P_asan_G100.txt P_asan_probe.txt | " + text("P_asan_G100.meta").splitlines()[-2] + " " + text("P_asan_G100.meta").splitlines()[-1] + "; AddressSanitizer lines in G100 " + str(text("P_asan_G100.txt").count("ERROR: AddressSanitizer")) + "; heap-buffer-overflow lines in probe " + str(text("P_asan_probe.txt").count("heap-buffer-overflow")))
    print("3 match | done | match_on_off.txt match_on_off.pgn | " + match_final("match_on_off.txt"))
    print("4 partner 023 | done | partner023_apply_check.txt partner023_HONESTY.txt partner023_compare_off.txt partner023_compare_on.txt partner023_match_R.txt | apply " + text("partner023_apply_check.txt").strip() + "; honesty " + honesty("partner023_HONESTY.txt") + "; off nodes_differ " + p_off["nodes_differ"] + "; on " + text("partner023_compare_on.txt").replace("\n", "; ") + "; match " + match_final("partner023_match_R.txt"))
    print("5 report | done | REPORT.md RESULT.txt | this file")


if __name__ == "__main__":
    main()
