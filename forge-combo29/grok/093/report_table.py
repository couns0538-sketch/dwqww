#!/usr/bin/env python3
"""Print the step table from the raw evidence files in this folder."""
import pathlib

here = pathlib.Path(__file__).resolve().parent


def text(name):
    return (here / name).read_text(encoding="utf-8", errors="replace").strip()


def differ_line(name):
    for line in text(name).splitlines():
        if line.startswith("differ "):
            return line
    return "missing"


def node_sum(name):
    found = []
    last = None
    for line in (here / name).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info ") and " nodes " in line:
            tail = line.split(" nodes ", 1)[1].split()[0]
            if tail.isdigit():
                last = int(tail)
        elif line.startswith("bestmove ") and last is not None:
            found.append(last)
            last = None
    return len(found), sum(found)


def elo_line(name):
    for line in text(name).splitlines():
        if line.startswith("Elo:"):
            return line
    return "missing"


off_o = differ_line("proof_off_O.txt")
off_g = differ_line("proof_off_G.txt")
on_o = differ_line("proof_on_O.txt")
on_n, on_sum = node_sum("O_P_on.raw.txt")
b_n, b_sum = node_sum("O_B_d12.raw.txt")
g_n, g_sum = node_sum("G_B_d12.raw.txt")
partner_off = differ_line("proof_partner_off.txt")
partner_on = differ_line("proof_partner_on.txt")
my_elo = elo_line("match_summary.txt")
partner_elo = elo_line("match_partner_summary.txt")
honesty_p = " ".join(text("HONESTY_P.txt").splitlines())
asan_meta = [line for line in text("G100_asan.meta").splitlines() if line.startswith("asan_symbols")]
asan_errors = sum(1 for line in (here / "G100_asan.raw.txt").read_text(encoding="utf-8", errors="replace").splitlines() if "ERROR:" in line or "runtime error" in line)
probe_errors = sum(1 for line in (here / "asan_probe.raw.txt").read_text(encoding="utf-8", errors="replace").splitlines() if "ERROR: AddressSanitizer" in line)
rows = [
    ("STEP 1 seat", "done", "SEAT.txt stamps.txt", "seat 093 idea 43"),
    ("STEP 2 honesty B and O/G", "done", "HONESTY_B.txt O_B_d12.raw.txt G_B_d12.raw.txt", f"pins match; O n {b_n} sum {b_sum}; G n {g_n} sum {g_sum}"),
    ("STEP 3 prediction", "done", "prediction.txt", "pushed before the patched measurements"),
    ("STEP 3 patch", "done", "idea.patch.txt apply_check.txt", text("apply_check.txt")),
    ("proof 1 honesty P", "done", "HONESTY_P.txt", honesty_p),
    ("proof 2 switch off", "done", "proof_off_O.txt proof_off_G.txt", f"O {off_o}; G {off_g}"),
    ("proof 3 switch on", "done", "proof_on_O.txt O_P_on.raw.txt", f"{on_o}; positions {on_n} sum {on_sum}"),
    ("proof 4 uci", "done", "uci_P.txt", " | ".join(line for line in text("uci_P.txt").splitlines() if "IdeaK4" in line)),
    ("proof 5 sanitizer", "done", "G100_asan.meta asan_probe.raw.txt", f"{asan_meta[0]}; G100 ERROR lines {asan_errors}; probe AddressSanitizer lines {probe_errors}"),
    ("STEP 3 match", "done", "match_summary.txt", my_elo),
    ("STEP 4 partner 043", "done", "proof_partner_off.txt proof_partner_on.txt match_partner_summary.txt", f"off {partner_off}; on vs their rows {partner_on}; {partner_elo}"),
    ("STEP 5 report", "done", "REPORT.md RESULT.txt", "this commit"),
]
print("step | status | evidence | result")
for row in rows:
    print(" | ".join(row))
