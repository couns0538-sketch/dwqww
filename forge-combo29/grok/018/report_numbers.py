#!/usr/bin/env python3
"""Print the report numbers by reading the raw files in this folder."""
import pathlib
import re

folder = pathlib.Path(__file__).resolve().parent

def tail_nodes(name):
    text = (folder / name).read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(text):
        if "nodes " in line:
            return line
    return "(no nodes line)"

print("HONESTY_B")
for name in ("honesty_b_bench11.txt", "honesty_b_bench13.txt", "honesty_b_bench16.txt", "honesty_b_perft5.txt"):
    print(tail_nodes(name))
print("HONESTY_P")
for name in ("honesty_p_bench11.txt", "honesty_p_bench13.txt", "honesty_p_bench16.txt", "honesty_p_perft5.txt"):
    print(tail_nodes(name))
print("COMPARE")
for name in ("compare_off_O.txt", "compare_off_G.txt", "compare_on_O.txt"):
    print(name, (folder / name).read_text(encoding="utf-8").strip())
print("O_FIRST3")
rows = []
for line in (folder / "b_O_d12.tsv").read_text(encoding="utf-8").splitlines()[1:]:
    parts = line.split("\t")
    if parts and parts[0].isdigit():
        rows.append(parts[1])
    if len(rows) == 3:
        break
print(" ".join(rows))
print("O_SUMS")
for name in ("b_O_d12.tsv", "p_off_O_d12.tsv", "p_on_O_d12.tsv", "b_G_d12.tsv", "p_off_G_d12.tsv"):
    last = (folder / name).read_text(encoding="utf-8").strip().splitlines()[-1]
    print(name, last)
print("ASAN")
print("hits", (folder / "asan_G100_hits.txt").read_text(encoding="utf-8").strip())
meta = (folder / "asan_G100_d10.meta").read_text(encoding="utf-8")
for line in meta.splitlines():
    if line.startswith("asan_symbols") or line.startswith("positions") or line.startswith("depth"):
        print(line)
def last_block(text):
    lines = text.splitlines()
    idxs = [i for i, line in enumerate(lines) if line.startswith("Results of")]
    if not idxs:
        return
    for line in lines[idxs[-1]:]:
        if line.startswith("Results of") or line.startswith("Elo:") or line.startswith("Games:"):
            print(line)

print("MATCH")
log = (folder / "match_OG.log").read_text(encoding="utf-8", errors="replace")
last_block(log)
print("PARTNER_HONESTY")
for name in ("partner_honesty_bench11.txt", "partner_honesty_bench13.txt", "partner_honesty_bench16.txt", "partner_honesty_perft5.txt"):
    print(tail_nodes(name))
print("PARTNER_COMPARE")
for name in ("partner_compare_off_O.txt", "partner_compare_on_O.txt", "partner_apply_check.txt"):
    print(name, (folder / name).read_text(encoding="utf-8").strip())
print("PARTNER_MATCH")
plog = (folder / "partner_match_R.log").read_text(encoding="utf-8", errors="replace")
last_block(plog)
elo_lines = re.findall(r"^Elo: ([+-]?\d+\.\d+) \+/- ([+-]?\d+\.\d+)", log, re.M)
elo = elo_lines[-1] if elo_lines else None
differ = re.search(r"differ (\d+)", (folder / "compare_on_O.txt").read_text(encoding="utf-8"))
print("STEPS")
print("step | status | evidence | result")
off_o = (folder / "compare_off_O.txt").read_text(encoding="utf-8").strip()
off_g = (folder / "compare_off_G.txt").read_text(encoding="utf-8").strip()
on_o = (folder / "compare_on_O.txt").read_text(encoding="utf-8").strip()
hits = (folder / "asan_G100_hits.txt").read_text(encoding="utf-8").strip()
symbols = [ln for ln in (folder / "asan_G100_d10.meta").read_text(encoding="utf-8").splitlines() if ln.startswith("asan_symbols")][0]
apply_exit = (folder / "apply_check.txt").read_text(encoding="utf-8").strip()
pon = [ln for ln in (folder / "p_on_O_d12.tsv").read_text(encoding="utf-8").splitlines() if ln.startswith("SUM")][0]
bo = [ln for ln in (folder / "b_O_d12.tsv").read_text(encoding="utf-8").splitlines() if ln.startswith("SUM")][0]
bg = [ln for ln in (folder / "b_G_d12.tsv").read_text(encoding="utf-8").splitlines() if ln.startswith("SUM")][0]
uci = [ln for ln in (folder / "uci_p.txt").read_text(encoding="utf-8").splitlines() if "IdeaS16" in ln]
partner_off = (folder / "partner_compare_off_O.txt").read_text(encoding="utf-8").strip()
partner_on = (folder / "partner_compare_on_O.txt").read_text(encoding="utf-8").strip()
partner_apply = (folder / "partner_apply_check.txt").read_text(encoding="utf-8").strip()
rows = [
    ("1 seat", "done", "SEAT.txt", (folder / "SEAT.txt").read_text(encoding="utf-8").strip()),
    ("2 honesty", "done", "HONESTY_B.txt honesty_p_*.txt", "see HONESTY_B and HONESTY_P above"),
    ("2 baseline", "done", "b_O_d12.tsv b_G_d12.tsv", bo + " ; " + bg),
    ("3 apply", "done", "apply_check.txt idea.patch.txt", apply_exit),
    ("3 off", "done", "compare_off_O.txt compare_off_G.txt", off_o + " ; " + off_g),
    ("3 on", "done", "compare_on_O.txt p_on_O_d12.tsv", on_o + " ; " + pon),
    ("3 uci", "done", "uci_p.txt", " | ".join(uci)),
    ("3 sanitizer", "done", "asan_G100_d10.meta asan_G100_hits.txt asan_scratch.raw", symbols + " hits " + hits),
    ("3 match", "done", "match_OG.log", f"elo {elo[0]} err {elo[1]}"),
    ("4 partner", "done", "partner_apply_check.txt partner_compare_off_O.txt partner_compare_on_O.txt partner_match_R.log", partner_apply + " ; " + partner_off + " ; " + partner_on),
]
for row in rows:
    print(" | ".join(row))
print("RESULT_FIELDS")
if elo and differ:
    print(f"elo={elo[0]} err={elo[1]} on_differs={differ.group(1)} of 200")
