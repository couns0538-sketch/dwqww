#!/usr/bin/env python3
"""M1: per-option ON benches and same-process restore check for one Forge exe.

For every config (Name=Value) one fresh engine process does, in order:
  uci; Threads 1; Hash 16; OwnBook false; isready
  setoption Name=Value                      -> record every line the engine prints before readyok (the "echo")
  bench d (each depth)                      -> ON node counts
  go depth G on a fixed position list       -> ON go-path node counts (after ucinewgame per position)
  setoption Name=<default>                  -> record the echo
  bench d (each depth)                      -> must equal the OFF pins (same process)
  go depth G on the same positions          -> must equal a fresh all-default process (same process)
A fresh all-default process gives the OFF go-path reference. Exit 1 on any mismatch or engine error.

usage: m1_option_bench.py <exe> --config Name=Value:Default [--config ...] [--depths 11,13,16] [--go-depth 10]
                          [--json out.json]
"""
import argparse
import json
import re
import subprocess
import sys

OFF_PINS = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
GO_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
]
BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1, creationflags=BELOW_NORMAL)
        self.log = []

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def wait(self, pat):
        rx = re.compile(pat)
        seen = []
        for line in self.p.stdout:
            line = line.rstrip("\n")
            self.log.append(line)
            seen.append(line)
            m = rx.search(line)
            if m:
                return m, seen
        raise SystemExit("engine exited before matching %r; last lines: %r" % (pat, self.log[-5:]))

    def setopt(self, name, value):
        self.send(f"setoption name {name} value {value}")
        self.send("isready")
        _, seen = self.wait(r"^readyok")
        return [l for l in seen if l != "readyok"]

    def bench(self, d):
        self.send(f"bench {d}")
        m, _ = self.wait(rf"bench depth {d} nodes (\d+)")
        return int(m.group(1))

    def go_nodes(self, fen, depth):
        self.send("ucinewgame")
        self.send(f"position fen {fen}")
        self.send(f"go depth {depth}")
        nodes = None
        rx = re.compile(r"\bnodes (\d+)")
        while True:
            _, seen = self.wait(r"^(info .*\bnodes \d+|bestmove)")
            line = seen[-1]
            if line.startswith("bestmove"):
                return nodes, line
            m = rx.search(line)
            if m:
                nodes = int(m.group(1))

    def quit(self):
        self.send("quit")
        try:
            self.p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            self.p.kill()


def start(exe):
    e = Engine(exe)
    e.send("uci")
    e.wait(r"^uciok")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        e.send("setoption name " + o)
    e.send("isready")
    e.wait(r"^readyok")
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--config", action="append", default=[], help="Name=Value:Default")
    ap.add_argument("--depths", default="11,13,16")
    ap.add_argument("--go-depth", type=int, default=10)
    ap.add_argument("--json")
    a = ap.parse_args()
    depths = [int(x) for x in a.depths.split(",") if x]
    ok = True

    ref = start(a.exe)
    off_go = [ref.go_nodes(f, a.go_depth)[0] for f in GO_FENS]
    ref.quit()
    print(f"OFF go depth {a.go_depth} nodes {off_go}", flush=True)
    out = {"exe": a.exe, "depths": depths, "go_depth": a.go_depth, "off_go": off_go, "configs": []}

    for c in a.config:
        name, _, rest = c.partition("=")
        value, _, default = rest.partition(":")
        e = start(a.exe)
        echo_on = e.setopt(name, value)
        on = {d: e.bench(d) for d in depths}
        on_go = [e.go_nodes(f, a.go_depth)[0] for f in GO_FENS]
        echo_off = e.setopt(name, default)
        back = {d: e.bench(d) for d in depths}
        back_go = [e.go_nodes(f, a.go_depth)[0] for f in GO_FENS]
        e.quit()
        errors = [l for l in e.log if "ERROR" in l]
        restored = all(back[d] == OFF_PINS[d] for d in depths) and back_go == off_go
        changed = any(on[d] != OFF_PINS[d] for d in depths)
        ok &= restored and not errors
        row = {"option": name, "value": value, "default": default, "echo_on": echo_on, "echo_off": echo_off,
               "on": on, "on_go": on_go, "back": back, "back_go": back_go, "restored": restored,
               "changed": changed, "errors": errors}
        out["configs"].append(row)
        print(f"{name}={value}: ON " + "/".join(str(on[d]) for d in depths)
              + f" | go {on_go} | echo_on {echo_on!r} | back to {default}: "
              + "/".join(str(back[d]) for d in depths) + f" go {back_go} -> "
              + ("RESTORED" if restored else "NOT RESTORED") + ("" if changed else " (ON == OFF!)")
              + (f" ERRORS {errors}" if errors else ""), flush=True)
    if a.json:
        with open(a.json, "w", newline="\n") as f:
            json.dump(out, f, indent=1)
    print("M1 ALL RESTORED" if ok else "M1 FAILURE")
    sys.exit(0 if ok else 1)


main()
