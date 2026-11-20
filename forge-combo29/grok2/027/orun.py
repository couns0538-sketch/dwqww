#!/usr/bin/env python3
"""orun.py RAW META EXE [true|false]
Depth-12 node counts on ~/first200.fens.
S14, then Threads 1, then Hash 16. An optional last argument sends IdeaK4.
Raw stdout is only what the engine printed. .meta lists the exe, its sha256,
its id name, and every option line sent.
"""
import hashlib
import os
import select
import subprocess
import sys
import time
from pathlib import Path

RAW = Path(sys.argv[1])
META = Path(sys.argv[2])
EXE = Path(sys.argv[3]).resolve()
SWITCH = sys.argv[4] if len(sys.argv) > 4 else None
FENS = Path.home() / "first200.fens"
STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.buf = b""
        self.err = b""

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, done, timeout):
        lines = []
        end = time.time() + timeout
        while time.time() < end:
            if lines and done(lines[-1]):
                return lines
            wait = min(0.5, max(0.0, end - time.time()))
            ready, _, _ = select.select([self.proc.stdout], [], [], wait)
            if not ready:
                if self.proc.poll() is not None:
                    self._drain_stderr()
                    raise SystemExit(
                        "STOP: engine exited rc="
                        + str(self.proc.returncode)
                        + " last="
                        + (lines[-1] if lines else "")
                        + " err="
                        + self.err.decode("utf-8", "replace")[-400:]
                    )
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if chunk == b"":
                raise SystemExit("STOP: stdout closed")
            self.buf += chunk
            while b"\n" in self.buf:
                raw, self.buf = self.buf.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                lines.append(line)
                if any(bit in line for bit in STOP_BITS):
                    raise SystemExit("STOP: " + line)
                if done(line):
                    return lines
        raise SystemExit("STOP: timeout last=" + (lines[-1] if lines else ""))

    def _drain_stderr(self):
        if self.proc.stderr is None:
            return
        while True:
            ready, _, _ = select.select([self.proc.stderr], [], [], 0)
            if not ready:
                return
            chunk = os.read(self.proc.stderr.fileno(), 65536)
            if not chunk:
                return
            self.err += chunk

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        self._drain_stderr()


def main():
    fens = [line.strip() for line in FENS.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(fens) != 200:
        raise SystemExit(f"STOP: expected 200 fens, got {len(fens)}")
    options = list(S14)
    if SWITCH is not None:
        if SWITCH not in ("true", "false"):
            raise SystemExit("STOP: switch must be true or false")
        options.append(("IdeaK4", SWITCH))
    option_lines = [f"setoption name {name} value {value}" for name, value in options]
    eng = Engine(EXE)
    transcript = []
    id_line = ""
    try:
        eng.send("uci")
        got = eng.read_until(lambda line: line == "uciok", 30)
        transcript.extend(got)
        for line in got:
            if line.startswith("id name "):
                id_line = line
        if not id_line:
            raise SystemExit("STOP: no id name")
        for line in option_lines:
            eng.send(line)
            eng.send("isready")
            got = eng.read_until(lambda row: row == "readyok", 30)
            transcript.extend(got)
        for fen in fens:
            eng.send("ucinewgame")
            eng.send("isready")
            got = eng.read_until(lambda row: row == "readyok", 30)
            transcript.extend(got)
            eng.send("position fen " + fen)
            eng.send("isready")
            got = eng.read_until(lambda row: row == "readyok", 30)
            transcript.extend(got)
            eng.send("go depth 12")
            got = eng.read_until(lambda row: row.startswith("bestmove "), 120)
            transcript.extend(got)
    finally:
        eng.close()
        if eng.err:
            Path(str(RAW) + ".err").write_bytes(eng.err)
    RAW.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    META.write_text(
        "\n".join(
            [
                f"exe {EXE}",
                f"sha256 {sha256(EXE)}",
                id_line,
                "options:",
                *option_lines,
                f"fens {FENS}",
                f"positions {len(fens)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {RAW} lines {len(transcript)} id {id_line}")


if __name__ == "__main__":
    main()
