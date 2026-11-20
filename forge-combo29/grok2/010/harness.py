#!/usr/bin/env python3
"""UCI harness for grok2 honesty checks and the three O runs.

A fresh engine process for every honesty line. No setoption on the honesty path.
After every setoption and every position this sends isready and reads every line
up to readyok. It stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


class Engine:
    def __init__(self, exe, raw_path):
        self.exe = str(Path(exe).resolve())
        self.raw = open(raw_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.options = []
        self.id_name = ""

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.raw.flush()
                raise SystemExit(f"STOP: engine closed stdout; last={lines[-5:]}")
            line = line.rstrip("\n")
            self.raw.write(line + "\n")
            self.raw.flush()
            lines.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise SystemExit(f"STOP: {line}")
            if done(line):
                return lines

    def ready(self):
        self.send("isready")
        self.read_until(lambda s: s == "readyok")

    def uci(self):
        self.send("uci")
        lines = self.read_until(lambda s: s == "uciok")
        for line in lines:
            if line.startswith("id name "):
                self.id_name = line[len("id name "):]
        self.ready()

    def setoption(self, name, value):
        cmd = f"setoption name {name} value {value}"
        self.options.append(cmd)
        self.send(cmd)
        self.ready()

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.raw.close()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: digest_read(handle), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_read(handle):
    return handle.read(1 << 20)


def write_meta(path, eng):
    lines = [
        f"exe={eng.exe}",
        f"sha256={sha256_file(eng.exe)}",
        f"id_name={eng.id_name}",
        "options:",
    ]
    lines.extend(eng.options if eng.options else ["(none)"])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def honesty_one(exe, outdir, label, commands, done):
    raw = Path(outdir) / f"{label}.txt"
    eng = Engine(exe, raw)
    try:
        eng.uci()
        for cmd in commands:
            eng.send(cmd)
            if cmd.startswith("position"):
                eng.ready()
            else:
                eng.read_until(done)
        write_meta(Path(outdir) / f"{label}.meta", eng)
    finally:
        eng.close()
    print(f"wrote {raw}", flush=True)


def honesty(exe, outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    prefix = sys.argv[4]
    jobs = [
        (f"{prefix}_bench11", ["bench 11"], lambda s: s.startswith("info string bench ")),
        (f"{prefix}_bench13", ["bench 13"], lambda s: s.startswith("info string bench ")),
        (f"{prefix}_bench16", ["bench 16"], lambda s: s.startswith("info string bench ")),
        (f"{prefix}_perft5", ["position startpos", "go perft 5"], lambda s: s.startswith("nodes ")),
    ]
    for label, commands, done in jobs:
        honesty_one(exe, outdir, label, commands, done)


def orun(exe, outdir, label, switch, value, fens_path):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    raw = Path(outdir) / f"{label}.txt"
    eng = Engine(exe, raw)
    try:
        eng.uci()
        for name, val in S14:
            eng.setoption(name, val)
        eng.setoption("Threads", "1")
        eng.setoption("Hash", "16")
        if switch != "-":
            eng.setoption(switch, value)
        fens = []
        for line in Path(fens_path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)
        for index, fen in enumerate(fens, 1):
            eng.send("ucinewgame")
            eng.ready()
            eng.send(f"position fen {fen}")
            eng.ready()
            eng.send("go depth 12")
            eng.read_until(lambda s: s.startswith("bestmove "))
            if index % 25 == 0:
                print(f"{label} position {index}", flush=True)
        write_meta(Path(outdir) / f"{label}.meta", eng)
    finally:
        eng.close()
    print(f"wrote {raw}", flush=True)


def main():
    cmd = sys.argv[1]
    if cmd == "honesty":
        honesty(sys.argv[2], sys.argv[3])
    elif cmd == "orun":
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
    else:
        sys.exit(
            "usage:\n"
            "  harness.py honesty EXE OUTDIR PREFIX\n"
            "  harness.py orun EXE OUTDIR LABEL SWITCH VALUE FENS\n"
            "SWITCH is - to omit the switch option"
        )


if __name__ == "__main__":
    main()
