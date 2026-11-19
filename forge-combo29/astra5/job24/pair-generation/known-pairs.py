"""Compare all values of the four published Job 24 endpoint vectors with the generated TSV."""
import argparse
import csv
from hashlib import sha256
from pathlib import Path
import re


def check(table, handoff):
    with table.open(newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    if len(rows) != 81 or any(len(row) != 81 for row in rows):
        raise ValueError("expected a header and 80 rows, with 81 columns each")
    text = handoff.read_text()
    for j in (1, 80):
        for suffix, columns in (("+", slice(1, 41)), ("-", slice(41, 81))):
            name = f"P{j}{suffix}"
            pattern = r"^" + re.escape(name) + r"\s*=\s*((?:\d+[ \t\r\n]+){39}\d+)"
            match = re.search(pattern, text, re.M)
            if not match:
                raise ValueError(f"missing reference {name}")
            expected = match[1].split()
            actual = rows[j][columns]
            if rows[j][0] != str(j) or actual != expected:
                raise ValueError(f"{name} differs\nactual {' '.join(actual)}\nexpected {' '.join(expected)}")
            print(f"{name} 40/40 equal  {' '.join(actual)}")
    print(f"80 pair sets, 40 plus and 40 minus values each. TSV SHA-256 {sha256(table.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", type=Path)
    parser.add_argument("handoff", type=Path)
    args = parser.parse_args()
    check(args.table, args.handoff)
