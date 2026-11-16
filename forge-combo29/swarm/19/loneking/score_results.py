#!/usr/bin/env python3
"""score_results.py EXE FENS OUTDIR : does the engine's move produce a WORSE RESULT than an available alternative?

Scoring by RESULT, not by ply count — the point of the job. For each lone-king position:

  1. ask the engine for its move at depth 16 and at `go nodes 20000` (fresh process, PC20, Threads 1, cold);
  2. for the engine's move AND for every legal alternative, compute the resulting position's terminal status:
       checkmate delivered?            -> WIN  (best possible)
       insufficient material after?    -> DRAW (unwinnable)
       game over otherwise?            -> DRAW (stalemate / dead)
       otherwise                       -> UNKNOWN (no tablebase available, so the true result is not known)
  3. a position is a DEFECT when the engine's move reaches a strictly worse terminal status than some legal
     alternative: engine move DRAW while an alternative is WIN, or engine move UNKNOWN while an alternative is
     WIN.

Honest limit, stated up front: without Syzygy tablebases (none on this machine, mirror unreachable) "WIN for
the side to move" can only be detected when the move MATES IMMEDIATELY. So this measures
  "the engine missed a mate in one that another legal move delivers, or chose a drawn line where another move
   mates at once"
which is a strictly narrower question than "loses six plies sooner". It is the question the three named
predicates can answer exactly, and it is reported as such.
"""
import os
import subprocess
import sys

import chess

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16"), ("Move Overhead", "10")]

positions = [l.strip() for l in open(fens) if l.strip()]
WIN, DRAW, UNKNOWN = 2, 1, 0


def status_name(v):
    return {WIN: "WIN", DRAW: "DRAW", None: "illegal"}.get(v, "unknown")


def status_after(board, move):
    """Terminal status of the position after `move`, judged by result not by ply count."""
    b = board.copy()
    b.push(move)
    if b.is_checkmate():
        return WIN
    if b.is_insufficient_material() or b.is_game_over():
        return DRAW
    return UNKNOWN


def ask(fen, cmd):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred):
        got = []
        for _ in range(400000):
            l = p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send(cmd)
    block = readto(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    best = None
    nodes_reported = 0
    for l in block:
        if l.startswith("bestmove"):
            parts = l.split()
            best = parts[1] if len(parts) > 1 else None
        if " nodes " in l:
            try:
                nodes_reported = max(nodes_reported, int(l.split("nodes ")[1].split()[0]))
            except (IndexError, ValueError):
                pass
    return best, nodes_reported


rows = []
defects = 0
for i, fen in enumerate(positions):
    board = chess.Board(fen)
    legal = list(board.legal_moves)
    by_uci = {m.uci(): m for m in legal}
    alt_best = max((status_after(board, m) for m in legal), default=UNKNOWN)
    m16, n16 = ask(fen, "go depth 16")
    m20k, n20k = ask(fen, "go nodes 20000")
    r16 = status_after(board, by_uci[m16]) if m16 in by_uci else None
    r20k = status_after(board, by_uci[m20k]) if m20k in by_uci else None
    # A DEFECT is a MISSED WIN: some legal alternative mates at once (WIN) while the engine's move does not.
    # The earlier version of this script ordered UNKNOWN < DRAW, which is wrong: a non-terminal position is not
    # known to be worse than a draw, it is simply unknown. That bug flagged two positions where the engine had
    # promoted correctly and an under-promotion would have thrown the win away. With no tablebases, WIN is the
    # ONLY status that can be established exactly, so the only defensible defect test is "missed an immediate
    # mate". See the report; the wider question ("loses six plies sooner") is NOT answerable here.
    worse16 = r16 is not None and alt_best == WIN and r16 != WIN
    worse20k = r20k is not None and alt_best == WIN and r20k != WIN
    if worse16 or worse20k:
        defects += 1
    rows.append((i, fen, len(legal), alt_best, m16, r16, n16, worse16, m20k, r20k, n20k, worse20k))
    print("pos %2d legal %2d best-avail %d | depth16 %s -> %s %s | nodes20k %s -> %s %s"
          % (i, len(legal), alt_best, m16, status_name(r16), "WORSE" if worse16 else "ok",
             m20k, status_name(r20k), "WORSE" if worse20k else "ok"), flush=True)

names = {WIN: "WIN", DRAW: "DRAW", UNKNOWN: "unknown"}
with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("# lone-king endings: does the engine's move produce a worse RESULT than an available alternative?\n\n")
    fh.write("PC r15, PC20, Threads 1, Hash 16, cold. %d positions.\n" % len(rows))
    fh.write("depth 16 and `go nodes 20000`. Status by python-chess is_insufficient_material/is_checkmate/"
             "is_game_over.\n\n")
    fh.write("| pos | legal | best available | depth16 move | its result | worse? | nodes20k move | its result | worse? |\n")
    fh.write("|---|---|---|---|---|---|---|---|---|\n")
    for (i, fen, nl, ab, m16, r16, n16, w16, m20k, r20k, n20k, w20k) in rows:
        fh.write("| %d | %d | %s | %s | %s | **%s** | %s | %s | **%s** |\n"
                 % (i, nl, names[ab], m16, names.get(r16, "illegal"), "YES" if w16 else "no",
                    m20k, names.get(r20k, "illegal"), "YES" if w20k else "no"))
    fh.write("\n## the count this job asks for\n\n")
    fh.write("**positions where the engine's move produces a worse result than an available alternative: "
             "%d of %d**\n" % (defects, len(rows)))
    fh.write("\n(of which depth-16: %d ; of which go-nodes-20000: %d)\n"
             % (sum(1 for r in rows if r[7]), sum(1 for r in rows if r[11])))
    fh.write("\nNote: 'best available' is WIN only when some legal move MATES AT ONCE — with no tablebases, a "
             "won-but-not-immediate position reads as 'unknown', so this counts missed immediate mates and "
             "drawn-instead-of-mating choices, not slow wins.\n")
print("\n" + open(os.path.join(outdir, "RESULT.txt")).read()[-800:])
