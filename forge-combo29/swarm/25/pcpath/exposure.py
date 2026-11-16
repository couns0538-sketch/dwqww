#!/usr/bin/env python3
"""exposure.py EXE FENS N : the number the owner needs.

For each position at `go nodes 20000` (a real match setting), PC20, Threads 1, Hash 16:
  * is the FINAL score a mate, and is its PV legal and a real mate?      (final-answer correctness)
  * does ANY intermediate info line carry an illegal move or a mate PV that fails play-out?  (streaming exposure)
Counts both, because they are different exposures:
  E1 final answer wrong      - a match/training record reading the last score gets a bad label
  E2 intermediate line bad   - a GUI or a pipeline parsing every line gets an unreplayable PV
Controls: report how many mate scores exist at all, so a 0 is not vacuous; and run `go depth 12` as the
reference for how often mates occur at all in this position set.
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
FENS = sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 100


def all_infos(fen, go):
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
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
            out.append(s)
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return out


def judge(fen, line):
    """(is_mate, legal, is_checkmate_at_end, plies, need)"""
    m = re.search(r"score mate (-?\d+)", line)
    if not m:
        return None
    v = int(m.group(1))
    need = 2 * v - 1 if v > 0 else 2 * abs(v)
    toks = line.split()
    pv = toks[toks.index("pv") + 1:]
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return (v, False, False, len(pv), need)
        if mm not in b.legal_moves:
            return (v, False, False, len(pv), need)
        b.push(mm)
    return (v, True, b.is_checkmate(), len(pv), need)


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print(f"### exposure of the `go nodes 20000` PV defect — PC r15/PC20, Threads 1, Hash 16, {len(fens)} positions")
e1 = e2 = mates_final = mates_any = illegal_intermediate = 0
bad_final_rows = []
bad_mid_rows = []
for fen in fens:
    b = chess.Board(fen)
    if b.is_game_over(claim_draw=False):
        continue
    infos = all_infos(fen, "go nodes 20000")
    if not infos:
        continue
    # E1: the final line, if it is a mate
    fin = None
    for line in reversed(infos):
        if "score mate" in line:
            fin = line
            break
    if fin is not None:
        mates_final += 1
        v, legal, mate, pl, need = judge(fen, fin)
        if not (legal and mate and pl == need):
            e1 += 1
            bad_final_rows.append((fen, v, pl, need, legal, mate))
    # E2: any intermediate line with an illegal PV
    for line in infos:
        r = judge(fen, line)
        if r is None:
            continue
        mates_any += 1
        v, legal, mate, pl, need = r
        if not legal:
            e2 += 1
            illegal_intermediate += 1
            bad_mid_rows.append((fen, v, pl, need, "ILLEGAL MOVE"))
            break

print(f"mate scores in final lines      : {mates_final}")
print(f"  of those, FINAL answer wrong  : {e1}"
      + (f"  ({100.0*e1/mates_final:.1f}%)" if mates_final else "  (vacuous)"))
print(f"mate scores across all lines    : {mates_any}")
print(f"  lines with an ILLEGAL PV move : {illegal_intermediate}"
      + (f"  ({100.0*illegal_intermediate/mates_any:.1f}% of mate lines)" if mates_any else "  (vacuous)"))
print()
for fen, v, pl, need, legal, mate in bad_final_rows[:6]:
    print(f"  E1 {fen[:44]} mate {v} pv {pl} need {need} legal={legal} mate={mate}")
for fen, v, pl, need, why in bad_mid_rows[:6]:
    print(f"  E2 {fen[:44]} mate {v} pv {pl} need {need} {why}")
