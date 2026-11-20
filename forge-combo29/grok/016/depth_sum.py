#!/usr/bin/env python3
"""Fixed-depth node sum. One engine process. isready after every setoption and position."""
import hashlib
import subprocess
import sys
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

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


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
        self.log: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        assert self.proc.stdout is not None
        got: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout early")
            self.log.append(line)
            got.append(line)
            stripped = line.strip()
            for mark in STOP_MARKS:
                if mark in stripped:
                    raise SystemExit(f"STOP {stripped}")
            if done(stripped):
                return got

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda s: s == "readyok")

    def close(self) -> None:
        self.send("quit")
        self.proc.wait(timeout=30)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fen_of(line: str) -> str:
    text = line.strip()
    if not text or text.startswith("#"):
        return ""
    # EPD lines may carry opcodes after the 6 FEN fields.
    parts = text.split()
    if len(parts) < 4:
        raise SystemExit(f"bad fen line: {text}")
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return text


def main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: depth_sum.py EXE FENS DEPTH OUT_PREFIX LABEL [Name=value ...]")
    exe = Path(sys.argv[1]).resolve()
    fens_path = Path(sys.argv[2]).resolve()
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4])
    label = sys.argv[5]
    extras = []
    for item in sys.argv[6:]:
        if "=" not in item:
            raise SystemExit(f"extra option must be Name=value, got {item}")
        name, value = item.split("=", 1)
        extras.append((name, value))
    fens = [fen_of(line) for line in fens_path.read_text().splitlines()]
    fens = [fen for fen in fens if fen]
    engine = Engine(exe)
    id_name = ""
    engine.send("uci")
    for line in engine.read_until(lambda s: s == "uciok"):
        if line.startswith("id name "):
            id_name = line.strip()
    options = ["setoption name Hash value 16", "setoption name Threads value 1"]
    options += [f"setoption name {name} value {value}" for name, value in S14]
    options += [f"setoption name {name} value {value}" for name, value in extras]
    for option in options:
        engine.send(option)
        engine.ready()
    rows = []
    total = 0
    for index, fen in enumerate(fens, start=1):
        engine.send("ucinewgame")
        engine.ready()
        engine.send(f"position fen {fen}")
        engine.ready()
        engine.send(f"go depth {depth}")
        chunk = engine.read_until(lambda s: s.startswith("bestmove "))
        nodes = None
        best = ""
        for line in chunk:
            stripped = line.strip()
            if " nodes " in stripped and stripped.startswith("info "):
                parts = stripped.split()
                nodes = int(parts[parts.index("nodes") + 1])
            if stripped.startswith("bestmove "):
                best = stripped.split()[1]
        if nodes is None:
            raise SystemExit(f"no nodes for position {index}")
        total += nodes
        rows.append(f"{index} {nodes} {best} {fen}")
        if index % 50 == 0 or index == len(fens):
            print(f"{label} {index}/{len(fens)} running {total}", flush=True)
    engine.close()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = prefix.with_suffix(".txt")
    raw_path.write_text("".join(engine.log))
    rows_path = Path(str(prefix) + ".rows")
    rows_path.write_text("\n".join(rows) + "\n")
    meta = (
        f"exe {exe}\n"
        f"sha256 {sha256_file(exe)}\n"
        f"{id_name}\n"
        + "".join(f"option {line}\n" for line in options)
        + f"depth {depth}\n"
        f"fens {fens_path}\n"
        f"count {len(fens)}\n"
        f"sum {total}\n"
        f"label {label}\n"
    )
    prefix.with_suffix(".meta").write_text(meta)
    print(f"{label} SUM {total} positions {len(fens)}", flush=True)


if __name__ == "__main__":
    main()
