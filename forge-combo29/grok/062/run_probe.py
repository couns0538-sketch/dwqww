#!/usr/bin/env python3
"""Show DeadMaterial firing on positions the gate recognizes.

Modes:
  off     DeadMaterial false
  on      DeadMaterial true, weights at their defaults
  corner  DeadMaterial true, IdeaP20_Corner 1, IdeaP20_King 1
"""

import pathlib
import queue
import subprocess
import sys
import threading
import time

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str, timeout: float) -> list[str]:
        got: list[str] = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=min(0.5, deadline - time.monotonic()))
            except queue.Empty:
                continue
            if line is None:
                raise SystemExit(f"engine exited waiting for {marker}")
            got.append(line)
            stripped = line.strip()
            for bad in BAD:
                if bad in stripped:
                    raise SystemExit("STOP " + bad + ": " + stripped)
            if stripped == marker or stripped.startswith(marker + " "):
                return got
        raise SystemExit(f"timeout waiting for {marker}")

    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
            self.proc.kill()


def main() -> None:
    exe, fen_path, mode, out_path = sys.argv[1:5]
    fens = [line.strip() for line in open(fen_path, encoding="utf-8") if line.strip()]
    engine = Engine(exe)
    raw: list[str] = []

    def talk(line: str, marker: str | None, timeout: float = 60) -> list[str]:
        raw.append(">> " + line + "\n")
        engine.send(line)
        if marker is None:
            return []
        got = engine.read_until(marker, timeout)
        raw.extend(got)
        return got

    try:
        talk("uci", "uciok")
        talk("isready", "readyok")
        talk("setoption name Threads value 1", None)
        talk("isready", "readyok")
        talk("setoption name Hash value 16", None)
        talk("isready", "readyok")
        for name, value in S14:
            talk(f"setoption name {name} value {value}", None)
            talk("isready", "readyok")
        if mode == "off":
            talk("setoption name DeadMaterial value false", None)
            talk("isready", "readyok")
        elif mode == "on":
            talk("setoption name DeadMaterial value true", None)
            talk("isready", "readyok")
        elif mode == "corner":
            talk("setoption name DeadMaterial value true", None)
            talk("isready", "readyok")
            talk("setoption name IdeaP20_Corner value 1", None)
            talk("isready", "readyok")
            talk("setoption name IdeaP20_King value 1", None)
            talk("isready", "readyok")
        else:
            raise SystemExit("mode")
        rows = []
        for index, fen in enumerate(fens, 1):
            talk("ucinewgame", None)
            talk("isready", "readyok")
            talk("position fen " + fen, None)
            talk("isready", "readyok")
            evaluated = talk("eval", "info string eval", 30)
            eval_line = evaluated[-1].strip()
            info = talk("go depth 10", "bestmove", 60)
            nodes = None
            score = None
            move = None
            for line in info:
                parts = line.split()
                if line.startswith("info depth") and "nodes" in parts:
                    nodes = parts[parts.index("nodes") + 1]
                    score = parts[parts.index("score") + 1] if "score" in parts else "?"
                if line.startswith("bestmove "):
                    move = parts[1]
            rows.append(f"{index} nodes {nodes} score {score} move {move} eval {eval_line} fen {fen}")
        text = "\n".join(rows) + "\n"
        pathlib.Path(out_path).write_text(text, encoding="utf-8")
        pathlib.Path(out_path + ".raw").write_text("".join(raw), encoding="utf-8")
        print(text, end="")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
