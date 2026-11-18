"""Execute one gated Job 4 part using the previously validated UCI harnesses."""

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
LAB = Path(os.environ.get("ASTRA5_LAB", str(Path(__file__).resolve().parent.parent)))
sys.path.insert(0, str(LAB / "job2"))
import run_counts


A = [("Base3", "PC20", "NullMoveBase=3"), ("Base4", "PC20", "NullMoveBase=4")]
B = [("S14", "S14"), ("PC20", "PC20"), ("B1", "PC20", "HistRework=0"),
     ("B2", "PC20", "CorrHistV2=false"), ("B3", "S14", "CuckooRep=true"),
     ("B4", "S14", "HistRework=2"), ("B5", "S14", "TtPruneV2=true"),
     ("B6", "S14", "CorrHistV2=true"), ("B7", "S14", "MateAlphaGuard=true")]


def read(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def first_difference(rows, ref, keys):
    if len(rows) != len(ref):
        return f"row counts: observed {len(rows)}, expected {len(ref)}"
    for index, (one, two) in enumerate(zip(rows, ref), 1):
        if any(one[k] != two[k] for k in keys):
            return f"row {index}: expected {two}; observed {one}"
    return None


def ladder(exe, directory, case):
    label, profile, *options = case
    prefix = directory / label
    cmd = [sys.executable, LAB / "job3/ladder.py", exe, profile, prefix, "--last", "20"]
    for option in options:
        cmd += ["--set", option]
    subprocess.run(cmd, check=True)
    rows = read(Path(str(prefix) + ".tsv"))
    if [int(r["requested_depth"]) for r in rows] != list(range(1, 21)):
        raise ValueError(f"incomplete {label} ladder")
    first = next((r for r in rows if r["mate_found"] == "1"), None)
    summary = f"D{first['requested_depth']} ({first['nodes']} nodes)" if first else "not by D20"
    return (f"{label} {profile} {' '.join(options)}: {summary}", rows)


def check_ladder(rows, profile):
    ref = read(LAB / "job3/step1" / (profile + ".tsv"))
    cols = ("requested_depth", "info_depth", "bestmove", "score_type", "score", "nodes")
    diff = first_difference(rows, ref, cols)
    if diff:
        raise ValueError(f"job 3 {profile} parity: {diff}")
    return "20/20 rows equal job3 " + profile


def suite(exe, epd, output, options):
    key = "job4_" + "_".join(k + v for k,v in options)
    run_counts.SETTINGS[key] = options
    args = argparse.Namespace(exe=exe, epd=epd, rows=output, first=None,
                              setting=key, slots=None, blind_counts=False)
    run_counts.run(args)
    return read(output)


def measure(args):
    part = args.part
    dest = args.out / part
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "checks.txt").open("x", encoding="utf-8") as log:
        def record(line):
            print(line, file=log, flush=True)
            print(line, flush=True)

        if part in ("A", "B"):
            cases = A if part == "A" else B
            with ThreadPoolExecutor(max_workers=args.jobs) as pool:
                for case, (summary, rows) in zip(cases, pool.map(lambda c: ladder(args.pc, dest, c), cases)):
                    if case[0] in ("S14", "PC20"):
                        summary += "; " + check_ladder(rows, case[0])
                    record(summary)
            if part == "B":
                return
            summary, rows = ladder(args.floor, dest, ("Floor0", "PC20", "NullChildFloor=0"))
            record(summary + "; " + check_ladder(rows, "PC20"))
        level = 0 if part == "A" else 1
        for name, count in (("O", 200), ("G", 353)):
            output = dest / f"{name}_floor{level}.tsv"
            rows = suite(args.floor, args.epds / (name + ".epd"), output, [("NullChildFloor", str(level))])
            if len(rows) != count:
                raise ValueError(f"expected {count} rows for {name}")
            values = [int(r["nodes"]) for r in rows]
            summary = f"{name} PC20 Floor{level} D12: {len(values)} rows, nodes {sum(values)}, first {values[:3]}"
            if part == "A":
                ref = read(LAB / "job1/rows" / (name + "_base_d12.tsv"))
                diff = first_difference(rows, ref, ("index", "fen", "nodes", "bestmove"))
                target = {"O": (8315168, [21812, 26844, 35173]), "G": (17611204, [31779, 46086, 84457])}[name]
                if diff or (sum(values), values[:3]) != target:
                    record(f"{name} reference difference: {diff}; expected sum and first three {target}")
                    summary += "; PC floor0 rows form the floor1 comparator per stated exception"
                else:
                    summary += "; every row equals job1; published sum and first three equal"
            else:
                ref = read(args.out / "A" / f"{name}_floor0.tsv")
                diff = first_difference(rows, ref, ("index", "fen"))
                if diff:
                    raise ValueError(diff)
                baseline = sum(int(r["nodes"]) for r in ref)
                changes = sum(r["bestmove"] != b["bestmove"] for r, b in zip(rows, ref))
                summary += f"; floor0 nodes {baseline}; ratio {sum(values)/baseline:.8f}; changed bestmoves {changes}"
            record(summary)
        if part == "A":
            summary, _ = ladder(args.floor, dest, ("Floor1", "PC20", "NullChildFloor=1"))
            record(summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=("A", "B", "D"))
    parser.add_argument("pc", type=Path)
    parser.add_argument("floor", type=Path)
    parser.add_argument("epds", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--jobs", type=int, default=3)
    measure(parser.parse_args())


if __name__ == "__main__":
    main()
