#!/usr/bin/env python3
"""seat 24, cycle check C9: independent check of seat 19's 19-F25.

Their claim: on the PC r15 build (settings none, Threads 1), an ABORTED search publishes the current position's
FIRST MOVE IN THE ENGINE'S GENERATOR ORDER (with 0 info depth lines) — not a stale bestmove, not a literal a2a3.
Evidence they give: Black-to-move P1 aborted -> `bestmove a7a6`, which is the first line of that position's own
`go perft 1` divide, while python-chess's lexicographic first is a7a5. White-to-move P2 -> a2a3. And after a
completed search returning d2d4, an aborted search on P1 still gives a7a6, so nothing is stale.

Why this matters to my area: every harness of mine reads `bestmove` as the search's answer. If an aborted search
publishes a generator-order move with zero nodes, a harness that quits mid-search measures that instead of a real
answer (this is the same family as 19-F12, which my checks/harness_audit.py already established my runners avoid).

The check, all fresh processes, PC r15, Threads 1:
  1  P1 `go perft 1` -> the engine's own generator order (the first line of the divide)
  2  P1 aborted: `go depth 12` then `quit` immediately -> bestmove, and how many info depth lines came out
  3  P1 python-chess lexicographic first move, for the contrast they make
  4  P2 (white to move) aborted -> bestmove
  5  P1 after a COMPLETED search on P2 returning something: abort again -> same move? (their "not stale" clause)
An aborted run is only counted when it produced a bestmove line at all; if the engine exits without one, that is
recorded as MISSING and the specific claim is reported INCONCLUSIVE, never as a confirmation.
"""
import argparse
import queue
import subprocess
import sys
import threading
import time

import chess

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
P1 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"   # black to move
P2 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1"   # white to move


class E:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0)
        self.q = queue.Queue()
        threading.Thread(target=self._r, daemon=True).start()
        self.send("uci"); self.until(lambda l: l == "uciok", 30)
        for k, v in opts:
            self.send(f"setoption name {k} value {v}"); self.send("isready"); self.until(lambda l: l == "readyok", 30)
        self.send("ucinewgame"); self.send("isready"); self.until(lambda l: l == "readyok", 30)

    def _r(self):
        for l in self.p.stdout:
            self.q.put(l.decode("utf-8", "replace").rstrip())
        self.q.put(None)

    def send(self, s):
        try:
            self.p.stdin.write((s + "\n").encode()); self.p.stdin.flush()
        except Exception:
            pass

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


def perft_order(exe, fen, opts):
    e = E(exe, opts)
    e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 30)
    e.send("go perft 1")
    lines, ok = e.until(lambda l: l.startswith("nodes "), 60)
    e.close()
    return [l.split(":")[0] for l in lines if ":" in l and l.split(":")[0].strip()[:1].isalpha()]


def aborted(exe, fen, opts, depth=12, delay=0.0):
    """start a search, optionally wait `delay` s, then quit while it runs; return (bestmove, n_info_lines)."""
    e = E(exe, opts)
    e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 30)
    e.send(f"go depth {depth}")
    if delay:
        time.sleep(delay)
    e.send("quit")
    lines, _ = e.until(lambda l: False, 10)
    bm = [l for l in lines if l.startswith("bestmove")]
    info = [l for l in lines if l.startswith("info depth")]
    try:
        e.p.wait(10)
    except Exception:
        e.p.kill()
    return (bm[-1].split()[1] if bm else None), len(info)


def completed(exe, fen, opts, depth=6):
    e = E(exe, opts)
    e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 30)
    e.send(f"go depth {depth}")
    lines, _ = e.until(lambda l: l.startswith("bestmove"), 120)
    bm = [l for l in lines if l.startswith("bestmove")]
    return (bm[-1].split()[1] if bm else None), e


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

opts = [("Threads", 1), ("Hash", 16), ("OwnBook", "false")]

order1 = perft_order(a.exe, P1, opts)
order2 = perft_order(a.exe, P2, opts)
py1 = sorted(m.uci() for m in chess.Board(P1).legal_moves)
py2 = sorted(m.uci() for m in chess.Board(P2).legal_moves)

bm_ab1, n_ab1 = aborted(a.exe, P1, opts)
bm_ab2, n_ab2 = aborted(a.exe, P2, opts)
bm_ab1b, n_ab1b = aborted(a.exe, P1, opts)

