#!/usr/bin/env python3
"""Depth search of a FEN list. One engine process.

Usage:
  depth_set.py <exe> <fen-file> <out-prefix> <depth> [extra setoption lines...]

Always sends S14, then Threads 1, then Hash 16, then the extra lines.
After every setoption and every position command, sends isready and reads
until readyok. Stops on unknown option, invalid value, invalid FEN, or
illegal move. ucinewgame + isready before every go.
"""
import hashlib
import pathlib
import queue
import subprocess
import sys
import threading
import time

S14 = (
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
)

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str, err_path: pathlib.Path) -> None:
        self.err_file = err_path.open("w")
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err_file,
            text=True,
            bufsize=1,
        )
        self.stdout_lines: list[str] = []
        self.lines: queue.Queue[str | None] = queue.Queue()

        def pump() -> None:
            assert self.proc.stdout is not None
            for raw in self.proc.stdout:
                self.lines.put(raw.rstrip("\r\n"))
            self.lines.put(None)

        # A reader thread, not select(): cout flushes the whole uci block at
        # once, and select on a text file misses lines already in the buffer.
        threading.Thread(target=pump, daemon=True).start()

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SystemExit("timeout waiting for engine")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                raise SystemExit("timeout waiting for engine")
            if line is None:
                raise SystemExit(f"engine closed stdout exit={self.proc.poll()}")
            self.stdout_lines.append(line)
            for bit in STOP_BITS:
                if bit in line:
                    raise SystemExit(f"STOP {line}")
            if done(line):
                return

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.err_file.close()


def load_fens(path: pathlib.Path) -> list[str]:
    fens = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # EPD may carry opcodes after the 6 FEN fields. Keep six fields.
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit(f"short fen line: {line}")
        fen = " ".join(parts[:6]) if len(parts) >= 6 else line
        fens.append(fen)
    return fens


def main() -> None:
    exe = str(pathlib.Path(sys.argv[1]).resolve())
    fen_file = pathlib.Path(sys.argv[2])
    prefix = pathlib.Path(sys.argv[3])
    depth = int(sys.argv[4])
    extra = sys.argv[5:]
    fens = load_fens(fen_file)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(pathlib.Path(exe).read_bytes()).hexdigest()
    err_path = prefix.with_suffix(".err")
    engine = Engine(exe, err_path)
    options = list(S14) + list(extra)
    id_name = ""
    try:
        engine.send("uci")
        engine.read_until(lambda line: line == "uciok", 60)
        for line in engine.stdout_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for option in options:
            engine.send(option)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 60)
        for index, fen in enumerate(fens):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 60)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 60)
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "), 120)
            if (index + 1) % 25 == 0 or index + 1 == len(fens):
                print(f"done {index + 1}/{len(fens)}", file=sys.stderr, flush=True)
    finally:
        raw_path = prefix.with_suffix(".txt")
        raw_path.write_text("\n".join(engine.stdout_lines) + ("\n" if engine.stdout_lines else ""))
        for line in engine.stdout_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
                break
        meta_lines = [
            f"exe={exe}",
            f"sha256={sha}",
            f"id_name={id_name}",
            f"fen_file={fen_file.resolve()}",
            f"depth={depth}",
            f"positions={len(fens)}",
        ]
        for option in options:
            meta_lines.append(f"option={option}")
        prefix.with_suffix(".meta").write_text("\n".join(meta_lines) + "\n")
        engine.close()


if __name__ == "__main__":
    main()
