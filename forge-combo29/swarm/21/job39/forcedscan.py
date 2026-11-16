#!/usr/bin/env python3
"""forcedscan.py EXE OUTDIR [NPOS]

The measurement the coordinator asked for, done with a FORCED-result metric instead of a
single play-out.

For each root position:
  - every legal root move's TRUE result is computed by exhaustive search with a mate-distance
    solver that also honours the fifty-move counter: a line that reaches counter 100 is a draw,
    a mate ends the game. The solver is exact up to SEARCH_PLIES; beyond that the position is
    recorded as UNKNOWN (never guessed).
  - the engine's `go depth 16` and `go nodes 20000` answers are compared to the best TRUE result.
  - a HIT = the chosen move's true result is strictly worse than the best available.

Positions are lone-king endings where a draw is REACHABLE (single minor, or R/Q at counter 90-99),
because that is the only region where the class can exist.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
SEED = 2101
SEARCH_PLIES = 7        # exact solver depth in plies (kept small enough to be fast and honest)
RANK = {"loss": 0, "draw": 1, "win": 2, "UNKNOWN": None}


def solve(b, ply_left, mover):
    """Exact result for `mover` with minimax: 'win'/'draw'/'loss', or 'UNKNOWN' when the ply
    budget runs out before the position is settled. Any UNKNOWN anywhere in a subtree makes that
    subtree's value UNKNOWN (never guessed), and an UNKNOWN child poisons the parent."""
    if b.is_checkmate():
        return "loss" if b.turn == mover else "win"
    if b.is_stalemate() or b.is_insufficient_material():
        return "draw"
    if b.halfmove_clock >= 100:
        return "draw"
    if ply_left <= 0:
        return "UNKNOWN"
    vals = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        vals.append(solve(c, ply_left - 1, mover))
    if any(v == "UNKNOWN" for v in vals):
        return "UNKNOWN"
    if b.turn == mover:                 # mover to move: best for mover
        best = max(vals, key=lambda v: RANK[v])
        return best
    else:                               # opponent to move: worst for mover
        best = min(vals, key=lambda v: RANK[v])
        return best


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    return e


def make_positions(n):
    rng = random.Random(SEED)
    out = []
    while len(out) < n:
        b = chess.Board(None)
        sq = list(chess.SQUARES)
        wk, bk = rng.sample(sq, 2)
        if chess.square_distance(wk, bk) < 3:
            continue
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        rest = [s for s in sq if s not in (wk, bk)]
        weak_white = rng.random() < 0.5
        strong = chess.BLACK if weak_white else chess.WHITE
        kind = rng.choice(["minor", "rook_high", "queen_high"])
        if kind == "minor":
            piece, hm = rng.choice([chess.KNIGHT, chess.BISHOP]), rng.randrange(0, 20)
        elif kind == "rook_high":
            piece, hm = chess.ROOK, rng.randrange(90, 100)
        else:
            piece, hm = chess.QUEEN, rng.randrange(90, 100)
        b.set_piece_at(rng.choice(rest), chess.Piece(piece, strong))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        if b.is_check() or b.is_checkmate() or b.is_stalemate() or b.legal_moves.count() == 0:
            continue
        out.append((b.fen().rsplit(" ", 2)[0] + " %d %d" % (hm, 60), kind))
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    os.makedirs(outdir, exist_ok=True)
    e = eng(exe, os.path.join(outdir, "forced_raw.txt"))
    positions = make_positions(npos)
    R = {}
    hits, decided = [], 0
    for i, (fen, kind) in enumerate(positions):
        b = chess.Board(fen)
        mover = b.turn
        true = {}
        for m in list(b.legal_moves):
            c = b.copy(); c.push(m)
            true[m.uci()] = solve(c, SEARCH_PLIES - 1, mover)
        known = {k: v for k, v in true.items() if v != "UNKNOWN"}
        chosen = {}
        for name, go in (("depth16", "go depth 16"), ("nodes20k", "go nodes 20000")):
            e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
            e.position("position fen " + fen)
            chosen[name] = bestmove_of(e.go(go, timeout=200))
        best = max((RANK[v] for v in known.values()), default=None)
        hit_names = []
        if best is not None and known:
            decided += 1
            for k, bm in chosen.items():
                v = true.get(bm)
                if v in RANK and RANK[v] is not None and RANK[v] < best:
                    hit_names.append(k)
        R["%d" % i] = dict(fen=fen, kind=kind, true=true, known_n=len(known),
                           chosen=chosen,
                           best={0: "loss", 1: "draw", 2: "win"}.get(best, "?"),
                           hits=hit_names)
        if hit_names:
            hits.append(i)
        if (i + 1) % 10 == 0:
            print("scanned %d/%d decided %d hits %d" % (i + 1, len(positions), decided, len(hits)))
    e.close()
    rows = ["| pos | kind | FEN | best true | chosen d16 | chosen 20k | hit |",
            "|---|---|---|---|---|---|---|"]
    for i, (fen, kind) in enumerate(positions):
        r = R["%d" % i]
        rows.append("| %d | %s | `%s` | %s | %s | %s | %s |" % (
            i, kind, fen, r["best"], r["chosen"]["depth16"], r["chosen"]["nodes20k"],
            "YES" if r["hits"] else "no"))
    text = "\n".join(rows)
    text += "\n\npositions where the true result was DECIDED: %d of %d\n" % (decided, len(positions))
    text += "HITS: %d\n" % len(hits)
    for i in hits:
        r = R["%d" % i]
        text += "  hit %d (%s) `%s` chosen %s, best %s\n" % (i, r["kind"], r["fen"], r["chosen"], r["best"])
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-700:])


if __name__ == "__main__":
    main()