#!/usr/bin/env python3
"""UCI harness for grok swarm 2 seat 052.

A fresh engine process for every honesty line and every O run.
After every setoption and every position: isready, then read every line
up to readyok. Stop on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import select
import subprocess
import sys

STOP_MARKS = ("unknown option", "invalid value", "invalid fen", "illegal move")

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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.lines = []
        self.id_name = ""

    def send(self, text):
        self.proc.stdin.write((text + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
        if not ready:
            tail = self.lines[-5:]
            raise SystemExit(f"STOP timeout after {timeout}s; last lines: {tail}")
        raw = self.proc.stdout.readline()
        if raw == b"":
            tail = self.lines[-5:]
            raise SystemExit(f"STOP eof; last lines: {tail}")
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        self.lines.append(line)
        low = line.lower()
        for mark in STOP_MARKS:
            if mark in low:
                raise SystemExit(f"STOP: {line}")
        if line.startswith("id name ") and not self.id_name:
            self.id_name = line[len("id name "):]
        return line

    def read_until(self, predicate, timeout):
        while True:
            line = self.readline(timeout)
            if predicate(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def write_meta(path, exe, digest, id_name, options, extra):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"exe={exe}\n")
        handle.write(f"sha256={digest}\n")
        handle.write(f"id_name={id_name}\n")
        for key, value in extra:
            handle.write(f"{key}={value}\n")
        handle.write("options:\n")
        if options:
            for option in options:
                handle.write(option + "\n")
        else:
            handle.write("(none)\n")


def uci_hello(engine):
    engine.send("uci")
    engine.read_until(lambda line: line == "uciok", 30)
    engine.send("isready")
    engine.read_until(lambda line: line == "readyok", 30)


def send_option(engine, option):
    engine.send(option)
    engine.send("isready")
    engine.read_until(lambda line: line == "readyok", 30)


def honesty(exe, out_path, command, kind):
    digest = sha256_file(exe)
    engine = Engine(exe)
    try:
        uci_hello(engine)
        engine.send(command)
        if kind == "bench":
            engine.read_until(lambda line: line.startswith("info string bench "), 180)
        elif kind == "perft":
            engine.read_until(lambda line: line.startswith("nodes "), 180)
        else:
            raise SystemExit(f"bad kind {kind}")
    finally:
        engine.close()
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(engine.lines) + "\n")
        write_meta(out_path + ".meta", exe, digest, engine.id_name, [], [("command", command)])
    print(f"wrote {out_path} id={engine.id_name!r} lines={len(engine.lines)}")


def orun(exe, fen_path, out_path, switch):
    digest = sha256_file(exe)
    with open(fen_path, encoding="utf-8") as handle:
        fens = [line.strip() for line in handle if line.strip()]
    options = list(S14)
    if switch is not None:
        options.append(f"setoption name IdeaB1 value {switch}")
    engine = Engine(exe)
    out = open(out_path, "w", encoding="utf-8")
    try:
        uci_hello(engine)
        for option in options:
            send_option(engine, option)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send("position fen " + fen)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send("go depth 12")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
            if index % 25 == 0:
                print(f"{out_path} position {index}", flush=True)
    finally:
        engine.close()
        out.write("\n".join(engine.lines) + "\n")
        out.close()
        extra = [
            ("positions", fen_path),
            ("positions_sha256", sha256_file(fen_path)),
            ("depth", "12"),
            ("switch", "omit" if switch is None else switch),
            ("count", str(len(fens))),
        ]
        write_meta(out_path + ".meta", exe, digest, engine.id_name, options, extra)
    print(f"wrote {out_path} lines={len(engine.lines)}")


def main():
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif mode == "orun":
        switch = None if sys.argv[5] == "omit" else sys.argv[5]
        if switch not in (None, "true", "false"):
            raise SystemExit("switch must be omit, true, or false")
        orun(sys.argv[2], sys.argv[3], sys.argv[4], switch)
    else:
        raise SystemExit("usage: harness.py honesty|orun ...")


if __name__ == "__main__":
    main()
