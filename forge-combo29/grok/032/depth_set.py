#!/usr/bin/env python3
"""Depth-sum harness. One engine process. S14, Threads 1, Hash 16.

Usage: depth_set.py EXE FENFILE DEPTH TAG [extra setoption lines...]
Writes TAG.txt (raw), TAG.meta, TAG.nodes, TAG.sum next to this script.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
from pathlib import Path

OUT = Path(__file__).resolve().parent
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
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str] = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.raw: list[str] = []

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))
        self.lines.put("__EOF__")

    def send(self, command: str) -> None:
        self.raw.append(">> " + command)
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def wait_for(self, predicate, timeout: float) -> list[str]:
        got: list[str] = []
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty as exc:
                raise SystemExit("timeout after: " + (got[-1] if got else "nothing")) from exc
            if line == "__EOF__":
                raise SystemExit("engine exited after: " + (got[-1] if got else "nothing"))
            self.raw.append(line)
            got.append(line)
            lowered = line.lower()
            for bad in BAD:
                if bad.lower() in lowered:
                    raise SystemExit(f"STOP {bad}: {line}")
            if predicate(line):
                return got

    def ready(self) -> None:
        self.send("isready")
        self.wait_for(lambda line: line == "readyok", 60)

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name(exe: str) -> str:
    proc = subprocess.run(
        [exe],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return "MISSING"


def last_nodes(lines: list[str]) -> tuple[int, int]:
    nodes = None
    depth = None
    for line in lines:
        if not line.startswith("info ") or " nodes " not in line:
            continue
        parts = line.split()
        if "nodes" in parts:
            nodes = int(parts[parts.index("nodes") + 1])
        if "depth" in parts:
            depth = int(parts[parts.index("depth") + 1])
    if nodes is None:
        raise SystemExit("no info nodes in:\n" + "\n".join(lines[-20:]))
    return nodes, -1 if depth is None else depth


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: depth_set.py EXE FENFILE DEPTH TAG [setoption...]")
    exe, fenfile, depth_s, tag = sys.argv[1:5]
    depth = int(depth_s)
    extra = sys.argv[5:]
    fens = []
    for line in Path(fenfile).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line.split(" bm ")[0].strip())
    engine = Engine(exe)
    options = [
        "setoption name Hash value 16",
        "setoption name Threads value 1",
        *S14,
        *extra,
    ]
    try:
        for option in options:
            engine.send(option)
            engine.ready()
        rows = []
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.ready()
            engine.send("position fen " + fen)
            engine.ready()
            engine.send(f"go depth {depth}")
            got = engine.wait_for(lambda line: line.startswith("bestmove "), 180)
            nodes, seen_depth = last_nodes(got)
            rows.append((index, nodes, seen_depth, fen))
            if index % 50 == 0:
                print(f"{tag} {index}/{len(fens)}", flush=True)
    finally:
        engine.close()
        (OUT / f"{tag}.txt").write_text("\n".join(engine.raw) + "\n")
    digest = sha256(Path(exe))
    name = id_name(exe)
    (OUT / f"{tag}.meta").write_text(
        "\n".join(
            [
                f"exe={exe}",
                f"sha256={digest}",
                f"id_name={name}",
                f"fenfile={fenfile}",
                f"depth={depth}",
                f"positions={len(rows)}",
                "options:",
                *options,
                "",
            ]
        )
    )
    node_lines = [f"{index} {nodes} depth {seen}" for index, nodes, seen, _fen in rows]
    (OUT / f"{tag}.nodes").write_text("\n".join(node_lines) + "\n")
    total = sum(nodes for _i, nodes, _d, _f in rows)
    first = " ".join(str(nodes) for _i, nodes, _d, _f in rows[:3])
    summary = f"positions {len(rows)} sum {total} first {first}\n"
    (OUT / f"{tag}.sum").write_text(summary)
    print(summary, end="")


if __name__ == "__main__":
    main()
