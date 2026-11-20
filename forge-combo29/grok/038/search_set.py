#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. One engine process.

Usage:
  search_set.py <exe> <positions> <depth> <raw-out> [--option Name Value]...

Sends ucinewgame and isready before every go. Sends isready after every
setoption and every position, and reads every line up to readyok.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import subprocess
import sys
from pathlib import Path

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str, log):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log = log

    def send(self, line: str) -> None:
        self.log.write(f"# >> {line}\n")
        self.log.flush()
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, limit: int = 100000) -> list[str]:
        lines = []
        assert self.proc.stdout is not None
        while len(lines) < limit:
            line = self.proc.stdout.readline()
            if line == "":
                self.log.write("# EOF\n")
                self.log.flush()
                raise SystemExit("engine closed stdout")
            line = line.rstrip("\n")
            self.log.write(line + "\n")
            self.log.flush()
            lines.append(line)
            low = line.lower()
            for bit in STOP_BITS:
                if bit.lower() in low:
                    raise SystemExit(f"STOP {bit}: {line}")
            if pred(line):
                return lines
        raise SystemExit("too many lines")

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda s: s == "readyok")

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except Exception:
                pass
            self.proc.wait(timeout=10)


def fen_of(line: str) -> str:
    return line.strip()


def main() -> int:
    args = sys.argv[1:]
    exe = args[0]
    positions = Path(args[1])
    depth = args[2]
    raw_path = Path(args[3])
    options = []
    i = 4
    while i < len(args):
        if args[i] != "--option":
            raise SystemExit(f"bad arg {args[i]}")
        options.append((args[i + 1], args[i + 2]))
        i += 3
    fens = [fen_of(line) for line in positions.read_text().splitlines() if line.strip()]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w") as log:
        eng = Engine(exe, log)
        try:
            eng.send("uci")
            eng.read_until(lambda s: s == "uciok")
            eng.ready()
            for name, value in options:
                eng.send(f"setoption name {name} value {value}")
                eng.ready()
            for index, fen in enumerate(fens):
                log.write(f"# position {index}\n")
                log.flush()
                eng.send("ucinewgame")
                eng.ready()
                eng.send(f"position fen {fen}")
                eng.ready()
                eng.send(f"go depth {depth}")
                eng.read_until(lambda s: s.startswith("bestmove "))
                log.write(f"# endposition {index}\n")
                log.flush()
        finally:
            eng.close()
    print(f"searched {len(fens)} depth {depth} -> {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
