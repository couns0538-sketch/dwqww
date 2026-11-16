#!/usr/bin/env python3
"""config_effect.py EXE FENS N : does each eval configuration actually change the numbers?

Reads the first N FENs of FENS, evaluates each under the four configurations in four long-lived processes
and prints, per configuration, how many positions have an hce or nnue or total value DIFFERENT from the
default configuration. A configuration that changes nothing would make seat 06's "4 configurations"
claim vacuous for that configuration.
"""
import subprocess
import sys

EXE, FENS, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
CONFIGS = {"default": [], "nonnue": [("UseNNUE", "false")],
           "deadmat": [("DeadMaterial", "true")], "both": [("UseNNUE", "false"), ("DeadMaterial", "true")]}


class Eng:
    def __init__(self, opts):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.send("uci"); self.send("isready"); self.read_until()
        for n, v in opts:
            self.send(f"setoption name {n} value {v}"); self.send("isready"); self.read_until()

    def send(self, c):
        self.p.stdin.write(c + "\n"); self.p.stdin.flush()

    def read_until(self):
        out = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                break
            l = l.rstrip("\n")
            out.append(l)
            if l.strip() == "readyok":
                break
        return out

    def ev(self, fen):
        self.send("position fen " + fen); self.send("isready"); self.read_until()
        self.send("eval"); self.send("isready")
        for l in self.read_until():
            if l.startswith("info string eval"):
                return l
        return None


fens = [l.strip() for l in open(FENS) if l.strip()][:N]
engines = {k: Eng(v) for k, v in CONFIGS.items()}
base = {f: engines["default"].ev(f) for f in fens}
for cfg in ("nonnue", "deadmat", "both"):
    changed = sum(1 for f in fens if engines[cfg].ev(f) != base[f])
    print(f"{cfg:8s} positions where the eval line differs from default: {changed} of {len(fens)}")
for e in engines.values():
    e.send("quit")
