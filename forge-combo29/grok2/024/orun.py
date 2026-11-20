#!/usr/bin/env python3
"""O runs: S14, Threads 1, Hash 16, ucinewgame + isready, go depth 12.
Usage: orun.py <tag> <exe> [switch true|false]
tag is B, Poff, or Pon. switch is omitted for exe B.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
FENS = Path.home() / "first200.fens"
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
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.log = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        self.log.append(">> " + line)

    def read_until(self, prefixes: tuple[str, ...]) -> str:
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit(f"STOP: engine closed stdout. log_tail={self.log[-8:]}")
            line = line.rstrip("\n")
            self.log.append("<< " + line)
            low = line.lower()
            for mark in STOP_MARKS:
                if mark.lower() in low:
                    raise SystemExit(f"STOP: {line}")
            if line.startswith(prefixes):
                return line

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(line: str):
    parts = line.split()
    if "nodes" not in parts:
        return None
    return int(parts[parts.index("nodes") + 1])


def main() -> int:
    tag = sys.argv[1]
    exe = Path(sys.argv[2])
    switch = sys.argv[3] if len(sys.argv) > 3 else None
    switch_value = sys.argv[4] if len(sys.argv) > 4 else None
    fens = [ln.strip() for ln in FENS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(fens) != 200:
        raise SystemExit(f"STOP: expected 200 fens, got {len(fens)}")

    eng = Engine(exe)
    try:
        eng.send("uci")
        id_line = ""
        while True:
            line = eng.read_until(("id ", "option ", "uciok"))
            if line.startswith("id name "):
                id_line = line
            if line == "uciok":
                break
        options = []
        for name, value in S14:
            sent = f"setoption name {name} value {value}"
            options.append(sent)
            eng.send(sent)
            eng.send("isready")
            eng.read_until(("readyok",))
        if switch is not None:
            sent = f"setoption name {switch} value {switch_value}"
            options.append(sent)
            eng.send(sent)
            eng.send("isready")
            eng.read_until(("readyok",))

        rows = []
        for i, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(("readyok",))
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(("readyok",))
            eng.send("go depth 12")
            last_info = ""
            while True:
                line = eng.read_until(("info ", "bestmove "))
                if line.startswith("info "):
                    last_info = line
                    continue
                if line.startswith("bestmove "):
                    break
            n = nodes_of(last_info)
            if n is None:
                raise SystemExit(f"STOP: no nodes on last info before bestmove at {i}: {last_info}")
            rows.append((i, n, last_info))
            if i % 25 == 0:
                print(f"{tag} {i}/200 nodes {n}", flush=True)
    finally:
        eng.close()

    raw = OUT / f"o_{tag}.txt"
    with raw.open("w", encoding="utf-8") as f:
        for i, n, info in rows:
            f.write(f"{i}\t{n}\t{info}\n")
    (OUT / f"o_{tag}.log").write_text("\n".join(eng.log) + "\n", encoding="utf-8")
    (OUT / f"o_{tag}.meta").write_text(
        "\n".join(
            [
                f"exe {exe}",
                f"sha256 {sha256(exe)}",
                id_line if id_line else "id name MISSING",
                "options:",
                *options,
                "",
            ]
        ),
        encoding="utf-8",
    )
    total = sum(n for _, n, _ in rows)
    first = [n for _, n, _ in rows[:3]]
    print(f"{tag} sum {total} first {first[0]} {first[1]} {first[2]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
