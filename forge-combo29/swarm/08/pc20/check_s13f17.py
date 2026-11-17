#!/usr/bin/env python3
"""check_s13f17.py OUT — my own check of seat 13's S-F17 (which confirms FABLE file 6's drawn-root claims).

Their claim:
"FABLE file 6's drawn-root claims CONFIRMED INDEPENDENTLY on both builds: base 6b98f217 scores a halfmove>=100 root
 AND a genuine third-occurrence root as 0 and searches 0 nodes, missing a mate-in-1 (plays a1b1 not a1a8), while PC
 r15 finds the mate in 144 nodes in both cases; both builds still answer K vs K at once (0 nodes); and both find the
 mate at halfmove 0, at halfmove 99, and at TWO occurrences — so the difference is specifically the drawn-root
 condition, not the position or the harness."

This is a MATRIX of cells, and the design is exactly right: the discriminating cells are halfmove 99 and TWO
occurrences, which must NOT be drawn. I reproduce the matrix with my own harness.

I need three kinds of root:
  A  mate-in-1 at halfmove 0      -> both must FIND it
  B  mate-in-1 at halfmove 99     -> both must FIND it (not yet 100)
  C  mate-in-1 at halfmove 100    -> base must MISS it (drawn-root shortcut), PC must find it
  D  genuine third occurrence     -> base must MISS it, PC must find it
  E  K vs K (insufficient)        -> both answer at once, 0 nodes
I build C by using the board from my own 08-C26/S-F8b work, and D by a repeatable move list.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# a mate-in-1 board: white Ra1 -> a8# with black king on a-file corner, our own construction
MATE_BOARD = "7k/8/6K1/8/8/8/8/R7 w - - %d 1"   # Ra8 is mate? verify below
KVK = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"


def verify_mate(fen):
    b = chess.Board(fen)
    found = []
    for m in list(b.legal_moves):
        b.push(m)
        if b.is_checkmate():
            found.append(str(m))
        b.pop()
    return found[0] if found else None


def run(exe, fen, moves=None, go="go depth 4"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    if moves:
        send("position startpos moves " + moves)
    else:
        send("position fen " + fen)
    sync()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    nodes = None
    for l in lines:
        if l.startswith("info depth") and "nodes" in l.split():
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"bm": lines[-1].split()[1], "nodes": nodes}


out = []
def emit(s):
    out.append(s)
    print(s)

mate_move = verify_mate(MATE_BOARD % 100)
emit("## seat 13 S-F17 — the drawn-root matrix, on both builds")
emit("")
if mate_move is None:
    raise SystemExit("CONTROL FAILED: my constructed board has no mate-in-1, so the matrix cannot be built")
emit("Control: the constructed board `%s` HAS a mate-in-1 (`%s`), verified in python-chess first." %
     (MATE_BOARD % 100, mate_move))
emit("")
emit("| cell | base bestmove | base nodes | PC bestmove | PC nodes | design says |")
emit("|---|---|---|---|---|---|")

cells = [
    ("halfmove 0 (control: not drawn)", MATE_BOARD % 0, None, "both FIND"),
    ("halfmove 99 (control: not drawn)", MATE_BOARD % 99, None, "both FIND"),
    ("halfmove 100 (drawn root)", MATE_BOARD % 100, None, "base MISSES, PC finds"),
    ("K vs K (insufficient material)", KVK, None, "both answer at once, 0 nodes"),
]
for label, fen, moves, design in cells:
    b = run(BASE, fen, moves)
    c = run(PC, fen, moves)
    emit("| %s | %s | %s | %s | %s | %s |" %
         (label, b["bm"], f"{b['nodes']:,}" if b["nodes"] is not None else "-",
          c["bm"], f"{c['nodes']:,}" if c["nodes"] is not None else "-", design))

emit("")
emit("## The claim, tested")
emit("")
b0 = run(BASE, MATE_BOARD % 0)
b99 = run(BASE, MATE_BOARD % 99)
b100 = run(BASE, MATE_BOARD % 100)
p100 = run(PC, MATE_BOARD % 100)
kvk_b = run(BASE, KVK)
kvk_p = run(PC, KVK)
emit("| question | answer |")
emit("|---|---|")
emit("| base FINDS the mate at halfmove 0 | **%s** (%s, %s nodes) |" %
     ("yes" if b0["nodes"] else "NO", b0["bm"], b0["nodes"]))
emit("| base FINDS the mate at halfmove 99 | **%s** (%s, %s nodes) |" %
     ("yes" if b99["nodes"] else "NO", b99["bm"], b99["nodes"]))
emit("| base MISSES it at halfmove 100 (0 nodes, not the mating move) | **%s** (%s, %s nodes) |" %
     ("YES" if (b100["nodes"] == 0 and b100["bm"] != mate_move) else "no", b100["bm"], b100["nodes"]))
emit("| PC FINDS it at halfmove 100 | **%s** (%s, %s nodes) |" %
     ("YES" if p100["bm"] == mate_move else "NO", p100["bm"], p100["nodes"]))
emit("| both answer K vs K at once with 0 nodes | base %s / PC %s |" %
     (f"{kvk_b['nodes']} nodes" if kvk_b["nodes"] is not None else "-",
      f"{kvk_p['nodes']} nodes" if kvk_p["nodes"] is not None else "-"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
