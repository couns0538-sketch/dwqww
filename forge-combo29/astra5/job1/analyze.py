"""Verify depth-12 rows and summarize depth-14 pairs from the astra5 job 1 harness."""

import argparse
import csv
import hashlib
import random
import re
import sys
from fractions import Fraction
from pathlib import Path


# Each entry is (sum, first three node counts, node digest, move digest).
EXPECTED_12 = {
    "O_base": (8315168, [21812, 26844, 35173], "fd609b7b1a8dd179", "14583c86b5f56cb6"),
    "O_fhb7": (7913480, [18623, 19820, 32078], "75509856e2b96287", "1ec0bb858b7ca372"),
    "G_base": (17611204, [31779, 46086, 84457], "60b6916f01395e99", "0846f027e7e9b77e"),
    "G_fhb7": (15879039, [30412, 57137, 44902], "48255179b3c50754", "6c7dc5dc109bdd8b"),
    "O_sd20_base": (7872425, [15316, 35349, 27851], "b3acd46e92320d05", "296c7c69b055cfd1"),
    "O_sd20_fhb7": (8464273, [26752, 32523, 30913], "56bf264a91c83fac", "451b92ec02705bfe"),
    "G_sd20_base": (9785780, [23141, 9625, 24306], "ba892ddade29aaa0", "5755b8f1445c16b6"),
    "G_sd20_fhb7": (10512013, [31876, 12304, 35729], "71bddd29608380cb", "53bc895f0cea1f02"),
}
EXPECTED_14 = {"O": (19377109, 18799184), "G": (41052503, 38199553)}
SIZES = {"O": 200, "G": 353}
SEED = 20261118


def read_rows(path, suite):
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != ["index", "fen", "nodes", "bestmove"]:
            raise ValueError(f"{path}: unexpected header {reader.fieldnames}")
        for index, row in enumerate(reader, start=1):
            if None in row or None in row.values() or row["index"] != str(index):
                raise ValueError(f"{path}: malformed row or index at position {index}: {row}")
            nodes = int(row["nodes"])
            if nodes < 0 or not row["bestmove"] or not row["fen"]:
                raise ValueError(f"{path}: missing move, FEN, or invalid nodes at position {index}: {row}")
            rows.append((row["fen"], nodes, row["bestmove"]))
    if len(rows) != SIZES[suite]:
        raise ValueError(f"{path}: read {len(rows)} rows, expected {SIZES[suite]}")
    return rows


def digest(values):
    payload = "".join(f"{value}\n" for value in values)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]


def check(path):
    match = re.fullmatch(r"(([OG])_(?:sd20_)?(?:base|fhb7))_d12\.tsv", path.name)
    if not match:
        raise ValueError(f"unexpected depth-12 filename: {path.name}")
    key, suite = match.groups()
    rows = read_rows(path, suite)
    nodes = [row[1] for row in rows]
    actual = (sum(nodes), nodes[:3], digest(nodes), digest(row[2] for row in rows))
    expected = EXPECTED_12[key]
    print(f"PCA {path.name} rows={len(rows)} sum={actual[0]} first3={actual[1]} "
          f"n={actual[2]} m={actual[3]} {'EQUAL' if actual == expected else 'MISMATCH'}")
    if actual != expected:
        print(f"expected sum={expected[0]} first3={expected[1]} n={expected[2]} m={expected[3]}")
        return False
    return True


def paired_interval(base, treatment):
    rng = random.Random(SEED)
    ratios = []
    count = len(base)
    for _ in range(4000):
        base_sum = treatment_sum = 0
        for _ in range(count):
            position = rng.randrange(count)
            base_sum += base[position]
            treatment_sum += treatment[position]
        ratios.append(treatment_sum / base_sum)
    ratios.sort()
    return ratios[100], ratios[3899]


def pair(args):
    if args.bounds and args.bounds[0] > args.bounds[1]:
        raise ValueError("prediction bounds out of order")
    suite = args.suite
    prefix = suite + ("_sd20" if args.sd20 else "")
    base_path = args.directory / f"{prefix}_base_d14.tsv"
    trial_path = args.directory / f"{prefix}_fhb7_d14.tsv"
    base = read_rows(base_path, suite)
    trial = read_rows(trial_path, suite)
    for index, (b, t) in enumerate(zip(base, trial), start=1):
        if b[0] != t[0]:
            raise ValueError(f"FEN mismatch at position {index}: {base_path.name} {b}, {trial_path.name} {t}")
    base_nodes = [b[1] for b in base]
    trial_nodes = [t[1] for t in trial]
    sums = sum(base_nodes), sum(trial_nodes)
    ratio = Fraction(sums[1], sums[0])
    ci_low, ci_high = paired_interval(base_nodes, trial_nodes)
    move_changes = sum(b[2] != t[2] for b, t in zip(base, trial))
    print(f"PCA {'PC20+SingularDepth20' if args.sd20 else 'PC20'} suite={suite} depth=14")
    print(f"{base_path.name} rows={len(base)} sum={sums[0]}")
    print(f"{trial_path.name} rows={len(trial)} sum={sums[1]}")
    print(f"fhb7/base={float(ratio):.9f} paired_bootstrap=[{ci_low:.9f}, {ci_high:.9f}] "
          f"seed={SEED} resamples=4000 indices=100,3899 different_bestmoves={move_changes}")
    if args.bounds:
        low, high = args.bounds
        grade = "inside" if low <= ratio <= high else "outside"
        print(f"prediction {grade} inclusive bounds [{float(low):g}, {float(high):g}]")
    if not args.sd20:
        print(f"known sums {EXPECTED_14[suite]} {'EQUAL' if sums == EXPECTED_14[suite] else 'MISMATCH'}")
        return sums == EXPECTED_14[suite]
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    known = commands.add_parser("check", help="check depth-12 rows against job 1, in argument order")
    known.add_argument("paths", nargs="+", type=Path)
    summary = commands.add_parser("pair", help="summarize matching depth-14 rows")
    summary.add_argument("directory", type=Path)
    summary.add_argument("suite", choices=SIZES)
    summary.add_argument("--sd20", action="store_true")
    summary.add_argument("--bounds", nargs=2, type=Fraction, metavar=("LOW", "HIGH"),
                         help="inclusive forecast bounds; grade against the exact ratio of sums")
    args = parser.parse_args()
    try:
        if args.command == "check":
            return 0 if all(check(path) for path in args.paths) else 1
        return 0 if pair(args) else 1
    except (ValueError, OSError, ZeroDivisionError) as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
