#!/usr/bin/env python3
"""Print the report numbers by reading the raw result files in this folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text().rstrip()


def main() -> None:
    print("HONESTY_B")
    print(text("HONESTY_B.txt"))
    print("HONESTY_P")
    print(text("HONESTY_P.txt"))
    print("O_B")
    print(text("O_d12_B.sum.txt"))
    print("G_B")
    print(text("G_d12_B.sum.txt"))
    print("O_OFF")
    print(text("compare_O_off.txt"))
    print("G_OFF")
    print(text("compare_G_off.txt"))
    print("O_ON")
    print(text("compare_O_on.txt"))
    print("O_ON_SUM")
    print(text("O_d12_P_on.sum.txt"))
    print("UCI")
    print(text("uci_options_IdeaA4.txt"))
    print("ASAN_NM")
    print(text("asan_nm_count.txt"))
    print("ASAN_G100")
    print(text("asan_G100_on.sum.txt"))
    print("ASAN_SCRATCH_NM")
    print(text("asan_scratch_nm_count.txt"))
    print("ASAN_SCRATCH_HIT")
    print(text("asan_scratch_hit.txt"))
    print("MATCH")
    print(text("match_result.txt"))
    print("OWN_APPLY")
    print(text("own_apply_check.txt"))
    print("PARTNER_APPLY")
    print(text("partner_apply_check.txt"))
    print("PARTNER_HONESTY")
    print(text("partner_HONESTY.txt"))
    print("PARTNER_OFF")
    print(text("partner_compare_off.txt"))
    print("PARTNER_ON")
    print(text("partner_compare_on.txt"))
    log = (HERE / "partner_match_r.log").read_text()
    start = log.rfind("Results of ")
    end = log.find("Finished match", start)
    print("PARTNER_MATCH")
    print(log[start:end].rstrip())
    print("Finished match")
    on_sum = text("O_d12_P_on.sum.txt").splitlines()[1]
    elo_line = [line for line in text("match_result.txt").splitlines() if line.startswith("Elo:")][0]
    games_line = [line for line in text("match_result.txt").splitlines() if line.startswith("Games:")][0]
    off_o = [line for line in text("compare_O_off.txt").splitlines() if line.startswith("differ")][0]
    off_g = [line for line in text("compare_G_off.txt").splitlines() if line.startswith("differ")][0]
    on_d = [line for line in text("compare_O_on.txt").splitlines() if line.startswith("differ")][0]
    p_off = [line for line in text("partner_compare_off.txt").splitlines() if line.startswith("node_differ")][0]
    p_on = [line for line in text("partner_compare_on.txt").splitlines() if line.startswith("node_differ")][0]
    p_games = [line for line in log[start:end].splitlines() if line.startswith("Games:")][0]
    asan_errors = (HERE / "asan_G100_on.raw.txt").read_text().count("ERROR:")
    print("TABLE")
    rows = [
        ("1 seat", "done", "SEAT.txt stamps.txt", text("SEAT.txt")),
        ("2 honesty B", "done", "HONESTY_B.txt", [line for line in text("HONESTY_B.txt").splitlines() if line.startswith("ALL")][0]),
        ("2 O depth 12 B", "done", "O_d12_B.sum.txt", " ".join(text("O_d12_B.sum.txt").splitlines())),
        ("2 G depth 12 B", "done", "G_d12_B.sum.txt", " ".join(text("G_d12_B.sum.txt").splitlines())),
        ("3 patch applies", "done", "idea.patch.txt own_apply_check.txt", text("own_apply_check.txt")),
        ("3 honesty P", "done", "HONESTY_P.txt", [line for line in text("HONESTY_P.txt").splitlines() if line.startswith("ALL")][0]),
        ("3 off O and G", "done", "compare_O_off.txt compare_G_off.txt", f"O {off_o}; G {off_g}"),
        ("3 on O", "done", "compare_O_on.txt O_d12_P_on.sum.txt", f"{on_d}; {on_sum}"),
        ("3 uci options", "done", "uci_options_IdeaA4.txt", " ".join(text("uci_options_IdeaA4.txt").splitlines())),
        ("3 sanitizer", "done", "asan_nm_count.txt asan_scratch_hit.txt", f"nm {text('asan_nm_count.txt')} asan_errors {asan_errors}"),
        ("3 match", "done", "match_result.txt match_on_off.pgn", f"{elo_line}; {games_line}"),
        ("4 partner 035", "done", "partner_compare_off.txt partner_compare_on.txt partner_match_r.log", f"off {p_off}; on {p_on}; {p_games}"),
        ("5 report", "done", "REPORT.md RESULT.txt", "written this step"),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {evidence} | {result}")


if __name__ == "__main__":
    main()
