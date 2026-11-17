#!/usr/bin/env python3
"""check_s21f8b.py OUT — my own check of seat 21's 21-F8b:

"`fullmove 0` is still REFUSED (`invalid FEN: invalid FEN fields`) and leaves the stale board (perft 1 = 20 where the
 position would give something else)."

Two links, both testable, and the second uses synchronous perft so it cannot be faked by a closed pipe:
  1. `fullmove 0` is refused with the expected info string, on PC r15 under PC20;
  2. after the refusal the engine holds the PREVIOUS board (perft 1 equals the previous position's legal-move count,
     not the refused position's).

CONTROLS:
  - the previous position must be ACCEPTED (else the test has nothing to keep);
  - the two boards must have DIFFERENT legal-move counts (else "which board is held" is unanswerable);
  - python-chess must accept the `fullmove 0` FEN (seat 21's claim is that the ENGINE is stricter than python-chess),
    which is what makes this an engine-strictness finding rather than a bad-FEN finding.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

PREV = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"   # 20 legal moves vs the refused board's 33
REFUSED = "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 0"   # fullmove 0


def session():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    return p, send, sync


out = []
def emit(s):
    out.append(s)
    print(s)

# control: python-chess must accept the fullmove-0 FEN
try:
    b0 = chess.Board(REFUSED)
    py_ok = True
    py_moves = b0.legal_moves.count()
except Exception as e:
    py_ok = False
    py_moves = None

prev = chess.Board(PREV)
prev_moves = prev.legal_moves.count()
emit("## seat 21's 21-F8b — is `fullmove 0` refused, and does it leave the stale board?")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| python-chess accepts the `fullmove 0` FEN? | **%s** |" % ("yes" if py_ok else "NO"))
emit("| its legal-move count (python-chess) | %s |" % py_moves)
emit("| the PREVIOUS position's legal-move count | %d |" % prev_moves)
emit("")
if not py_ok:
    raise SystemExit("CONTROL FAILED: python-chess rejects the fullmove-0 FEN, so the engine's refusal is not "
                     "strictness and this test cannot run as designed")
if py_moves == prev_moves:
    raise SystemExit("CONTROL FAILED: the two boards have the same legal-move count (%d), so 'which board is held' "
                     "cannot be answered by perft 1" % py_moves)

p, send, sync = session()
# 1. put PREV on the board
send("position fen " + PREV)
sync()
# 2. try the REFUSED fen and capture the answer
send("position fen " + REFUSED)
pre = sync()
refusal = [l for l in pre if "invalid FEN" in l]
# 3. perft 1 — which board is held?
send("go perft 1")
lines = []
while True:
    l = p.stdout.readline()
    if not l:
        raise EOFError
    lines.append(l.rstrip("\n"))
    if l.startswith("nodes "):
        break
sync()
nodes = int([l for l in lines if l.startswith("nodes ")][-1].split()[1])
try:
    send("quit"); p.wait(timeout=10)
except Exception:
    p.kill()

emit("## The measurement")
emit("")
emit("| step | result |")
emit("|---|---|")
emit("| `position fen` with `fullmove 0` | **%s** |" % (refusal[0] if refusal else "NOT REFUSED"))
emit("| `go perft 1` afterwards | **%d nodes** |" % nodes)
emit("")
emit("| their claim | my measurement |")
emit("|---|---|")
emit("| `fullmove 0` is still REFUSED on the PC build | **%s** |" % ("YES" if refusal else "NO"))
emit("| the refusal leaves the STALE board | **%s** (perft 1 = %d; the previous board gives %d, the refused one would give %s) |" %
     ("YES" if nodes == prev_moves else "NO", nodes, prev_moves, py_moves))
emit("")
ok = bool(refusal) and nodes == prev_moves
if ok:
    emit("**CONFIRMS**: the engine is stricter than python-chess on `fullmove 0`, refuses it, and keeps the previous")
    emit("board. Synchronous perft proves the stale-board half, so no reader pattern can have influenced it.")
else:
    emit("**NOT CONFIRMED as stated** — see the two rows above.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
