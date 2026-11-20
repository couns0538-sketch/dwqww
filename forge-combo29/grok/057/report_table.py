#!/usr/bin/env python3
"""Print the step table from the raw files in this folder."""
from pathlib import Path

folder = Path(__file__).resolve().parent

def bench(path, label):
    for line in path.read_text().splitlines():
        if line.startswith("info string bench") or line.startswith("nodes "):
            return line
    return label + " MISSING"

def rows_sum(path):
    nodes = [int(line.split()[1]) for line in path.read_text().splitlines() if line.strip()]
    return len(nodes), sum(nodes)

def text(path):
    return path.read_text().rstrip()

bo_n, bo_s = rows_sum(folder / "B_O.rows.txt")
bg_n, bg_s = rows_sum(folder / "B_G.rows.txt")
on_n, on_s = rows_sum(folder / "P_on_O.rows.txt")
off = text(folder / "compare_off_O.txt").replace("\n", "; ")
offg = text(folder / "compare_off_G.txt").replace("\n", "; ")
on = text(folder / "compare_on_O.txt").replace("\n", "; ")
p_off = text(folder / "partner_007_off_vs_B.txt").replace("\n", "; ")
p_on = text(folder / "partner_007_on_vs_theirs.txt").replace("\n", "; ")
p_on_b = text(folder / "partner_007_on_vs_B.txt").replace("\n", "; ")
asan = text(folder / "asan_g100.meta").splitlines()
asan_note = [line for line in asan if line.startswith("note ") or line.startswith("nm_asan")]
scratch = [line for line in (folder / "asan_scratch.meta").read_text().splitlines() if line.startswith("note ")]
rows = [
    ("honesty B", "done", "HONESTY_B.txt", bench(folder / "honesty_b_bench11.txt", "b11") + " | " + bench(folder / "honesty_b_bench13.txt", "b13") + " | " + bench(folder / "honesty_b_bench16.txt", "b16") + " | " + bench(folder / "honesty_b_perft5.txt", "perft")),
    ("baseline O G", "done", "B_O.rows.txt B_G.rows.txt", f"O n {bo_n} sum {bo_s}; G n {bg_n} sum {bg_s}"),
    ("patch applies", "done", "apply_check.txt idea.patch.txt", text(folder / "apply_check.txt")),
    ("honesty P", "done", "HONESTY_P.txt", bench(folder / "honesty_p_bench11.txt", "b11") + " | " + bench(folder / "honesty_p_bench13.txt", "b13") + " | " + bench(folder / "honesty_p_bench16.txt", "b16") + " | " + bench(folder / "honesty_p_perft5.txt", "perft")),
    ("proof off O", "done", "compare_off_O.txt", off),
    ("proof off G", "done", "compare_off_G.txt", offg),
    ("proof on O", "done", "compare_on_O.txt", on + f"; sum {on_s}"),
    ("uci options", "done", "honesty_p_bench11.txt", " | ".join(line for line in (folder / "honesty_p_bench11.txt").read_text().splitlines() if "IdeaS31" in line)),
    ("sanitizer G100", "done", "asan_g100.meta asan_g100.stderr.txt", "; ".join(asan_note) + "; stderr bytes " + str((folder / "asan_g100.stderr.txt").stat().st_size)),
    ("sanitizer scratch", "done", "asan_scratch.stderr.txt asan_scratch.meta", "; ".join(scratch)),
    ("match on vs off", "done", "match_summary.txt match_on_off.log match_on_off.pgn", text(folder / "match_summary.txt").splitlines()[1]),
    ("partner 007", "done", "partner_007_off_vs_B.txt partner_007_on_vs_theirs.txt partner_007_on_vs_B.txt", "off " + p_off + " | on vs theirs " + p_on + " | on vs B " + p_on_b),
    ("partner R match", "done", "match_partner_summary.txt", text(folder / "match_partner_summary.txt").splitlines()[1]),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
