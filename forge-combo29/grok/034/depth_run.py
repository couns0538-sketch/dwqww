#!/usr/bin/env python3
"""Fixed-depth node harness.

One engine process. Before every go: ucinewgame, isready, Hash 16, Threads 1,
then S14 in the brief's order, each followed by isready, then the position and
isready. Stops on unknown option, invalid value, invalid FEN, or illegal move.
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
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str, raw):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.raw = raw

    def send(self, line: str) -> None:
        self.raw.write(">>> " + line + "\n")
        self.raw.flush()
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done) -> list[str]:
        lines = []
        assert self.proc.stdout is not None
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.raw.write("<<< EOF\n")
                raise SystemExit("engine closed stdout early")
            line = line.rstrip("\n")
            self.raw.write("<<< " + line + "\n")
            self.raw.flush()
            lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    raise SystemExit(f"STOP {bad}: {line}")
            if done(line):
                return lines

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            raise SystemExit(f"short fen line: {line}")
        fens.append(" ".join(parts[:6]))
    return fens


def main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: depth_run.py EXE FENS DEPTH OUT_RAW OUT_META [Name=value ...]")
    exe, fens_path, depth, out_raw, out_meta = sys.argv[1:6]
    extra = []
    # optional trailing args: Name=value pairs sent after S14
    for item in sys.argv[6:]:
        name, value = item.split("=", 1)
        extra.append((name, value))
    fens = load_fens(Path(fens_path))
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    raw_path = Path(out_raw)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w") as raw:
        eng = Engine(exe, raw)
        eng.send("uci")
        uci_lines = eng.read_until(lambda line: line == "uciok")
        id_name = ""
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        options = [("Hash", "16"), ("Threads", "1"), *S14, *extra]
        for index, fen in enumerate(fens, start=1):
            raw.write(f"### position {index}\n")
            eng.send("ucinewgame")
            eng.ready()
            for name, value in options:
                eng.send(f"setoption name {name} value {value}")
                eng.ready()
            eng.send(f"position fen {fen}")
            eng.ready()
            eng.send(f"go depth {depth}")
            eng.read_until(lambda line: line.startswith("bestmove "))
            raw.write(f"### end {index}\n")
        eng.close()
    option_lines = "\n".join(f"setoption name {n} value {v}" for n, v in options)
    Path(out_meta).write_text(
        f"exe={exe}\nsha256={sha}\nid name {id_name}\ndepth={depth}\nfens={fens_path}\ncount={len(fens)}\noptions:\n{option_lines}\n"
    )
    print(f"wrote {out_raw} positions={len(fens)} sha256={sha}")


if __name__ == "__main__":
    main()
