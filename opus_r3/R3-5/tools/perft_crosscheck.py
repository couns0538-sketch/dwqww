#!/usr/bin/env python3
"""R3-5: recompute every reference node count of tests/data/perft_suite.tsv with python-chess.

The published counts in the suite come from the sources listed in the TSV header; this script is the
independent second check (python-chess move generator, fully legal moves, bulk counting at depth 1).
Single-threaded; prints one line per reference as soon as it is done (cheapest first).

usage: perft_crosscheck.py <perft_suite.tsv> [--max-nodes N] [--only id,id,...]
exit status 0 when every computed count equals the reference, 1 otherwise.
"""
import argparse
import sys
import time

import chess


def perft(board: chess.Board, depth: int) -> int:
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    nodes = 0
    for move in board.legal_moves:
        board.push(move)
        nodes += perft(board, depth - 1)
        board.pop()
    return nodes


def read_suite(path):
    cases = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) != 6:
                raise SystemExit(f"bad line ({len(fields)} fields): {line!r}")
            refs = []
            for item in fields[3].split():
                depth, nodes = item.split(":")
                refs.append((int(depth), int(nodes)))
            cases.append({"id": fields[0], "group": fields[1], "fen": fields[2], "refs": refs})
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("suite")
    parser.add_argument("--max-nodes", type=int, default=0, help="skip references above this many nodes (0 = none)")
    parser.add_argument("--only", default="", help="comma-separated case ids")
    args = parser.parse_args()
    only = {item for item in args.only.split(",") if item}
    jobs = []
    for case in read_suite(args.suite):
        if only and case["id"] not in only:
            continue
        for depth, nodes in case["refs"]:
            if args.max_nodes and nodes > args.max_nodes:
                print(f"SKIP {case['id']} depth {depth} reference {nodes} (above --max-nodes)", flush=True)
                continue
            jobs.append((nodes, case, depth))
    jobs.sort(key=lambda job: job[0])
    print(f"python-chess {chess.__version__}, python {sys.version.split()[0]}, {len(jobs)} references", flush=True)
    failures = 0
    started = time.time()
    for expected, case, depth in jobs:
        board = chess.Board(case["fen"])
        assert board.is_valid(), case["fen"]
        t0 = time.time()
        got = perft(board, depth)
        status = "OK" if got == expected else "MISMATCH"
        failures += got != expected
        print(f"{status} {case['id']} depth {depth} reference {expected} python-chess {got} "
              f"({time.time() - t0:.1f} s)", flush=True)
    print(f"done: {len(jobs)} references, {failures} mismatches, {time.time() - started:.0f} s total", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
