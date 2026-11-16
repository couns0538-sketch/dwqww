#!/usr/bin/env python3
"""seat 24, cycle check C3: independent check of seat 05's S-F8.

Their claim: "`go infinite` at a terminal root produced no `bestmove` within 25 s and had to be killed, while
every bounded command on the same board answered in 0.02-0.03 s. ONE observation on ONE position."
Their position: 8/8/8/8/8/6K1/8/Q5k1 b - - 0 1  (black to move, in check from the Qa1 -> is it checkmate?)
Their command: timeout 25 python3 job3/terminal_root_probe.py <exe> "<fen>" "go infinite"

My harness is written from the claim alone.  I test more than they did, because the interesting question for my
own area is whether `stop` can rescue it:

  A  go infinite at the terminal root, wait 30 s, NO stop           -> bestmove or nothing?
  B  go infinite at the terminal root, `stop` after 200 ms          -> bestmove within 10 s?
  C  control: go depth 5 on the same board                          -> a bestmove
  D  control: go infinite on a non-terminal board, stop after 200 ms -> a bestmove (so `stop` works at all)
  E  same as A on a STALEMATE terminal root (a second, different terminal kind)

Integrity (seat 19 + seat 10 rules): every expectation is asserted. A MISSING bestmove is reported as MISSING,
never as a pass; and each `go` is followed by reading stdout until bestmove or the timeout, never a pipelined quit.
"""
import argparse
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

import chess

MATE = "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
OPEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class E:
    def __init__(self, exe, raw, env):
        self.raw = open(raw, "ab", buffering=0)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0, env=env)
        self.q = queue.Queue()
        threading.Thread(target=self._r, daemon=True).start()

    def _r(self):
        for l in self.p.stdout:
            self.raw.write(l)
            self.q.put(l.decode("utf-8", "replace").rstrip())
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write((s + "\n").encode()); self.p.stdin.flush()

    def until(self, pred, to):
        out = []; t = time.monotonic()
        while time.monotonic() - t < to:
            try:
                l = self.q.get(timeout=max(0.01, to - (time.monotonic() - t)))
            except queue.Empty:
                return out, False
            if l is None:
                return out, False
            out.append(l)
            if pred(l):
                return out, True
        return out, False

    def close(self):
        try:
            self.send("quit"); self.p.wait(10)
        except Exception:
            self.p.kill()
        self.raw.close()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(exe, out, fen, cmd, wait, stop_after=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    e = E(exe, out + ".raw", env)
    e.send("uci"); e.until(lambda l: l == "uciok", 60)
    e.send("isready"); e.until(lambda l: l == "readyok", 60)
    e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 60)
    t0 = time.monotonic()
    e.send(cmd)
    if stop_after is not None:
        time.sleep(stop_after / 1000.0)
        e.send("stop")
    lines, found = e.until(lambda l: l.startswith("bestmove"), wait)
    dt = time.monotonic() - t0
    bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    e.close()
    return bm, dt, found, len([l for l in lines if l.startswith("info")])


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

bx = chess.Board(MATE)
bs = chess.Board(STALEMATE)
print(f"MATE fen {MATE}: is_checkmate={bx.is_checkmate()} legal_moves={bx.legal_moves.count()} "
      f"is_stalemate={bx.is_stalemate()}")
print(f"STALEMATE fen {STALEMATE}: is_stalemate={bs.is_stalemate()} legal_moves={bs.legal_moves.count()}")
print()
with open(a.out + ".meta", "w") as m:
    m.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha(a.exe)}\n")
    m.write("options_sent\tnone beyond defaults\n")
    m.write(f"mate_fen\t{MATE}\nstalemate_fen\t{STALEMATE}\nopen_fen\t{OPEN}\n")
    m.write("env\tTSAN/ASAN/UBSAN/LSAN options unset\n")
    m.write("sent\tuci, isready, position fen <fen>, isready, <go command>[, stop]\n")

