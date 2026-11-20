#!/usr/bin/env python3
"""Depth-node harness. One engine process. Stops on unknown option, invalid value, invalid FEN, illegal move.

Usage:
  depth_harness.py EXE OUTPREFIX FENFILE DEPTH [LIMIT]
Writes OUTPREFIX.txt (index nodes), OUTPREFIX.raw (engine lines), OUTPREFIX.meta.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    if len(sys.argv) < 5:
        die("usage: depth_harness.py EXE OUTPREFIX FENFILE DEPTH [LIMIT] [EXTRA_SETOPTION ...]")
    exe = str(Path(sys.argv[1]).resolve())
    out_prefix = Path(sys.argv[2])
    fen_file = Path(sys.argv[3])
    depth = int(sys.argv[4])
    limit = None
    extra: list[str] = []
    rest = sys.argv[5:]
    if rest and rest[0].lstrip("-").isdigit():
        limit = int(rest[0])
        rest = rest[1:]
    extra = rest
    fens = []
    for line in fen_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fen = line.split(";")[0].strip()
        fens.append(fen)
    if limit is not None:
        fens = fens[:limit]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdin and proc.stdout
    raw_lines: list[str] = []
    id_name = ""

    def send(line: str) -> None:
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker: str) -> list[str]:
        got: list[str] = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                die("engine closed while waiting for " + marker)
            line = line.rstrip("\n")
            raw_lines.append(line)
            got.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    proc.kill()
                    die("STOP " + bad + " :: " + line)
            if marker in line:
                return got

    send("uci")
    uci_lines = read_until("uciok")
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]

    options = S14 + extra
    for opt in options:
        send(opt)
        send("isready")
        read_until("readyok")

    rows: list[str] = []
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        send("position fen " + fen)
        send("isready")
        read_until("readyok")
        send(f"go depth {depth}")
        info = read_until("bestmove")
        nodes = None
        for line in info:
            if " nodes " in line:
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
        if nodes is None:
            proc.kill()
            die(f"no nodes for position {index}")
        rows.append(f"{index} {nodes}")
        if index % 50 == 0:
            print(f"progress {index}/{len(fens)}", file=sys.stderr, flush=True)

    send("quit")
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    (out_prefix.parent / (out_prefix.name + ".txt")).write_text("\n".join(rows) + "\n")
    (out_prefix.parent / (out_prefix.name + ".raw")).write_text("\n".join(raw_lines) + "\n")
    meta = [
        f"exe {exe}",
        f"sha256 {sha}",
        f"id name {id_name}",
        "options:",
    ]
    meta.extend(options)
    meta.append(f"depth {depth}")
    meta.append(f"positions {len(fens)}")
    meta.append(f"fenfile {fen_file.resolve()}")
    (out_prefix.parent / (out_prefix.name + ".meta")).write_text("\n".join(meta) + "\n")
    total = sum(int(r.split()[1]) for r in rows)
    print(f"positions {len(fens)} nodes {total}")


if __name__ == "__main__":
    main()
