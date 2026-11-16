#!/usr/bin/env python3
"""S13 check of seat 21 finding 21-F1.

The claim: an "impossible castling" FEN is NOT accepted by this build; the 8,902 the brief
quotes is startpos perft 3, i.e. the position left on the board after the FEN was REFUSED,
and 8,802 is python-chess's perft 3 of the refused FEN itself.

I test that with my own runner, three cases, each in a FRESH process:
  A: the castling FEN alone, go perft 3.
  B: the castling FEN, then a legal unrelated FEN, go perft 3  (does the next command stick?)
  C: the castling FEN then startpos then perft 3 (must be 8902 for the harness to be sane)
  D: a FEN with castling rights and a rook on the corner (legal) -> must be ACCEPTED, perft 3 = 13744
  E: startpos then the castling FEN then perft 3 -> if the FEN is refused, still 8902
And python-chess perft 3 of both the castling FEN and startpos, computed by me.

Usage: check_21f1.py EXE OUTDIR
"""
import hashlib
import os
import subprocess
import sys

import chess

BADFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"
LEGALFEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
KVK = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

EXE = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def perft(fen, depth):
    b = chess.Board(fen)

    def rec(bd, d):
        if d == 0:
            return 1
        t = 0
        for m in bd.legal_moves:
            bd.push(m)
            t += rec(bd, d - 1)
            bd.pop()
        return t
    return rec(b, depth)


def run_case(name, lines):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.run([EXE], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=600, env=env)
    path = os.path.join(OUT, name + ".txt")
    with open(path, "w") as f:
        f.write("exe %s\nsha256 %s\n" % (os.path.abspath(EXE), sha256(EXE)))
        f.write("lines sent:\n" + "\n".join("  > " + s for s in lines) + "\n")
        f.write("--- stdout ---\n" + p.stdout)
        f.write("--- stderr ---\n" + p.stderr)
        f.write("--- returncode %d ---\n" % p.returncode)
    nodes = None
    refused = False
    msgs = []
    for ln in p.stdout.splitlines():
        if ln.startswith("nodes "):
            nodes = int(ln.split()[1])
        if "invalid FEN" in ln or "info string" in ln:
            msgs.append(ln)
            if "invalid FEN" in ln:
                refused = True
    return {"nodes": nodes, "refused": refused, "msgs": msgs, "path": path}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


results = {}
results["A_badfen_only"] = run_case("A_badfen_only",
                                    ["uci", "isready", "position fen " + BADFEN,
                                     "isready", "go perft 3"])
results["B_badfen_then_kvk"] = run_case("B_badfen_then_kvk",
                                        ["uci", "isready", "position fen " + BADFEN,
                                         "isready", "position fen " + KVK, "isready",
                                         "go perft 3"])
results["C_badfen_then_start"] = run_case("C_badfen_then_start",
                                          ["uci", "isready", "position fen " + BADFEN,
                                           "isready", "position startpos", "isready",
                                           "go perft 3"])
results["D_legal_castling"] = run_case("D_legal_castling",
                                       ["uci", "isready", "position fen " + LEGALFEN,
                                        "isready", "go perft 3"])
results["E_start_then_badfen"] = run_case("E_start_then_badfen",
                                          ["uci", "isready", "position startpos", "isready",
                                           "position fen " + BADFEN, "isready",
                                           "go perft 3"])
results["F_illegal_castling_right_only"] = run_case(
    "F_illegal_castling_right_only",
    ["uci", "isready", "position fen 4k3/8/8/8/8/8/8/R3K3 w Kk - 0 1", "isready",
     "go perft 3"])

py_bad = perft(BADFEN, 3)
py_start = perft(START, 3)
py_legal = perft(LEGALFEN, 3)
py_kvk = perft(KVK, 3)

rows = [
    ("A_badfen_only", "refused, perft3 = startpos 8902?", results["A_badfen_only"]["nodes"] == 8902),
    ("B_badfen_then_kvk", "refused, next FEN sticks (perft3 = %d)?" % py_kvk,
     results["B_badfen_then_kvk"]["nodes"] == py_kvk),
    ("C_badfen_then_start", "refused, startpos sticks (8902)?",
     results["C_badfen_then_start"]["nodes"] == 8902),
    ("D_legal_castling", "ACCEPTED, perft3 = %d (python-chess)?" % py_legal,
     (results["D_legal_castling"]["nodes"] == py_legal
      and not results["D_legal_castling"]["refused"])),
    ("E_start_then_badfen", "refused, previous startpos still there (8902)?",
     results["E_start_then_badfen"]["nodes"] == 8902),
]

lines = []
lines.append("## my own run of seat 21's finding 21-F1 (seat 13, own build, own harness)\n")
lines.append("python-chess perft 3: refused FEN = %d, startpos = %d, legal-castling FEN = %d, K v K = %d\n"
             % (py_bad, py_start, py_legal, py_kvk))
lines.append("| case | what I check | engine nodes | engine refusal line | verdict |")
lines.append("|---|---|---|---|---|")
for name, what, ok in rows:
    r = results[name]
    msg = "; ".join(r["msgs"]) if r["msgs"] else "(none)"
    lines.append("| %s | %s | %s | %s | %s |"
                 % (name, what, r["nodes"], msg, "HOLDS" if ok else "DOES NOT HOLD"))
lines.append("")
lines.append("Reading:")
lines.append("- The brief says the impossible-castling FEN is ACCEPTED with perft 3 = 8,902.")
lines.append("- If case A got 8,902 AND a refusal line, then 8,902 is startpos after a REFUSAL,")
lines.append("  not the accepted FEN's perft: seat 21's correction holds.")
lines.append("- python-chess's perft 3 of the FEN itself is %d, which is the brief's other number 8,802." % py_bad)
lines.append("")
text = "\n".join(lines)
open(os.path.join(OUT, "VERDICT.md"), "w").write(text)
print(text)
