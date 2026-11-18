"""Check the 17-slot build against every applicable PCADC reference row."""
import argparse
import csv
from pathlib import Path

SUITES = {"G": 353, "O": 200}
SETTINGS = ("base", "fhb7", "del", "del_fhb7")
FIELDS = ["index", "fen", "nodes", "bestmove", "a25c"]


def rows(path):
    with path.open() as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path}: expected {FIELDS}, found {reader.fieldnames}")
        result = list(reader)
    metadata = Path(str(path) + ".meta").read_text().splitlines()
    if f"completed_rows {len(result)}" not in metadata:
        raise ValueError(f"{path}: missing completion marker for {len(result)} rows")
    return result


def counters(row, width):
    label, *values = row["a25c"].split()
    if label != "A25C" or len(values) != width:
        raise ValueError(f"expected A25C plus {width} counters: {row}")
    return [int(value) for value in values]


def check_pair(reference, extended, suite, setting, first20):
    rowfile = f"{suite}_{setting}.tsv"
    prior, current = rows(reference / rowfile), rows(extended / rowfile)
    expected_count = 20 if first20 else SUITES[suite]
    if len(prior) != SUITES[suite] or len(current) != expected_count:
        raise ValueError(f"{rowfile}: reference {len(prior)}, candidate {len(current)} rows")
    total = inside = 0
    for i, (a, b) in enumerate(zip(prior, current), 1):
        old, new = counters(a, 16), counters(b, 17)
        if b["index"] != str(i) or any(a[key] != b[key] for key in FIELDS[:4]) or old != new[:16]:
            raise ValueError(f"{rowfile} position {i}\nPCADC {a}\nPCADC + slot {b}")
        nodes = int(b["nodes"])
        if not (0 <= new[16] <= nodes) or (new[0] == 0 and new[16] != 0):
            raise ValueError(f"{rowfile} position {i}: invalid verification-node count: {b}")
        if new[0] != sum(new[1:7]) or new[15] != sum(new[11:15]):
            raise ValueError(f"{rowfile} position {i}: original counters do not close: {b}")
        if setting.startswith("del") and new[2] != 0:
            raise ValueError(f"{rowfile} position {i}: two-ply extension with limit -1: {b}")
        total += nodes
        inside += new[16]
    rate = 1000 * inside / total
    print(f"{suite}\t{setting}\t{len(current)}\t{total}\t{inside}\t{rate:.6f}")
    return inside, total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="complete PCADC Step 4 rows")
    parser.add_argument("extended", type=Path, help="matching rows from PCADC plus slot 16")
    parser.add_argument("--first20", action="store_true", help="check separate 20-position preflight runs")
    args = parser.parse_args()
    print("suite\tsetting\trows_equal\tnodes\tverification_nodes\tverification_per_1000")
    for suite in SUITES:
        results = {
            setting: check_pair(args.reference, args.extended, suite, setting, args.first20)
            for setting in SETTINGS
        }
        if not args.first20:
            for base, blend in (("base", "fhb7"), ("del", "del_fhb7")):
                a, total_a = results[base]
                b, total_b = results[blend]
                print(f"{suite} {blend}/{base}: normalized verification-node rate ratio "
                      f"{(b / total_b) / (a / total_a):.6f}")


if __name__ == "__main__":
    main()
