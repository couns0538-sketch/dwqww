#!/usr/bin/env python3
"""Fixed-depth search of a FEN list. S14, Threads 1, Hash 16.

ucinewgame resets this engine to the start position, so it is sent before
position, and both are followed by isready. Stops on unknown option,
invalid value, invalid FEN, or illegal move.

Usage:
  harness_search.py --exe EXE --fens FILE --depth N --out PREFIX
                    [--switch absent|false|true] [--max N]
"""
import argparse
import hashlib
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


def load_fens(path: str, limit: int) -> list[str]:
    fens = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            raise SystemExit(f"short fen line: {line}")
        fens.append(" ".join(parts[:6]))
        if limit and len(fens) >= limit:
            break
    return fens


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log: list[str] = []
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        self.log.append(">> " + line + "\n")

    def read_until(self, marker: str, timeout: float) -> str:
        deadline = time.time() + timeout
        got = ""
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=max(0.01, deadline - time.time()))
            except queue.Empty:
                break
            if line is None:
                break
            self.log.append(line)
            got += line
            if any(bad in line for bad in BAD):
                raise SystemExit("STOP " + line.strip())
            if marker in line:
                return got
        raise SystemExit(f"timeout waiting for {marker}")

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


def option_lines(switch: str) -> list[str]:
    lines = [f"setoption name {name} value {value}" for name, value in S14]
    lines.insert(0, "setoption name Threads value 1")
    lines.insert(0, "setoption name Hash value 16")
    if switch == "absent":
        return lines
    if switch not in ("false", "true"):
        raise SystemExit("switch must be absent, false, or true")
    lines.append(f"setoption name IdeaS29 value {switch}")
    lines.append("setoption name IdeaS29_Threshold value 0")
    lines.append("setoption name IdeaS29_Scale value 1")
    return lines


def nodes_of(chunk: str) -> int:
    last = None
    for line in chunk.splitlines():
        if " nodes " in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "nodes" and i + 1 < len(parts):
                    last = int(parts[i + 1])
    if last is None:
        raise SystemExit("no nodes line before bestmove")
    return last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--switch", default="absent")
    parser.add_argument("--max", type=int, default=0)
    args = parser.parse_args()
    fens = load_fens(args.fens, args.max)
    digest = hashlib.sha256(open(args.exe, "rb").read()).hexdigest()
    options = option_lines(args.switch)
    engine = Engine(args.exe)
    rows = []
    try:
        engine.send("uci")
        uci = engine.read_until("uciok", 30)
        id_name = ""
        for line in uci.splitlines():
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for line in options:
            engine.send(line)
            engine.send("isready")
            engine.read_until("readyok", 30)
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until("readyok", 30)
            engine.send("position fen " + fen)
            engine.send("isready")
            engine.read_until("readyok", 30)
            engine.send(f"go depth {args.depth}")
            chunk = engine.read_until("bestmove", 180)
            rows.append(nodes_of(chunk))
    finally:
        raw_path = args.out + ".txt"
        open(raw_path, "w", encoding="utf-8").write("".join(engine.log))
        engine.close()
    open(args.out + ".rows", "w", encoding="utf-8").write(
        "".join(f"{n}\n" for n in rows)
    )
    meta = [
        f"exe={args.exe}",
        f"sha256={digest}",
        f"id_name={id_name}",
        f"depth={args.depth}",
        f"fens={args.fens}",
        f"count={len(rows)}",
        f"switch={args.switch}",
    ]
    meta.extend(f"option={line}" for line in options)
    open(args.out + ".meta", "w", encoding="utf-8").write("\n".join(meta) + "\n")
    print(args.out, "n", len(rows), "sum", sum(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
