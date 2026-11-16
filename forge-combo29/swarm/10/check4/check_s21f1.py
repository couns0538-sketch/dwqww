#!/usr/bin/env python3
"""check_s21f1.py -- seat 10's OWN harness for seat 21's finding 21-F1.

Claim under test: the brief's "impossible-castling FEN is ACCEPTED (perft 3 8,902)" is a
misdiagnosis -- the FEN is REFUSED and 8,902 is startpos perft 3 left on the board.

Written from the finding's TEXT; it does not import or copy seat 21's script.

Four cases, each in a FRESH engine process, raw output kept:
  A  `position fen BAD` then perft 3                       -> is it refused? what does perft give?
  B  `position startpos` then `position fen BAD` then perft 3 -> same two questions
  C  `position fen BAD` then a DIFFERENT legal FEN then perft 3 -> does the second one take effect?
  D  `position fen GOOD-with-KQkq`? no: startpos only, as the control for 8902 == startpos perft 3.

python-chess side: perft 3 of startpos and perft 3 of the bad board (which python-chess accepts
as a board and only flags), computed by a plain recursion, so both published numbers are checked.

Usage: check_s21f1.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys

import chess

EXE = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

BAD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"
OTHER = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"


def perft(b, d):
    if d == 0:
        return 1
    if d == 1:
        return b.legal_moves.count()
    n = 0
    for m in list(b.legal_moves):
        b.push(m)
        n += perft(b, d - 1)
        b.pop()
    return n


def run(name, lines):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.run([EXE], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=300, env=env)
    with open(os.path.join(OUT, name + ".txt"), "w") as f:
        f.write("=== exe: %s\n=== commands sent:\n" % EXE)
        for l in lines:
            f.write("  " + l + "\n")
        f.write("=== stdout:\n" + p.stdout)
        f.write("=== stderr:\n" + p.stderr)
        f.write("=== exit: %s\n" % p.returncode)
    refused = [l.strip() for l in p.stdout.splitlines() if "invalid fen" in l.lower()]
    total = None
    for l in p.stdout.splitlines():
        if l.startswith("nodes "):
            total = int(l.split()[1])
    return {"case": name, "refused": bool(refused), "refusal_lines": refused,
            "perft_total": total, "exit": p.returncode}


pre = ["uci", "isready"]
cases = {
    "A_bad_only": pre + ["position fen " + BAD, "isready", "go perft 3"],
    "B_startpos_then_bad": pre + ["position startpos", "isready", "position fen " + BAD,
                                  "isready", "go perft 3"],
    "C_bad_then_other": pre + ["position fen " + BAD, "isready", "position fen " + OTHER,
                               "isready", "go perft 3"],
    "D_startpos_control": pre + ["position startpos", "isready", "go perft 3"],
}
res = {k: run(k, v) for k, v in cases.items()}

# python-chess side
py_start = perft(chess.Board(), 3)
bad_board = chess.Board(BAD)
py_bad = perft(chess.Board(BAD), 3)
py_bad_status = bad_board.status()
py_other = perft(chess.Board(OTHER), 3)

summary = {
    "engine": {k: v for k, v in res.items()},
    "python_chess": {
        "startpos_perft3": py_start,
        "bad_board_parses": True,
        "bad_board_status": py_bad_status,
        "bad_board_status_has_impossible_castling":
            bool(py_bad_status & chess.STATUS_BAD_CASTLING_RIGHTS),
        "bad_board_perft3": py_bad,
        "other_endgame_perft3": py_other,
    },
    "verdict_inputs": {
        "P1_bad_fen_refused": res["A_bad_only"]["refused"],
        "P2_perft3_after_refusal_is_8902": res["A_bad_only"]["perft_total"] == 8902,
        "P2b_startpos_control_is_8902": res["D_startpos_control"]["perft_total"] == 8902,
        "P3_python_startpos_8902": py_start == 8902,
        "P3b_python_bad_board_8802": py_bad == 8802,
        "P5_second_fen_takes_effect": res["C_bad_then_other"]["perft_total"] == py_other,
        "P5b_C_expected_other_perft3": py_other,
        "B_refused_too": res["B_startpos_then_bad"]["refused"],
        "B_perft_after_refusal": res["B_startpos_then_bad"]["perft_total"],
    },
}
with open(os.path.join(OUT, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
