#!/usr/bin/env python3
"""Depth search of a FEN list. S14, Threads 1, Hash 16, ucinewgame before every go.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the raw engine output and a .meta file.
"""
import hashlib
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

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        fens.append(text.split(";")[0].strip())
    return fens


class Engine:
    def __init__(self, exe: Path):
        self.exe = exe
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.out_lines: list[str] = []

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
                err = ""
                if self.proc.stderr is not None:
                    err = self.proc.stderr.read()
                raise SystemExit(f"engine closed early\n{''.join(got)}\n{err}")
            self.out_lines.append(line)
            got.append(line)
            if any(mark in line for mark in STOP_MARKS):
                raise SystemExit("STOP " + line.rstrip())
            if done(line):
                return got

    def close(self) -> str:
        self.send("quit")
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        err = ""
        if self.proc.stderr is not None:
            err = self.proc.stderr.read()
        if err:
            self.out_lines.append("\n[stderr]\n")
            self.out_lines.append(err)
        return "".join(self.out_lines)


def id_name_from(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name ") :].rstrip()
    return ""


def main() -> int:
    if len(sys.argv) != 6:
        print("usage: search_positions.py EXE FENS DEPTH OUT_RAW EXTRA_SETOPTIONS", file=sys.stderr)
        return 2
    exe = Path(sys.argv[1])
    fens = load_fens(Path(sys.argv[2]))
    depth = int(sys.argv[3])
    out_raw = Path(sys.argv[4])
    extra = [line for line in sys.argv[5].split("|") if line]
    options = S14 + extra
    engine = Engine(exe)
    try:
        _run(engine, exe, fens, depth, out_raw, options, sys.argv[2])
    except SystemExit as exc:
        try:
            engine.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            engine.proc.kill()
        partial = "".join(engine.out_lines)
        if engine.proc.stderr is not None:
            partial += "\n[stderr]\n" + engine.proc.stderr.read()
        partial += "\n[runner]\n" + str(exc) + "\n"
        out_raw.parent.mkdir(parents=True, exist_ok=True)
        out_raw.write_text(partial)
        raise
    return 0


def _run(engine: Engine, exe: Path, fens: list[str], depth: int, out_raw: Path, options: list[str], fens_path: str) -> None:
    engine.send("uci")
    uci_lines = engine.read_until(lambda line: line.startswith("uciok"))
    ident = id_name_from(uci_lines)
    engine.send("isready")
    engine.read_until(lambda line: line.strip() == "readyok")
    for option in options:
        engine.send(option)
        engine.send("isready")
        engine.read_until(lambda line: line.strip() == "readyok")
    for index, fen in enumerate(fens):
        engine.send("ucinewgame")
        engine.send("isready")
        engine.read_until(lambda line: line.strip() == "readyok")
        engine.send(f"position fen {fen}")
        engine.send("isready")
        engine.read_until(lambda line: line.strip() == "readyok")
        engine.send(f"go depth {depth}")
        engine.read_until(lambda line: line.startswith("bestmove "))
        if (index + 1) % 25 == 0 or index + 1 == len(fens):
            print(f"searched {index + 1}/{len(fens)}", file=sys.stderr, flush=True)
    text = engine.close()
    out_raw.write_text(text)
    meta = [
        f"exe {exe}",
        f"sha256 {sha256(exe)}",
        f"id_name {ident}",
        "options",
        *options,
        f"depth {depth}",
        f"positions {len(fens)}",
        f"fens {fens_path}",
        "",
    ]
    out_raw.with_suffix(out_raw.suffix + ".meta").write_text("\n".join(meta))
    print(f"wrote {out_raw}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