# their "not stale" case: complete a search on P2 first, then abort on P1 in the SAME process
e = E(a.exe, opts)
e.send("position fen " + P2); e.send("isready"); e.until(lambda l: l == "readyok", 30)
e.send("go depth 8")
done, _ = e.until(lambda l: l.startswith("bestmove"), 120)
done_bm = done[-1].split()[1] if done and done[-1].startswith("bestmove") else None
e.send("position fen " + P1); e.send("isready"); e.until(lambda l: l == "readyok", 30)
e.send("go depth 12")
e.send("quit")
tail, _ = e.until(lambda l: False, 10)
bm_after = [l for l in tail if l.startswith("bestmove")]
bm_after = bm_after[-1].split()[1] if bm_after else None
n_after = len([l for l in tail if l.startswith("info depth")])

with open(a.out, "w") as f:
    def w(s):
        print(s); f.write(s + "\n")
    w("SEAT 19 19-F25 — independent check by seat 24 (PC r15 build, Threads 1, Hash 16, OwnBook false)")
    w("")
    w(f"P1 (black to move) = {P1}")
    w(f"P2 (white to move) = {P2}")
    w("")
    w("| measure | value |")
    w("|---|---|")
    w(f"| P1 engine `go perft 1` generator order (first 3) | {order1[:3]} |")
    w(f"| P1 python-chess lexicographic first (first 3) | {py1[:3]} |")
    w(f"| **P1 aborted bestmove** | **{bm_ab1 or 'MISSING'}** with {n_ab1} info depth lines |")
    w(f"| P1 aborted, repeated | {bm_ab1b or 'MISSING'} with {n_ab1b} info depth lines |")
    w(f"| P2 engine perft order (first 3) | {order2[:3]} |")
    w(f"| P2 python-chess first (first 3) | {py2[:3]} |")
    w(f"| **P2 aborted bestmove** | **{bm_ab2 or 'MISSING'}** with {n_ab2} info depth lines |")
    w(f"| completed search on P2 (depth 8) | {done_bm} |")
    w(f"| then P1 aborted in the same process | {bm_after or 'MISSING'} with {n_after} info depth lines |")
    w("")
    missing = [n for n, v in (("P1 aborted", bm_ab1), ("P2 aborted", bm_ab2), ("P1 after completed", bm_after))
               if v is None]
    if missing:
        w(f"ASSERTION: no bestmove line in: {missing}. The engine exited without publishing, so the specific")
        w("claim ('publishes the generator-order first move') cannot be confirmed or refuted this way.")
        w("VERDICT: INCONCLUSIVE")
        sys.exit(2)
    gen_match = (bm_ab1 == order1[0]) if order1 else False
    gen_match2 = (bm_ab2 == order2[0]) if order2 else False
    differs_from_python = (order1 and py1 and order1[0] != py1[0])
    not_stale = (bm_after == bm_ab1)
    zero_info = (n_ab1 == 0 and n_ab2 == 0)
    ok = gen_match and gen_match2 and differs_from_python and not_stale
    w("VERDICT: " + ("CONFIRMS seat 19 19-F25" if ok else "does NOT reproduce 19-F25 as stated"))
    w("")
    w(f"P1 aborted bestmove == P1's own generator-first move: {gen_match} ({bm_ab1} vs {order1[0] if order1 else '-'})")
    w(f"P2 aborted bestmove == P2's own generator-first move: {gen_match2} ({bm_ab2} vs {order2[0] if order2 else '-'})")
    w(f"engine generator order differs from python-chess lexicographic: {differs_from_python} "
      f"({order1[0] if order1 else '-'} vs {py1[0] if py1 else '-'})")
    w(f"aborted searches emitted 0 info depth lines: {zero_info} ({n_ab1}, {n_ab2})")
    w(f"not stale (same move after a completed search on the other side): {not_stale} ({bm_after} vs {bm_ab1})")
    w("")
    w("Consequence for harnesses (which is why this seat checked it): an aborted search answers with a move that")
    w("the engine has NOT evaluated. Any harness that closes stdin or sends `quit` while a search runs records that")
    w("move as the engine's answer. My runners read to `bestmove` before the next command, so they are not affected")
    w("(checks/harness_audit.py, 590 rows, none shaped like this artefact).")
