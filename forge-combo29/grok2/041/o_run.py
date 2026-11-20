#!/usr/bin/env python3
"""o_run.py EXE FENS OUT_RAW META [SWITCH]
Depth-12 node count over each FEN. One engine process. S14, Threads 1 and
Hash 16 are sent before every position, each followed by isready. SWITCH is
omitted, or "false", or "true" for option IdeaB1. Stops on unknown option,
invalid value, invalid FEN or illegal move.

Talks to the engine with unbuffered binary pipes. A text-mode pipe stalled
against this executable (both sides blocked in read, no bytes exchanged).
"""
import hashlib
import os
import select
import subprocess
import sys

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
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.buf = b""

    def send(self, line):
        os.write(self.proc.stdin.fileno(), (line + "\n").encode())

    def readline(self, timeout):
        while b"\n" not in self.buf:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                raise SystemExit("STOP: timeout waiting for the engine")
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise SystemExit("STOP: engine closed stdout\n" + self.buf.decode("utf-8", "replace"))
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        return raw.decode("utf-8", "replace").rstrip("\r")

    def close(self):
        try:
            self.send("quit")
        except OSError:
            pass
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        self.proc.wait(timeout=30)


def main():
    exe, fens_path, out_raw, meta_path = sys.argv[1:5]
    switch = sys.argv[5] if len(sys.argv) > 5 else ""
    options = list(S14)
    if switch:
        if switch not in ("true", "false"):
            sys.exit(f"STOP: switch must be true or false, got {switch}")
        options.append(("IdeaB1", switch))
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    engine = Engine(exe)
    engine_lines = []

    def read_until(done, timeout):
        while True:
            line = engine.readline(timeout)
            engine_lines.append(line)
            if any(mark in line for mark in BAD):
                open(out_raw, "w", encoding="utf-8").write("\n".join(engine_lines) + "\n")
                engine.proc.kill()
                sys.exit("STOP: " + line)
            if done(line):
                return

    engine.send("uci")
    hello = []
    while True:
        line = engine.readline(30)
        engine_lines.append(line)
        hello.append(line)
        if line == "uciok":
            break
    id_name = next((line for line in hello if line.startswith("id name ")), "id name MISSING")
    engine.send("isready")
    read_until(lambda line: line == "readyok", 30)

    def apply_options():
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            read_until(lambda line: line == "readyok", 30)

    for index, fen in enumerate(fens, start=1):
        engine.send("ucinewgame")
        engine.send("isready")
        read_until(lambda line: line == "readyok", 30)
        engine.send("position fen " + fen)
        engine.send("isready")
        read_until(lambda line: line == "readyok", 30)
        apply_options()
        engine.send("go depth 12")
        read_until(lambda line: line.startswith("bestmove "), 120)
        if index % 50 == 0:
            print(f"{index}/{len(fens)}", flush=True)

    engine.close()
    open(out_raw, "w", encoding="utf-8").write("\n".join(engine_lines) + "\n")
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {sha}\n")
        meta.write(id_name + "\n")
        meta.write("options sent before every position, each followed by isready:\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
        meta.write(f"fens {fens_path}\n")
        meta.write(f"positions {len(fens)}\n")
    print(f"WROTE {out_raw} positions {len(fens)}", flush=True)


if __name__ == "__main__":
    main()
