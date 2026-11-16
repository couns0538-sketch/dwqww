#!/usr/bin/env python3
"""check_s12f1.py — seat 20, area 10 job 6: my OWN check of seat 12's S-F1.

The claim: `ucinewgame` resets the board to startpos, so `position fen X` then `ucinewgame` then `go` searches
startpos instead of X. I test the ORDER of the two commands as the variable, and I use python-chess to decide
which position each answer is legal in — so "which board did it search" is decided by the rules, not by me.

usage: check_s12f1.py <release-exe> <outdir>
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

MID = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
# a BLACK-to-move position: no black move is legal in startpos (white to move), so the verdict is decisive
BLACK = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1"
MOVELIST = "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 d2d3 f8c5 c2c3 d7d6"


def legal_set(fen):
    b = chess.Board(fen)
    return {m.uci() for m in b.legal_moves}


def after_moves(fen, moves):
    b = chess.Board(fen)
    for m in moves.split():
        b.push_uci(m)
    return b.fen()


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


def verdict(bm, fen):
    if not bm or bm == "0000":
        return "no move"
    S = legal_set(chess.STARTING_FEN)
    L = legal_set(fen)
    if bm in S and bm in L:
        return "legal in BOTH"
    if bm in S:
        return "legal in STARTPOS only"
    if bm in L:
        return "legal in the position only"
    return "legal in NEITHER"


PRE = ["uci", "setoption name OwnBook value false", "isready"]
CASES = [
    ("A_position_then_ucinewgame", PRE + [f"position fen {MID}", "isready", "ucinewgame", "isready", "go depth 6"], MID),
    ("B_position_no_ucinewgame", PRE + [f"position fen {MID}", "isready", "go depth 6"], MID),
    ("A2_blackpos_then_ucinewgame",
     PRE + [f"position fen {BLACK}", "isready", "ucinewgame", "isready", "go depth 6"], BLACK),
    ("A3_blackpos_no_ucinewgame",
     PRE + [f"position fen {BLACK}", "isready", "go depth 6"], BLACK),
    ("C_ucinewgame_then_position", PRE + ["ucinewgame", "isready", f"position fen {MID}", "isready", "go depth 6"], MID),
    ("D_movelist_then_ucinewgame",
     PRE + [f"position startpos moves {MOVELIST}", "isready", "ucinewgame", "isready", "go depth 6"],
     after_moves(chess.STARTING_FEN, MOVELIST)),
    ("E_movelist_no_ucinewgame",
     PRE + [f"position startpos moves {MOVELIST}", "isready", "go depth 6"],
     after_moves(chess.STARTING_FEN, MOVELIST)),
]

report = {"exe": EXE, "midgame": MID, "blackpos": BLACK, "movelist_fen": after_moves(chess.STARTING_FEN, MOVELIST), "cases": []}
print(f"midgame FEN   {MID}")
print(f"movelist FEN  {report['movelist_fen']}")
print()
print(f"{'case':30s} {'bestmove':8s} {'verdict':22s} {'info lines'}")
for label, lines, fen in CASES:
    tr = ask(lines)
    bests = [x.split()[1] for x in tr if x.startswith("bestmove")]
    bm = bests[-1] if bests else "<none>"
    v = verdict(bm, fen)
    infos = [x for x in tr if x.startswith("info string")]
    report["cases"].append({"case": label, "command_list": lines, "bestmove": bm, "verdict": v,
                            "info_string": infos, "fen_under_test": fen, "transcript": tr})
    print(f"{label:30s} {bm:8s} {v:22s} {len(infos)}")
    for s in infos:
        print(f"    | {s}")

# Q3: does ucinewgame print anything about the reset?
print()
print("== does ucinewgame print anything? (its own answer, excluding 'option' lines)")
tr = ask(["uci", "setoption name OwnBook value false", "isready", f"position fen {MID}", "isready",
          "ucinewgame", "isready", "quit"])
seen_position_lines = [x for x in tr if x.startswith("position")]
reset_lines = [x for x in tr if "reset" in x.lower() or "startpos" in x.lower()]
print(f"  lines echoed by the engine starting with 'position': {seen_position_lines}")
print(f"  lines mentioning reset/startpos: {reset_lines}")
report["q3"] = {"position_lines": seen_position_lines, "reset_lines": reset_lines}

with open(os.path.join(OUT, "check_s12f1.json"), "w") as f:
    json.dump(report, f, indent=1)
with open(os.path.join(OUT, "check_s12f1.txt"), "w") as f:
    for c in report["cases"]:
        f.write(f"### {c['case']}  bestmove={c['bestmove']}  verdict={c['verdict']}\n")
        for line in c["command_list"]:
            f.write(f"  --> {line}\n")
        for line in c["transcript"]:
            if line.startswith("option"):
                continue
            f.write(f"  | {line}\n")
        f.write("\n")
print("\nwrote", os.path.join(OUT, "check_s12f1.txt"))
