#!/usr/bin/env python3
"""mate_game.py EXE : a full self-play game that MUST end in mate, audited the same way.

The 90-ply game in S-F30 ended by threefold repetition, so the mate path of a real game was never exercised. This
starts both sides in a position with overwhelming but not immediate material for White, so the game ends in mate
(or gets decided), and audits every move exactly as S-F30 did:
  * illegal moves / missing final info lines / completed iterations
  * node spend vs the requested budget
  * and specifically: does the engine ever report a MATE score whose PV is not a mate, DURING the game?
That last check is the one my S-F27 work got wrong by typing a PV; here the PV is sliced from the engine line and
played out immediately, so no reconstruction is possible.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
# White has Q + R vs a lone king: mate is forced, so the game must end in checkmate.
START = "4k3/8/8/8/8/8/8/K1QR4 w - - 0 1"
MAXPLY = 120
NODES = 20000


def ask(fen):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go nodes {NODES}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    score, nodes, pv = "?", None, []
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        score = m.group(0) if m else "?"
        n = re.search(r"nodes (\d+)", last)
        nodes = int(n.group(1)) if n else None
        toks = last.split()
        if "pv" in toks:
            pv = toks[toks.index("pv") + 1:]
    return best, score, nodes, pv


def pv_is_mate(fen, score, pv):
    m = re.search(r"score mate (-?\d+)", score)
    if not m:
        return None
    v = int(m.group(1))
    need = 2 * v - 1 if v > 0 else 2 * abs(v)
    b = chess.Board(fen)
    for mv in pv:                      # sliced from the engine line, never typed
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return False
        if mm not in b.legal_moves:
            return False
        b.push(mm)
    return b.is_checkmate() and len(pv) == need


b = chess.Board(START)
rows = []
illegal = no_info = completed = mate_claims = mate_bad = 0
nodes_ratios = []
for ply in range(MAXPLY):
    if b.is_game_over(claim_draw=True):
        break
    best, score, nodes, pv = ask(b.fen())
    legal = False
    if best and best != "0000":
        try:
            mv = chess.Move.from_uci(best)
            legal = mv in b.legal_moves
        except ValueError:
            legal = False
    if not legal:
        illegal += 1
        rows.append((ply, best, score, nodes, len(pv), "ILLEGAL"))
        break
    if score == "?":
        no_info += 1
    if pv:
        completed += 1
    if nodes is not None:
        nodes_ratios.append(nodes / NODES)
    verdict = ""
    chk = pv_is_mate(b.fen(), score, pv)
    if chk is not None:
        mate_claims += 1
        if not chk:
            mate_bad += 1
            verdict = "MATE-PV-WRONG"
    rows.append((ply, best, score, nodes, len(pv), verdict))
    b.push(chess.Move.from_uci(best))

print(f"### self-play to mate at the match setting — PC r15/PC20, Threads 1, Hash 16, {NODES} nodes/move")
print(f"start: {START}")
print(f"plies: {len(rows)}   result: {b.outcome(claim_draw=True)}")
print(f"illegal: {illegal} | missing info: {no_info} | completed-iteration moves: {completed}/{len(rows)}")
print(f"mate scores claimed during the game: {mate_claims} | of those whose PV was NOT a mate: {mate_bad}")
if nodes_ratios:
    import statistics
    print(f"nodes/N: median {statistics.median(nodes_ratios):.2f}, min {min(nodes_ratios):.2f}, "
          f"max {max(nodes_ratios):.2f}")
print()
for ply, best, score, nodes, pvlen, verdict in rows[-12:]:
    print(f"  ply {ply:>3} {best:>6} {score:>12} nodes {str(nodes):>6} pv {pvlen:>2} {verdict}")
