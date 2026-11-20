#!/usr/bin/env python3
"""Fixed-depth node harness.

Sends S14, then Threads 1 and Hash 16, then any extra Name=value arguments.
ucinewgame and isready before every go. isready after every setoption and
position. Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.raw: list[str] = []
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.lines.put(None)

    def send(self, line: str) -> None:
        self.raw.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> list[str]:
        deadline = time.monotonic() + timeout
        got: list[str] = []
        while time.monotonic() < deadline:
            remain = deadline - time.monotonic()
            try:
                line = self.lines.get(timeout=min(0.5, max(0.01, remain)))
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
                continue
            if line is None:
                break
            self.raw.append(line)
            got.append(line)
            lowered = line.lower()
            for bad in BAD:
                if bad.lower() in lowered:
                    raise RuntimeError(line)
            if predicate(line):
                return got
        raise TimeoutError("timed out waiting for engine")

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except (BrokenPipeError, OSError):
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def nodes_and_move(lines: list[str]) -> tuple[str, str]:
    nodes = ""
    move = ""
    for line in lines:
        parts = line.split()
        if line.startswith("info ") and "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
        if line.startswith("bestmove "):
            move = parts[1]
    if nodes == "" or move == "":
        raise RuntimeError("search did not report nodes and bestmove")
    return nodes, move


def ready(engine: Engine) -> None:
    engine.send("isready")
    engine.read_until(lambda line: line == "readyok", 60)


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: harness_search.py EXE OUT_PREFIX FEN_FILE DEPTH [Name=value ...]",
            file=sys.stderr,
        )
        return 2
    exe = Path(sys.argv[1]).resolve()
    prefix = Path(sys.argv[2])
    prefix.parent.mkdir(parents=True, exist_ok=True)
    fens = [line.strip() for line in Path(sys.argv[3]).read_text().splitlines() if line.strip()]
    depth = int(sys.argv[4])
    extra: list[tuple[str, str]] = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extra.append((name, value))
    options = S14 + extra
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    engine = Engine(exe)
    rows: list[str] = []
    id_name = ""
    error = ""
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok", 60)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            ready(engine)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            ready(engine)
            engine.send(f"position fen {fen}")
            ready(engine)
            engine.send(f"go depth {depth}")
            played = engine.read_until(lambda line: line.startswith("bestmove "), 120)
            nodes, move = nodes_and_move(played)
            rows.append(f"{index}\t{nodes}\t{move}")
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        engine.close()
        prefix.with_suffix(".raw.txt").write_text("\n".join(engine.raw) + "\n")
        prefix.with_suffix(".rows.tsv").write_text("\n".join(rows) + ("\n" if rows else ""))
        option_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
        meta = (
            f"exe={exe}\n"
            f"sha256={digest}\n"
            f"id_name={id_name}\n"
            f"depth={depth}\n"
            f"positions={len(fens)}\n"
            f"rows={len(rows)}\n"
            f"error={error}\n"
            f"options_sent:\n{option_lines}\n"
        )
        prefix.with_suffix(".meta").write_text(meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
