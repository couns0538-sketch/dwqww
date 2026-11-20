#!/usr/bin/env python3
"""Print report numbers by reading the raw result files in this folder."""
import os

here = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(here, name)) as handle:
        return handle.read().rstrip("\n")


def section(title, body):
    print(title)
    print(body)
    print()


section("HONESTY_B", "\n".join(read("HONESTY_B.txt").splitlines()[:9]))
section("HONESTY_P", read("HONESTY_P.txt"))
section("PROOF_O", read("proof_o.txt"))
section("PROOF_G", read("proof_g.txt"))
section("UCI_NEW_OPTIONS", read("uci_p_new_options.txt"))
section("APPLY_CHECK", read("apply_check.txt"))
section("ASAN_NM", read("asan_nm_count.txt"))
section("ASAN_CLEAN_LINES", read("asan_g100_sanitizer_lines.txt"))
section("ASAN_SCRATCH", read("asan_scratch_result.txt"))
section("MATCH_OG", read("match_og_result.txt"))
section("MATCH_R", read("match_r.txt").split("Results of ")[-1])
section("PARTNER_FETCH", read("partner_fetch.txt"))

def field(text, prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1]
    return "missing"


def diff_line(text, label):
    hits = [line for line in text.splitlines() if line.startswith("diff " + label)]
    for line in hits:
        if " differ=" in line:
            return line
    return hits[-1] if hits else "missing"


proof_o = read("proof_o.txt")
proof_g = read("proof_g.txt")
honesty_b = read("HONESTY_B.txt")
honesty_p = read("HONESTY_P.txt")
match_og = read("match_og_result.txt")
match_r = read("match_r.txt")
rows = [
    ("1 seat", "done", "SEAT.txt", read("SEAT.txt")),
    ("2 honesty B", "done", "HONESTY_B.txt", field(honesty_b, "result=")),
    ("3 prediction", "done", "prediction.txt", "file present"),
    ("3 patch", "done", "apply_check.txt", field(read("apply_check.txt"), "apply_check_exit=")),
    ("3 honesty P", "done", "HONESTY_P.txt", field(honesty_p, "result=")),
    ("3 off O", "done", "proof_o.txt", diff_line(proof_o, "o_p_off")),
    ("3 off G", "done", "proof_g.txt", diff_line(proof_g, "g_p_off")),
    ("3 on default", "done", "proof_o.txt", diff_line(proof_o, "o_p_on")),
    ("3 cap 0", "done", "proof_o.txt", diff_line(proof_o, "o_p_cap0")),
    ("3 uci", "done", "uci_p_new_options.txt", read("uci_p_new_options.txt").replace("\n", " | ")),
    ("3 asan nm", "done", "asan_nm_count.txt", read("asan_nm_count.txt").splitlines()[0]),
    ("3 asan clean", "done", "asan_g100_sanitizer_lines.txt", read("asan_g100_sanitizer_lines.txt")),
    ("3 asan scratch", "done", "asan_scratch_result.txt", "runner_exit=" + field(read("asan_scratch_result.txt"), "runner_exit=")),
    ("3 match", "done", "match_og_result.txt", next(line for line in match_og.splitlines() if line.startswith("Elo:"))),
    ("4 partner patch", "not done", "partner_fetch.txt", read("partner_fetch.txt").replace("\n", " | ")),
    ("4 second match", "done", "match_r.txt", next(line for line in match_r.splitlines() if line.startswith("Elo:"))),
]
print("STEP_TABLE")
print("step | status | evidence | result")
for row in rows:
    print(" | ".join(row))
