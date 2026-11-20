#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. Writes the engine's raw output and a .meta file.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
S14 is sent first, then Threads, Hash, and IdeaB1 when requested.
isready is read to readyok after every setoption and every position.
ucinewgame + isready is sent before every go.
"""
import hashlib
import pathlib
import subprocess
import sys
import time

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


class Session:
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
        self.lines: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, token: str, timeout: float) -> None:
        assert self.proc.stdout is not None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("engine closed stdout")
            self.lines.append(line)
            if any(mark in line for mark in STOP_MARKS):
                raise SystemExit(f"STOP saw {line.strip()}")
            if token in line:
                return
        raise SystemExit(f"timeout waiting for {token}")

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


def main() -> None:
    if len(sys.argv) != 6:
        raise SystemExit("usage: run_depth_set.py EXE POSITIONS DEPTH IDEA OUT_PREFIX")
    exe, positions, depth_text, idea, out_prefix = sys.argv[1:]
    depth = int(depth_text)
    if idea not in ("omit", "false", "true"):
        raise SystemExit("IDEA must be omit, false, or true")
    fens = []
    for raw in pathlib.Path(positions).read_text().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        fens.append(fen_of(raw))
    options = list(S14)
    if idea != "omit":
        options.append(f"setoption name IdeaB1 value {idea}")
    session = Session(exe)
    error = ""
    try:
        session.send("uci")
        session.read_until("uciok", 30)
        for option in options:
            session.send(option)
            session.send("isready")
            session.read_until("readyok", 30)
        per_position = 180 if depth <= 12 else 300
        for fen in fens:
            session.send("ucinewgame")
            session.send("isready")
            session.read_until("readyok", 30)
            session.send(f"position fen {fen}")
            session.send("isready")
            session.read_until("readyok", 30)
            session.send(f"go depth {depth}")
            session.read_until("bestmove", per_position)
    except SystemExit as exc:
        error = str(exc)
    finally:
        session.close()
    out = pathlib.Path(out_prefix)
    text = "".join(session.lines)
    out.write_text(text)
    id_name = ""
    for line in session.lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :].rstrip("\n")
            break
    meta = [
        f"exe={exe}",
        f"sha256={sha256(pathlib.Path(exe))}",
        f"id_name={id_name}",
        f"positions={positions}",
        f"depth={depth}",
        f"idea={idea}",
        f"count={len(fens)}",
        "options:",
        *options,
        "",
    ]
    out.with_suffix(out.suffix + ".meta").write_text("\n".join(meta))
    print(f"wrote {out} positions {len(fens)}", flush=True)
    if error:
        print(error, flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