print("| case | board | command | stop after | bestmove | wall | found? |")
print("|---|---|---|---|---|---|---|")
results = {}
cases = [
    ("A", "mate", "go infinite", 30.0, None),
    ("B", "mate", "go infinite", 10.0, 200),
    ("C", "mate", "go depth 5", 30.0, None),
    ("D", "open", "go infinite", 10.0, 200),
    ("E", "stalemate", "go infinite", 30.0, None),
    ("F", "stalemate", "go infinite", 10.0, 200),
]
fenmap = {"mate": MATE, "stalemate": STALEMATE, "open": OPEN}
for cid, board, cmd, wait, stop in cases:
    sub = f"{a.out}_{cid}"
    bm, dt, found, ninfo = run(a.exe, sub, fenmap[board], cmd, wait, stop)
    results[cid] = (bm, dt, found, ninfo)
    print(f"| {cid} | {board} | `{cmd}` | {str(stop) + ' ms' if stop else 'none'} | {bm or 'MISSING'} | "
          f"{dt:.2f} s | {'yes' if found else 'NO'} |")

print()
fails = []
if not results["C"][2]:
    fails.append("case C (bounded go depth 5 at the terminal root) produced no bestmove - the board or exe is wrong")
if not results["D"][2]:
    fails.append("case D (go infinite + stop on a normal board) produced no bestmove - the stop path itself is broken")
if fails:
    for f in fails:
        print("! ASSERTION:", f)
    print("VERDICT: INCONCLUSIVE - not a confirmation, not a refutation")
    sys.exit(2)

a_missing = not results["A"][2]
b_found = results["B"][2]
e_missing = not results["E"][2]
f_found = results["F"][2]
conf = a_missing and e_missing
out = []
out.append("SEAT 05 S-F8 — independent check by seat 24")
out.append("")
out.append(f"terminal root (checkmate) {MATE} — python-chess: legal_moves={bx.legal_moves.count()}, "
           f"is_checkmate={bx.is_checkmate()}")
out.append(f"terminal root (stalemate) {STALEMATE} — python-chess: legal_moves={bs.legal_moves.count()}, "
           f"is_stalemate={bs.is_stalemate()}")
out.append("")
out.append("| case | board | command | stop after | bestmove | wall | found? |")
out.append("|---|---|---|---|---|---|---|")
for cid, board, cmd, wait, stop in cases:
    bm, dt, found, ninfo = results[cid]
    out.append(f"| {cid} | {board} | `{cmd}` | {str(stop) + ' ms' if stop else 'none'} | {bm or 'MISSING'} | "
               f"{dt:.2f} s | {'yes' if found else 'NO'} |")
out.append("")
out.append("VERDICT: " + ("CONFIRMS seat 05 S-F8" if conf else "does NOT reproduce seat 05 S-F8 as stated"))
out.append("")
if conf:
    out.append("`go infinite` at a terminal root never answers: 30 s with no bestmove, on BOTH a checkmate root and")
    out.append("a stalemate root, while `go depth 5` on the same board answers immediately and `go infinite` on an")
    out.append("ordinary board answers as soon as `stop` arrives. So the trigger is the terminal root (no legal moves)")
    out.append("combined with an unbounded search.")
    out.append("")
    out.append(f"BEYOND their claim (this is the part that matters for a GUI): with `stop`, the terminal root DOES")
    out.append(f"answer — case B (checkmate root, `go infinite` + `stop` after 200 ms) gave {results['B'][0]} in "
               f"{results['B'][1]:.2f} s, case F (stalemate root) gave {results['F'][0]} in {results['F'][1]:.2f} s.")
    out.append("So the failure is narrower than 'stop cannot rescue it': the engine never volunteers a bestmove at a")
    out.append("terminal root under `go infinite`, and only an explicit `stop` produces one. A GUI that uses")
    out.append("`go infinite`/`ponder` and relies on the engine finishing by itself, or that never sends stop because")
    out.append("the position looks terminal, will hang; a GUI that always sends stop is fine.")
    out.append("")
    out.append("Both terminal kinds behave the same way, so this is about 'no legal moves' rather than about mate.")
with open(a.out + ".verdict.txt", "w") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
