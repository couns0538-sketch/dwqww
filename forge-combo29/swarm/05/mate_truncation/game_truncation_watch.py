#!/usr/bin/env python3
"""game_truncation_watch.py EXE -- watch a whole match-clock game for mate-score truncation AND for move consistency.

S-F59 showed a truncated mate score did not change the move on two positions. This checks it in PLAY: play a
self-play game at the owner's clock, and for every move where the engine reports a mate score, (a) apply the 2N-1
rule and record any truncation, and (b) re-search the same position at a much larger budget to see whether a STRONGER
search would have played a different move. That is the end-to-end question: does the defect ever cost a move in a game?

PC20, Threads 1, Hash 16, OwnBook false. One process per side (WARM, as a real match is), recorded as such.
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
MAXPLY = int(sys.argv[2]) if len(sys.argv) > 2 else 90
CLOCK, INC = 6000, 60

OPTS = ["setoption name Threads value 1", "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
        "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
        "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
        "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
        "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
        "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
        "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
        "setoption name CuckooRep value true", "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
        "setoption name MateAlphaGuard value true"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci"); self.until("uciok")
        for o in OPTS:
            self.send(o); self.send("isready"); self.until("readyok")
        self.send("ucinewgame"); self.send("isready"); self.until("readyok")

    def send(self, x):
        self.p.stdin.write(x + "\n"); self.p.stdin.flush()

    def until(self, tok, lim=300):
        L = []; t0 = time.time()
        while time.time() - t0 < lim:
            l = self.p.stdout.readline()
            if l == "":
                return L, False
            l = l.rstrip(); L.append(l)
            if any(b in l for b in BAD):
                return L, False
            if l.startswith(tok):
                return L, True
        return L, False

    def go(self, cmd, fen):
        self.send(f"position fen {fen}"); self.send("isready"); self.until("readyok")
        t0 = time.monotonic()
        self.send(cmd)
        L, ok = self.until("bestmove")
        wall = time.monotonic() - t0
        if not ok:
            return None
        pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
        last = pv[-1] if pv else ""
        m = re.search(r"score (mate|cp) (-?\d+)", last)
        bm = next((x for x in L if x.startswith("bestmove")), "")
        moves = last.split(" pv ", 1)[1].split() if " pv " in last else []
        return dict(score=((m.group(1), int(m.group(2))) if m else None),
                    move=(bm.split()[1] if len(bm.split()) > 1 else None),
                    plies=len(moves), wall=wall)

    def close(self):
        try:
            self.send("quit"); self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


w = Eng()
b = Eng()
board = chess.Board()
wm = bm_ = CLOCK
rows = []
trunc_seen = 0
move_mismatch = 0

print(f"exe: {EXE}   clock {CLOCK}+{INC}   PC20, Threads 1, Hash 16, OwnBook false")
print(f"WARM process per side (as a real match). Watching every mate score against the 2N-1 rule.")
print(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| ply | side | score | pv plies | needed | truncated? | move | deep-budget move | same? |")
print("|---|---|---|---|---|---|---|---|---|")

for _ in range(MAXPLY):
    if board.is_game_over(claim_draw=True):
        break
    side = "white" if board.turn else "black"
    eng = w if board.turn else b
    cmd = f"go wtime {wm} btime {bm_} winc {INC} binc {INC}"
    r = eng.go(cmd, board.fen())
    if not r:
        print("NO BESTMOVE — stopping")
        break
    spent = int(r["wall"] * 1000)
    if board.turn:
        wm = wm - spent + INC
    else:
        bm_ = bm_ - spent + INC
    kind, val = r["score"] if r["score"] else (None, None)
    need = None
    trunc = False
    if kind == "mate" and val:
        need = 2 * abs(val) - 1 if val > 0 else 2 * abs(val)
        trunc = (r["plies"] != need)
        if trunc:
            trunc_seen += 1
    # only deep-check the positions that TRUNCATED, plus a same-move sanity check there
    deep_move = "-"; same = "-"
    if trunc:
        d = w.go(f"go nodes 250000", board.fen())
        if d:
            deep_move = d["move"] or "-"
            same = "yes" if deep_move == r["move"] else "**NO**"
            if deep_move != r["move"]:
                move_mismatch += 1
    if trunc:
        print(f"| {board.ply()} | {side} | {kind} {val:+d} | {r['plies']} | {need} | **YES** | "
              f"{r['move']} | {deep_move} | {same} |")
    try:
        mv = chess.Move.from_uci(r["move"])
        if mv not in board.legal_moves:
            print(f"ILLEGAL {r['move']} at ply {board.ply()}")
            break
        board.push(mv)
    except Exception as e:
        print(f"BAD MOVE {r['move']}: {e}")
        break

w.close(); b.close()
print()
print(f"plies played: {board.ply()}")
print(f"mate-score truncations seen during the game: {trunc_seen}")
print(f"of those, positions where a 250,000-node search played a DIFFERENT move: {move_mismatch}")
print(f"final position: {board.fen()}")
