#!/usr/bin/env python3
"""book_width.py EXE OUT — how wide is the opening book that 08-F3 hit?
For a set of opening positions reached by move lists, ask the engine with OwnBook TRUE (the default) whether
it answers from the book, with a real search waited out (never a piped quit).
"""
import subprocess
import sys

import chess

exe, outpath = sys.argv[1:3]

LINES = [
    ("startpos", ""),
    ("1.e4", "e2e4"),
    ("1.e4 e5", "e2e4 e7e5"),
    ("1.e4 e5 2.Nf3", "e2e4 e7e5 g1f3"),
    ("1.e4 e5 2.Nf3 Nc6 3.Bb5", "e2e4 e7e5 g1f3 b8c6 f1b5"),
    ("1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4", "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4"),
    ("1.d4", "d2d4"),
    ("1.d4 d5", "d2d4 d7d5"),
    ("1.d4 d5 2.c4", "d2d4 d7d5 c2c4"),
    ("1.c4", "c2c4"),
    ("1.Nf3", "g1f3"),
    ("1.a3 (non-opening)", "a2a3"),
    ("1.h4 (non-opening)", "h2h4"),
    ("random 20 plies", None),
]


def book_answer(exe, moves, go="go movetime 50"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write("uci\nisready\nucinewgame\nisready\n")
    if moves:
        p.stdin.write("position startpos moves %s\nisready\n" % moves)
    else:
        p.stdin.write("position startpos\nisready\n")
    p.stdin.flush()
    while True:
        if p.stdout.readline().startswith("readyok"):
            break
    p.stdin.write(go + "\n")
    p.stdin.flush()
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    book = [l for l in lines if "book move" in l]
    infos = [l for l in lines if l.startswith("info depth")]
    bm = lines[-1].split()[1]
    return bm, bool(book), len(infos)


out = []


def emit(s):
    out.append(s)
    print(s)


emit("## how wide is the book? OwnBook at its default TRUE, `go movetime 50`")
emit("| position | moves | answered by | bestmove | info lines |")
emit("|---|---|---|---|---|")
nbook = 0
tests = 0
for label, moves in LINES:
    if moves is None:
        # a random 20-ply line with a fixed seed, to get out of any book
        import random
        rng = random.Random(8101)
        b = chess.Board()
        ms = []
        for _ in range(20):
            lm = list(b.legal_moves)
            if not lm:
                break
            m = rng.choice(lm)
            ms.append(b.uci(m))
            b.push(m)
        moves = " ".join(ms)
    bm, book, ni = book_answer(exe, moves)
    tests += 1
    if book:
        nbook += 1
    emit("| %s | %s | %s | %s | %d |" % (label, moves[:44] if moves else "(none)", "BOOK" if book else "search", bm, ni))

emit("")
emit("## the `go depth 12` control: is the book probed for a depth search too?")
bm, book, ni = book_answer(exe, "", "go depth 12")
emit("| go | bestmove | answered by | info lines |")
emit("|---|---|---|---|")
emit("| go depth 12 from startpos | %s | %s | %d |" % (bm, "BOOK" if book else "search", ni))

emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions tested at movetime 50 | %d |" % tests)
emit("| answered from the book | %d |" % nbook)

with open(outpath, "w") as fh:
    fh.write("\n".join(out) + "\n")
