#!/usr/bin/env python3
"""count_book.py EXE FENFILE OUT — how many of these positions the engine answers from its own book
(OwnBook default true), with the bestmove. One process, ucinewgame per position, movetime 50.
"""
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]

exe, fenfile, outpath = sys.argv[1:4]
fens = [l.strip() for l in open(fenfile) if l.strip()]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(line):
    p.stdin.write(line + "\n")
    p.stdin.flush()


def sync():
    send("isready")
    lines = []
    while True:
        l = p.stdout.readline().rstrip("\n")
        if l == "":
            raise EOFError("engine closed")
        lines.append(l)
        if l.startswith("readyok"):
            return lines


send("uci")
while not p.stdout.readline().startswith("uciok"):
    pass
for n, v in S14:
    send("setoption name %s value %s" % (n, v))
sync()
send("setoption name Threads value 1")
sync()
send("setoption name Hash value 16")
sync()

rows = []
for i, fen in enumerate(fens):
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    send("go movetime 50")
    lines = []
    while True:
        l = p.stdout.readline().rstrip("\n")
        if l.startswith("bestmove"):
            lines.append(l)
            break
        lines.append(l)
    book = [l for l in lines if "book move" in l]
    rows.append((i, "BOOK" if book else "search", lines[-1].split()[1] if len(lines[-1].split()) > 1 else "?",
                 book[0] if book else ""))
send("quit")
p.wait(timeout=10)

with open(outpath, "w") as fh:
    fh.write("| i | answered by | bestmove | book line | fen |\n|---|---|---|---|---|\n")
    for i, kind, bm, bl in rows:
        if kind == "BOOK":
            fh.write("| %d | book | %s | %s | %s |\n" % (i, bm, bl, fens[i]))
    fh.write("\nbook-answered %d of %d\n" % (sum(1 for r in rows if r[1] == "BOOK"), len(rows)))
print(open(outpath).read())
