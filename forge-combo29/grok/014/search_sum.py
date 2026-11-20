#!/usr/bin/env python3
"""Fixed-depth node sum. One engine process. Stops on a protocol error.

Usage: search_sum.py EXE FENFILE DEPTH OUT META OPTIONS
OPTIONS is a text file of full UCI lines (setoption ...), sent in order.
After every setoption and every position command the script sends isready
and reads every line until readyok.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(2)


class Engine:
    def __init__(self, exe: str) -> None:
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        lines: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                die("engine closed stdout")
            line = line.rstrip("\r\n")
            lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    die("STOP " + line)
            if done(line):
                return lines

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self) -> None:
        self.send("quit")
        self.proc.wait(timeout=30)


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def nodes_of(lines: list[str]) -> int:
    found = None
    for line in lines:
        if " nodes " not in line:
            continue
        bits = line.split()
        for i, bit in enumerate(bits):
            if bit == "nodes" and i + 1 < len(bits):
                found = int(bits[i + 1])
    if found is None:
        die("no nodes field")
    return found


def main() -> None:
    if len(sys.argv) != 7:
        die("usage: search_sum.py EXE FENFILE DEPTH OUT META OPTIONS")
    exe, fenfile, depth_s, out_path, meta_path, opt_path = sys.argv[1:]
    depth = int(depth_s)
    options = [ln.strip() for ln in Path(opt_path).read_text().splitlines() if ln.strip()]
    fens = [fen_of(ln) for ln in Path(fenfile).read_text().splitlines() if ln.strip()]
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    eng.send("uci")
    uci_lines = eng.read_until(lambda line: line == "uciok")
    eng.ready()
    id_name = next(ln for ln in uci_lines if ln.startswith("id name"))
    for opt in options:
        if not opt.startswith("setoption "):
            die("option line is not setoption: " + opt)
        eng.send(opt)
        eng.ready()
    rows: list[str] = []
    total = 0
    for index, fen in enumerate(fens, start=1):
        eng.send("ucinewgame")
        eng.ready()
        eng.send("position fen " + fen)
        eng.ready()
        eng.send(f"go depth {depth}")
        played = eng.read_until(lambda line: line.startswith("bestmove "))
        nodes = nodes_of(played)
        best = played[-1].split()[1]
        total += nodes
        rows.append(f"{index}\t{nodes}\t{best}\t{fen}")
        if index % 25 == 0:
            print(f"progress {index} sum {total}", flush=True)
    eng.close()
    Path(out_path).write_text("\n".join(rows) + f"\nSUM\t{total}\n")
    meta = [
        f"exe={exe}",
        f"sha256={sha}",
        f"id_name={id_name}",
        f"depth={depth}",
        f"positions={len(fens)}",
        "options:",
        *options,
    ]
    Path(meta_path).write_text("\n".join(meta) + "\n")
    print(f"SUM {total} positions {len(fens)}")


if __name__ == "__main__":
    main()
