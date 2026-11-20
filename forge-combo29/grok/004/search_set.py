#!/usr/bin/env python3
"""Measured fixed-depth search. Stops on an illegal engine reply."""
import hashlib
import queue
import subprocess
import sys
import threading
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 4:
        raise SystemExit(f"not a position: {line}")
    if len(parts) >= 6 and parts[1] in ("w", "b"):
        return " ".join(parts[:6])
    return line.strip()


class Engine:
    def __init__(self, exe: Path):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.log: list[str] = []

        def reader() -> None:
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.lines.put(line)
            self.lines.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.log.append(">> " + command + "\n")
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        got: list[str] = []
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty as exc:
                raise SystemExit("timeout waiting for engine\n" + "".join(self.log[-40:])) from exc
            if line is None:
                raise SystemExit("engine closed stdout\n" + "".join(got))
            self.log.append(line)
            got.append(line)
            stripped = line.strip()
            for marker in BAD:
                if marker in stripped:
                    raise SystemExit(f"STOP {stripped}")
            if done(stripped):
                return got

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


def nodes_from(info_lines: list[str], depth: int) -> int:
    found = None
    for line in info_lines:
        if not line.startswith("info "):
            continue
        parts = line.split()
        if "depth" in parts and "nodes" in parts:
            if int(parts[parts.index("depth") + 1]) == depth:
                found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no depth nodes line\n" + "".join(info_lines[-20:]))
    return found


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 8:
        raise SystemExit(
            "usage: search_set.py --exe E --positions P --depth N --out PREFIX "
            "[--switch true|false] [--limit N] [--extra name=value]..."
        )
    exe = None
    positions = None
    depth = None
    out = None
    switch = None
    limit = None
    extras: list[tuple[str, str]] = []
    i = 0
    while i < len(args):
        key = args[i]
        if key == "--switch":
            switch = args[i + 1]
            i += 2
            continue
        if key == "--limit":
            limit = int(args[i + 1])
            i += 2
            continue
        if key == "--extra":
            name, value = args[i + 1].split("=", 1)
            extras.append((name, value))
            i += 2
            continue
        value = args[i + 1]
        if key == "--exe":
            exe = Path(value).resolve()
        elif key == "--positions":
            positions = Path(value)
        elif key == "--depth":
            depth = int(value)
        elif key == "--out":
            out = Path(value)
        else:
            raise SystemExit(f"unknown arg {key}")
        i += 2
    if exe is None or positions is None or depth is None or out is None:
        raise SystemExit("missing required argument")
    fens = [fen_of(line.strip()) for line in positions.read_text().splitlines() if line.strip()]
    if limit is not None:
        fens = fens[:limit]
    option_lines = [("Hash", "16"), ("Threads", "1")] + S14
    if switch is not None:
        option_lines.append(("LmrLateParentRelief", switch))
    option_lines.extend(extras)
    engine = Engine(exe)
    try:
        engine.send("uci")
        uci_lines = engine.read_until(lambda line: line == "uciok", 30)
        id_name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :].strip()
        for name, value in option_lines:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
        counts: list[int] = []
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"go depth {depth}")
            info = engine.read_until(lambda line: line.startswith("bestmove "), 180)
            counts.append(nodes_from(info, depth))
    finally:
        raw_path = Path(str(out) + ".raw.txt")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("".join(engine.log))
        engine.close()
    nodes_path = Path(str(out) + ".nodes.txt")
    nodes_path.write_text("".join(f"{n}\n" for n in counts))
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id name {id_name}",
        f"positions {positions}",
        f"count {len(counts)}",
        f"depth {depth}",
        f"sum {sum(counts)}",
    ]
    meta.extend(f"option {name} {value}" for name, value in option_lines)
    Path(str(out) + ".meta").write_text("\n".join(meta) + "\n")
    head = " ".join(str(n) for n in counts[:3])
    print(f"positions {len(counts)} sum {sum(counts)} first {head}")


if __name__ == "__main__":
    main()
