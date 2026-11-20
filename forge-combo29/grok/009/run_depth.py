#!/usr/bin/env python3
"""Depth-sum harness. One engine process. S14, Threads 1, Hash 16, then extra Name=Value options.

usage: run_depth.py EXE POSITIONS OUTPREFIX DEPTH [Name=Value ...]
Writes OUTPREFIX.raw, OUTPREFIX.meta, OUTPREFIX.rows
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
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

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: Path) -> None:
        self.exe = exe
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
        self.log.append(">> " + line)
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.log.append("<< EOF")
                raise SystemExit("engine closed stdout early")
            line = line.rstrip("\r\n")
            self.log.append("<< " + line)
            got.append(line)
            for bit in STOP_BITS:
                if bit in line:
                    raise SystemExit("STOP " + line)
            if done(line):
                return got

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: run_depth.py EXE POSITIONS OUTPREFIX DEPTH [Name=Value ...]", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    positions = Path(sys.argv[2]).resolve()
    outprefix = Path(sys.argv[3])
    depth = int(sys.argv[4])
    extra: list[tuple[str, str]] = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extra.append((name, value))
    fens = [fen_of(line.strip()) for line in positions.read_text().splitlines() if line.strip()]
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    eng = Engine(exe)
    try:
        eng.send("uci")
        uci_lines = eng.read_until(lambda line: line == "uciok")
        id_name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        sent: list[str] = []
        for name, value in S14 + extra:
            eng.send(f"setoption name {name} value {value}")
            sent.append(f"setoption name {name} value {value}")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok")
        rows: list[str] = []
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok")
            eng.send(f"position fen {fen}")
            sent_pos = f"position fen {fen}"
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok")
            eng.send(f"go depth {depth}")
            info = eng.read_until(lambda line: line.startswith("bestmove "))
            nodes = None
            for line in info:
                tokens = line.split()
                if "nodes" in tokens and line.startswith("info "):
                    nodes = tokens[tokens.index("nodes") + 1]
            if nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            rows.append(f"{index} {nodes} {fen}")
            del sent_pos
        outprefix.parent.mkdir(parents=True, exist_ok=True)
        (Path(str(outprefix) + ".raw")).write_text("\n".join(eng.log) + "\n")
        (Path(str(outprefix) + ".rows")).write_text("\n".join(rows) + "\n")
        meta = [
            f"exe {exe}",
            f"sha256 {digest}",
            f"id_name {id_name}",
            f"positions {positions}",
            f"depth {depth}",
            f"count {len(fens)}",
        ]
        for line in sent:
            meta.append("option " + line)
        (Path(str(outprefix) + ".meta")).write_text("\n".join(meta) + "\n")
        print(f"positions {len(rows)} last {rows[-1].split()[1]}")
    finally:
        eng.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
