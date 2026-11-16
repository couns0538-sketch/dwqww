#!/usr/bin/env python3
"""root_instr.py EXE

The root-repetition experiment. For each history length we send one search and capture the
INSTRUMENTED line the engine prints from the root, which reports:
  guard=<FORGE_FIX_ROOT_DRAWN value>  halfmove  legal=<root moves>  key_history=<length>
  is_repetition()=<true|false>        WOULD_BE_DRAWN=<true|false>   used_by_guard=<YES|NO>

The instrumentation CALLS board.is_repetition() unconditionally so we learn its RESULT even when the
guard does not use it. Occurrence counts are verified with python-chess before each run: a claim
about "three occurrences" is checked, not assumed.

Controls:
  - history with ONE occurrence (startpos): is_repetition() must be false
  - history with TWO occurrences: must be false (needs 3)
  - history with THREE occurrences: the interesting case
  - a startpos search that must print a normal score (proves the search path is reached)
Threads 1.
"""
import argparse
import queue
import re
import subprocess
import threading
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
CYCLE = ["g1f3", "g8f6", "f3g1", "f6g8"]


def key(b):
    return (b.board_fen(), b.turn, b.castling_xfen(), b.ep_square)


def build(cycles):
    b = chess.Board()
    moves = []
    counts = {key(b): 1}
    for _ in range(cycles):
        for u in CYCLE:
            b.push(chess.Move.from_uci(u))
            moves.append(u)
            counts[key(b)] = counts.get(key(b), 0) + 1
    return moves, counts[key(b)]


def run(exe, poscmd, depth=8, limit=180):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q_out, q_err = queue.Queue(), queue.Queue()
    out, err = [], []

    def rd(stream, q, store):
        for line in stream:
            q.put(line.rstrip("\n"))
            store.append(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, args=(p.stdout, q_out, out), daemon=True).start()
    threading.Thread(target=rd, args=(p.stderr, q_err, err), daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait_out(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT"
            try:
                line = q_out.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT"
            if line is None:
                return "EOF"
            if pred(line):
                return line

    send("uci"); wait_out(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready"); wait_out(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait_out(lambda l: l == "readyok", 30)
    send(poscmd); send("isready"); wait_out(lambda l: l == "readyok", 30)
    send("go depth %d" % depth)
    bm = wait_out(lambda l: l.startswith("bestmove"), limit)
    time.sleep(0.2)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [l for l in out if l.startswith("info depth")]
    last = infos[-1] if infos else None
    score = nodes = None
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        score = ("%s %s" % (m.group(1), m.group(2))) if m else "PARSE_FAIL"
        m2 = re.search(r"\bnodes (\d+)", last)
        nodes = int(m2.group(1)) if m2 else "PARSE_FAIL"
    rootline = next((l for l in err if l.startswith("ROOT-REP")), None)
    return {"root_line": rootline, "score": score, "nodes": nodes, "bestmove": bm}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    a = ap.parse_args()
    print("exe: %s   Threads 1" % a.exe, flush=True)
    print(flush=True)

    print("=== control: plain startpos must reach the search path ===", flush=True)
    r = run(a.exe, "position startpos")
    print("  score=%s nodes=%s %s" % (r["score"], r["nodes"], r["bestmove"]), flush=True)
    print("  %s" % (r["root_line"] or "NO ROOT-REP LINE — instrumentation not reached"), flush=True)
    print(flush=True)

    for cycles, want in ((0, 1), (1, 2), (2, 3), (3, 4)):
        moves, occ = build(cycles)
        assert occ == want, "built %d, wanted %d" % (occ, want)
        cmd = "position startpos" + (" moves " + " ".join(moves) if moves else "")
        r = run(a.exe, cmd)
        print("=== %d occurrence(s) of the final position (%d plies) ===" % (occ, len(moves)),
              flush=True)
        print("  engine: score=%s nodes=%s %s" % (r["score"], r["nodes"], r["bestmove"]),
              flush=True)
        print("  %s" % (r["root_line"] or "NO ROOT-REP LINE (root-drawn early return may skip it)"),
              flush=True)
        print(flush=True)


if __name__ == "__main__":
    main()
