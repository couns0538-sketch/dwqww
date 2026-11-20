#!/usr/bin/env python3
"""Fixed-depth node counts. S14, Threads 1, Hash 16, ucinewgame before every go."""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

S14 = [
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
]
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit(f"short fen line: {line}")
        fen = " ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts[:4]) + " 0 1"
        fens.append(fen)
        if limit and len(fens) >= limit:
            break
    return fens


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.queue: queue.Queue[str | None] = queue.Queue()
        self.log: list[str] = []

        def reader() -> None:
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.log.append(line)
                self.queue.put(line)
            self.queue.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> list[str]:
        collected: list[str] = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self.queue.get(timeout=0.5)
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise SystemExit("engine exited early")
                continue
            if line is None:
                raise SystemExit("engine closed stdout")
            text = line.rstrip("\n")
            collected.append(text)
            for mark in STOP_MARKS:
                if mark in text:
                    raise SystemExit(f"STOP {mark}: {text}")
            if predicate(text):
                return collected
        raise SystemExit("timeout waiting for engine")

    def close(self) -> None:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(lines: list[str]) -> int:
    found = None
    for line in lines:
        if " nodes " not in line:
            continue
        parts = line.split()
        if "nodes" in parts:
            found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes field")
    return found


def bestmove_of(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("bestmove "):
            return line.split()[1]
    raise SystemExit("no bestmove")


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit(
            "usage: depth_search.py EXE FENS DEPTH OUT_PREFIX [LIMIT] [extra setoption ...]"
        )
    exe = Path(sys.argv[1]).resolve()
    fens_path = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    out_prefix = Path(sys.argv[4]).resolve()
    limit = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5].lstrip("-").isdigit() else 0
    extra_start = 6 if len(sys.argv) > 5 and sys.argv[5].lstrip("-").isdigit() else 5
    extra = sys.argv[extra_start:]
    fens = load_fens(fens_path, limit)
    engine = Engine(str(exe))
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok", 30)
        options = list(S14) + list(extra)
        for option in options:
            engine.send(option)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
        id_name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        rows = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"go depth {depth}")
            go_lines = engine.read_until(lambda line: line.startswith("bestmove "), 180)
            nodes = nodes_of(go_lines)
            move = bestmove_of(go_lines)
            rows.append(f"{index} {nodes} {move} {fen}")
            print(f"{index} {nodes} {move}", flush=True)
    finally:
        log_path = Path(str(out_prefix) + ".log")
        log_path.write_text("".join(engine.log))
        engine.close()
    out_path = Path(str(out_prefix) + ".txt")
    out_path.write_text("\n".join(rows) + "\n")
    meta_path = Path(str(out_prefix) + ".meta")
    option_text = "\n".join(options)
    meta_path.write_text(
        f"exe: {exe}\nsha256: {sha256(exe)}\nid name: {id_name}\n"
        f"depth: {depth}\nfens: {fens_path}\ncount: {len(fens)}\n"
        f"options:\n{option_text}\n"
    )
    total = sum(int(row.split()[1]) for row in rows)
    print(f"SUM {total} positions {len(rows)}", flush=True)


if __name__ == "__main__":
    main()
