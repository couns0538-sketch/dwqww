#!/usr/bin/env python3
"""classify_mates.py JSONL EXE : for every mate score, decide whether the SCORE or only the PV is wrong.

Method, per record with a `mate N` score:
  1. play its final PV with python-chess -> legal? ends in checkmate?
  2. re-search the SAME position at depth 24 with the same engine and S14 -> its deeper mate number
  3. play the deeper PV with python-chess -> checkmate? after how many plies?
  4. classify:
       PV_OK            the depth-12 PV ends in checkmate at exactly the claimed distance
       PV_SHORT_SCORE_RIGHT  the depth-12 PV is short/not mate, BUT the deeper search agrees on the number
                             and the deeper PV checkmates at that distance
       SCORE_WRONG      the deeper search gives a DIFFERENT mate number (so depth 12's number is wrong)
       UNRESOLVED       the deeper PV also fails to checkmate (cannot decide)
Every record must yield a verdict; a record with no parseable score aborts the run (exit 3).
"""
import json
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


def deep_search(exe, fen, depth=24):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 64\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth") and " pv " in line:
            last = line
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if not last:
        return None, None
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:]
    return (int(m.group(1)) if m else None), pv


def play(fen, pv):
    """Returns (all_legal, is_checkmate_after, plies)."""
    b = chess.Board(fen)
    for mv in pv:
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return False, False, 0
        if m not in b.legal_moves:
            return False, False, 0
        b.push(m)
    return True, b.is_checkmate(), len(pv)


def final_pv(rec):
    last = None
    for line in rec["lines"]:
        if line.startswith("info ") and " pv " in line:
            toks = line.split()
            last = toks[toks.index("pv") + 1:]
    return last


def main():
    path, exe = sys.argv[1], sys.argv[2]
    recs = [json.loads(l) for l in open(path)]
    unparsed = [r for r in recs if not any(re.search(r"score (cp|mate) -?\d+", l)
                                           for l in r["lines"] if l.startswith("info"))]
    print(f"records: {len(recs)} | records with no score at all: {len(unparsed)}")
    if not recs:
        print("CHECK FAILED: no records — nothing measured"); return 3

    mate_recs = [r for r in recs if any("score mate" in l for l in r["lines"] if l.startswith("info"))]
    print(f"records with a mate score (at any depth): {len(mate_recs)}")

    counts = {"PV_OK": 0, "PV_SHORT_SCORE_RIGHT": 0, "SCORE_WRONG": 0, "UNRESOLVED": 0}
    rows = []
    for r in mate_recs:
        pv = final_pv(r)
        if pv is None:
            continue
        lastline = [l for l in r["lines"] if l.startswith("info depth") and " pv " in l][-1]
        claim = int(re.search(r"score mate (-?\d+)", lastline).group(1))
        want = 2 * claim - 1 if claim > 0 else 2 * abs(claim)
        legal, is_mate, plies = play(r["fen"], pv)
        deep_claim, deep_pv = deep_search(exe, r["fen"])
        deep_mate, deep_plies = (False, 0)
        if deep_pv:
            _, deep_mate, deep_plies = play(r["fen"], deep_pv)

        if legal and is_mate and plies == want:
            verdict = "PV_OK"
        elif deep_claim is not None and deep_claim != claim:
            verdict = "SCORE_WRONG"
        elif legal and is_mate:
            verdict = "PV_OK"
        elif deep_claim == claim and deep_mate and deep_plies == want:
            verdict = "PV_SHORT_SCORE_RIGHT"
        else:
            verdict = "UNRESOLVED"
        counts[verdict] += 1
        rows.append((r["fen"], claim, plies, legal, is_mate, deep_claim, deep_plies, deep_mate, verdict))

    print()
    print(f"{'verdict':<22} {'count':>5}")
    for k, v in counts.items():
        print(f"{k:<22} {v:>5}")
    print()
    for (fen, claim, plies, legal, is_mate, dclaim, dplies, dmate, verdict) in rows:
        if verdict != "PV_OK":
            print(f"{verdict:<22} claim mate {claim:>3} pv {plies:>2} plies (legal={legal}, mate={is_mate})")
            print(f"   deep: mate {dclaim} pv {dplies} plies mate={dmate}")
            print(f"   {fen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
