#!/usr/bin/env python3
"""Fixed-depth node harness. One engine process. Stops on a bad UCI reply."""
import argparse
import hashlib
import os
import select
import subprocess
import sys
from pathlib import Path

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
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fen_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 6:
        raise SystemExit(f"short fen line: {line!r}")
    return " ".join(parts[:6])

class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.lines: list[str] = []
        self.pending = b""

    def send(self, text: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write((text + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout: float) -> str:
        assert self.proc.stdout is not None
        while b"\n" not in self.pending:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                self.proc.kill()
                raise SystemExit("timeout waiting for the engine")
            chunk = os.read(self.proc.stdout.fileno(), 1 << 16)
            if chunk == b"":
                self.proc.kill()
                raise SystemExit("engine closed stdout")
            self.pending += chunk
        raw, self.pending = self.pending.split(b"\n", 1)
        line = raw.decode("utf-8", "replace").rstrip("\r")
        self.lines.append(line)
        for bad in BAD:
            if bad in line:
                self.proc.kill()
                raise SystemExit(f"stopped on: {line}")
        return line

    def read_until(self, pred, timeout: float) -> str:
        while True:
            line = self.readline(timeout)
            if pred(line):
                return line

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

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--no-s14", action="store_true")
    args = parser.parse_args()
    exe = Path(args.exe).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fens = [fen_of(line) for line in Path(args.fens).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        fens = fens[: args.limit]
    options = [] if args.no_s14 else list(S14)
    options.extend(args.extra)
    engine = Engine(exe)
    id_name = ""
    try:
        engine.send("uci")
        engine.read_until(lambda line: line == "uciok", 30)
        id_name = next((line[len("id name "):] for line in engine.lines if line.startswith("id name ")), "")
        for option in options:
            engine.send(option)
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
            engine.send(f"go depth {args.depth}")
            nodes = None
            while True:
                line = engine.readline(120)
                if " nodes " in line and line.startswith("info "):
                    parts = line.split()
                    nodes = int(parts[parts.index("nodes") + 1])
                if line.startswith("bestmove "):
                    best = line.split()[1]
                    break
            if nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            rows.append((index, nodes, best))
            if index % 50 == 0:
                print(f"{args.tag} {index}/{len(fens)} running_sum {sum(n for _, n, _ in rows)}", flush=True)
    finally:
        engine.close()
    raw = out / f"{args.tag}.raw.txt"
    raw.write_text("\n".join(engine.lines) + "\n", encoding="utf-8")
    tsv = out / f"{args.tag}.rows.tsv"
    tsv.write_text("".join(f"{i}\t{n}\t{b}\n" for i, n, b in rows), encoding="utf-8")
    total = sum(n for _, n, _ in rows)
    first = " ".join(str(n) for _, n, _ in rows[:3])
    summary = out / f"{args.tag}.sum.txt"
    summary.write_text(
        f"tag {args.tag}\ncount {len(rows)}\ndepth {args.depth}\nsum {total}\nfirst {first}\n",
        encoding="utf-8",
    )
    asan = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True, check=False)
    asan_count = sum(1 for line in asan.stdout.splitlines() if "__asan_" in line)
    meta = out / f"{args.tag}.meta"
    meta_lines = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id_name {id_name}",
        f"asan_symbol_count {asan_count}",
        "options",
        *options,
    ]
    meta.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")
    print(summary.read_text(), end="")
    if asan.returncode != 0 and asan_count == 0:
        print(f"nm note {asan.stderr.strip()}")

if __name__ == "__main__":
    main()
