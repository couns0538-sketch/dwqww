#!/usr/bin/env python3
"""Depth-limited node sum. S14, Threads 1, Hash 16. ucinewgame before every go.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Does not send IdeaS32 unless --switch is given (exe B has no such option).
"""

import argparse
import sys
from pathlib import Path

from uci_session import Session, UciError, sha256_file, write_meta

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]


def load_fens(path, limit):
    fens = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fens.append(text.split(";")[0].strip())
            if limit and len(fens) >= limit:
                break
    return fens


def last_depth_nodes(lines, depth):
    prefix = f"info depth {depth} "
    found = None
    for line in lines:
        if line.startswith(prefix) and " nodes " in line:
            parts = line.split()
            found = int(parts[parts.index("nodes") + 1])
    if found is None:
        for line in reversed(lines):
            if line.startswith("info depth ") and " nodes " in line:
                parts = line.split()
                return int(parts[parts.index("nodes") + 1]), parts[2]
        raise UciError("no info depth line")
    return found, str(depth)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--switch", choices=("omit", "false", "true"), default="omit")
    args = parser.parse_args()
    out = Path(__file__).resolve().parent
    fens = load_fens(args.fens, args.limit)
    options = list(S14)
    if args.switch != "omit":
        options.append(f"setoption name IdeaS32 value {args.switch}")
    session = Session(args.exe)
    raw_lines = []
    nodes = []
    out = Path(__file__).resolve().parent
    failed = None
    try:
        session.send("uci")
        session.read_until(lambda line: line == "uciok", 30)
        id_name = "MISSING"
        for line in session.lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for option in options:
            before = len(session.lines)
            session.send(option)
            session.send("isready")
            session.read_until(lambda line: line == "readyok", 30)
            raw_lines.extend(session.lines[before:])
        for index, fen in enumerate(fens, start=1):
            before = len(session.lines)
            session.send("ucinewgame")
            session.send("isready")
            session.read_until(lambda line: line == "readyok", 30)
            session.send(f"position fen {fen}")
            session.send("isready")
            session.read_until(lambda line: line == "readyok", 30)
            session.send(f"go depth {args.depth}")
            session.read_until(lambda line: line.startswith("bestmove "), 180)
            chunk = session.lines[before:]
            raw_lines.extend(chunk)
            count, seen_depth = last_depth_nodes(chunk, args.depth)
            nodes.append((index, count, seen_depth, fen))
            if index % 25 == 0 or index == len(fens):
                print(f"{args.tag} {index}/{len(fens)} last {count}", flush=True)
    except UciError as exc:
        failed = str(exc)
        print(f"STOP {exc}", flush=True)
        raw_lines = list(session.lines)
    finally:
        session.close()
    if session.lines and not raw_lines:
        raw_lines = list(session.lines)
    (out / f"{args.tag}.raw.txt").write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
    if failed is not None:
        (out / f"{args.tag}.error.txt").write_text(failed + "\n", encoding="utf-8")
        sys.exit(1)
    digest = sha256_file(args.exe)
    (out / f"{args.tag}.raw.txt").write_text("\n".join(raw_lines) + "\n", encoding="utf-8")
    write_meta(out / f"{args.tag}.meta", args.exe, digest, id_name, options)
    rows = out / f"{args.tag}.nodes.txt"
    with rows.open("w", encoding="utf-8") as handle:
        for index, count, seen_depth, fen in nodes:
            handle.write(f"{index} {count} depth {seen_depth} {fen}\n")
    total = sum(count for _, count, _, _ in nodes)
    print(f"SUM {args.tag} {total} n {len(nodes)}")
    if len(nodes) >= 3:
        print("FIRST3", nodes[0][1], nodes[1][1], nodes[2][1])


if __name__ == "__main__":
    main()
