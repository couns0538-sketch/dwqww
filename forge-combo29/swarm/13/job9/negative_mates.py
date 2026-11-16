#!/usr/bin/env python3
"""Negative mate scores on the PC's real path: filter real lost positions, search, verify.

The verification predicate for `mate -M` is NOT the same as for `mate +M`:
  mate +M : the SIDE TO MOVE forces mate within 2M-1 plies
  mate -M : after the side to move plays any move, the OPPONENT forces mate within 2|M|-1 plies
Getting this wrong produces a confident FALSE FAILURE (I did exactly that once; see NEGATIVE_MATES.md).

Usage: negative_mates.py EXE G_FENS OUTDIR [MAX_POS] [MATERIAL_THRESHOLD]
"""
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
G_FENS = sys.argv[2]
OUTDIR = sys.argv[3]
MAX_POS = int(sys.argv[4]) if len(sys.argv) > 4 else 6
THRESH = int(sys.argv[5]) if len(sys.argv) > 5 else 700
os.makedirs(OUTDIR, exist_ok=True)
BUDGETS = [20000, 250000]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
assert len(PC20) == 22, "PC20 must be 22 entries; a short list silently measures a different regime"
VAL = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500,
       chess.QUEEN: 900, chess.KING: 0}


def forces_mate(b, n):
    """Side to move forces mate within n plies."""
    if n <= 0:
        return False
    moves = list(b.legal_moves)
    if not moves:
        return False
    for m in moves:
        b.push(m)
        if b.is_checkmate():
            b.pop()
            return True
        if n >= 2:
            opp = list(b.legal_moves)
            if opp:
                all_mated = True
                for om in opp:
                    b.push(om)
                    ok = forces_mate(b, n - 2)
                    b.pop()
                    if not ok:
                        all_mated = False
                        break
                if all_mated:
                    b.pop()
                    return True
        b.pop()
    return False


def side_is_mated_within(b, n):
    """The side to move gets mated by the opponent within n plies. THE test for mate -M."""
    if b.is_checkmate():
        return True
    if not b.legal_moves:
        return False
    for m in b.legal_moves:
        b.push(m)
        ok = forces_mate(b, n - 1)
        b.pop()
        if ok:
            return True
    return False


def pv_mates_in(fen, pv):
    b = chess.Board(fen)
    for i, u in enumerate(pv, 1):
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return None
        if m not in b.legal_moves:
            return None
        b.push(m)
        if b.is_checkmate():
            return i
    return None


def search(fen, N):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    opts = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: engine died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            opts.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in opts):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        while p.stdout.readline().rstrip("\n") != "readyok":
            pass
    send("position fen " + fen)
    send("isready")
    while p.stdout.readline().rstrip("\n") != "readyok":
        pass
    send("go nodes %d" % N)
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: engine died during search")
        l = l.rstrip("\n")
        if any(b in l.lower() for b in ("unknown option", "invalid value", "error")):
            raise SystemExit("FAIL: bad line %r" % l)
        if l.startswith("bestmove"):
            bm = l
            break
        if l.startswith("info depth"):
            last = l
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    mt = re.search(r"score mate (-?\d+)", last) if last else None
    cp = re.search(r"score cp (-?\d+)", last) if last else None
    pv = last.split(" pv ", 1)[1].split() if last and " pv " in last else []
    return (int(mt.group(1)) if mt else None, int(cp.group(1)) if cp else None, bm, pv)


def main():
    fens = [l.strip() for l in open(G_FENS) if l.strip()]
    cands = []
    for fen in fens:
        try:
            b = chess.Board(fen)
        except ValueError:
            continue
        bal = 0
        for sq in chess.SQUARES:
            piece = b.piece_at(sq)
            if piece:
                bal += VAL[piece.piece_type] * (1 if piece.color else -1)
        stm = bal if b.turn else -bal
        if stm <= -THRESH:
            cands.append((stm, fen))
    cands.sort()
    chosen = [f for _, f in cands[:MAX_POS]]
    print("lost candidates (side to move down >= %d): %d, using %d" % (THRESH, len(cands), len(chosen)))
    json.dump(chosen, open(os.path.join(OUTDIR, "lost_candidates.json"), "w"), indent=1)

    rows = []
    for fen in chosen:
        for N in BUDGETS:
            mate, cp, bm, pv = search(fen, N)
            row = {"fen": fen, "N": N, "mate": mate, "cp": cp, "bestmove": bm, "pv": pv}
            if mate is not None and mate < 0:
                need = 2 * abs(mate)
                forced = side_is_mated_within(chess.Board(fen), need)
                delivered = pv_mates_in(fen, pv)
                row.update({"need_plies": need, "opponent_forces_within": forced,
                            "pv_mates_at_ply": delivered,
                            "correct": bool(forced) and delivered is not None and delivered <= need})
            rows.append(row)
            print("%-52s N %-7d mate %-6s cp %-8s %s"
                  % (fen[:52], N, mate, cp, row.get("correct", "-")), flush=True)

    neg = [r for r in rows if r["mate"] is not None and r["mate"] < 0]
    summary = {
        "runs": len(rows),
        "negative_mate_claims": len(neg),
        "negative_claims_correct": sum(1 for r in neg if r["correct"]),
        "negative_cp_scores": sum(1 for r in rows if r["cp"] is not None and r["cp"] < 0),
        "non_negative_scores_in_lost_positions":
            sum(1 for r in rows if (r["mate"] is not None and r["mate"] >= 0)
                or (r["cp"] is not None and r["cp"] >= 0)),
    }
    json.dump({"summary": summary, "rows": rows},
              open(os.path.join(OUTDIR, "lost_positions.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        print("%-40s %s" % (k, v))


main()
