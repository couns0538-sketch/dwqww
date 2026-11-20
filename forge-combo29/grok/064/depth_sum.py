#!/usr/bin/env python3
"""Fixed-depth node sum. ucinewgame + isready before every go.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import pathlib
import queue
import subprocess
import sys
import threading

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


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.stderr = ""

        def read_out() -> None:
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.lines.put(line.rstrip("\n"))
            self.lines.put(None)

        def read_err() -> None:
            assert self.proc.stderr is not None
            self.stderr = self.proc.stderr.read()

        self.out_thread = threading.Thread(target=read_out, daemon=True)
        self.err_thread = threading.Thread(target=read_err, daemon=True)
        self.out_thread.start()
        self.err_thread.start()
        self.log: list[str] = []
        self.id_name = ""

    def send(self, command: str) -> None:
        self.log.append(">> " + command)
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        got: list[str] = []
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty as exc:
                raise RuntimeError("timeout waiting for engine") from exc
            if line is None:
                raise RuntimeError("engine closed stdout")
            self.log.append("<< " + line)
            got.append(line)
            if any(bit in line for bit in STOP_BITS):
                raise RuntimeError("stop: " + line)
            if done(line):
                return got

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.err_thread.join(timeout=2)


def nodes_of(lines: list[str]) -> str:
    found = ""
    for line in lines:
        parts = line.split()
        if "nodes" in parts:
            found = parts[parts.index("nodes") + 1]
    if not found:
        raise RuntimeError("no nodes in search output")
    return found


def bestmove_of(lines: list[str]) -> str:
    for line in reversed(lines):
        if line.startswith("bestmove "):
            return line.split()[1]
    return ""


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: depth_sum.py EXE FENS DEPTH OUT_PREFIX EXTRA_OPTIONS", file=sys.stderr)
        return 2
    exe, fen_path, depth_s, prefix, extra = sys.argv[1:]
    depth = int(depth_s)
    extra_options = []
    if extra != "-":
        for item in extra.split(","):
            name, value = item.split("=", 1)
            extra_options.append((name, value))
    fens = [fen_of(line) for line in pathlib.Path(fen_path).read_text().splitlines() if line.strip()]
    engine = Engine(exe)
    out = pathlib.Path(prefix)
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok", 30)
        for line in uci_lines:
            if line.startswith("id name "):
                engine.id_name = line[len("id name ") :]
        for name, value in [*S14, *extra_options]:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
        rows = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"go depth {depth}")
            played = engine.read_until(lambda line: line.startswith("bestmove "), 300)
            nodes = nodes_of(played)
            move = bestmove_of(played)
            rows.append((index, nodes, move, fen))
            if index % 25 == 0:
                print(f"progress {index}/{len(fens)}", flush=True)
    finally:
        engine.close()
        raw_path = pathlib.Path(str(out) + ".raw.txt")
        raw_path.write_text("\n".join(engine.log) + "\n")
        pathlib.Path(str(out) + ".err").write_text(engine.stderr)
    node_lines = [f"{index}\t{nodes}\t{move}\t{fen}" for index, nodes, move, fen in rows]
    pathlib.Path(str(out) + ".nodes.txt").write_text("\n".join(node_lines) + "\n")
    options = [*S14, *extra_options]
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(pathlib.Path(exe))}",
        f"id name {engine.id_name}",
        "options",
        *[f"setoption name {name} value {value}" for name, value in options],
        f"depth {depth}",
        f"fens {fen_path}",
        f"count {len(rows)}",
    ]
    pathlib.Path(str(out) + ".meta").write_text("\n".join(meta) + "\n")
    total = sum(int(nodes) for _, nodes, _, _ in rows)
    first = " ".join(nodes for _, nodes, _, _ in rows[:3])
    print(f"positions {len(rows)}")
    print(f"sum {total}")
    print(f"first3 {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
