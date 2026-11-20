#!/usr/bin/env python3
"""Measurement harness for grok2 seat 080, arm 10.

honesty: one fresh engine process per command, no setoption.
orun: one process, S14 then Threads and Hash, optional HindsightDepth,
ucinewgame and isready before every position, isready after every
setoption and every position, go depth 12.

Raw engine stdout is written as-is. A .meta file records the exe path
this process started, its sha256, its id name, and every option line sent.
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
    ("Threads", "1"),
    ("Hash", "16"),
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe, raw):
        self.raw = raw
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.id_name = ""

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred):
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("STOP: engine closed stdout before the expected reply")
            self.raw.write(line)
            self.raw.flush()
            for mark in STOP_MARKS:
                if mark in line:
                    raise SystemExit(f"STOP: {line.rstrip()}")
            if line.startswith("id name "):
                self.id_name = line[len("id name "):].rstrip("\r\n")
            if pred(line):
                return line

    def handshake(self):
        self.send("uci")
        self.read_until(lambda line: line.startswith("uciok"))

    def isready(self):
        self.send("isready")
        self.read_until(lambda line: line.startswith("readyok"))

    def setoption(self, name, value):
        self.send(f"setoption name {name} value {value}")
        self.isready()

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        self.proc.stdin.close()
        rest = self.proc.stdout.read()
        if rest:
            self.raw.write(rest)
        return self.proc.wait(timeout=60)


def write_meta(path, exe, digest, id_name, options, command):
    lines = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={id_name}",
        f"command={command}",
        "options:",
    ]
    if options:
        lines.extend(options)
    else:
        lines.append("(none)")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def honesty(exe, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(exe)
    commands = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench depth 11 ")),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench depth 13 ")),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench depth 16 ")),
        ("perft5", "go perft 5", lambda line: line.startswith("nodes ")),
    ]
    for label, command, pred in commands:
        raw_path = out_dir / f"honesty_{label}.txt"
        print(f"honesty {command} -> {raw_path}", file=sys.stderr)
        with raw_path.open("w", encoding="utf-8") as raw:
            engine = Engine(exe, raw)
            # uci only identifies the engine. It is not a setoption.
            engine.handshake()
            engine.send(command)
            engine.read_until(pred)
            engine.close()
            id_name = engine.id_name
        write_meta(out_dir / f"honesty_{label}.meta", exe, digest, id_name, [], command)
        print(f"honesty {label} done", file=sys.stderr)


def orun(exe, fens_path, out_raw, out_meta, switch):
    options = list(S14)
    if switch is not None:
        options.append(("HindsightDepth", switch))
    sent = [f"setoption name {name} value {value}" for name, value in options]
    fens = [line.strip() for line in Path(fens_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(fens) != 200:
        raise SystemExit(f"STOP: expected 200 fens, got {len(fens)}")
    digest = sha256_file(exe)
    print(f"orun switch={switch} -> {out_raw}", file=sys.stderr)
    with open(out_raw, "w", encoding="utf-8") as raw:
        engine = Engine(exe, raw)
        engine.handshake()
        for name, value in options:
            engine.setoption(name, value)
        for index, fen in enumerate(fens, 1):
            engine.send("ucinewgame")
            engine.isready()
            engine.send(f"position fen {fen}")
            engine.isready()
            engine.send("go depth 12")
            engine.read_until(lambda line: line.startswith("bestmove"))
            if index % 50 == 0:
                print(f"position {index}", file=sys.stderr)
        engine.close()
        id_name = engine.id_name
    command = "go depth 12 x200"
    if switch is not None:
        command += f" HindsightDepth={switch}"
    write_meta(out_meta, exe, digest, id_name, sent, command)
    print(f"orun done {out_raw}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: measure.py honesty|orun ...")
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3])
    elif mode == "orun":
        # measure.py orun EXE FENS RAW META omit|true|false
        switch = sys.argv[6]
        if switch == "omit":
            switch = None
        elif switch not in ("true", "false"):
            raise SystemExit("switch must be omit, true, or false")
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], switch)
    else:
        raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    main()
