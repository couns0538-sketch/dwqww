#!/usr/bin/env python3
"""Measured depth search. S14, Threads 1, Hash 16. One engine process.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
After every setoption and every position, sends isready and reads to readyok.
ucinewgame + isready before every go.
"""
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


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 6:
        raise SystemExit(f"short fen line: {line!r}")
    return " ".join(parts[:6])


def load_fens(path: Path, limit: int | None) -> list[str]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(fen_of(line))
        if limit is not None and len(rows) >= limit:
            break
    return rows


class Engine:
    def __init__(self, exe: str) -> None:
        self.exe = exe
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

        def reader() -> None:
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.q.put(line)
            self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.lines.append("> " + line + "\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> list[str]:
        got: list[str] = []
        while True:
            try:
                line = self.q.get(timeout=timeout)
            except queue.Empty as exc:
                tail = "".join(self.lines[-40:])
                raise SystemExit("timeout waiting for engine\n" + tail) from exc
            if line is None:
                raise SystemExit("engine closed\n" + "".join(got))
            if not line.endswith("\n"):
                line += "\n"
            self.lines.append(line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP {bad}: {line}")
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


def nodes_from(lines: list[str]) -> int:
    found = None
    for line in lines:
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes line\n" + "".join(lines))
    return found


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: run_depth.py EXE FENS OUTSTEM DEPTH [limit|all] [Name=value ...]",
            file=sys.stderr,
        )
        return 2
    exe = sys.argv[1]
    limit = None if len(sys.argv) <= 5 or sys.argv[5] == "all" else int(sys.argv[5])
    fens = load_fens(Path(sys.argv[2]), limit)
    outstem = sys.argv[3]
    depth = int(sys.argv[4])
    extra = sys.argv[6:]
    options = [("Threads", "1"), ("Hash", "16"), *S14]
    for spec in extra:
        name, value = spec.split("=", 1)
        options.append((name, value))
    eng = Engine(exe)
    sent: list[str] = []
    try:
        eng.send("uci")
        uci_lines = eng.read_until(lambda s: s.startswith("uciok"), 30)
        ident = ""
        for line in uci_lines:
            if line.startswith("id name "):
                ident = line[len("id name ") :].strip()
        for name, value in options:
            cmd = f"setoption name {name} value {value}"
            sent.append(cmd)
            eng.send(cmd)
            eng.send("isready")
            eng.read_until(lambda s: s.startswith("readyok"), 30)
        rows = []
        for index, fen in enumerate(fens):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda s: s.startswith("readyok"), 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda s: s.startswith("readyok"), 30)
            eng.send(f"go depth {depth}")
            got = eng.read_until(lambda s: s.startswith("bestmove "), 180)
            nodes = nodes_from(got)
            best = ""
            for line in got:
                if line.startswith("bestmove "):
                    best = line.split()[1]
            rows.append((index, nodes, best, fen))
            print(f"{index} {nodes} {best}", flush=True)
        raw_path = Path(outstem + ".raw.txt")
        raw_path.write_text("".join(eng.lines))
        Path(outstem + ".rows.txt").write_text(
            "".join(f"{i} {n} {b} {f}\n" for i, n, b, f in rows)
        )
        digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
        Path(outstem + ".raw.txt.meta").write_text(
            "\n".join(
                [
                    f"exe: {exe}",
                    f"sha256: {digest}",
                    f"id name: {ident}",
                    "options sent:",
                    *sent,
                    "",
                ]
            )
        )
        print(f"SUM {sum(n for _, n, _, _ in rows)} N {len(rows)}", flush=True)
        return 0
    finally:
        raw_fail = Path(outstem + ".raw.txt")
        if not raw_fail.exists():
            raw_fail.write_text("".join(eng.lines))
        eng.close()


if __name__ == "__main__":
    sys.exit(main())
