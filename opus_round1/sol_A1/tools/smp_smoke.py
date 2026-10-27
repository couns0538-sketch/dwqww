#!/usr/bin/env python3
"""SMP smoke for UCI HistRework (Astra A1): searches with Threads 1 and 4 at HistRework 0 and 3.

usage: smp_smoke.py <forge_exe> [depth] [threads list]      (defaults: depth 9, threads 1,1,4)
For each (HistRework, Threads) pair: one engine process, `go depth <d>` on 4 positions (ucinewgame before every
second one), then `go movetime 300`, then `go infinite` + stop. Each search must return a bestmove that the
engine itself lists as legal (checked with `go perft 1` on the same position), and the process must exit 0 after
`quit`. The first two runs of the threads list must be Threads 1; their node counts must match (determinism).
On the PC run it with "1,1" (one thread per process); CI TSan runs "1,1,4". Exit 1 on any failure."""
import re
import subprocess
import sys
import threading

FENS = [
    "startpos",
    "fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "fen 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, pat, collect=None):
        rx = re.compile(pat)
        for line in self.p.stdout:
            if collect is not None:
                collect.append(line.rstrip("\n"))
            m = rx.search(line)
            if m:
                return m
        raise RuntimeError("engine exited before matching " + pat)


def legal_moves(eng, pos):
    eng.send("position " + pos)
    eng.send("go perft 1")
    lines = []
    eng.until(r"^nodes \d+", lines)
    return {l.split(":")[0].strip() for l in lines if ":" in l}


def run(exe, value, threads, depth):
    eng = Engine(exe)
    eng.send("uci")
    eng.until(r"^uciok")
    for opt in (f"Threads value {threads}", "Hash value 16", "OwnBook value false", f"HistRework value {value}"):
        eng.send("setoption name " + opt)
    eng.send("isready")
    eng.until(r"^readyok")
    results, nodes_total, ok = [], 0, True
    for i, pos in enumerate(FENS):
        if i % 2 == 0:
            eng.send("ucinewgame")
        legal = legal_moves(eng, pos)
        eng.send("position " + pos)
        eng.send(f"go depth {depth}")
        info = []
        m = eng.until(r"^bestmove (\S+)", info)
        best = m.group(1)
        nodes = [int(x) for x in re.findall(r" nodes (\d+)", " ".join(info))]
        nodes_total += nodes[-1] if nodes else 0
        good = best in legal
        ok &= good
        results.append(f"{pos.split()[0] if pos == 'startpos' else pos[4:30]}.. bestmove {best} {'legal' if good else 'ILLEGAL'}")
    for go in ("go movetime 300", "go infinite"):
        pos = FENS[1]
        legal = legal_moves(eng, pos)
        eng.send("position " + pos)
        eng.send(go)
        if go == "go infinite":
            t = threading.Timer(0.5, lambda: eng.send("stop"))
            t.start()
        m = eng.until(r"^bestmove (\S+)")
        good = m.group(1) in legal
        ok &= good
        results.append(f"{go}: bestmove {m.group(1)} {'legal' if good else 'ILLEGAL'}")
    eng.send("quit")
    rc = eng.p.wait(timeout=600)
    ok &= rc == 0
    return ok, nodes_total, rc, results


def main():
    exe = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    thread_list = [int(t) for t in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 1, 4]
    all_ok = True
    for value in (0, 3):
        runs = []
        for threads in thread_list:
            ok, nodes, rc, lines = run(exe, value, threads, depth)
            all_ok &= ok
            runs.append((threads, nodes))
            print(f"{'PASS' if ok else 'FAIL'} HistRework={value} Threads={threads} depth {depth}: exit {rc}, "
                  f"depth-search nodes {nodes}", flush=True)
            for line in lines:
                print("    " + line, flush=True)
        same = runs[0][1] == runs[1][1]
        all_ok &= same
        print(f"{'PASS' if same else 'FAIL'} HistRework={value} Threads=1 determinism: {runs[0][1]} == {runs[1][1]}", flush=True)
    print("smp_smoke " + ("PASS" if all_ok else "FAIL"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
