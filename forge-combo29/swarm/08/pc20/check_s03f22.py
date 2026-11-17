#!/usr/bin/env python3
"""check_s03f22.py OUT — my own check of seat 03's S-F22, WITH A PLANT.

Their claim:
" In 50 real-game lone-king positions at depth 16 (PC build, PC20, Threads 1, Hash 16) the strict S-F20 signature
 (chosen move scored worse than an available alternative by more than a queen) occurs 0 of 50; the smaller-magnitude
 version (any margin) occurs 11 of 45 scorable positions, median 36 cp, max 161 cp."

This is a ZERO about their own defect, so it needs a plant or it is "not shown" — that is the rule this seat has been
held to all night. The plant: a position where the signature is KNOWN to occur (their S-F20 board,
`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`, on which they prove `c6c7` loses and `c6d6` survives), run through the
SAME scanner. If the scanner does not flag that board, the 0 of 50 is void.

The signature, as I implement it independently:
  for each root move, score it with `go depth D searchmoves <move>`; the chosen move's score is compared against the
  best alternative's. "Strict" = chosen is worse by more than a QUEEN (900 cp, or any mate-vs-cp gap).
  For mates, compare plies-to-mate: a mated move is worse than any non-mated one.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
DEPTH = 12          # reduced from their 16 for time; stated in the report
QUEEN = 900
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

PLANT_FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
# a handful of real-game lone-king positions (a king on the board for the side to move and few pieces)
g = [" ".join(l.strip().split()[:6]) for l in open("../job1/set_G.epd") if l.strip()]
LONE = [f for f in g if len(chess.Board(f).piece_map()) <= 8][:12]


def score_move(fen, move, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    send("go depth %d searchmoves %s" % (depth, move))
    ok = done.wait(60.0)
    if not ok:
        p.kill()
        return None
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    for l in reversed(lines):
        if l.startswith("info depth") and " score " in l:
            t = l.split()
            si = t.index("score")
            return "%s %s" % (t[si + 1], t[si + 2])
    return None


def value(score):
    """cp -> cp; mate N -> +-(30000 - |N|) so a mate beats any cp and a closer mate beats a further one."""
    if not score:
        return None
    t = score.split()
    try:
        v = int(t[1])
    except (IndexError, ValueError):
        return None
    if t[0] == "cp":
        return v
    if t[0] == "mate":
        return (30000 - abs(v)) * (1 if v > 0 else -1)
    return None


def scan(fen, depth=DEPTH, max_moves=8):
    """Return (chosen_move, chosen_value, best_alt_value, margin, is_mate_gap)."""
    b = chess.Board(fen)
    moves = [b.uci(m) for m in b.legal_moves][:max_moves]
    if len(moves) < 2:
        return None
    # the engine's own choice, unrestricted
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send("go depth %d" % depth)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    chosen = lines[-1].split()[1]
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()

    chosen_v = value(score_move(fen, chosen, depth)) if chosen in moves else None
    best_v = chosen_v
    for m in moves:
        if m == chosen:
            continue
        v = value(score_move(fen, m, depth))
        if v is not None and (best_v is None or v > best_v):
            best_v = v
    if chosen_v is None or best_v is None:
        return None
    margin = best_v - chosen_v
    mate_gap = best_v > 20000 and chosen_v < 20000
    return {"chosen": chosen, "chosen_v": chosen_v, "best_v": best_v, "margin": margin, "mate_gap": mate_gap}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 03 S-F22 — the strict signature ('chosen worse than an alternative by more than a queen'), WITH A PLANT")
emit("")
emit("PC r15, PC20, Threads 1, Hash 16, depth **%d** here (their 16 reduced for time — stated)." % DEPTH)
emit("")
emit("### THE PLANT first — their S-F20 board, where the signature is KNOWN to occur")
pr = scan(PLANT_FEN)
if pr is None:
    raise SystemExit("PLANT FAILED TO RUN")
emit("")
emit("| chosen | its value | best alternative | margin | mate gap? |")
emit("|---|---|---|---|---|")
emit("| %s | %d | %d | **%d** | %s |" %
     (pr["chosen"], pr["chosen_v"], pr["best_v"], pr["margin"], "YES" if pr["mate_gap"] else "no"))
plant_hit = pr["margin"] > QUEEN or pr["mate_gap"]
emit("")
emit("**PLANT: the scanner %s the known-bad board — the zero below %s.**" %
     ("FLAGS" if plant_hit else "DOES NOT FLAG",
      "is meaningful" if plant_hit else "is VOID (harness cannot see the defect)"))
if not plant_hit:
    emit()
    emit("Because the plant failed, I will not report the 0 of N as a measurement.")

emit("")
emit("### The sample — real-game positions with few pieces")
emit("")
emit("| position | chosen | its value | best alt | margin | strict hit (>%d cp or mate gap)? |" % QUEEN)
emit("|---|---|---|---|---|---|")
strict = anym = 0
tot = 0
for fen in LONE:
    r = scan(fen)
    if r is None:
        continue
    tot += 1
    hit = r["margin"] > QUEEN or r["mate_gap"]
    if hit:
        strict += 1
    if r["margin"] > 0 or r["mate_gap"]:
        anym += 1
    emit("| %s | %s | %d | %d | %d | %s |" %
         (fen[:30], r["chosen"], r["chosen_v"], r["best_v"], r["margin"], "**YES**" if hit else "no"))

emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions scanned | %d |" % tot)
emit("| strict hits (more than a queen, or a mate gap) | **%d** |" % strict)
emit("| any-margin hits | %d |" % anym)
emit("| scanner provably able to flag the defect (plant) | **%s** |" % ("YES" if plant_hit else "NO"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
