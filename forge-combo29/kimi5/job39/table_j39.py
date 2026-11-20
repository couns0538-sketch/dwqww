#!/usr/bin/env python3
"""kimi5 job 39 step 5: the table. Reads canonical game files, prints how many lines it
read per file, counts every ending, and prints the readings of file 39.
Rows: OFF (ours, K3) / OFF (yours) / DeadMaterial (ours, K4) / ON / C-PLANT, at
go softnodes 2000 and go nodes 50000 where run. "Ours" rows are the known answers of
file 39 (no per-game text of theirs exists here, so per-kind mate mean plies is n/a).
Usage: table_j39.py <jobdir>   (jobdir = folder with the canonical files)
"""
import os
import sys

JOB = sys.argv[1]

def read_canon(path):
    lines = []
    with open(path, encoding="ascii") as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                lines.append(line)
    print(f"read {len(lines)} lines from {os.path.basename(path)}")
    rows = []
    for line in lines:
        kind, fen, result, plies, final = line.split("|")
        rows.append((kind, fen, result, int(plies), final))
    return rows

def stats(rows, label):
    kinds = ("KQ", "KR", "KBN")
    mates = {k: 0 for k in kinds}
    mate_plies = {k: [] for k in kinds}
    other = {"fifty": 0, "repetition": 0, "stalemate": 0, "insufficient": 0, "cap": 0}
    plies_sum = 0
    for kind, fen, result, plies, final in rows:
        plies_sum += plies
        if result == "mate":
            mates[kind] += 1
            mate_plies[kind].append(plies)
        else:
            other[result] = other.get(result, 0) + 1
    means = {k: (f"{sum(v) / len(v):.1f}" if v else "-") for k, v in mate_plies.items()}
    return {"label": label, "mates": mates, "other": other, "plies_sum": plies_sum, "means": means, "rows": rows}

def print_row(s):
    o = s["other"]
    print(f"| {s['label']} | {s['mates']['KQ']} | {s['mates']['KR']} | {s['mates']['KBN']} | "
          f"{o.get('fifty', 0)} | {o.get('repetition', 0)} | {o.get('stalemate', 0)} | "
          f"{o.get('insufficient', 0)} | {o.get('cap', 0)} | {s['plies_sum']} | "
          f"{s['means']['KQ']} | {s['means']['KR']} | {s['means']['KBN']} |")

# Known answers of file 39 (theirs), as constants: (mates KQ/KR/KBN, fifty, repetition, plies sum)
OURS_SN = {"label": "OFF (ours, K3) sn2000", "mates": {"KQ": 43, "KR": 35, "KBN": 4},
           "other": {"fifty": 96, "repetition": 2, "stalemate": 0, "insufficient": 0, "cap": 0},
           "plies_sum": 12888, "means": {"KQ": "n/a", "KR": "n/a", "KBN": "n/a"}}
OURS_N50 = {"label": "OFF (ours, K3) n50000", "mates": {"KQ": 59, "KR": 60, "KBN": 23},
            "other": {"fifty": 35, "repetition": 3, "stalemate": 0, "insufficient": 0, "cap": 0},
            "plies_sum": 8295, "means": {"KQ": "n/a", "KR": "n/a", "KBN": "n/a"}}
DM_SN = {"label": "DeadMaterial (ours, K4) sn2000", "mates": {"KQ": 43, "KR": 35, "KBN": 41},
         "other": {"fifty": 60, "repetition": 1, "stalemate": 0, "insufficient": 0, "cap": 0},
         "plies_sum": 11707, "means": {"KQ": "n/a", "KR": "n/a", "KBN": "n/a"}}

runs = [OURS_SN]
mine_off_sn = None
if os.path.exists(f"{JOB}/k3/plain_sn2000.txt"):
    mine_off_sn = stats(read_canon(f"{JOB}/k3/plain_sn2000.txt"), "OFF (yours) sn2000")
    runs.append(mine_off_sn)
runs.append(DM_SN)
on_sn = stats(read_canon(f"{JOB}/games/on_sn2000.txt"), "ON sn2000")
runs.append(on_sn)
plant = stats(read_canon(f"{JOB}/games/plant_on_sn2000.txt"), "C-PLANT ON sn2000 (120 games: KQ+KR only)")
runs.append(plant)
runs.append(OURS_N50)
off_n50 = stats(read_canon(f"{JOB}/games/off_n50000.txt"), "OFF (yours) n50000")
runs.append(off_n50)
on_n50 = stats(read_canon(f"{JOB}/games/on_n50000.txt"), "ON n50000")
runs.append(on_n50)

print()
print("| run | mates KQ /60 | KR /60 | KBN /60 | fifty | repetition | stalemate | insufficient | cap | plies sum | mean plies mated KQ | KR | KBN |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for s in runs:
    print_row(s)

print()
print("## ON games that did NOT end in mate, both limits")
for s in (on_sn, on_n50):
    n = 0
    for kind, fen, result, plies, final in s["rows"]:
        if result != "mate":
            n += 1
            print(f"{s['label']}: {kind}|{fen}|{result}|{plies}|{final}")
    print(f"{s['label']}: {n} non-mate games")

print()
print("## readings")
kq, kr = on_sn["mates"]["KQ"], on_sn["mates"]["KR"]
verdict = "THE GUARD MATES" if (kq >= 58 and kr >= 58) else "THE GUARD DOES NOT"
print(f"ON sn2000 mates: KQ {kq}/60, KR {kr}/60 -> {verdict} (bar: >= 58 of 60 for both)")
kbn = on_sn["mates"]["KBN"]
print(f"KBN: ON {kbn} vs DeadMaterial's 41 at sn2000 (counts, no verdict per file 39)")
