#!/usr/bin/env python3
"""Print the report tables from the raw files in this folder."""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent


def nodes_of(path: pathlib.Path) -> str:
    lines = path.read_text().splitlines()
    for line in reversed(lines):
        if "nodes " in line:
            return line
    return "MISSING"


def tsv_sum(path: pathlib.Path) -> tuple[int, int]:
    rows = [line.split("\t") for line in path.read_text().splitlines()[1:] if line.strip()]
    return len(rows), sum(int(row[1]) for row in rows)


def differ_line(path: pathlib.Path) -> str:
    text = path.read_text().splitlines()
    keep = [line for line in text if line.startswith(("LEFT", "RIGHT", "MINE", "THEIRS", "COMPARED", "DIFFER", "SAME", "O_", "G_", "ALL_"))]
    return "\n".join(keep)


print("HONESTY_B")
print((root / "HONESTY_B.txt").read_text().rstrip())
print("HONESTY_P")
print((root / "HONESTY_P.txt").read_text().rstrip())
print("BASE_SUMS")
print((root / "B_known_sums.txt").read_text().rstrip())
print("UCI")
print((root / "uci_options_ideak6.txt").read_text().rstrip())
print("CMP_OFF_O")
print(differ_line(root / "cmp_off_O.txt"))
print("CMP_OFF_G")
print(differ_line(root / "cmp_off_G.txt"))
print("CMP_ON_O")
print(differ_line(root / "cmp_on_O.txt"))
on_n, on_sum = tsv_sum(root / "P_on_O_d12.tsv")
print(f"ON_O_POSITIONS {on_n}")
print(f"ON_O_SUM {on_sum}")
print("ASAN")
print((root / "asan_summary.txt").read_text().rstrip())
print("MATCH")
text = (root / "match_result.txt").read_text()
for line in text.splitlines():
    if line.startswith(("Results", "Elo:", "Games:", "PGN_")):
        print(line)
print("PARTNER")
print((root / "partner_source.txt").read_text().rstrip())
for name in ("partner_cmp_off_O.txt", "partner_cmp_off_G.txt", "partner_cmp_on_vs_B.txt", "partner_cmp_on_rows.txt"):
    print(name)
    print(differ_line(root / name))
plog = (root / "partner_match_R.log").read_text()
idx = plog.rfind("Results of ")
print(plog[idx:].split("Finished match")[0].rstrip())
pgn = (root / "partner_match_R.pgn").read_text(errors="replace")
print("PARTNER_PGN_RESULTS", len(re.findall(r"(?m)^\[Result ", pgn)))
print("HONESTY_PARTNER")
for tag in ("bench11", "bench13", "bench16", "perft5"):
    print(tag, nodes_of(root / f"honesty_partner_{tag}.txt"))

print("STEP_TABLE")
print("step | status | evidence | result")
print("1 seat | done | SEAT.txt stamps.txt | seat 095 idea 45")
off_o = "DIFFER 0" in (root / "cmp_off_O.txt").read_text() and "SAME 200" in (root / "cmp_off_O.txt").read_text()
off_g = "DIFFER 0" in (root / "cmp_off_G.txt").read_text() and "SAME 353" in (root / "cmp_off_G.txt").read_text()
on = "DIFFER 200" in (root / "cmp_on_O.txt").read_text()
hon_b = "ALL_MATCH True" in (root / "HONESTY_B.txt").read_text()
hon_p = "ALL_MATCH True" in (root / "HONESTY_P.txt").read_text()
base = "O_MATCH True" in (root / "B_known_sums.txt").read_text() and "G_MATCH True" in (root / "B_known_sums.txt").read_text()
asan = "CLEAN_SANITIZER_LINES 0" in (root / "asan_summary.txt").read_text() and "asan_symbols=35" in (root / "asan_G100_d10.meta").read_text()
poison = "runtime error" in (root / "asan_poison.raw.txt").read_text()
games = (root / "match_result.txt").read_text().count("[Result ")  # pgn count is stored as a line
match_games = "PGN_RESULTS 1106" in (root / "match_result.txt").read_text()
partner_same = "DIFFER 0" in (root / "partner_cmp_on_rows.txt").read_text() and "SAME 200" in (root / "partner_cmp_on_rows.txt").read_text()
partner_off = "DIFFER 0" in (root / "partner_cmp_off_O.txt").read_text()
print(f"2 builds and honesty | {'done' if hon_b and base else 'partly'} | HONESTY_B.txt B_known_sums.txt | honesty {hon_b} base sums {base}")
print(f"3 idea proofs | {'done' if hon_p and off_o and off_g and on and asan and poison else 'partly'} | HONESTY_P.txt cmp_off_O.txt cmp_off_G.txt cmp_on_O.txt asan_summary.txt uci_options_ideak6.txt | off_o {off_o} off_g {off_g} on_differs_200 {on} asan_clean {asan} poison_reported {poison}")
print(f"3e test match | {'done' if match_games else 'partly'} | match_og.log match_og.pgn match_result.txt | games_1106 {match_games}")
print(f"4 partner | {'done' if partner_same and partner_off else 'partly'} | partner_cmp_off_O.txt partner_cmp_on_rows.txt partner_match_R.log | off_identical {partner_off} on_rows_equal {partner_same}")
print("5 report | done | REPORT.md RESULT.txt | this report")
