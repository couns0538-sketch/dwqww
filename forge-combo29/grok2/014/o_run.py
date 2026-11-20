#!/usr/bin/env python3
"""o_run.py EXE FENS OUTSTEM [SWITCH true|false]
One engine process. Threads 1, Hash 16, then S14 in order, then the switch.
ucinewgame + isready before every position. isready after every setoption and position.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

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
)

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.q: queue.Queue[str | None] = queue.Queue()
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        while True:
            raw = self.proc.stdout.readline()
            if not raw:
                self.q.put(None)
                return
            self.q.put(raw.decode("utf-8", "replace").rstrip("\r\n"))

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> list[str]:
        lines: list[str] = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self.q.get(timeout=0.2)
            except queue.Empty:
                if self.proc.poll() is not None and self.q.empty():
                    raise SystemExit(f"STOP: engine exited while waiting, last lines {lines[-5:]}")
                continue
            if line is None:
                raise SystemExit(f"STOP: engine closed stdout, last lines {lines[-5:]}")
            lines.append(line)
            for needle in BAD:
                if needle in line:
                    raise SystemExit(f"STOP: {line}")
            if predicate(line):
                return lines
        raise SystemExit(f"STOP: timeout, last lines {lines[-8:]}")

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main() -> None:
    exe = str(Path(sys.argv[1]).resolve())
    fens = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    fens = [line.strip() for line in fens if line.strip()]
    outstem = Path(sys.argv[3])
    switch = sys.argv[4] if len(sys.argv) > 4 else None
    switch_value = sys.argv[5] if len(sys.argv) > 5 else None
    if switch is not None and switch_value not in ("true", "false"):
        raise SystemExit("STOP: switch value must be true or false")

    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch is not None:
        options.append(f"setoption name {switch} value {switch_value}")

    digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    engine = Engine(exe)
    transcript: list[str] = []

    def record(sent: str, got: list[str]) -> None:
        transcript.append(">> " + sent)
        transcript.extend(got)

    try:
        engine.send("uci")
        got = engine.read_until(lambda line: line == "uciok", 30)
        record("uci", got)
        name = "?"
        for line in got:
            if line.startswith("id name "):
                name = line[len("id name ") :]
        engine.send("isready")
        got = engine.read_until(lambda line: line == "readyok", 30)
        record("isready", got)
        for option in options:
            engine.send(option)
            engine.send("isready")
            got = engine.read_until(lambda line: line == "readyok", 30)
            record(option, [])
            record("isready", got)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            got = engine.read_until(lambda line: line == "readyok", 30)
            record("ucinewgame", [])
            record("isready", got)
            position = f"position fen {fen}"
            engine.send(position)
            engine.send("isready")
            got = engine.read_until(lambda line: line == "readyok", 30)
            record(position, [])
            record("isready", got)
            engine.send("go depth 12")
            got = engine.read_until(lambda line: line.startswith("bestmove "), 120)
            record("go depth 12", got)
            if index % 20 == 0 or index == len(fens):
                print(f"position {index}/{len(fens)}", flush=True)
    finally:
        engine.close()

    outstem.parent.mkdir(parents=True, exist_ok=True)
    raw_path = outstem.with_suffix(".raw")
    meta_path = outstem.with_suffix(".meta")
    raw_path.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    meta_lines = [
        f"exe {exe}",
        f"sha256 {digest}",
        f"id name {name}",
        *[f"option {option}" for option in options],
    ]
    meta_path.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")
    print(f"WROTE {raw_path}")
    print(f"WROTE {meta_path}")


if __name__ == "__main__":
    main()
