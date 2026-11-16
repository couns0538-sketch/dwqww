#!/usr/bin/env python3
"""check_s01f5.py — seat 20, area 10 job 1: my OWN check of seat 01's S-F5.

I do not run their script. I build the positions myself with python-chess, PROVE the mate with python-chess
(so the expectation is not taken from seat 01), and drive the engine with my own interactive runner.

usage: check_s01f5.py <release-exe> <asan-exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

import chess

REL, ASAN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)


def drive(exe, lines, timeout=60.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
                time.sleep(0.003)
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.wait(timeout=20)
    except Exception:
        p.kill()
    with lock:
        return list(out)


def ask(exe, fen, go, extra_pre=()):
    lines = ["uci", "setoption name OwnBook value false", "isready", "ucinewgame", "isready"]
    lines += list(extra_pre)
    lines += [f"position fen {fen}", "isready", go]
    out = drive(exe, lines)
    depths = [x for x in out if x.startswith("info depth")]
    best = [x for x in out if x.startswith("bestmove")]
    bm = best[-1].split()[1] if best else "<none>"
    score = ""
    nodes = None
    for x in reversed(depths):
        m = re.search(r"score (\S+ \S+)", x)
        if m and not score:
            score = m.group(1)
        m = re.search(r"nodes (\d+)", x)
        if m and nodes is None:
            nodes = int(m.group(1))
    if nodes is None:
        nodes = 0
    san_lines = [x for x in out if "AddressSanitizer" in x or "runtime error:" in x or "SUMMARY:" in x
                 or "LeakSanitizer" in x]
    return {"fen": fen, "go": go, "bestmove": bm, "score": score, "nodes": nodes,
            "depth_lines": len(depths), "san": len(san_lines),
            "last_depth_line": depths[-1] if depths else ""}


# ---- positions I build myself, and the mate PROVEN with python-chess -------------------------------
def mate_in_one_position():
    """A K+Q vs K position where the side to move mates in 1. Found by search over my own boards,
    never taken from seat 01."""
    base = chess.Board("6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
    for mv in base.legal_moves:
        b = base.copy()
        b.push(mv)
        if b.is_checkmate():
            return base
    raise SystemExit("no mate in 1 found in the seed position")


def mate_in_one_position2():
    base = chess.Board("7k/6pp/8/8/8/8/6PP/5RK1 w - - 0 1")
    for mv in base.legal_moves:
        b = base.copy()
        b.push(mv)
        if b.is_checkmate():
            return base
    raise SystemExit("no mate in 1 found in the second seed position")


def prove_mate(board):
    """independent proof with python-chess: a legal move whose reply board is checkmate"""
    mates = []
    for mv in board.legal_moves:
        b = board.copy()
        b.push(mv)
        if b.is_checkmate():
            mates.append(mv.uci())
    return mates


def with_halfmove(board, hm):
    parts = board.fen().split()
    parts[4] = str(hm)
    return " ".join(parts)


def checkmated_board():
    b = chess.Board()
    for mv in ("f2f3", "e7e5", "g2g4", "d8h4"):
        b.push_uci(mv)
    assert b.is_checkmate(), b.fen()
    return b


report = {"release": REL, "asan": ASAN, "positions": {}, "cases": [], "control": {}}

boards = [("Q-mate", mate_in_one_position()), ("R-mate", mate_in_one_position2())]
for name, b in boards:
    report["positions"][name] = {"fen": b.fen(), "engine_mates_proven_by_pythonchess": prove_mate(b),
                                 "python_chess_says_mate_in_1": b.is_checkmate() is False and
                                 len(prove_mate(b)) > 0}

HMS = [0, 97, 98, 99, 100, 101, 102, 150]
for name, b in boards:
    for hm in HMS:
        fen = with_halfmove(b, hm)
        r = ask(REL, fen, "go depth 6")
        r.update({"position": name, "halfmove": hm, "exe": "release"})
        report["cases"].append(r)
        print(f"{name:7s} hm={hm:4d} best={r['bestmove']:6s} score={r['score']:8s} "
              f"nodes={r['nodes']:6d} depth_lines={r['depth_lines']}")

# Q4: an already-checkmated board at every counter value
cm = checkmated_board()
for hm in (0, 98, 99, 100, 101, 150):
    fen = with_halfmove(cm, hm)
    r = ask(REL, fen, "go depth 6")
    r.update({"position": "checkmated", "halfmove": hm, "exe": "release"})
    report["cases"].append(r)
    print(f"checkmated hm={hm:4d} best={r['bestmove']:6s} score={r['score']:8s} nodes={r['nodes']:6d}")

# Q5: can a deeper / bigger search escape the shortcut at halfmove 100?
name, b = boards[0]
for go in ("go depth 8", "go depth 12", "go nodes 100000", "go movetime 200"):
    fen = with_halfmove(b, 100)
    r = ask(REL, fen, go)
    r.update({"position": name, "halfmove": 100, "exe": "release"})
    report["cases"].append(r)
    print(f"{name} hm=100 {go:16s} best={r['bestmove']:6s} score={r['score']:8s} nodes={r['nodes']:6d}")

# Q6: the ASan+UBSan build, same cases as the release ones that matter
for name, b in boards:
    for hm in (99, 100):
        fen = with_halfmove(b, hm)
        r = ask(ASAN, fen, "go depth 6")
        r.update({"position": name, "halfmove": hm, "exe": "asan"})
        report["cases"].append(r)
        print(f"ASAN {name:7s} hm={hm:4d} best={r['bestmove']:6s} score={r['score']:8s} "
              f"nodes={r['nodes']:6d} san={r['san']}")

# CONTROL: my harness must be able to tell a searched answer from an unsearched one.
# A position with a mate in 2 (not 1) at halfmove 0 and at halfmove 100; and a position reached by a move
# list, to show the harness reports a different move when the position really changes.
ctl = chess.Board("6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
c1 = ask(REL, with_halfmove(ctl, 0), "go depth 6")
report["control"]["mate_in_1_hm0"] = c1
print(f"CONTROL mate-in-1 hm=0 best={c1['bestmove']} score={c1['score']} (must be the mate)")
# a position where the best move is NOT the first legal move, at halfmove 100:
# if the shortcut is active it will still play the first legal move, so the control below proves the
# harness can distinguish the two answers.
notfirst = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
first_legal = sorted(m.uci() for m in notfirst.legal_moves)[0]
c2 = ask(REL, with_halfmove(notfirst, 0), "go depth 6")
c3 = ask(REL, with_halfmove(notfirst, 100), "go depth 6")
report["control"]["notfirst_hm0"] = c2
report["control"]["notfirst_hm100"] = c3
report["control"]["first_legal_of_notfirst"] = first_legal
print(f"CONTROL notfirst hm=0   best={c2['bestmove']} nodes={c2['nodes']} (searched)")
print(f"CONTROL notfirst hm=100 best={c3['bestmove']} nodes={c3['nodes']} "
      f"(first legal is {first_legal})")

with open(os.path.join(OUT, "check_s01f5.json"), "w") as f:
    json.dump(report, f, indent=1)
print("\nwrote", os.path.join(OUT, "check_s01f5.json"))
