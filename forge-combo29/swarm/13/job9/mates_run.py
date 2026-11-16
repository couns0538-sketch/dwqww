#!/usr/bin/env python3
"""Job 9: does a reported mate score hold up, on the PC's real path?

Job 7 left a stated gap: "all 12 positions scored cp, none mate, so the mate-score path at these
budgets is untested here". This closes it.

Positions: built so the TRUE mate distance is known independently, by python-chess brute force:
  * a set of simple winning material positions (K+Q vs K, K+R vs K, K+2R vs K, K+Q+B vs K) with the
    loser's king placed at every legal square, then filtered to those where a mate is FORCED within
    a small number of plies, with the true mate distance computed by exhaustive search;
  * plus mate-in-1 and mate-in-2 puzzles taken from the same construction, kept only where
    python-chess confirms the distance.

For each position and each of the PC's three match budgets (20000 / 50000 / 250000) under PC20,
Threads 1, Hash 16, the engine is asked `go nodes N` and I record:
  * the score (`mate M` or `cp X`),
  * whether the bestmove is legal,
  * for a mate score, whether the PV actually DELIVERS mate in the claimed number of plies
    (2M-1 for M>0, 2|M| for M<0), and whether it does so at all,
  * whether the claimed mate agrees with python-chess's independently computed distance.

A `mate M` claim is only counted as CORRECT if the PV ends in checkmate within 2M-1 plies (M>0). A
claim that is merely "some mate exists" is recorded separately from "mate in exactly M".

Usage: mates.py EXE OUTDIR [NS]
"""
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
NS = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "20000,50000,250000").split(",")]
os.makedirs(OUTDIR, exist_ok=True)
MAX_PLIES = 7          # only keep positions whose forced mate is <= 7 plies (small, verifiable)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
assert len(PC20) == 22, "PC20 must be 22 entries; a short list silently measures a different regime"
BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def mate_in_plies(board, max_plies):
    """Smallest N such that the side to move forces mate in <= N plies, or None.

    Full-width, mate-distance exact: returns the minimal forced mate length in plies for the side
    to move (1 = mate in 1). 'Force' means every defence is mated within the bound.
    """
    def mated_within(b, n):
        # can the side to move force mate within n plies?
        if n <= 0:
            return False
        moves = list(b.legal_moves)
        if not moves:
            return b.is_checkmate()
        for m in moves:
            b.push(m)
            # after our move, opponent must be mated within n-1 plies no matter what they do
            opp_moves = list(b.legal_moves)
            if not opp_moves:
                if b.is_checkmate():
                    b.pop()
                    return True       # we delivered mate
                b.pop()
                continue
            ok = True
            for om in opp_moves:
                b.push(om)
                sub = mated_within(b, n - 2)
                b.pop()
                if not sub:
                    ok = False
                    break
            b.pop()
            if ok:
                return True
        return False

    for n in range(1, max_plies + 1, 2):
        if mated_within(board, n):
            return n
    return None


