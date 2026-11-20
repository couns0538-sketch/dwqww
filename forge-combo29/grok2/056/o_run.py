#!/usr/bin/env python3
"""o_run.py EXE OUT.raw OUT.meta SWITCH
SWITCH is omit, false, or true.
S14, Threads 1, Hash 16, then IdeaS32 when SWITCH is false or true.
ucinewgame + isready before every position. go depth 12.
After every setoption and every position, isready and read through readyok.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import os
import select
import subprocess
import sys

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


class StopError(Exception):
    pass


class Engine:
    def __init__(self, path):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.buf = b""

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        while b"\n" not in self.buf:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                raise TimeoutError(f"no engine output for {timeout}s, held {self.buf[:200]!r}")
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                if self.buf:
                    line = self.buf.decode("utf-8", "replace")
                    self.buf = b""
                    return line
                return None
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        return raw.decode("utf-8", "replace")

    def read_until(self, done, timeout, sink):
        lines = []
        while True:
            line = self.readline(timeout)
            if line is None:
                raise StopError("engine closed stdout")
            sink.write(line + "\n")
            sink.flush()
            lines.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise StopError(line)
            if done(line):
                return lines

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def id_name(path):
    proc = subprocess.run(
        [path],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: o_run.py EXE OUT.raw OUT.meta omit|false|true")
    exe, out_path, meta_path, switch = sys.argv[1:]
    if switch not in ("omit", "false", "true"):
        sys.exit("switch must be omit, false, or true")
    here = os.path.dirname(os.path.abspath(__file__))
    fens_path = os.path.join(here, "first200.fens")
    with open(fens_path, encoding="utf-8") as f:
        fens = [line.strip() for line in f if line.strip()]
    if len(fens) != 200:
        sys.exit(f"expected 200 fens, got {len(fens)}")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    name = id_name(exe)
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch != "omit":
        options.append(("IdeaS32", switch))
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe={exe}\n")
        meta.write(f"sha256={sha}\n")
        meta.write(f"id name {name}\n")
        meta.write("id-name-source=separate uci invocation of this exe, not the measured process\n")
        meta.write("options:\n")
        for opt_name, value in options:
            meta.write(f"setoption name {opt_name} value {value}\n")
        meta.write("before-each-position=ucinewgame / isready / position fen / isready / go depth 12\n")
    engine = Engine(exe)
    try:
        with open(out_path, "w", encoding="utf-8") as sink:
            for opt_name, value in options:
                engine.send(f"setoption name {opt_name} value {value}")
                engine.send("isready")
                engine.read_until(lambda line: line == "readyok", 60, sink)
            for index, fen in enumerate(fens, start=1):
                engine.send("ucinewgame")
                engine.send("isready")
                engine.read_until(lambda line: line == "readyok", 60, sink)
                engine.send(f"position fen {fen}")
                engine.send("isready")
                engine.read_until(lambda line: line == "readyok", 60, sink)
                engine.send("go depth 12")
                engine.read_until(lambda line: line.startswith("bestmove "), 180, sink)
                if index % 25 == 0:
                    print(f"{index}/200", file=sys.stderr, flush=True)
    except (StopError, TimeoutError) as exc:
        print(f"STOP {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        engine.close()
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
