"""Recount raw NC0 rows and check the search identity against paired uncounted rows."""
import argparse
import csv
import sys
from pathlib import Path


SIZES = {"O_F0": 200, "G_F0": 353, "P_F0": 1, "G_F1": 353}
P = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
KEYS = ("index", "fen", "nodes", "bestmove")
LABELS = (
    "Null searches started",
    "Starts at child depth ≤0",
    "All actual null cutoffs",
    "Cutoffs at child depth ≤0",
    "Cutoffs at child depth ≤0 with a quiet mate in one",
    "All actual null cutoffs (repeated denominator)",
    "Cutoffs at child depth 1 or 2",
    "Cutoffs at child depth 1 or 2 with a quiet mate in one",
)


def load(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def reference_rows(path, case):
    rows = load(path)
    if case == "P_F0" and rows and "requested_depth" in rows[0]:
        rows = [dict(row, index="1", fen=P) for row in rows if int(row["requested_depth"]) == 16]
    return rows


def validate(path, reference):
    case = path.stem
    count = SIZES[case]
    rows = load(path)
    ref = reference_rows(reference, case) if reference else None
    if ref is not None:
        for i in range(max(len(rows), len(ref))):
            observed = rows[i] if i < len(rows) else None
            expected = ref[i] if i < len(ref) else None
            if observed is None or expected is None or any(observed[k] != expected[k] for k in KEYS):
                raise ValueError(f"{case}: first differing row {i + 1}\nobserved {observed}\nreference {expected}")
    if len(rows) != count:
        raise ValueError(f"{case}: read {len(rows)} rows, expected {count}")
    totals = [0] * 8
    nodes = 0
    starts12 = 0
    positions4 = []
    positions7 = []
    for i, row in enumerate(rows, 1):
        if row["index"] != str(i):
            raise ValueError(f"{case}: unexpected row index at {i}: {row}")
        values = row["nc0"].split()
        if len(values) != 9 or values[0] != "NC0" or any(not x.isdecimal() for x in values[1:]):
            raise ValueError(f"{case}: malformed NC0 in row {i}: {row}")
        slots = list(map(int, values[1:]))
        c0, c1, c2, c3, c4, c5, c6, c7 = slots
        started12 = int(row["started_1_2"])
        if not (0 <= started12 <= c0 and c1 + started12 <= c0 and c2 == c5 <= c0
                and c3 <= c1 and c6 <= started12 and c3 + c6 <= c2 and c4 <= c3 and c7 <= c6):
            raise ValueError(f"{case}: subset accounting fails in row {i}: {row}")
        if case.endswith("F1") and any((c1, c3, c4)):
            raise ValueError(f"{case}: floor-one child depth ≤0 in row {i}: {row}")
        if case == "P_F0" and (row["fen"] != P or c4 < 1):
            raise ValueError(f"{case}: expected supplied P, depth 16, [4] ≥1; counted row {row}")
        n = int(row["nodes"])
        if n <= 0:
            raise ValueError(f"{case}: non-positive nodes in row {i}: {row}")
        totals = [a + b for a, b in zip(totals, slots)]
        nodes += n
        starts12 += started12
        if c4:
            positions4.append(i)
        if c7:
            positions7.append(i)
    return case, nodes, totals, positions4, positions7, starts12, ref is not None


def report(results):
    print("PC with the null-floor and counter patches, PC20, Threads 1, Hash 16, built-in evaluation. "
          "O and G use depth 12; P uses depth 16.")
    print("\n| Suite, floor | NC0 lines read | Nodes | Searches with [4] | Searches with [7] | "
          "Starts at child depth 1–2 | Search rows equal reference |")
    print("|---|---:|---:|---:|---:|---:|---|")
    for case, nodes, _, pos4, pos7, starts12, compared in results:
        print(f"| {case} | {SIZES[case]} | {nodes:,} | {len(pos4)} | {len(pos7)} | {starts12:,} | "
              f"{'all' if compared else 'uncompared'} |")
    print("\nEach cell gives the raw total followed by events per 1,000 nodes in parentheses.\n")
    print("| Slot | Event | " + " | ".join(r[0] for r in results) + " |")
    print("|---:|---|" + "---:|" * len(results))
    for slot, label in enumerate(LABELS):
        cells = [f"{totals[slot]:,} ({1000 * totals[slot] / nodes:.6f})"
                 for _, nodes, totals, *_ in results]
        print(f"| [{slot}] | {label} | " + " | ".join(cells) + " |")
    print("\nPosition indices are 1-based, in the original suite order.")
    for case, _, _, positions4, positions7, *_ in results:
        print(f"{case}: [4] {positions4}; [7] {positions7}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("check", help="validate and summarize one completed count file")
    one.add_argument("rows", type=Path)
    one.add_argument("--reference", type=Path)
    table = sub.add_parser("table", help="validate all completed runs and print the report tables")
    table.add_argument("rows_dir", type=Path, help="directory with {O_F0,G_F0,P_F0,G_F1}.tsv")
    table.add_argument("a_dir", type=Path, help="uncounted Part A reference directory")
    table.add_argument("--d-dir", type=Path, help="uncounted Part D directory, to check G_F1 as well")
    args = parser.parse_args()
    if args.cmd == "check":
        if args.rows.stem.endswith("F0") and not args.reference:
            parser.error("floor zero requires --reference from uncounted Part A")
        report([validate(args.rows, args.reference)])
    else:
        refs = {"O_F0": args.a_dir / "O_floor0.tsv", "G_F0": args.a_dir / "G_floor0.tsv",
                "P_F0": args.a_dir / "Floor0.tsv",
                "G_F1": args.d_dir / "G_floor1.tsv" if args.d_dir else None}
        report([validate(args.rows_dir / f"{case}.tsv", refs[case]) for case in SIZES])


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError) as exc:
        sys.exit(str(exc))
