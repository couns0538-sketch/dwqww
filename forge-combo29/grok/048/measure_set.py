#!/usr/bin/env python3
"""Depth search of a FEN list. S14, Threads 1, Hash 16, ucinewgame before every go.

Reads every line until readyok after each setoption and each position.
Stops on unknown option, invalid value, invalid FEN, illegal move.
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
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


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
        self.q: queue.Queue[str | None] = queue.Queue()
        self.lines: list[str] = []
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.rstrip("\r\n")
            self.lines.append(line)
            self.q.put(line)
        self.q.put(None)

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise TimeoutError("timed out waiting for engine")
            try:
                line = self.q.get(timeout=min(0.5, remain))
            except queue.Empty:
                if self.proc.poll() is not None:
                    raise RuntimeError(f"engine exited {self.proc.returncode}")
                continue
            if line is None:
                raise RuntimeError(f"engine closed stdout, exit {self.proc.poll()}")
            for bad in BAD:
                if bad in line:
                    raise RuntimeError(line)
            if predicate(line):
                return line

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def load_fens(path: Path) -> list[str]:
    fens = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # EPD opcodes, if any, start after the six FEN fields.
        parts = line.split()
        if len(parts) < 4:
            raise SystemExit(f"short fen line: {line}")
        fen = " ".join(parts[:6]) if len(parts) >= 6 else " ".join(parts[:4]) + " 0 1"
        fens.append(fen)
    return fens


def nodes_from_last_depth(lines: list[str], depth: int) -> int:
    found = None
    for line in lines:
        if line.startswith("bestmove"):
            break
        if not line.startswith("info depth "):
            continue
        parts = line.split()
        if "nodes" not in parts:
            continue
        try:
            shown = int(parts[2])
        except ValueError:
            continue
        if shown == depth:
            found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise RuntimeError(f"no info depth {depth} nodes line")
    return found


def main() -> None:
    if len(sys.argv) != 6:
        raise SystemExit("usage: measure_set.py EXE FENS DEPTH RAW_OUT NODES_OUT")
    exe, fen_path, depth_s, raw_out, nodes_out = sys.argv[1:]
    depth = int(depth_s)
    fens = load_fens(Path(fen_path))
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    sent = ["uci"]
    try:
        eng.send("uci")
        eng.read_until(lambda line: line == "uciok", 30)
        for name, value in [("Threads", "1"), ("Hash", "16"), *S14]:
            command = f"setoption name {name} value {value}"
            sent.append(command)
            eng.send(command)
            sent.append("isready")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 30)
        id_name = ""
        for line in eng.lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
                break
        rows = []
        for index, fen in enumerate(fens, start=1):
            before = len(eng.lines)
            eng.send("ucinewgame")
            sent.append("ucinewgame")
            eng.send("isready")
            sent.append("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send(f"position fen {fen}")
            sent.append(f"position fen {fen}")
            eng.send("isready")
            sent.append("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send(f"go depth {depth}")
            sent.append(f"go depth {depth}")
            eng.read_until(lambda line: line.startswith("bestmove "), 180)
            block = eng.lines[before:]
            nodes = nodes_from_last_depth(block, depth)
            rows.append((index, nodes, fen))
            if index % 25 == 0 or index == len(fens):
                print(f"{index} {nodes} sum {sum(n for _, n, _ in rows)}", flush=True)
        text = []
        text.append(f"exe={exe}")
        text.append(f"sha256={sha}")
        text.append(f"id_name={id_name}")
        text.append("options_sent:")
        text.extend(sent)
        text.append("engine_output:")
        text.extend(eng.lines)
        Path(raw_out).write_text("\n".join(text) + "\n")
        node_lines = [f"{index}\t{nodes}\t{fen}" for index, nodes, fen in rows]
        Path(nodes_out).write_text("\n".join(node_lines) + "\n")
        meta = Path(raw_out).with_suffix(Path(raw_out).suffix + ".meta.txt")
        # raw_out may already end in .txt; keep a sibling .meta.txt
        meta = Path(str(raw_out) + ".meta.txt")
        meta.write_text(
            f"exe={exe}\nsha256={sha}\nid_name={id_name}\n"
            + "options_sent:\n"
            + "\n".join(sent)
            + "\n"
        )
        print(f"SUM {sum(n for _, n, _ in rows)} POS {len(rows)}")
    finally:
        eng.close()


if __name__ == "__main__":
    main()
