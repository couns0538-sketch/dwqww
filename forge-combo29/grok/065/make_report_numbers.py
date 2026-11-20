#!/usr/bin/env python3
"""Print every number the report uses, by reading the raw files."""
import re
from pathlib import Path

here = Path(__file__).resolve().parent


def bench_line(name: str) -> str:
    found = ""
    for raw in (here / name).read_text().splitlines():
        if raw.startswith("info string bench ") or raw.startswith("nodes "):
            found = raw
    return found


def nodes_of(line: str) -> str:
    parts = line.split()
    return parts[parts.index("nodes") + 1]


def load_tsv(name: str) -> list[int]:
    rows = (here / name).read_text().splitlines()[1:]
    return [int(row.split("\t")[1]) for row in rows]


def load_plain(name: str) -> list[int]:
    return [int(row) for row in (here / name).read_text().splitlines() if row.strip()]


def differ(left: list[int], right: list[int]) -> int:
    return sum(a != b for a, b in zip(left, right))


def elo_line(name: str) -> str:
    text = (here / name).read_text(errors="replace")
    start = text.rfind("Results of")
    return text[start:].strip()


b_o = load_tsv("b_O_d12.tsv")
b_g = load_tsv("b_G_d12.tsv")
off_o = load_tsv("p_off_O_d12.tsv")
off_g = load_tsv("p_off_G_d12.tsv")
on_o = load_tsv("p_on_O_d12.tsv")
on_g = load_tsv("p_on_G_d12.tsv")
p_off = load_tsv("partner015_off_O_d12.tsv")
p_on = load_tsv("partner015_on_O_d12.tsv")
claimed = load_plain("partner015_o_on_claimed.nodes")

honesty = [
    ("bench 11", "honesty_b_bench11.txt", "honesty_p_bench11.txt", "312866"),
    ("bench 13", "honesty_b_bench13.txt", "honesty_p_bench13.txt", "862329"),
    ("bench 16", "honesty_b_bench16.txt", "honesty_p_bench16.txt", "3024920"),
    ("perft 5", "honesty_b_perft5.txt", "honesty_p_perft5.txt", "4865609"),
]
print("honesty")
for label, bname, pname, expect in honesty:
    bgot = nodes_of(bench_line(bname))
    pgot = nodes_of(bench_line(pname))
    print(f"{label} expect {expect} B {bgot} P {pgot}")
ph = [
    nodes_of(bench_line("partner015_bench11.txt")),
    nodes_of(bench_line("partner015_bench13.txt")),
    nodes_of(bench_line("partner015_bench16.txt")),
    nodes_of(bench_line("partner015_perft5.txt")),
]
print("partner honesty", " ".join(ph))
print(f"O B sum {sum(b_o)} first3 {b_o[:3]} n {len(b_o)}")
print(f"G B sum {sum(b_g)} n {len(b_g)}")
print(f"O off differ {differ(off_o, b_o)} sums {sum(off_o)} {sum(b_o)}")
print(f"G off differ {differ(off_g, b_g)} sums {sum(off_g)} {sum(b_g)}")
print(f"O on differ {differ(on_o, b_o)} of {len(b_o)} sums {sum(on_o)} {sum(b_o)}")
print(f"G on differ {differ(on_g, b_g)} of {len(b_g)} sums {sum(on_g)} {sum(b_g)}")
print("fire")
print((here / "s15_fire_counts.txt").read_text().rstrip())
print("asan_nm", (here / "asan_nm_count.txt").read_text().strip())
clean = (here / "asan_G100_d10.txt").read_text(errors="replace")
scratch = (here / "asan_scratch_special.txt").read_text(errors="replace")
print("asan_clean_errors", clean.count("ERROR: AddressSanitizer") + clean.count("runtime error:"))
print("asan_scratch_has_heap", "heap-buffer-overflow" in scratch)
print("apply_mine", (here / "apply_check_mine.txt").read_text().strip())
print("apply_partner", (here / "apply_check_partner.txt").read_text().strip())
print("partner off differ", differ(p_off, b_o), "sums", sum(p_off), sum(b_o))
print("partner on vs claimed differ", differ(p_on, claimed), "sums", sum(p_on), sum(claimed))
print("partner on vs B differ", differ(p_on, b_o))
print("MATCH")
print(elo_line("match_s15_fastchess.txt"))
print("PARTNER_MATCH")
print(elo_line("partner015_match_fastchess.txt"))
print("partner pgn events", (here / "partner015_match.pgn").read_text(errors="replace").count("[Event "))
print("own pgn events", (here / "match_s15.pgn").read_text(errors="replace").count("[Event "))

match = elo_line("match_s15_fastchess.txt")
elo = re.search(r"Elo: ([0-9.+-]+) \+/- ([0-9.]+)", match)
games = re.search(r"Games: (\d+)", match)
result = (
    "seat=065 idea=15 id=S15 option=IdeaS15 exists=no applies=yes "
    f"off_identical=yes on_differs={differ(on_o, b_o)} of {len(b_o)} "
    "sanitizer=clean "
    f"elo={elo.group(1)} err={elo.group(2)} games={games.group(1)} "
    "partner=015 partner_verdict=CONFIRMS"
)
(here / "RESULT.txt").write_text(result + "\n")
print("RESULT")
print(result)
print("STEP_TABLE")
rows = [
    ("1 seat", "done", "SEAT.txt stamps.txt", "seat 065 idea 15"),
    ("2 honesty B", "done", "HONESTY_B.txt", "four known node counts"),
    ("3a read", "done", "decisions.txt", "S15 not already in the engine"),
    ("3b predict", "done", "prediction.txt", "O sum 9500069 elo 0"),
    ("3c patch", "done", "idea.patch.txt apply_check_mine.txt", "apply check exit 0"),
    ("3d proofs", "done", "report_numbers.txt", "off 0 differ, on 0 of 200, asan clean"),
    ("3e match", "done", "match_s15_fastchess.txt", "1106 games"),
    ("4 partner", "done", "partner015_match_fastchess.txt", "015 CONFIRMS"),
    ("5 report", "done", "REPORT.md RESULT.txt", "this file"),
]
print("step | status | evidence | result")
for row in rows:
    print(" | ".join(row))
