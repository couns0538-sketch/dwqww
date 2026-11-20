#!/usr/bin/env python3
"""Depth-sum harness. One engine process. isready after every setoption and position.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("Threads", "1"),
    ("Hash", "16"),
]

STOP_MARKS = ("unknown option", "invalid value", "invalid fen", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe: Path):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.log.append(f">>> {line}")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> str:
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout")
            line = line.rstrip("\r\n")
            self.log.append(line)
            lowered = line.lower()
            for mark in STOP_MARKS:
                if mark in lowered:
                    raise SystemExit(f"STOP {line}")
            if done(line):
                return line

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True, help="prefix for .raw .nodes .meta")
    parser.add_argument("--switch", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--limit", type=int, default=0, help="first N positions only; 0 = all")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    fens = [line.strip() for line in Path(args.fens).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        fens = fens[: args.limit]
    prefix = Path(args.out)
    options = list(S14)
    if args.switch != "omit":
        options.append(("IdeaS38", args.switch))

    engine = Engine(exe)
    id_name = ""
    nodes_rows: list[str] = []
    total = 0
    raw_path = Path(str(prefix) + ".raw")
    nodes_path = Path(str(prefix) + ".nodes")
    meta_path = Path(str(prefix) + ".meta")
    try:
        engine.send("uci")
        engine.read_until(lambda line: line == "uciok")
        for line in engine.log:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok")
            engine.send(f"go depth {args.depth}")
            engine.read_until(lambda line: line.startswith("bestmove "))
            nodes = None
            for line in reversed(engine.log):
                if " nodes " in line and line.startswith("info "):
                    parts = line.split()
                    try:
                        nodes = int(parts[parts.index("nodes") + 1])
                    except (ValueError, IndexError):
                        continue
                    break
            if nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            total += nodes
            nodes_rows.append(f"{index} {nodes}")
            if index % 50 == 0:
                print(f"{prefix.name} {index}/{len(fens)} sum {total}", flush=True)
    finally:
        engine.close()
        prefix.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("\n".join(engine.log) + "\n", encoding="utf-8")
        nodes_path.write_text("\n".join(nodes_rows + [f"SUM {total}", ""]), encoding="utf-8")
        option_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
        meta_path.write_text(
            f"exe={exe}\nsha256={sha256(exe)}\nid_name={id_name}\ndepth={args.depth}\n"
            f"fens={Path(args.fens).resolve()}\ncount={len(fens)}\nswitch={args.switch}\n"
            f"options:\n{option_lines}\n",
            encoding="utf-8",
        )
    print(f"SUM {total} positions {len(fens)} wrote {nodes_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
