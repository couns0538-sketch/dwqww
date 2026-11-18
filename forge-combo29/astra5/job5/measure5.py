"""Run one job 5 option at one value on P, O and G and check its paired baselines."""

import argparse
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
LAB = Path(os.environ.get("ASTRA5_LAB", str(Path(__file__).resolve().parent.parent)))
sys.path.insert(0, str(LAB / "job4"))
from measure import first_difference, ladder, read, suite

PARTS = {"A": "NullMateGuard", "B": "QsNullChecks"}
P_COLS = ("requested_depth", "info_depth", "score_type", "score", "bestmove", "nodes")
SUITE_COLS = ("index", "fen", "nodes", "bestmove")


def equal(rows, reference, keys, label):
    difference = first_difference(rows, reference, keys)
    if difference:
        raise ValueError(f"{label}: {difference}")


def summarize(args, record):
    option = PARTS[args.part]
    value = args.value
    stage = args.out / args.part / ("one" if value else "zero")
    zero = args.out / args.part / "zero"
    floor = LAB / "job4/A"
    summary, rows = ladder(args.exe, stage, ("P", "PC20", option + "=" + str(value)))
    if not value:
        equal(rows, read(floor / "Floor0.tsv"), P_COLS, "P Floor0 known answer")
        summary += ", 20/20 identical to job4 Floor0"
    record(summary)
    for name, expected_count, expected_nodes in (("O", 200, 8315168), ("G", 353, 17611204)):
        rows = suite(args.exe, args.epds / (name + ".epd"), stage / (name + ".tsv"), [(option, str(value))])
        nodes = [int(row["nodes"]) for row in rows]
        if len(rows) != expected_count:
            raise ValueError(f"expected {expected_count} rows for {name}, got {len(rows)}")
        summary = f"{name} PC20 {option}={value} D12: {len(rows)} rows; nodes {sum(nodes)}; first three {nodes[:3]}"
        reference = read(zero / (name + ".tsv") if value else floor / (name + "_floor0.tsv"))
        if not value:
            equal(rows, reference, SUITE_COLS, f"{name} Floor0 known answer")
            if sum(nodes) != expected_nodes:
                raise ValueError(f"{name} expected {expected_nodes} nodes, got {sum(nodes)}")
            record(summary + f"; all {expected_count} identical to job4 Floor0")
            continue
        equal(rows, reference, ("index", "fen"), f"{name} paired row identifiers")
        base_nodes = sum(int(row["nodes"]) for row in reference)
        changed = [row["bestmove"] != base["bestmove"] for row, base in zip(rows, reference)]
        summary += f"; base {base_nodes}; ratio {sum(nodes)/base_nodes:.8f}; changed {sum(changed)}/{len(rows)}"
        if name == "G":
            counts = read(LAB / "job4/C/rows/G_F0.tsv")
            equal(reference, counts, SUITE_COLS, "job4 G_F0 counter row alignment and baseline")
            flagged = []
            for row in counts:
                fields = row["nc0"].split()
                if len(fields) != 9 or fields[0] != "NC0":
                    raise ValueError(f"invalid NC0 line at row {row['index']}")
                flagged.append(int(fields[5]) > 0)  # Slot [4] follows the NC0 tag and slots [0..3].
            if sum(flagged) != 81 or len(flagged) - sum(flagged) != 272:
                raise ValueError("job4 G_F0 slot [4] split differs from 81/272")
            changed_flagged = sum(c and f for c, f in zip(changed, flagged))
            changed_other = sum(c and not f for c, f in zip(changed, flagged))
            summary += f"; changed flagged {changed_flagged}/81; changed other {changed_other}/272"
        record(summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=PARTS)
    parser.add_argument("value", type=int, choices=(0, 1))
    parser.add_argument("exe", type=Path)
    parser.add_argument("epds", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    directory = args.out / args.part / ("one" if args.value else "zero")
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "checks.txt").open("x", encoding="utf-8") as log:
        def record(line):
            print(line, file=log, flush=True)
            print(line, flush=True)
        try:
            summarize(args, record)
        except (ValueError, OSError, RuntimeError) as error:
            record(f"STOP {args.part}: {error}")
            raise


if __name__ == "__main__":
    main()
