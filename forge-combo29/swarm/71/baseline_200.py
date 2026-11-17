#!/usr/bin/env python3
"""Reproduce the 200-opening identity baseline exactly.

Conditions taken from the pinned provenance of the figure (swarm/08, seat 08 Step 1b):
per position `ucinewgame` + `isready`, then `position fen`, then `go depth 12`; Threads 1,
Hash 16, PC20's 20 option values plus OwnBook false, test net loaded with NNUEArchFile
first and then NNUEArch true. The expected node sum is 27,944,084 over the committed
`OG200.fens` (first 100 of O + first 100 of G).

Every search is awaited to `bestmove` under a wall-clock timeout; `go infinite` is never used.
Both the position reply and the `go` output are scanned for `invalid FEN`, because a refused
board would otherwise silently search the previous position.

Usage: baseline_200.py <engine> <net> <fens> <expected-sum> <out csv>
"""
import queue
import subprocess
import sys
import threading
import time

EXE, NET, FENS, EXPECTED, OUT = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
DEPTH = 12
TIMEOUT = 300.0

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self.send("uci")
        self.read_until("uciok")

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\n"))
        self.q.put(None)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, prefix, timeout=TIMEOUT):
        out = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timeout waiting for %r (last %r)" % (prefix, out[-1] if out else None))
            line = self.q.get(timeout=remaining)
            if line is None:
                raise EOFError("engine closed stdout waiting for %r" % prefix)
            out.append(line)
            if line.startswith(prefix):
                return out

    def sync(self):
        self.send("isready")
        return self.read_until("readyok")

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except Exception:
            self.p.kill()


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()]
    print("BASELINE positions_requested %d depth %d net %s" % (len(fens), DEPTH, NET))
    eng = Engine()
    eng.send("setoption name NNUEArchFile value " + NET)
    eng.sync()
    eng.send("setoption name NNUEArch value true")
    eng.sync()
    for key, value in PC20:
        eng.send("setoption name %s value %s" % (key, value))
        eng.sync()
    eng.send("setoption name Threads value 1")
    eng.sync()
    eng.send("setoption name Hash value 16")
    eng.sync()

    rows = []
    refused = 0
    missing_nodes = 0
    started = time.monotonic()
    for index, fen in enumerate(fens, 1):
        eng.send("ucinewgame")
        eng.sync()
        eng.send("position fen " + fen)
        pos = eng.sync()
        if any("invalid FEN" in line for line in pos):
            refused += 1
            print("BASELINE REFUSED position %d %s" % (index, fen))
            continue
        eng.send("go depth %d" % DEPTH)
        go_out = eng.read_until("bestmove")
        pre = []
        for line in go_out:
            if line.startswith("info depth"):
                break
            pre.append(line)
        if any("invalid FEN" in line for line in pre):
            refused += 1
            print("BASELINE REFUSED-in-go position %d %s" % (index, fen))
            continue
        nodes = None
        for line in go_out:
            if line.startswith("info depth") and "nodes" in line.split():
                parts = line.split()
                nodes = int(parts[parts.index("nodes") + 1])
        if nodes is None:
            missing_nodes += 1
        best = [l for l in go_out if l.startswith("bestmove")]
        rows.append((index, fen, nodes, best[-1].split()[1] if best else "-"))
        if index % 25 == 0:
            print("BASELINE progress %d/%d (%ds)" % (index, len(fens), int(time.monotonic() - started)))
    eng.close()

    total = sum(n for _, _, n, _ in rows if n is not None)
    print("BASELINE rows %d refused %d missing_nodes %d" % (len(rows), refused, missing_nodes))
    print("BASELINE node_sum %d expected %d match %d" % (total, EXPECTED, 1 if total == EXPECTED else 0))
    with open(OUT, "w") as handle:
        handle.write("index,fen,nodes,bestmove\n")
        for index, fen, nodes, best in rows:
            handle.write("%d,%s,%s,%s\n" % (index, fen, nodes, best))
        handle.write("TOTAL,%d,,%d\n" % (total, EXPECTED))
    return 0 if total == EXPECTED and refused == 0 and missing_nodes == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
