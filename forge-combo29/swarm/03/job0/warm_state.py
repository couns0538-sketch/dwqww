#!/usr/bin/env python3
"""warm_state.py EXE OUT : does warm process state change the numbers MY results rest on?

Seat 10 reports (and I reproduced): two identical `go depth 12` searches in ONE process give 56,720 then 4,951 then
4,516 nodes, while three separate processes give 56,720 each; `ucinewgame` restores cold, `Clear Hash` does not.

My area-3 results are NOT depth searches — every number I published comes from `go perft d`, and my harnesses run
MANY positions in ONE process (500 positions per process in job 1). If perft were state-dependent, every one of my
tables would be wrong. This script measures that directly:

  A. perft 4 on one position, TEN times in one process, nothing between.
  B. perft 4 on the same position after `ucinewgame`.
  C. perft 4 on the same position after `Clear Hash`.
  D. perft 4 on the same position in TEN separate processes, each reading to the `nodes` line before `quit`.
  E. as a control that this harness CAN see warm-state effects, three `go depth 12` searches in one process.

Every number is read from the engine's output line, and the script FAILS if any read produced no number.
"""
import subprocess
import sys

EXE, OUT = sys.argv[1], sys.argv[2]

FEN = "r1bqk1nr/pppp1ppp/n7/4p3/3P3P/b3P3/PPP1QPP1/RNB1KBNR b KQkq - 2 4"  # a mid-game R position


class E:
    def __init__(self, log):
        self.log = open(log, "w")
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(self, c):
        self.log.write(f">>> {c}\n")
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def until(self, tok, keep=True):
        got = []
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise RuntimeError(f"engine died waiting for {tok!r}")
            self.log.write(line)
            self.log.flush()
            s = line.strip()
            got.append(s)
            if s.startswith(tok):
                return got

    def close(self):
        self.send("quit")
        try:
            self.p.wait(timeout=60)
        except Exception:  # noqa: BLE001
            self.p.kill()
        self.log.close()


def nodes_of(lines):
    """the `nodes <N>` total of a perft, or raise — never return None/a default."""
    for s in reversed(lines):
        if s.startswith("nodes "):
            return int(s.split()[1])
    raise RuntimeError(f"no `nodes ` line in: {lines[-3:]}")


def depth_nodes(lines):
    vals = [s for s in lines if " nodes " in s and s.startswith("info depth")]
    if not vals:
        raise RuntimeError("no info depth line with a node count")
    return int(vals[-1].split(" nodes ")[1].split()[0])


rows = []

# A: ten perfts in one process, nothing between
e = E(f"{OUT}.a.raw")
e.send("uci"); e.until("uciok")
e.send("isready"); e.until("readyok")
e.send("ucinewgame"); e.send("isready"); e.until("readyok")
e.send(f"position fen {FEN}"); e.send("isready"); e.until("readyok")
a_vals = []
for i in range(10):
    e.send("go perft 4")
    a_vals.append(nodes_of(e.until("nodes ")))
e.close()
rows.append(("A perft 4 x10 in one process", a_vals))

# B: perft after ucinewgame
e = E(f"{OUT}.b.raw")
e.send("uci"); e.until("uciok")
e.send("isready"); e.until("readyok")
e.send(f"position fen {FEN}"); e.send("isready"); e.until("readyok")
e.send("go perft 4"); first = nodes_of(e.until("nodes "))
e.send("ucinewgame"); e.send("isready"); e.until("readyok")
e.send(f"position fen {FEN}"); e.send("isready"); e.until("readyok")
e.send("go perft 4"); after = nodes_of(e.until("nodes "))
e.close()
rows.append(("B perft 4, then ucinewgame, then perft 4", [first, after]))

# C: perft after Clear Hash
e = E(f"{OUT}.c.raw")
e.send("uci"); e.until("uciok")
opt = [s for s in open(f"{OUT}.c.raw").read().splitlines() if "Clear Hash" in s]
e.send("isready"); e.until("readyok")
e.send(f"position fen {FEN}"); e.send("isready"); e.until("readyok")
e.send("go perft 4"); first = nodes_of(e.until("nodes "))
e.send("setoption name Clear Hash"); e.send("isready"); e.until("readyok")
e.send(f"position fen {FEN}"); e.send("isready"); e.until("readyok")
e.send("go perft 4"); after_clear = nodes_of(e.until("nodes "))
e.close()
rows.append(("C perft 4, then Clear Hash, then perft 4", [first, after_clear]))

# D: ten separate processes
d_vals = []
for i in range(10):
    e = E(f"{OUT}.d{i}.raw")
    e.send("uci"); e.until("uciok")
    e.send("isready"); e.until("readyok")
    e.send("ucinewgame"); e.send("isready"); e.until("readyok")
    e.send(f"position fen {FEN}"); e.send("isready"); e.until("readyok")
    e.send("go perft 4")
    d_vals.append(nodes_of(e.until("nodes ")))
    e.close()
rows.append(("D perft 4 x10 in ten separate processes", d_vals))

# E: control — three depth searches in one process (must show the warm effect)
e = E(f"{OUT}.e.raw")
e.send("uci"); e.until("uciok")
e.send("isready"); e.until("readyok")
e.send("ucinewgame"); e.send("isready"); e.until("readyok")
e.send("position startpos")
e_vals = []
for i in range(3):
    e.send("go depth 12")
    e_vals.append(depth_nodes(e.until("bestmove")))
e.close()
rows.append(("E CONTROL go depth 12 x3 in one process", e_vals))

with open(OUT, "w") as f:
    for name, vals in rows:
        uniq = sorted(set(vals))
        f.write(f"{name}\n  values: {vals}\n  distinct: {uniq}  "
                f"{'STABLE' if len(uniq) == 1 else 'VARIES'}\n\n")
    f.write("Clear Hash option line seen in uci output: "
            f"{[l for l in open(f'{OUT}.c.raw').read().splitlines() if 'Clear Hash' in l]}\n")
print(open(OUT).read())
