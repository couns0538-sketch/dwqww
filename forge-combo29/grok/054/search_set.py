#!/usr/bin/env python3
"""Depth search of a FEN list. S14, Threads 1, Hash 16. One engine process."""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

S14 = (
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
)

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: Path, transcript: Path):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.transcript = transcript.open("w", encoding="utf-8")
        self.options_sent: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.transcript.write(">> " + line + "\n")
        self.transcript.flush()
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        lines: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                err = ""
                if self.proc.stderr is not None:
                    err = self.proc.stderr.read()
                raise SystemExit(f"engine closed stdout. stderr={err!r} lines={lines[-5:]}")
            self.transcript.write(line)
            self.transcript.flush()
            stripped = line.strip()
            for mark in STOP_MARKS:
                if mark in stripped:
                    raise SystemExit(f"STOP {stripped}")
            lines.append(stripped)
            if done(stripped):
                return lines

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def setoption(self, name: str, value: str) -> None:
        command = f"setoption name {name} value {value}"
        self.options_sent.append(command)
        self.send(command)
        self.ready()

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.transcript.close()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 6:
        raise SystemExit(f"short FEN: {line!r}")
    return " ".join(parts[:6])


def nodes_of(lines: list[str]) -> int:
    last = None
    for line in lines:
        if not line.startswith("info depth "):
            continue
        parts = line.split()
        if "nodes" not in parts:
            continue
        last = int(parts[parts.index("nodes") + 1])
    if last is None:
        raise SystemExit("no info depth nodes line")
    return last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True, help="prefix for .raw .nodes .meta")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--extra", action="append", default=[], metavar="NAME=VALUE")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    fens = [fen_of(line) for line in Path(args.fens).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        fens = fens[: args.limit]
    prefix = Path(args.out)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    engine = Engine(exe, prefix.with_suffix(".raw"))
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok")
        id_name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in S14:
            engine.setoption(name, value)
        for item in args.extra:
            name, value = item.split("=", 1)
            engine.setoption(name, value)
        nodes: list[int] = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.ready()
            engine.send(f"position fen {fen}")
            engine.ready()
            engine.send(f"go depth {args.depth}")
            got = engine.read_until(lambda line: line.startswith("bestmove "))
            count = nodes_of(got)
            nodes.append(count)
            print(f"{index} {count}", flush=True)
    finally:
        engine.close()

    prefix.with_suffix(".nodes").write_text("".join(f"{count}\n" for count in nodes), encoding="utf-8")
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    meta_lines = [
        f"exe {exe}",
        f"sha256 {digest}",
        f"id name {id_name}",
        f"depth {args.depth}",
        f"positions {len(nodes)}",
        f"sum {sum(nodes)}",
        "options sent:",
        *engine.options_sent,
    ]
    prefix.with_suffix(".meta").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")
    print(f"SUM {sum(nodes)} N {len(nodes)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
