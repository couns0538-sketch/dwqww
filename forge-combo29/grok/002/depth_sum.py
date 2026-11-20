#!/usr/bin/env python3
"""Fixed-depth node sum. One engine process.

S14 is sent in the brief's order. Threads 1 and Hash 16 are sent first.
After every setoption and every position command, isready is sent and every
line up to readyok is read. ucinewgame and isready are sent before every go.

Usage:
  depth_sum.py <exe> <fenfile> <depth> <outbase> [extra setoption line ...]
"""
import hashlib
import sys
from pathlib import Path

from uci_io import Engine

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
]

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    return text.split(";")[0].strip()


def nodes_of(lines: list[str]) -> tuple[int, int]:
    depth = -1
    nodes = -1
    for line in lines:
        if not line.startswith("info ") or " nodes " not in line or " score " not in line:
            continue
        parts = line.split()
        if "depth" in parts:
            depth = int(parts[parts.index("depth") + 1])
        nodes = int(parts[parts.index("nodes") + 1])
    if nodes < 0:
        raise RuntimeError("no info nodes line")
    return depth, nodes


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: depth_sum.py <exe> <fenfile> <depth> <outbase> [extra setoption ...]", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    fenfile = Path(sys.argv[2])
    depth = int(sys.argv[3])
    outbase = Path(sys.argv[4])
    extras = sys.argv[5:]
    fens = [fen for fen in (fen_of(line) for line in fenfile.read_text(encoding="utf-8").splitlines()) if fen]
    engine = Engine(exe)
    id_name = ""
    try:
        engine.send("uci")
        ident = engine.read_until(lambda line: line == "uciok", 30)
        for line in ident:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        setup = [
            "setoption name Threads value 1",
            "setoption name Hash value 16",
            *S14,
            *extras,
        ]
        for option in setup:
            engine.send(option)
            engine.ready()
        rows: list[str] = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.ready()
            engine.send("position fen " + fen)
            engine.ready()
            engine.send(f"go depth {depth}")
            go_lines = engine.read_until(lambda line: line.startswith("bestmove "), 120)
            got_depth, nodes = nodes_of(go_lines)
            rows.append(f"{index} {got_depth} {nodes}")
            if index % 50 == 0:
                print(f"progress {index}/{len(fens)}", flush=True)
    finally:
        engine.close()
    raw_path = Path(str(outbase) + ".raw.txt")
    nodes_path = Path(str(outbase) + ".nodes.txt")
    meta_path = Path(str(outbase) + ".meta")
    raw_path.write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
    nodes_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    meta_path.write_text(
        f"exe {exe}\n"
        f"sha256 {sha256(exe)}\n"
        f"id name {id_name}\n"
        f"fenfile {fenfile.resolve()}\n"
        f"depth {depth}\n"
        f"positions {len(fens)}\n"
        "setoption lines:\n"
        + "\n".join(
            [
                "setoption name Threads value 1",
                "setoption name Hash value 16",
                *S14,
                *extras,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    total = sum(int(row.split()[2]) for row in rows)
    first = " ".join(row.split()[2] for row in rows[:3])
    print(f"positions {len(rows)}")
    print(f"sum {total}")
    print(f"first3 {first}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
