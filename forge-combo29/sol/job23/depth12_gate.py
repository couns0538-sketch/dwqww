#!/usr/bin/env python3
"""Replay the first 200 UHO openings on Job 4 and W at depth 12."""

import argparse
from hashlib import file_digest, sha256
from itertools import islice
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
BOOK_SHA256 = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
O_SHA256 = "ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8"
JOB4_SHA256 = "63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333"
EXPECTED = (7610402, [16744, 20853, 38882])


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def find_runner():
    for directory in ("job2", "sol-job2"):
        runner = HERE.parent / directory / "run_matrix.py"
        if runner.is_file():
            return runner
    raise FileNotFoundError("Job 2 run_matrix.py is missing from the adjacent job2 or sol-job2 directory")


def read_arm(path, positions):
    meta = json.loads(path.with_suffix(path.suffix + ".meta").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    counts = [row["nodes"] for row in rows]
    if meta["status"] != "complete" or meta["positions_completed"] != len(positions):
        raise ValueError(f"{path}: {meta['status']} after {meta['positions_completed']} rows: {meta.get('error', '')}")
    if len(rows) != len(positions) or meta["nodes_sum"] != sum(counts):
        raise ValueError(f"{path}: row count or node sum differs from metadata")
    for index, (position, row) in enumerate(zip(positions, rows, strict=True), 1):
        if (row["index"], row["fen"], row["depth"]) != (index, position, 12):
            raise ValueError(f"{path}: expected index {index}, original O FEN, and final depth 12")
    return meta, rows, (sum(counts), counts[:3])


def run(args):
    if digest(args.job4) != JOB4_SHA256:
        raise ValueError(f"{args.job4}: executable is not the pinned Job 4 build")
    if digest(args.book) != BOOK_SHA256:
        raise ValueError(f"{args.book}: opening book SHA-256 differs from the Job 12 pin")
    with args.book.open("rb") as archive:
        lines = list(islice(archive, 200))
    fixture_bytes = b"".join(lines)
    if len(lines) != 200 or sha256(fixture_bytes).hexdigest() != O_SHA256:
        raise ValueError("first 200 book lines differ from the previously pinned O fixture")
    positions = fixture_bytes.decode("utf-8").splitlines()
    if any(len(line.split()) != 6 for line in positions):
        raise ValueError("O contains a line that is not a six-field FEN")

    runner = find_runner()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fixture = args.output_dir / "O-first200.fens"
    with fixture.open("xb") as stream:
        stream.write(fixture_bytes)
    with (args.output_dir / "depth12-summary.txt").open("x", encoding="utf-8") as summary:
        def log(line):
            print(line, flush=True)
            print(line, file=summary, flush=True)

        log(f"Book SHA-256 {BOOK_SHA256}. First 200 lines SHA-256 {O_SHA256}.")
        log("Protocol: source six-field FENs, PC20, Threads 1, Hash 16, EvalSwingMult 64, "
            "default EvalSwingMax, ucinewgame + isready before each go depth 12.")
        results = {}
        for name, engine in (("job4", args.job4), ("w", args.wide)):
            path = args.output_dir / f"{name}.jsonl"
            completed = subprocess.run(
                [sys.executable, runner, engine, fixture, path, "depth", "12", "--set", "EvalSwingMult", "64"],
                check=False, capture_output=True, text=True,
            )
            for line in (completed.stdout + completed.stderr).splitlines():
                log(line)
            if completed.returncode:
                log(f"STOP: {name} runner exited {completed.returncode}.")
                return 1
            meta, rows, receipt = read_arm(path, positions)
            log(f"{name}: SHA-256 {meta['exe_sha256']}; {meta['id_name']}; "
                f"sum {receipt[0]}; first three {receipt[1]}.")
            results[name] = rows, receipt

        base, base_receipt = results["job4"]
        wide, wide_receipt = results["w"]
        for row_b, row_w in zip(base, wide, strict=True):
            if (row_b["nodes"], row_b["bestmove"]) != (row_w["nodes"], row_w["bestmove"]):
                mismatch = {"index": row_b["index"], "job4": row_b, "w": row_w}
                with (args.output_dir / "first-difference.json").open("x", encoding="utf-8") as stream:
                    json.dump(mismatch, stream, indent=2)
                    stream.write("\n")
                log(f"STOP: first difference at position {mismatch['index']}, FEN {row_b['fen']}: "
                    f"Job 4 {row_b['nodes']} {row_b['bestmove']}; W {row_w['nodes']} {row_w['bestmove']}.")
                return 1

        log(f"Job 4 and W agree on all {len(base)} node-count and bestmove rows.")
        if base_receipt != EXPECTED or wide_receipt != EXPECTED:
            log(f"STOP: prescribed sum {EXPECTED[0]} and first three {EXPECTED[1]} differ. "
                "No position-by-position PC reference was supplied.")
            return 1
        log("PASS: both executables match the prescribed depth-12 node counts and each other.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job4", type=Path)
    parser.add_argument("wide", type=Path)
    parser.add_argument("book", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    try:
        return run(args)
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
