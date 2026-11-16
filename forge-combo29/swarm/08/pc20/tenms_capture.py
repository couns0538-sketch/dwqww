#!/usr/bin/env python3
"""tenms_capture.py OUT — how bad is the 10 ms case in practice?

Five positions where a capture is available. At `go wtime 10 btime 10` the engine plays its one-ply answer; does
that answer at least CAPTURE? A one-ply move that captures a defended piece is a weak move; one that ignores a free
piece, or that hangs material, is arguably a lost game at 10 ms.

For each position I record: the one-ply answer, whether it is a capture, whether the captured piece is worth more
than the capturing piece (SEE proxy from python-chess material), and — the important control — what a REAL search
answers (`go movetime 50`), so "the one-ply move loses material the real search would have won" is measurable.

Threads 1, Hash 16, PC20 on the PC build; the base tree for comparison.
"""
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
BUILDS = [("base tree", "/home/ubuntu/builds/release/forge", False),
          ("PC r15 PC20", "/home/ubuntu/builds/pc/forge", True)]

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

# five positions, each with at least one capture available to the side to move
FENS = [
    # a free queen on offer
    "4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1",
    # rook takes an undefended rook
    "4k3/8/8/8/8/8/8/R3K2r w Q - 0 1",
    # a defended queen: capture is available but loses
    "4k3/8/2q5/3P4/8/8/8/4K3 w - - 0 1",
    # knight fork-style: a knight can take a rook
    "4k3/8/8/4n3/8/3R4/8/4K3 b - - 0 1",
    # middlegame with several captures
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
]


def ask(exe, fen, go, pc20):
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
    if pc20:
        opts = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
                ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
                ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
                ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
                ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
                ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
        for n, v in opts:
            send("setoption name %s value %s" % (n, v))
            sync()
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    t0 = time.monotonic()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    depths = [l for l in lines if l.startswith("info depth")]
    return lines[-1].split()[1], wall, max((int(l.split()[2]) for l in depths), default=None)


def describe(fen, uci):
    b = chess.Board(fen)
    try:
        m = chess.Move.from_uci(uci)
    except Exception:
        return "unparsable", 0
    if m not in b.legal_moves:
        return "ILLEGAL", 0
    victim = b.piece_at(m.to_square)
    if victim is None:
        return "quiet", 0
    attacker = b.piece_at(m.from_square)
    gain = VAL[victim.piece_type] - (VAL[attacker.piece_type] if not m.promotion else 0)
    return "captures %s" % chess.piece_name(victim.piece_type), gain


out = []


def emit(s):
    out.append(s)
    print(s)


emit("## How bad is the 10 ms case? Does the one-ply answer at least capture? (Threads 1)")
emit("")
emit("| build | position | 10 ms answer | that move | material delta | real search (movetime 50) | that move | same? |")
emit("|---|---|---|---|---|---|---|---|")
for label, exe, pc20 in BUILDS:
    for fen in FENS:
        bm10, w10, d10 = ask(exe, fen, "go wtime 10 btime 10", pc20)
        bm50, w50, d50 = ask(exe, fen, "go movetime 50", pc20)
        kind10, gain10 = describe(fen, bm10)
        kind50, gain50 = describe(fen, bm50)
        emit("| %s | %s | %s (d=%s) | %s | %+d | %s (d=%s) | %s | %s |" %
             (label, fen[:20], bm10, d10, kind10, gain10, bm50, d50, kind50,
              "yes" if bm10 == bm50 else "NO"))

emit("")
emit("### how many one-ply answers were captures")
emit("| build | captures at 10 ms | agrees with the real search |")
emit("|---|---|---|")
for label, exe, pc20 in BUILDS:
    caps = agree = 0
    for fen in FENS:
        bm10, _, _ = ask(exe, fen, "go wtime 10 btime 10", pc20)
        bm50, _, _ = ask(exe, fen, "go movetime 50", pc20)
        k, _ = describe(fen, bm10)
        caps += k.startswith("captures")
        agree += (bm10 == bm50)
    emit("| %s | %d of %d | %d of %d |" % (label, caps, len(FENS), agree, len(FENS)))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
