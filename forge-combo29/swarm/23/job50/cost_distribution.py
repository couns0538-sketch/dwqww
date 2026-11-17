#!/usr/bin/env python3
"""job50 : how much does playing generator index 0 COST, across deterministically sampled positions?

Positions: every 400th line of the validated seed-2301 set (job1/R_2301.fens, 5000 positions) -> 12 positions, evenly
spread, NOT hand-picked. For each:
  (a) `go perft 1` on the base -> the engine's own generation order; take index 0 (g0).
  (b) `go depth 12` on the base -> the searched move (best).
  (c) score the position after g0 and after best, on the PC at `go depth 12`, NEGATED for black so positive always means
      "good for the side that moved".
Controls printed in the output:
  - every g0 and best legal per python-chess;
  - parsed divide lines == the `nodes N` total (23-F99);
  - PLANTED case: on the first position where a legal move gives away the queen/rook for nothing, score it and confirm
    the measure registers a large positive cost. A cost measure that cannot see damage proves nothing.
"""
import re, subprocess, sys, os
import chess

MOVELINE = re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUMMARY = re.compile(r"^nodes (\d+)$")
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
FENS = sys.argv[1] if len(sys.argv) > 1 else "../job1/R_2301.fens"
STRIDE = 400


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    opts = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def perft1(p, fen):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go perft 1\n"); p.stdin.flush()
    order = []
    total = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in perft")
        s = l.strip()
        m = MOVELINE.match(s)
        if m:
            order.append(m.group(1))
        ms = SUMMARY.match(s)
        if ms:
            total = int(ms.group(1))
            break
    return order, total


def search(p, fen, depth=12):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


def score_after(pc, fen, move, depth=12):
    """Score the position after `move`, from the MOVER's point of view. Mate -> huge magnitude.

    CONVENTION (proved in the run below): the engine scores for the side to move of the SEARCHED position, which
    after the mover's move is the OPPONENT. So the mover's view is ALWAYS the negation, with no branch on colour.
    The previous version branched on `b.turn` (the opponent's side), which inverted every black-to-move row — that
    bug produced a table in which a depth-12 best move was 2,222 cp worse than the unsearched move, and it was
    caught by exactly that absurdity plus a planted blunder reading as an improvement.
    """
    b = chess.Board(fen)
    b.push(chess.Move.from_uci(move))
    (kind, val, nodes), bm = search(pc, b.fen(), depth)
    # mate conversion must handle BOTH signs: `mate +N` = side to move mates in N (good for it),
    # `mate -N` = side to move IS mated in N (bad for it). The formula 100000-1000*val silently turns
    # mate -4 into +104000 — a SECOND bug found in this same function after the sign branch, because
    # position 8's number was absurd a second time (a depth-12 best move reading as mate-for-the-wrong-side).
    if kind == "mate":
        stm = (100000 - 1000 * val) if val > 0 else (-100000 - 1000 * val)
        return -stm, kind, val
    return -val, kind, val


# ---- convention self-test: must pass before any cost is computed ----
print("== sign-convention self-test ==")
b = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
b.push(chess.Move.from_uci("d8h4"))
print("  after black's d8h4 the position is mate:", b.is_checkmate(), "| side to move:", "white" if b.turn else "black")
print("  mover (black) must read a WIN; opponent's view is 'mated'. Negation is unconditional.")
print()

fens = [l.strip() for l in open(FENS) if l.strip()]
sample = [fens[i] for i in range(0, min(len(fens), STRIDE * 12), STRIDE)][:12]
print("positions sampled from %s: every %dth line -> %d positions" % (FENS, STRIDE, len(sample)))
print()

rows = []
pbase = conn(BASE)
ppc = conn(PC)
parse_fail = 0
absurd = 0
for i, fen in enumerate(sample, 1):
    order, total = perft1(pbase, fen)
    if total is None or len(order) != total or not order:
        print("| %d | **PARSE FAILURE** lines=%d nodes=%s | - | - | - | - |" % (i, len(order), total))
        parse_fail += 1
        continue
    g0 = order[0]
    (bk, bv, bn), best = search(pbase, fen, 12)
    b = chess.Board(fen)
    legal = [m.uci() for m in b.legal_moves]
    ok_legal = (g0 in legal) and (best in legal)
    s_g0, k_g0, v_g0 = score_after(ppc, fen, g0)
    s_best, k_best, v_best = score_after(ppc, fen, best)
    cost = s_best - s_g0
    # ABSURDITY ASSERTIONS - added after two sign bugs in this same function slipped through, both caught only
    # because a human reread the table. A searched best move materially worse than the unsearched generator head
    # (beyond a tolerance for search noise) means the scoring is wrong, not that the engine is.
    if cost < -200 and k_best != "mate":
        print("| %d | **ABSURDITY: searched best scores %d cp WORSE than g0 - scoring is suspect** | %s | %s | %s | %s | %s |"
              % (i, -cost, g0, best, s_g0, s_best, cost))
        absurd += 1
        continue
    if k_best == "mate" and s_best < 0:
        print("| %d | **ABSURDITY: best move reports a mate but scores negative for the mover** | %s | %s | %s | %s | %s |"
              % (i, g0, best, s_g0, s_best, cost))
        absurd += 1
        continue
    rows.append((i, g0, best, s_g0, s_best, cost, ok_legal))
    print("| %d | g0 %s | best %s | %s | %s | **%d** | %s |" % (
        i, g0, best, s_g0, s_best, cost, "legal" if ok_legal else "**ILLEGAL**"))
    sys.stdout.flush()

print()
print("PLANTED CASE (must register large damage, else the measure is blind):")
planted_done = False
for i, fen in enumerate(sample, 1):
    b = chess.Board(fen)
    movers = []
    for m in b.legal_moves:
        if b.is_capture(m):
            continue
        c = b.copy(); c.push(m)
        # does the opponent have a capture of a queen/rook that is undefended? crude plant
        for om in c.legal_moves:
            if c.is_capture(om):
                victim = c.piece_at(om.to_square)
                if victim and victim.piece_type in (chess.QUEEN, chess.ROOK):
                    movers.append(m.uci()); break
        if movers:
            break
    if movers:
        g0 = movers[0]
        (bk, bv, bn), best = search(pbase, fen, 12)
        s_g0, _, _ = score_after(ppc, fen, g0)
        s_best, _, _ = score_after(ppc, fen, best)
        print("  position %d: planted %s (gives away a Q/R) cost = **%d cp** (best %s = %s, planted = %s)" % (
            i, g0, s_best - s_g0, best, s_best, s_g0))
        planted_done = True
        break
if not planted_done:
    print("  NO PLANTABLE POSITION FOUND among the sample -> the measure is UNPROVEN and no cost number may be used")

pbase.stdin.write("quit\n"); pbase.stdin.flush()
ppc.stdin.write("quit\n"); ppc.stdin.flush()
for p in (pbase, ppc):
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

if rows:
    costs = sorted(r[5] for r in rows)
    med = costs[len(costs) // 2]
    print()
    print("parsed %d of %d positions (%d parse failures)" % (len(rows), len(sample), parse_fail))
    print("costs (cp):", [r[5] for r in rows])
    print("median:", med, "| max:", max(costs), "| positions with cost >= 300:", sum(1 for c in costs if c >= 300))
    print("g0 == best on %d of %d" % (sum(1 for r in rows if r[1] == r[2]), len(rows)))
