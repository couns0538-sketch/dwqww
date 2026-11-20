#!/usr/bin/env python3
"""Depth-sum harness. One engine process. Waits for bestmove before the next command.

isready is sent after every setoption and every position, and every line up to
readyok is read. Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import os
import select
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line.split(";")[0].strip())
        if limit and len(fens) >= limit:
            break
    return fens


class Engine:
    def __init__(self, exe: Path, err_path: Path):
        self.err_file = err_path.open("w")
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err_file,
            bufsize=0,
        )
        self.buf = b""
        self.lines: list[str] = []
        self.sent: list[str] = []

    def send(self, line: str) -> None:
        self.sent.append(line)
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, done, timeout: float) -> None:
        assert self.proc.stdout is not None
        fd = self.proc.stdout.fileno()
        while True:
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode(errors="replace") + "\n"
                self.lines.append(line)
                low = line.lower()
                for mark in STOP_MARKS:
                    if mark.lower() in low:
                        raise RuntimeError(f"stop mark {mark!r} in {line.rstrip()}")
                if done(line):
                    return
            ready, _, _ = select.select([fd], [], [], timeout)
            if not ready:
                raise TimeoutError(f"no engine line for {timeout}s after {self.sent[-1]!r}")
            chunk = os.read(fd, 65536)
            if not chunk:
                raise RuntimeError("engine closed stdout")
            self.buf += chunk

    def ready(self) -> None:
        self.send("isready")
        self.read_until(lambda line: line.startswith("readyok"), 60)

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.err_file.close()


def main() -> int:
    exe = Path(sys.argv[1])
    fens_path = Path(sys.argv[2])
    out_prefix = Path(sys.argv[3])
    depth = int(sys.argv[4])
    extra_options = sys.argv[5:]
    limit = 0
    kept = []
    for token in extra_options:
        if token.startswith("--limit="):
            limit = int(token.split("=", 1)[1])
        else:
            kept.append(token)
    extra_options = kept
    fens = load_fens(fens_path, limit)
    options = [("Threads", "1"), ("Hash", "16"), *S14]
    for token in extra_options:
        name, value = token.split("=", 1)
        options.append((name, value))
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    engine = Engine(exe, Path(str(out_prefix) + ".err"))
    id_name = ""
    status = 0
    try:
        engine.send("uci")
        engine.read_until(lambda line: line.startswith("uciok"), 60)
        for line in engine.lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :].rstrip("\n")
        engine.ready()
        for fen in fens:
            engine.send("ucinewgame")
            engine.ready()
            for name, value in options:
                engine.send(f"setoption name {name} value {value}")
                engine.ready()
            engine.send(f"position fen {fen}")
            engine.ready()
            engine.send(f"go depth {depth}")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
    except Exception as exc:
        print(f"harness exception: {exc}", file=sys.stderr)
        status = 1
    finally:
        engine.close()
    raw_path = Path(str(out_prefix) + ".txt")
    raw_path.write_text("".join(engine.lines))
    Path(str(out_prefix) + ".sent").write_text("\n".join(engine.sent) + "\n")
    option_lines = "\n".join(f"setoption name {name} value {value}" for name, value in options)
    Path(str(out_prefix) + ".meta").write_text(
        "\n".join(
            [
                f"exe {exe}",
                f"sha256 {sha256(exe)}",
                f"id name {id_name}",
                f"fens {fens_path}",
                f"count {len(fens)}",
                f"depth {depth}",
                "options",
                option_lines,
                "",
            ]
        )
    )
    bestmoves = sum(1 for line in engine.lines if line.startswith("bestmove "))
    print(f"positions {len(fens)} bestmoves {bestmoves} raw {raw_path}")
    if bestmoves != len(fens):
        print("bestmove count does not match positions", file=sys.stderr)
        return 1
    return status


if __name__ == "__main__":
    sys.exit(main())
