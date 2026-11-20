#!/usr/bin/env python3
"""Fixed-depth node harness. One engine process. isready after every setoption and position."""
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
]

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


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
    parts = text.split()
    if len(parts) < 6:
        return text
    return " ".join(parts[:6])


def id_name_of(exe: Path) -> str:
    result = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
    for line in (result.stdout + result.stderr).splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :].strip()
    return ""


class Engine:
    def __init__(self, exe: Path) -> None:
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> None:
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise RuntimeError("engine closed stdout")
            self.lines.append(line)
            if any(mark in line for mark in STOP_MARKS):
                raise RuntimeError("STOP " + line.rstrip())
            if done(line):
                return

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


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: run_depth.py EXE POSITIONS DEPTH OUT_RAW OUT_META", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1]).resolve()
    positions = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    raw_path = Path(sys.argv[4]).resolve()
    meta_path = Path(sys.argv[5]).resolve()
    fens = [fen_of(line) for line in positions.read_text(encoding="utf-8").splitlines()]
    fens = [fen for fen in fens if fen]
    name = id_name_of(exe)
    digest = sha256(exe)
    option_lines = [f"setoption name Threads value 1", f"setoption name Hash value 16"]
    option_lines += [f"setoption name {key} value {value}" for key, value in S14]
    engine = Engine(exe)
    try:
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line.startswith("readyok"))
            for command in option_lines:
                engine.send(command)
                engine.send("isready")
                engine.read_until(lambda line: line.startswith("readyok"))
            engine.send("position fen " + fen)
            engine.send("isready")
            engine.read_until(lambda line: line.startswith("readyok"))
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "))
    finally:
        engine.close()
    raw_path.write_text("".join(engine.lines), encoding="utf-8")
    meta = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={name}",
        f"positions={positions}",
        f"depth={depth}",
        f"count={len(fens)}",
        "options:",
        *option_lines,
    ]
    meta_path.write_text("\n".join(meta) + "\n", encoding="utf-8")
    print(f"wrote {raw_path} lines={len(engine.lines)} positions={len(fens)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
