#!/usr/bin/env python3
"""Job 3 R1 test: the root that is already drawn.

Cases, each run in its own process:
  1 third_occurrence_mate  the job's position after its 8-ply list: must play
                           d1d8 with a mate score
  2 clock100_mate          the same position at halfmove clock 100: must play d1d8
  3 third_no_mate          a third-occurrence root without a mate: must print at
                           least one `info depth` line with nodes > 0 and play a
                           legal move
  4 stalemate              stalemate root: answered as today (no legal move)
  5 checkmate              checkmate root: answered as today

Pass/fail is computed per case and printed as a table; the exit code is 0 when
every case passes. Raw engine output for every case is printed as well.
"""

import json
import queue
import subprocess
import sys
import threading
import time
import chess

ENGINE = sys.argv[1]
OUT = sys.argv[2]

MATE_FEN = "6k1/5ppp/8/8/8/1q6/8/R2Q2K1 w - - 0 1"
MATE_MOVES = "d1e2 b3c4 e2d1 c4b3 d1e2 b3c4 e2d1 c4b3"


def run(position_cmd, go="go depth 12", extra=(), settle=6.0):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def collect(until, limit):
        t0 = time.time()
        got = []
        while time.time() - t0 < limit:
            try:
                ln = q.get(timeout=max(0.01, limit - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if until and until(ln):
                break
        return got

    send("uci")
    collect(lambda l: l.strip() == "uciok", 10)
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    for e in extra:
        send(e)
    send("isready")
    collect(lambda l: l.strip() == "readyok", 10)
    send(position_cmd)
    send(go)
    lines = collect(lambda l: l.startswith("bestmove"), 30)
    send("quit")
    try:
        p.wait(timeout=10)
        rc = p.returncode
    except Exception:
        p.kill()
        rc = "killed"
    return {"lines": lines, "exit": rc}


def parse(res):
    best = None
    score = None
    maxnodes = 0
    depth_lines = 0
    for ln in res["lines"]:
        if ln.startswith("bestmove"):
            best = ln.split()[1]
        if ln.startswith("info") and " score " in ln:
            t = ln.split()
            i = t.index("score")
            score = (t[i + 1], int(t[i + 2]))
        if " nodes " in ln:
            try:
                n = int(ln.split(" nodes ")[1].split()[0])
                maxnodes = max(maxnodes, n)
            except Exception:
                pass
        if ln.startswith("info depth"):
            depth_lines += 1
    return {"best": best, "score": score, "maxnodes": maxnodes, "depth_lines": depth_lines}


def legal_moves_of(fen):
    b = chess.Board(fen)
    return {m.uci() for m in b.legal_moves}


def main():
    cases = []

    r = run("position fen " + MATE_FEN + " moves " + MATE_MOVES)
    info = parse(r)
    cases.append({"name": "third_occurrence_mate", "raw": r["lines"], **info,
                  "expect": "best d1d8, score mate + or a large win",
                  "pass": info["best"] == "d1d8" and info["score"] is not None
                          and info["score"][0] == "mate" and info["score"][1] > 0})

    # the same position, halfmove clock 100: the FEN AFTER the move list, with
    # only its clock changed (the list itself must not be replayed from a 100 clock,
    # which would push the clock past 100).
    after = chess.Board(MATE_FEN)
    for u in MATE_MOVES.split():
        after.push_uci(u)
    parts = after.fen().split()
    parts[4] = "100"
    fen100 = " ".join(parts)
    r = run("position fen " + fen100)
    info = parse(r)
    cases.append({"name": "clock100_mate", "raw": r["lines"], **info,
                  "expect": "best d1d8",
                  "pass": info["best"] == "d1d8"})

    # third occurrence where the position is NOT immediately lost for black: the
    # job's structure with the white queen removed. (The engine still finds a mate
    # here -- rook and king against a bare king -- which is fine: the point of this
    # case is only that the root is SEARCHED, i.e. depth lines with nodes > 0.)
    no_mate = "6k1/5ppp/8/8/8/1q6/8/R5K1 w - - 0 1"
    shuffle = "a1b1 b3c4 b1a1 c4b3 a1b1 b3c4 b1a1 c4b3"
    r = run("position fen " + no_mate + " moves " + shuffle)
    info = parse(r)
    legal = legal_moves_of(no_mate)
    cases.append({"name": "third_occurrence_searched", "raw": r["lines"], **info,
                  "expect": "at least one info depth line, nodes > 0, a legal move",
                  "pass": info["depth_lines"] > 0 and info["maxnodes"] > 0
                          and info["best"] in legal})

    # stalemate: black to move, no legal move, not in check
    stale = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    r = run("position fen " + stale)
    info = parse(r)
    cases.append({"name": "stalemate_root", "raw": r["lines"], **info,
                  "expect": "answered as today: score cp 0, 0 nodes",
                  "pass": r["exit"] == 0 and info["score"] == ("cp", 0) and info["maxnodes"] == 0})

    # checkmate: black to move and mated (king h8 in check from Qg7, Kg6 covers g7/h7)
    mate = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
    r = run("position fen " + mate)
    info = parse(r)
    cases.append({"name": "checkmate_root", "raw": r["lines"], **info,
                  "expect": "answered as today: 0 nodes, no crash (the engine reports the "
                            "mated root itself as no legal move; the -MateValue score lives in "
                            "result.score, which UCI does not print for a root with no moves)",
                  "pass": r["exit"] == 0 and info["maxnodes"] == 0 and info["best"] == "0000"})

    json.dump(cases, open(OUT, "w"), indent=1)
    print(f"{'case':22s} {'result':6s} best      score          depth_lines nodes")
    for c in cases:
        print(f"{c['name']:22s} {'PASS' if c['pass'] else 'FAIL':6s} "
              f"{str(c['best']):9s} {str(c['score']):14s} {c['depth_lines']:11d} {c['maxnodes']}")
    print()
    for c in cases:
        print(f"--- {c['name']}: {c['expect']}")
        for ln in c["raw"][-6:]:
            print("   ", ln)
    fails = [c["name"] for c in cases if not c["pass"]]
    print("\nFAILING:", fails if fails else "none")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
