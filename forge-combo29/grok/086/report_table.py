#!/usr/bin/env python3
"""Step table. Each result cell is read from a file in this folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def grab(name: str, needle: str) -> str:
    for line in (HERE / name).read_text(errors="replace").splitlines():
        if needle in line:
            return line.strip()
    raise SystemExit(f"{needle} not in {name}")


rows = [
    ("1 seat", "done", "SEAT.txt", (HERE / "SEAT.txt").read_text().strip()),
    ("2 honesty B", "done", "HONESTY_B.txt", grab("HONESTY_B.txt", "ALL_OK")),
    ("2 O depth 12 B", "done", "B_O_d12.nodes", grab("proof_summary.out", "off_O")),
    ("2 G depth 12 B", "done", "B_G_d12.nodes", grab("proof_summary.out", "off_G")),
    ("3 prediction", "done", "prediction.txt", "pushed before any exe P search"),
    ("3 patch applies", "done", "apply_check.txt", grab("apply_check.txt", "exit=")),
    ("3 proof off", "done", "P_off_O_d12.nodes P_off_G_d12.nodes", grab("proof_summary.out", "off_O") + " ; " + grab("proof_summary.out", "off_G")),
    ("3 proof on", "done", "P_on_O_d12.nodes", grab("proof_summary.out", "on_O differ")),
    ("3 uci options", "done", "P_uci.txt", grab("proof_summary.out", "IdeaA5 type check")),
    ("3 sanitizer", "done", "asan_G100_d10.raw asan_scratch.raw", grab("proof_summary.out", "asan_error_lines") + " ; " + grab("proof_summary.out", "scratch_heap")),
    ("3 match", "done", "match_OG.out match_final.txt", grab("match_final.txt", "Elo:")),
    ("4 partner", "done", "partner_compare.out partner_match_final.txt", grab("partner_compare.out", "partner_on_vs_claim") + " ; " + grab("partner_match_final.txt", "Games:")),
    ("5 report", "done", "REPORT.md RESULT.txt", "this commit"),
]
print("step | status | evidence | result")
for row in rows:
    print(" | ".join(row))
