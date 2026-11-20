#!/usr/bin/env python3
"""Depth-12 node run. S14 options in the given order, then Threads and Hash.
Optional switch is sent after those, value true or false only.
ucinewgame + isready, then position + isready, before every position.
"""
import hashlib
import os
import select
import sys
import time
import subprocess

FORBID = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, path):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.pending = b""

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        got = []
        while time.monotonic() < deadline:
            if b"\n" in self.pending:
                raw, self.pending = self.pending.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                got.append(line)
                if predicate(line):
                    return got
                continue
            wait = max(0.0, deadline - time.monotonic())
            r, _, _ = select.select([self.proc.stdout], [], [], min(1.0, wait))
            if not r:
                if self.proc.poll() is not None:
                    raise SystemExit("STOP: engine exited")
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise SystemExit("STOP: engine closed stdout")
            self.pending += chunk
        raise SystemExit("STOP: timeout last=%r" % (got[-1] if got else None,))

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def forbid(lines):
    for line in lines:
        for bad in FORBID:
            if bad in line:
                raise SystemExit("STOP: %s" % line)


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: orun.py <exe> <fens> <rawout> [<switch> <true|false>]")
    exe, fens, rawout = sys.argv[1], sys.argv[2], sys.argv[3]
    switch = None
    if len(sys.argv) == 6:
        switch, sval = sys.argv[4], sys.argv[5]
        if sval not in ("true", "false"):
            sys.exit("switch value must be true or false")
    else:
        sval = None
    positions = [ln.strip() for ln in open(fens, encoding="utf-8") if ln.strip()]
    if len(positions) != 200:
        sys.exit("expected 200 fens, got %d" % len(positions))
    sent = []
    eng = Engine(exe)
    raw_lines = []
    try:
        eng.send("uci")
        sent.append("uci")
        lines = eng.read_until(lambda line: line == "uciok", 10.0)
        raw_lines.extend(lines)
        forbid(lines)
        id_name = ""
        for line in lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        opts = list(S14)
        if switch is not None:
            opts.append((switch, sval))
        for name, value in opts:
            cmd = "setoption name %s value %s" % (name, value)
            eng.send(cmd)
            sent.append(cmd)
            eng.send("isready")
            sent.append("isready")
            lines = eng.read_until(lambda line: line == "readyok", 10.0)
            raw_lines.extend(lines)
            forbid(lines)
        for i, fen in enumerate(positions, 1):
            eng.send("ucinewgame")
            sent.append("ucinewgame")
            eng.send("isready")
            sent.append("isready")
            lines = eng.read_until(lambda line: line == "readyok", 10.0)
            raw_lines.extend(lines)
            forbid(lines)
            cmd = "position fen %s" % fen
            eng.send(cmd)
            sent.append(cmd)
            eng.send("isready")
            sent.append("isready")
            lines = eng.read_until(lambda line: line == "readyok", 10.0)
            raw_lines.extend(lines)
            forbid(lines)
            eng.send("go depth 12")
            sent.append("go depth 12")
            lines = eng.read_until(lambda line: line.startswith("bestmove "), 120.0)
            raw_lines.extend(lines)
            forbid(lines)
            if i % 50 == 0 or i == 1:
                print("pos %d best %s" % (i, lines[-1]), flush=True)
    finally:
        eng.close()
    os.makedirs(os.path.dirname(rawout) or ".", exist_ok=True)
    with open(rawout, "w", encoding="utf-8") as f:
        f.write("\n".join(raw_lines) + "\n")
    meta = rawout + ".meta"
    with open(meta, "w", encoding="utf-8") as f:
        f.write("exe=%s\n" % os.path.abspath(exe))
        f.write("sha256=%s\n" % sha256_file(exe))
        f.write("id name %s\n" % id_name)
        f.write("fens=%s\n" % os.path.abspath(fens))
        f.write("fens_sha256=%s\n" % sha256_file(fens))
        f.write("options:\n")
        for line in sent:
            if line.startswith("setoption "):
                f.write(line + "\n")
    print("wrote %s lines %d" % (rawout, len(raw_lines)))


if __name__ == "__main__":
    main()
