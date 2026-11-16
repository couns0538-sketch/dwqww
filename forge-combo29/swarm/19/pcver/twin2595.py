#!/usr/bin/env python3
"""twin2595.py EXE OUTDIR LABEL : the root-drawn fallback at src/search.cpp:2595 — reachable, and correct?

Two tests, one each way. Every search WAITS for `bestmove` before anything else is sent (19-F12: a piped quit
aborts the search and the answer tells you nothing).

TEST 1 — reachable by a GUI and must be correct: K+N vs K (insufficient material, legal moves exist).
         Any legal move draws, so the test is that the answer is LEGAL and the score is 0.

TEST 2 — the case FORGE_FIX_ROOT_DRAWN removes: a threefold repetition with a mate in one available,
         reached by a real move list. With the flag at its default 1 this must be SEARCHED (nodes > 0).
         If it answers 0 nodes on the first legal move, the fallback fired and the old defect is present.
         The base tree (flag absent) is expected to show exactly that.
"""
import os
import subprocess
import sys

import chess

exe, outdir, label = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        self.read_to(lambda l: l.startswith("uciok"))

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_to(self, pred, limit=20000):
        got = []
        for _ in range(limit):
            l = self.p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    def ready(self):
        self.send("isready")
        self.read_to(lambda l: l.startswith("readyok"))

    def search(self, go):
        self.send(go)
        block = self.read_to(lambda l: l.startswith("bestmove"))
        last_info = None
        best = None
        for l in block:
            if l.startswith("info depth"):
                last_info = l
            if l.startswith("bestmove"):
                best = l.split()[1] if len(l.split()) > 1 else None
        nodes, score = 0, None
        if last_info:
            if " nodes " in last_info:
                try:
                    nodes = int(last_info.split("nodes ")[1].split()[0])
                except (IndexError, ValueError):
                    nodes = 0
            if "score cp " in last_info:
                score = ("cp", int(last_info.split("score cp ")[1].split()[0]))
            elif "score mate " in last_info:
                score = ("mate", int(last_info.split("score mate ")[1].split()[0]))
        return best, nodes, score, last_info

    def close(self):
        try:
            self.send("quit")
            self.p.communicate(timeout=30)
        except Exception:  # noqa: BLE001
            self.p.kill()


out = ["# " + label, ""]

# ---------- TEST 1: insufficient material ----------
T1 = "8/8/8/4k3/8/8/8/4K1N1 w - - 0 1"
e = Eng()
e.send("position fen " + T1)
e.ready()
t1_best, t1_nodes, t1_score, t1_info = e.search("go depth 6")
e.close()
b1 = chess.Board(T1)
legal1 = [m.uci() for m in b1.legal_moves]
t1_legal = t1_best in legal1
out += ["## TEST 1 — K+N vs K (insufficient material; a GUI reaches this by playing the ending out)",
        "FEN: " + T1,
        "python-chess: is_insufficient_material=%s, legal moves=%d" % (b1.is_insufficient_material(), len(legal1)),
        "engine: bestmove %s (legal=%s)  score %s  nodes %d" % (t1_best, t1_legal, t1_score, t1_nodes),
        "raw last info: " + (t1_info or "(none)"),
        "TEST 1 verdict: %s" % ("REACHABLE and CORRECT (legal move, score 0 — every move draws here)"
                                if (t1_legal and t1_score == ("cp", 0))
                                else "REACHABLE but SUSPICIOUS (legal=%s score=%s)" % (t1_legal, t1_score)),
        ""]

# ---------- TEST 2: threefold repetition with mate in one ----------
BASE = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
SHUF = ["a1a2", "g8h8", "a2a1", "h8g8", "a1a2", "g8h8", "a2a1", "h8g8"]
bb = chess.Board(BASE)
played = []
for u in SHUF:
    mv = chess.Move.from_uci(u)
    if mv in bb.legal_moves:
        bb.push(mv)
        played.append(u)
e = Eng()
e.send("position fen %s moves %s" % (BASE, " ".join(played)))
e.ready()
t2_best, t2_nodes, t2_score, t2_info = e.search("go depth 8")
e.close()
mate_move = None
for mv in bb.legal_moves:
    bb2 = bb.copy()
    bb2.push(mv)
    if bb2.is_checkmate():
        mate_move = mv.uci()
        break
out += ["## TEST 2 — threefold repetition with a mate in one on the board",
        "position: %s moves %s" % (BASE, " ".join(played)),
        "python-chess: is_repetition(3)=%s, halfmove_clock=%d, mate-in-1 move=%s"
        % (bb.is_repetition(3), bb.halfmove_clock, mate_move),
        "engine: bestmove %s  score %s  nodes %d" % (t2_best, t2_score, t2_nodes),
        "raw last info: " + (t2_info or "(none)"),
        "TEST 2 verdict: the engine %s this repetition root -> the 2595 fallback %s"
        % ("SEARCHED" if t2_nodes > 0 else "did NOT search",
           "did not fire" if t2_nodes > 0 else "FIRED"),
        ""]

text = "\n".join(out)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