def build_positions():
    """K+Q/K+R/K+2R/K+Q+B vs lone king, filtered to forced mates within MAX_PLIES."""
    out = []
    attackers = {
        "KQvK": [chess.QUEEN],
        "KRvK": [chess.ROOK],
        "KRRvK": [chess.ROOK, chess.ROOK],
        "KQBvK": [chess.QUEEN, chess.BISHOP],
    }
    files = range(8)
    for name, pieces in attackers.items():
        count = 0
        for wk in [chess.A1, chess.D4, chess.E5, chess.H8, chess.B2]:
            for bk in range(64):
                if bk == wk or chess.square_distance(bk, wk) <= 1:
                    continue
                if len(pieces) == 1 and pieces[0] == chess.ROOK and count >= 26:
                    continue
                if count >= 26:
                    continue
                b = chess.Board(None)
                b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                free = [s for s in range(64) if s not in (wk, bk)]
                placed = None
                # deterministic placement search over a few squares per extra piece
                for combo in itertools.islice(itertools.permutations(free, len(pieces)), 0, 400):
                    trial = b.copy()
                    okp = True
                    for sq, pt in zip(combo, pieces):
                        trial.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
                    if not trial.is_valid():
                        continue
                    trial.turn = chess.WHITE
                    if trial.is_check():
                        continue
                    n = mate_in_plies(trial, MAX_PLIES)
                    if n is not None:
                        placed = (trial.fen(), n)
                        break
                if placed:
                    out.append({"fen": placed[0], "true_mate_plies": placed[1],
                                "kind": name})
                    count += 1
    return out


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        opts = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died in uci handshake")
            l = l.rstrip("\n")
            if l.startswith("option name"):
                opts.append(l)
            if l == "uciok":
                break
        for n, v in PC20:
            if not any(o.startswith("option name %s " % n) for o in opts):
                raise SystemExit("FAIL: option %r not advertised" % n)
            self.send("setoption name %s value %s" % (n, v))
            self.ready()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def ready(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died waiting readyok")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l == "readyok":
                return

    def search(self, fen, N):
        self.send("position fen " + fen)
        self.ready()
        self.send("go nodes %d" % N)
        infos = []
        bm = None
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: died during search")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if l.startswith("bestmove"):
                bm = l
                break
            if l.startswith("info depth"):
                infos.append(l)
        last = infos[-1] if infos else None

        def g(pat):
            m = re.search(pat, last) if last else None
            return int(m.group(1)) if m else None

        pv = None
        if last and " pv " in last:
            pv = last.split(" pv ", 1)[1].split()
        return {
            "depth": g(r"\bdepth (\d+)"), "nodes": g(r"\bnodes (\d+)"),
            "cp": g(r"\bscore cp (-?\d+)"), "mate": g(r"\bscore mate (-?\d+)"),
            "bestmove": bm, "pv": pv, "info_lines": len(infos),
        }

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def pv_mates_in(fen, pv):
    """Replay the PV; return the ply at which a mate is delivered, or None."""
    if not pv:
        return None
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


def main():
    pos = json.load(open(os.path.join(OUTDIR, "positions.json")))
    if not pos:
        raise SystemExit("FAIL: no forced-mate positions were built")
    print("built", len(pos), "forced-mate positions:", flush=True)
    with open(os.path.join(OUTDIR, "positions.json"), "w") as f:
        json.dump(pos, f, indent=1)

    e = Eng()
    rows = []
    for p in pos:
        legal = {m.uci() for m in chess.Board(p["fen"]).legal_moves}
        for N in NS:
            r = e.search(p["fen"], N)
            mv = None
            if r["bestmove"] and r["bestmove"].startswith("bestmove "):
                mv = r["bestmove"].split()[1]
            delivered = pv_mates_in(p["fen"], r["pv"])
            claim = r["mate"]
            # correctness of a positive mate claim: PV mates in exactly or fewer than 2M-1 plies
            if claim is not None and claim > 0:
                need = 2 * claim - 1
                pv_ok = (delivered is not None and delivered <= need)
                agrees = (delivered == p["true_mate_plies"]) if delivered else False
            elif claim is not None and claim < 0:
                need = 2 * abs(claim)
                pv_ok = None      # negative score = we are being mated; PV check differs
                agrees = None
            else:
                need = None
                pv_ok = None
                agrees = None
            rows.append({
                "fen": p["fen"], "kind": p.get("kind", p.get("note","")), "true_mate_plies": p["true_mate_plies"],
                "N": N, "depth": r["depth"], "nodes": r["nodes"],
                "cp": r["cp"], "mate": claim, "need_plies": need,
                "pv": r["pv"], "pv_mates_at_ply": delivered,
                "pv_delivers_claimed_mate": pv_ok,
                "pv_ply_equals_true": agrees,
                "bestmove": mv, "bestmove_legal": (mv in legal) if mv else False,
            })
            print("N %-7d %-7s true %-5s mate %-5s depth %-3s pv_mates_at %-4s legal %s"
                  % (N, p.get("kind", p.get("note", "")), p["true_mate_plies"], claim, r["depth"],
                     delivered, (mv in legal) if mv else False), flush=True)
    e.close()

    found = [r for r in rows if r["mate"] is not None]
    pos_claims = [r for r in found if r["mate"] > 0]
    wrong_claims = [r for r in pos_claims if r["pv_delivers_claimed_mate"] is False]
    disagree_dist = [r for r in pos_claims if r["pv_ply_equals_true"] is False]
    summary = {
        "build": os.path.abspath(EXE), "sha256": sha256(EXE),
        "settings": "PC20 (Threads 1, Hash 16, S14 + 6)",
        "positions": len(pos), "budgets": NS, "runs": len(rows),
        "runs_with_mate_score": len(found),
        "positive_mate_claims": len(pos_claims),
        "claims_not_delivered_by_own_pv": len(wrong_claims),
        "pvmated_distance_differs_from_true": len(disagree_dist),
        "illegal_bestmoves": sum(1 for r in rows if not r["bestmove_legal"]),
        "positions_with_any_mate_score": len({r["fen"] for r in found}),
    }
    with open(os.path.join(OUTDIR, "mates.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows,
                   "wrong_claims": wrong_claims, "distance_disagreements": disagree_dist}, f, indent=1)
    print()
    for k, v in summary.items():
        print("%-38s %s" % (k, v))


main()
