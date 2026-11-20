#!/usr/bin/env python3
"""Depth search harness. Stops on unknown option, invalid value, invalid FEN, illegal move.

S14 is sent, in the brief's order, before every go. Threads 1 and Hash 16 go first.
ucinewgame and isready run before every go. isready is read to readyok after every
setoption and every position.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

S14 = [
    "setoption name Threads value 1",
    "setoption name Hash value 16",
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
]

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def stop_reason(line: str) -> str:
    for token in STOP:
        if token in line:
            return token
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--tsv", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[])
    args = parser.parse_args()

    exe = str(Path(args.exe).resolve())
    fens = [line.strip() for line in Path(args.fens).read_text().splitlines() if line.strip()]
    if args.limit > 0:
        fens = fens[: args.limit]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    options = list(S14) + list(args.extra)

    raw_path = Path(args.raw)
    tsv_path = Path(args.tsv)
    meta_path = Path(args.meta)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def send(line: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker: str, echo) -> list[str]:
        assert proc.stdout is not None
        got: list[str] = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit(f"eof waiting for {marker}")
            echo.write(line)
            echo.flush()
            reason = stop_reason(line)
            if reason:
                raise SystemExit(f"STOP {reason}: {line.rstrip()}")
            got.append(line)
            if line.startswith(marker) or line.rstrip("\n") == marker:
                return got

    id_name = ""
    with raw_path.open("w") as raw, tsv_path.open("w") as tsv:
        raw.write(f"# exe {exe}\n")
        send("uci")
        uci_lines = read_until("uciok", raw)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line.rstrip("\n")
        tsv.write("index\tnodes\tbestmove\tfen\n")
        depth_key = f"info depth {args.depth} "
        total = 0
        for index, fen in enumerate(fens):
            for option in options:
                send(option)
                send("isready")
                read_until("readyok", raw)
            send("ucinewgame")
            send("isready")
            read_until("readyok", raw)
            send(f"position fen {fen}")
            send("isready")
            read_until("readyok", raw)
            send(f"go depth {args.depth}")
            lines = read_until("bestmove", raw)
            nodes = None
            best = ""
            for line in lines:
                if line.startswith(depth_key):
                    parts = line.split()
                    if "nodes" in parts:
                        nodes = int(parts[parts.index("nodes") + 1])
                if line.startswith("bestmove "):
                    best = line.split()[1]
            if nodes is None:
                raise SystemExit(f"no depth {args.depth} nodes for index {index}")
            total += nodes
            tsv.write(f"{index}\t{nodes}\t{best}\t{fen}\n")
            tsv.flush()
            if index % 25 == 0:
                print(f"pos {index} nodes {nodes} sum {total}", flush=True)
        send("quit")
        print(f"SUM {total} POSITIONS {len(fens)}", flush=True)

    meta_path.write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={sha}",
                f"id_name={id_name}",
                f"depth={args.depth}",
                f"fens={Path(args.fens).resolve()}",
                f"positions={len(fens)}",
                "options:",
                *options,
                "",
            ]
        )
    )
    proc.wait(timeout=30)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(exc, file=sys.stderr)
        raise
