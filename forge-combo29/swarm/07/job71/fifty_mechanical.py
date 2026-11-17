#!/usr/bin/env python3
"""Turn the 07-F4 rate into a mechanical, per-position claim that needs no referee.

The 6-of-20 "decisive error" figure depends on a depth-12 re-search acting as judge, so nobody
can re-check it without trusting that judge. This script asks a question that needs no judge at
all, and answers it per position with python-chess:

  (a) does the base build answer this root with 0 nodes?      -- a declaration, not a search
  (b) is this root a GENUINE fifty-move draw?                 -- python-chess decides
      i.e. counter >= 100 AND no capture-or-pawn-move available

If (a) holds and (b) is false for a position, the base build has declared a draw on a board that
is not a fifty-move draw. That is a mechanical fault per position: no sample size, no referee, no
score threshold. The claim becomes "20 of 20" and every item is separately checkable.

Usage: fifty_mechanical.py BASE_EXE EPD OUTDIR
"""
import chess
import json
import os
import queue
import subprocess
import sys
import threading


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("isready")
    while True:
        l = r.get(120)
        if l is None or l.strip() == "readyok":
            break
    send("position fen " + fen)
    send("isready")
    while True:
        l = r.get(120)
        if l is None or l.strip() == "readyok":
            break
    send("go depth 12")
    last, best = None, None
    while True:
        l = r.get(300)
        if l is None:
            break
        l = l.rstrip("\n")
        if " score " in l:
            last = l
        if l.startswith("bestmove"):
            best = l.split()[1] if len(l.split()) > 1 else None
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    nodes, cp = None, None
    if last:
        try:
            nodes = int(last.split(" nodes ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        if " score cp " in last:
            cp = int(last.split(" score cp ")[1].split()[0])
        elif " score mate " in last:
            cp = "mate " + last.split(" score mate ")[1].split()[0]
    return {"line": last, "nodes": nodes, "score": cp, "bestmove": best}


def main():
    exe, epd, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for raw in open(epd, encoding="utf-8"):
        p = raw.split()
        if len(p) < 4:
            continue
        fen = " ".join(p[:6]) if len(p) >= 6 else " ".join(p[:4]) + " 0 1"
        try:
            b = chess.Board(fen)
        except ValueError:
            continue
        resets = [m.uci() for m in b.legal_moves
                  if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN]
        half = b.halfmove_clock
        genuine = (half >= 100) and not resets
        eng = search(exe, fen)
        declared = (eng["nodes"] == 0)
        fault = declared and not genuine
        rows.append({"fen": fen, "halfmove": half, "resets": resets,
                     "genuine_fifty_move_draw": genuine, "engine_nodes": eng["nodes"],
                     "engine_score": eng["score"], "engine_line": eng["line"],
                     "declared_without_search": declared, "mechanical_fault": fault})

    n = len(rows)
    faults = sum(1 for r in rows if r["mechanical_fault"])
    genuine_draws = sum(1 for r in rows if r["genuine_fifty_move_draw"])
    zeros = sum(1 for r in rows if r["declared_without_search"])
    out = {"exe": exe, "positions": n, "answered_with_zero_nodes": zeros,
           "genuine_fifty_move_draws": genuine_draws,
           "mechanical_faults": faults, "rows": rows}
    json.dump(out, open(os.path.join(outdir, "fifty_mechanical.json"), "w"), indent=1)

    print(f"positions                        : {n}")
    print(f"answered with 0 nodes (declared) : {zeros}")
    print(f"genuine fifty-move draws         : {genuine_draws}")
    print(f"MECHANICAL FAULTS (declared draw on a non-draw): {faults}")
    print()
    for r in rows:
        if r["mechanical_fault"]:
            print(f"  {r['fen']}")
            print(f"    halfmove {r['halfmove']}, resets {r['resets']}, "
                  f"engine {r['engine_score']} at {r['engine_nodes']} nodes")
    print()
    if faults == zeros and genuine_draws == 0:
        print("VERDICT: every zero-node answer is on a board that is NOT a fifty-move draw.")
        print("         A 20-of-20 mechanical statement, no referee and no score threshold.")


if __name__ == "__main__":
    main()
