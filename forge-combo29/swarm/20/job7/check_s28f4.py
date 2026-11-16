#!/usr/bin/env python3
"""check_s28f4.py — seat 20, area 10 job 7: my OWN check of seat 28's S-F4.

Claim: the 0-node root adjudication also fires on `board.is_repetition()`, so a mate-in-1 board reached a THIRD
time by legal moves is adjudicated a draw (cp 0, 0 nodes, first legal move) while the same board given by
`position fen` finds the mate.

How I build it (my own construction, not theirs): take a mate-in-1 board, walk two reversible moves back and
forth so the board recurs; the THIRD occurrence is the one python-chess calls a claimable threefold.

usage: check_s28f4.py <exe> <outdir> [label]
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else "base"
os.makedirs(OUT, exist_ok=True)


def ask(lines, timeout=40.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    lock = threading.Lock()

    def rd():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rd, daemon=True).start()
    for line in lines:
        p.stdin.write(line + "\n")
        p.stdin.flush()
        if line.startswith("go"):
            t0 = time.monotonic()
            while time.monotonic() - t0 < timeout:
                with lock:
                    if any(x.startswith("bestmove") for x in out):
                        break
                time.sleep(0.002)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=15)
    except Exception:
        p.kill()
    with lock:
        return list(out)


def parse(tr):
    bests = [x.split()[1] for x in tr if x.startswith("bestmove")]
    depths = [x for x in tr if x.startswith("info depth")]
    nodes = 0
    score = ""
    for x in depths:
        m = re.search(r"nodes (\d+)", x)
        if m:
            nodes = max(nodes, int(m.group(1)))
    for x in reversed(depths):
        m = re.search(r"score (\S+(?: \S+)?)", x)
        if m:
            score = m.group(1)
            break
    return {"bestmove": bests[-1] if bests else "<none>", "nodes": nodes, "score": score,
            "depth_lines": len(depths), "san": sum(1 for x in tr if "AddressSanitizer" in x
                                                   or "runtime error:" in x)}


# ---- build the position myself ---------------------------------------------------------------------
# K+Q vs K, white to move, mate in 1 by Qd8#.  I put the mate in the position, then make the position recur by
# walking the white king out and back twice (reversible, no capture, no pawn move) so the SAME board appears
# three times: after the initial position, after 4 plies, after 8 plies.
BASE = chess.Board("6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
mates = [mv.uci() for mv in BASE.legal_moves if (lambda b: (b.push(mv), b.is_checkmate())[1])(BASE.copy())]
assert mates, "no mate in 1 in the seed board"
MATE = mates[0]

# Find reversible white+black move pairs that return to the same board.
def find_cycle(b):
    for wm in b.legal_moves:
        b1 = b.copy()
        b1.push(wm)
        if b1.is_checkmate():
            continue
        for bm in b1.legal_moves:
            b2 = b1.copy()
            b2.push(bm)
            for wm2 in b2.legal_moves:
                b3 = b2.copy()
                b3.push(wm2)
                if b3.is_checkmate():
                    continue
                for bm2 in b3.legal_moves:
                    b4 = b3.copy()
                    b4.push(bm2)
                    if b4.board_fen() == b.board_fen() and b4.turn == b.turn and \
                       b4.has_castling_rights(chess.WHITE) == b.has_castling_rights(chess.WHITE) and \
                       b4.has_castling_rights(chess.BLACK) == b.has_castling_rights(chess.BLACK) and \
                       b4.ep_square == b.ep_square:
                        return [wm.uci(), bm.uci(), wm2.uci(), bm2.uci()]
    return None


cycle = find_cycle(BASE)
assert cycle, "no 4-ply cycle found"
moves = cycle + cycle          # after 8 plies the board is back a THIRD time

b = BASE.copy()
occurrences = []
for i in range(len(moves) + 1):
    occurrences.append((i, b.fen(), b.can_claim_threefold_repetition(), b.is_repetition(3),
                        b.halfmove_clock))
    if i < len(moves):
        b.push_uci(moves[i])

print(f"exe {EXE} ({LABEL})")
print(f"base board  {BASE.fen()}")
print(f"mate in 1   {MATE}")
print(f"cycle       {cycle}")
print(f"occ  ply  can_claim_3fold  is_repetition(3)  halfmove  fen")
for ply, fen, claim, rep3, hm in occurrences:
    print(f"  {occurrences.index((ply, fen, claim, rep3, hm)):3d} {ply:4d} {str(claim):16s} {str(rep3):17s} {hm:8d}  {fen}")

PRE = ["uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready"]
cases = {}
# A: the board by FEN (no history)
tr = ask(PRE + [f"position fen {BASE.fen()}", "isready", "go depth 6"])
cases["A_fen_only"] = parse(tr)
# B: the bare start from the base board, then the same board via the 4-ply cycle (SECOND occurrence)
tr = ask(PRE + [f"position fen {BASE.fen()} moves {' '.join(cycle)}", "isready", "go depth 6"])
cases["B_second_occurrence"] = parse(tr)
# C: the THIRD occurrence
tr = ask(PRE + [f"position fen {BASE.fen()} moves {' '.join(moves)}", "isready", "go depth 6"])
cases["C_third_occurrence"] = parse(tr)

# check the engine and python-chess agree the third occurrence is a repetition
b3 = BASE.copy()
for m in moves:
    b3.push_uci(m)
assert b3.fen().split()[0] == BASE.fen().split()[0], "third occurrence is not the same board"
assert b3.can_claim_threefold_repetition(), "python-chess does not call it a threefold"

print()
print(f"{'case':22s} {'bestmove':8s} {'score':9s} {'nodes':6s} depth_lines")
for k, v in cases.items():
    print(f"{k:22s} {v['bestmove']:8s} {v['score']:9s} {v['nodes']:6d} {v['depth_lines']}")

res = {"exe": EXE, "label": LABEL, "base_fen": BASE.fen(), "mate": MATE, "cycle": cycle,
       "moves": moves, "third_occurrence_halfmove": b3.halfmove_clock,
       "third_can_claim_threefold": b3.can_claim_threefold_repetition(),
       "cases": cases,
       "occurrences": [{"ply": p, "fen": f, "claim": c, "rep3": r, "halfmove": h}
                       for p, f, c, r, h in occurrences]}
with open(os.path.join(OUT, f"check_s28f4_{LABEL}.json"), "w") as f:
    json.dump(res, f, indent=1)
print(f"\nwrote check_s28f4_{LABEL}.json")
