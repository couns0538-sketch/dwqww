#!/usr/bin/env python3
"""Fixed-depth node harness.

Sends S14, then Threads and Hash, then any extra options, with isready after
each setoption and after each position. ucinewgame + isready before every go.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
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
    ("Threads", "1"),
    ("Hash", "16"),
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
        self.log = []

    def send(self, line: str) -> None:
        self.log.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, predicate, limit: int = 100000) -> list[str]:
        assert self.proc.stdout is not None
        got = []
        for _ in range(limit):
            line = self.proc.stdout.readline()
            if line == "":
                self.log.append("<< EOF")
                raise SystemExit("engine closed stdout early")
            line = line.rstrip("\n")
            self.log.append("<< " + line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP {bad}: {line}")
            if predicate(line):
                return got
        raise SystemExit("read limit exceeded")

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) >= 6:
        return " ".join(parts[:6])
    return line.strip()


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit(
            "usage: measure_depth.py EXE FENS DEPTH OUTPREFIX [Name=value ...]"
        )
    exe, fen_path, depth_s, out_prefix = sys.argv[1:5]
    depth = int(depth_s)
    extra = []
    for item in sys.argv[5:]:
        name, value = item.split("=", 1)
        extra.append((name, value))
    fens = []
    for raw in Path(fen_path).read_text().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        fens.append(fen_of(raw))
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    id_lines = eng.read_until(lambda line: line == "uciok") if False else []
    eng.send("uci")
    uci_lines = eng.read_until(lambda line: line == "uciok")
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    options = list(S14) + extra
    rows = []
    try:
        for index, fen in enumerate(fens):
            for name, value in options:
                eng.send(f"setoption name {name} value {value}")
                eng.ready()
            eng.send("ucinewgame")
            eng.ready()
            eng.send(f"position fen {fen}")
            eng.ready()
            eng.send(f"go depth {depth}")
            go_lines = eng.read_until(lambda line: line.startswith("bestmove "))
            nodes = None
            for line in go_lines:
                if line.startswith("info ") and " nodes " in line and f"depth {depth} " in line:
                    parts = line.split()
                    nodes = int(parts[parts.index("nodes") + 1])
            if nodes is None:
                raise SystemExit(f"no depth {depth} nodes for position {index}")
            rows.append((index, nodes, fen))
            print(f"{index} {nodes}", flush=True)
    finally:
        raw_path = Path(out_prefix + ".txt")
        raw_path.write_text("\n".join(eng.log) + "\n")
        eng.close()
    row_path = Path(out_prefix + ".rows")
    with row_path.open("w") as handle:
        for index, nodes, fen in rows:
            handle.write(f"{index}\t{nodes}\t{fen}\n")
    total = sum(nodes for _, nodes, _ in rows)
    first = [str(nodes) for _, nodes, _ in rows[:3]]
    summary = Path(out_prefix + ".sum")
    summary.write_text(
        f"positions={len(rows)}\nsum={total}\nfirst3={' / '.join(first)}\n"
    )
    meta = Path(out_prefix + ".meta")
    option_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
    meta.write_text(
        f"exe={exe}\nsha256={sha}\nid_name={id_name}\ndepth={depth}\n"
        f"fen_file={fen_path}\npositions={len(rows)}\n"
        f"options:\n{option_lines}\n"
    )
    print(f"SUM {total} FIRST {' / '.join(first)} N {len(rows)}")


if __name__ == "__main__":
    main()
