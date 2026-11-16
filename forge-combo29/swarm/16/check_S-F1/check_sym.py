#!/usr/bin/env python3
"""check_sym.py EXE CONFIG OUT.tsv : my own harness for S-F1.

CONFIG: "default", "nonnue" (UseNNUE false), "deadmat" (DeadMaterial true), "both".
For every FEN it sends position / isready / eval / isready and compares with the colour mirror.
Checks every answer line up to readyok for unknown option / invalid value / invalid FEN / illegal move.
"""
import hashlib
import os
import subprocess
import sys

import chess

EXE, CONFIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

OPTS = {
    "default": [],
    "nonnue": [("UseNNUE", "false")],
    "deadmat": [("DeadMaterial", "true")],
    "both": [("UseNNUE", "false"), ("DeadMaterial", "true")],
}[CONFIG]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.send("uci")
        self.send("isready")
        uci = self.read_until()
        self.ids = [l for l in uci if l.startswith("id ")]
        self.known_options = {l.split("name ", 1)[1].split(" type")[0].strip()
                              for l in uci if l.startswith("option name ")}
        for name, val in OPTS:
            if name not in self.known_options:
                raise SystemExit(f"STOP: option {name} not in the engine's uci answer")
            self.send(f"setoption name {name} value {val}")
            self.send("isready")
            self.check(self.read_until())

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def read_until(self):
        lines = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                lines.append("<<EOF>>")
                break
            line = line.rstrip("\n")
            lines.append(line)
            if line.strip() == "readyok":
                break
        return lines

    def check(self, lines):
        for line in lines:
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    raise SystemExit("STOP: bad answer line: " + line)

    def evaluate(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        self.check(self.read_until())
        self.send("eval")
        self.send("isready")
        lines = self.read_until()
        self.check(lines)
        for line in lines:
            if line.startswith("info string eval"):
                return line
        return None


def parse(line):
    parts = line.split()
    out = {}
    for i, tok in enumerate(parts):
        if tok in ("hce", "nnue", "total") and i + 1 < len(parts):
            out[tok] = int(parts[i + 1])
    return out


def run_file(eng, path, out_fh):
    n = diff = invalid = 0
    with open(path) as fh:
        for line in fh:
            fen = line.strip()
            if not fen:
                continue
            try:
                mirror = chess.Board(fen).mirror().fen()
            except ValueError:
                invalid += 1
                continue
            a = eng.evaluate(fen)
            b = eng.evaluate(mirror)
            if a is None or b is None:
                continue
            da, db = parse(a), parse(b)
            d = [k for k in ("hce", "nnue", "total") if da.get(k) != db.get(k)]
            n += 1
            if d:
                diff += 1
                out_fh.write("\t".join([CONFIG, os.path.basename(path), fen, a, b, ",".join(d)]) + "\n")
    return n, diff, invalid


sha = hashlib.sha256(open(EXE, "rb").read()).hexdigest()
eng = Engine()
total = 0
diffs = 0
bad = 0
with open(OUT, "w") as out:
    out.write(f"# exe {EXE}\n# sha256 {sha}\n# config {CONFIG} options {OPTS}\n")
    out.write(f"# id lines {' | '.join(eng.ids)}\n")
    out.write("config\tfile\tfen\tengine_eval\tmirror_eval\tdiff_fields\n")
    for path in sys.argv[4:]:
        n, d, inv = run_file(eng, path, out)
        print(f"{CONFIG:8s} {os.path.basename(path):16s} pairs {n:6d} diffs {d:4d} py_invalid {inv}")
        total += n
        diffs += d
        bad += inv
eng.send("quit")
print(f"TOTAL {CONFIG}: pairs {total} diffs {diffs} py_invalid {bad}")
