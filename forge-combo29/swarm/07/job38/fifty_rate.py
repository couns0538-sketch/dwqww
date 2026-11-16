#!/usr/bin/env python3
"""fifty_rate.py OUTDIR

Turns 07-F3's single detailed case into a RATE, which is the number that says what FORGE_FIX_ROOT_DRAWN
is worth.

For each of the 20 fifty-move-counter-100 positions in the targeted sample:

  1. Is a counter-RESETTING move available?  A move that resets the halfmove clock is a capture or a
     pawn move (FIDE 9.3 / the fifty-move rule). python-chess decides this, not the engine.
  2. What does the BASE build answer, and what does the PC build answer?  (read from the differential
     already recorded, plus a fresh run so the pairing is certain)
  3. Is the base's `cp 0` actually a DRAW claim, and is it WRONG?

The "is it wrong" test follows file 6 but with the correction 07-F3 established: file 6's inequality
(2N-1 <= 100-counter) is only valid when the fifty-move draw CANNOT be reset. So:

  * if a resetting move exists and the side to move is winning (evaluable by asking a deep search on the
    SAME board with counter 0, which cannot be a fifty-move draw),
    then a base answer of `cp 0` is a WRONG draw declaration;
  * if no resetting move exists, the position really is drawn and base's `cp 0` is right.

The counter-0 probe is the independent referee: with the clock reset the fifty-move rule is out of the
way for 100 half-moves, so a mate or a winning score there means a win existed at the root.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

import chess

BASE = "/agent/repos/base/forge-combo29/build-rel/forge"
PC = "/agent/repos/pcbase/forge-combo29/build-pc/forge"


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=300):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen, depth=12):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for o in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(f"go depth {depth}")
    nodes, score, best = None, None, None
    while True:
        l = r.get(600)
        if l is None:
            best = "ABSENT"
            break
        if l.startswith("info depth") and " nodes " in l:
            m = re.search(r" nodes (\d+) ", l)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = f"{m.group(1)} {m.group(2)}"
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"nodes": nodes, "score": score, "best": best}


def resetting_moves(b):
    """Moves that reset the halfmove clock: pawn moves and captures."""
    out = []
    for m in b.legal_moves:
        pc = b.piece_at(m.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            out.append(m.uci())
        elif b.is_capture(m):
            out.append(m.uci())
    return out


def with_counter(fen, value):
    f = fen.split()
    f[4] = str(value)
    return " ".join(f)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    samples = json.load(open("../job37/raw/samples.json"))
    fif = [t for t in samples["targeted"] if t["tag"] == "fifty_move_100"]
    rows = []
    print(f"{'#':>2} {'resets':>7} {'base':>18} {'pc':>18} {'counter0 probe':>20} verdict")
    for i, t in enumerate(fif):
        fen = t["fen"]
        b = chess.Board(fen)
        resets = resetting_moves(b)
        base = search(BASE, fen)
        pc = search(PC, fen)
        # independent referee: the same board with the clock reset
        probe_fen = with_counter(fen, 0)
        probe = search(BASE, probe_fen)
        decisive = probe["score"] is not None and not probe["score"].startswith("cp 0")
        base_draw = base["score"] == "cp 0"
        if resets and base_draw and decisive:
            verdict = "BASE WRONG (win exists, reset available, base claimed a draw)"
        elif resets and base_draw and not decisive:
            verdict = "base draw, reset available but probe finds no win"
        elif not resets and base_draw:
            verdict = "base draw correct (no reset available)"
        elif base_draw and decisive:
            verdict = "base draw but probe sees a win, no reset"
        else:
            verdict = "base not a draw"
        rows.append({"i": i, "fen": fen, "resets": resets, "base": base, "pc": pc,
                     "probe_counter0": probe, "verdict": verdict})
        print(f"{i:>2} {len(resets):>7} {str(base['score']) + '/' + str(base['nodes']):>18} "
              f"{str(pc['score']) + '/' + str(pc['nodes']):>18} "
              f"{str(probe['score']) + '/' + str(probe['nodes']):>20} {verdict}", flush=True)

    n = len(rows)
    with_reset = [r for r in rows if r["resets"]]
    wrong = [r for r in rows if r["verdict"].startswith("BASE WRONG")]
    no_reset = [r for r in rows if not r["resets"]]
    print()
    print(f"fifty-move positions:                       {n}")
    print(f"  with a counter-resetting move available:  {len(with_reset)}")
    print(f"  with NO reset available (genuinely drawn): {len(no_reset)}")
    print(f"  base claims a draw while a win exists:     {len(wrong)}")
    print()
    print("THE RATE that says what ROOT_DRAWN is worth on this sample:")
    print(f"  {len(wrong)} of {n} fifty-move roots ({100.0 * len(wrong) / n:.0f}%) are base-tree "
          f"errors (a draw claimed where a win exists)")
    if with_reset:
        print(f"  {len(wrong)} of {len(with_reset)} of the reset-available ones "
              f"({100.0 * len(wrong) / len(with_reset):.0f}%)")
    json.dump(rows, open(os.path.join(outdir, "fifty_rate.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
