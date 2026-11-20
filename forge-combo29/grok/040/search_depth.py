#!/usr/bin/env python3
"""Depth search of a FEN/EPD file under Threads 1, Hash 16, then S14.

One engine process. After every setoption and every position command, sends
isready and reads every line up to readyok. Stops on unknown option, invalid
value, invalid FEN, or illegal move.

Usage:
  search_depth.py EXE FENS DEPTH PREFIX [LIMIT] [Name=value ...]
Writes PREFIX.raw and PREFIX.meta.
"""
import hashlib
import select
import subprocess
import sys
import time
from pathlib import Path

S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def load_fens(path: Path):
    fens = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        parts = text.split()
        if len(parts) >= 6:
            fens.append(" ".join(parts[:6]))
        else:
            fens.append(text)
    return fens

class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.raw = []
        self.buf = b""

    def send(self, line: str) -> None:
        self.raw.append(">> " + line)
        assert self.proc.stdin is not None
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_line(self, timeout: float) -> str:
        assert self.proc.stdout is not None
        deadline = time.monotonic() + timeout
        while b"\n" not in self.buf:
            if time.monotonic() > deadline:
                tail = self.buf.decode(errors="replace")[-200:]
                raise SystemExit("TIMEOUT waiting; buf=" + tail)
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.2)
            if not ready:
                if self.proc.poll() is not None and not self.buf:
                    raise SystemExit("engine exited")
                continue
            chunk = self.proc.stdout.read(65536)
            if not chunk:
                if self.buf:
                    tail = self.buf.decode(errors="replace").rstrip("\r")
                    self.raw.append(tail)
                    self.buf = b""
                raise SystemExit("engine closed stdout")
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        line = raw.decode(errors="replace").rstrip("\r")
        self.raw.append(line)
        for bad in BAD:
            if bad in line:
                raise SystemExit("STOP " + line)
        return line

    def read_until(self, done, timeout: float):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SystemExit("TIMEOUT waiting")
            line = self.read_line(remaining)
            if done(line):
                return

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

def main() -> int:
    exe = str(Path(sys.argv[1]).resolve())
    fen_path = Path(sys.argv[2])
    depth = int(sys.argv[3])
    prefix = Path(sys.argv[4])
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    extra = []
    if len(sys.argv) > 6:
        for item in sys.argv[6:]:
            name, value = item.split("=", 1)
            extra.append((name, value))
    fens = load_fens(fen_path)
    if limit:
        fens = fens[:limit]
    ident = subprocess.run(
        [exe], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False
    )
    id_name = ""
    for line in ident.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    eng = Engine(exe)
    failed = None
    try:
        eng.send("uci")
        eng.read_until(lambda line: line == "uciok", 30)
        options = S14 + extra
        for name, value in options:
            eng.send(f"setoption name {name} value {value}")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 30)
        for fen in fens:
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 30)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda line: line == "readyok", 60)
            eng.send(f"go depth {depth}")
            eng.read_until(lambda line: line.startswith("bestmove "), 180)
    except SystemExit as exc:
        failed = str(exc)
        eng.raw.append("!! " + failed)
    finally:
        eng.close()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".raw").write_text("\n".join(eng.raw) + "\n")
    option_lines = "\n".join(f"option {name} {value}" for name, value in (S14 + extra))
    meta = "\n".join(
        [
            f"exe={exe}",
            f"sha256={sha256(Path(exe))}",
            f"id_name={id_name}",
            f"fens={fen_path}",
            f"depth={depth}",
            f"count={len(fens)}",
            "options:",
            option_lines,
        ]
    ) + "\n"
    prefix.with_suffix(".meta").write_text(meta)
    print(f"wrote {prefix.with_suffix('.raw')} positions {len(fens)}")
    if failed:
        print(failed, file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
