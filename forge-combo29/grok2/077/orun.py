#!/usr/bin/env python3
"""Depth-12 node run over first200.fens.

Usage:
  python3 orun.py <exe> <fens> <out-stem> [SwitchName true|false]

Sends Threads, Hash, then S14 in the brief's order, then the optional switch.
ucinewgame + isready before every position; isready after every setoption and
every position. Stops on unknown option, invalid value, invalid FEN, illegal move.
Writes <out-stem>.txt (engine stdout) and <out-stem>.meta.
"""
import hashlib
import select
import subprocess
import sys
import time
from pathlib import Path

S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class StopError(RuntimeError):
    pass


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.lines: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> None:
        assert self.proc.stdout is not None
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise TimeoutError("engine timed out")
            ready, _, _ = select.select([self.proc.stdout], [], [], remain)
            if not ready:
                raise TimeoutError("engine timed out")
            raw = self.proc.stdout.readline()
            if raw == b"":
                raise EOFError("engine closed stdout")
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            self.lines.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise StopError(line)
            if done(line):
                return

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except OSError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def main() -> int:
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: orun.py <exe> <fens> <out-stem> [SwitchName true|false]")
    exe = str(Path(sys.argv[1]).resolve())
    fens = [line.strip() for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if line.strip()]
    stem = Path(sys.argv[3])
    switch: tuple[str, str] | None = None
    if len(sys.argv) == 6:
        switch = (sys.argv[4], sys.argv[5])
        if switch[1] not in ("true", "false"):
            sys.exit("switch value must be true or false")
    options = list(S14)
    if switch is not None:
        options.append(switch)
    name = "id name MISSING"
    engine = Engine(exe)
    error = ""
    try:
        engine.send("uci")
        engine.read_until(lambda line: line == "uciok", 30)
        for line in engine.lines:
            if line.startswith("id name "):
                name = line
                break
        for opt_name, value in options:
            engine.send(f"setoption name {opt_name} value {value}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send("go depth 12")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
    except (StopError, TimeoutError, EOFError, OSError) as exc:
        error = str(exc)
    finally:
        engine.close()
        stem.parent.mkdir(parents=True, exist_ok=True)
        stem.with_suffix(".txt").write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
        meta_lines = [
            f"exe={exe}",
            f"sha256={sha256_file(Path(exe))}",
            name,
            "options:",
        ]
        meta_lines.extend(f"setoption name {opt_name} value {value}" for opt_name, value in options)
        if error:
            meta_lines.append(f"STOP={error}")
        stem.with_suffix(".meta").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")
    if error:
        print(f"STOP {stem.name}: {error}", file=sys.stderr)
        return 1
    bestmoves = sum(1 for line in engine.lines if line.startswith("bestmove "))
    print(f"{stem.name} positions {len(fens)} bestmove {bestmoves}")
    if bestmoves != len(fens):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
