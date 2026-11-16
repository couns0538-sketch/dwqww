#!/usr/bin/env python3
"""exactscan.py EXE OUTDIR [NPOS]

The exact version of the position-155 measurement, in the only region where an exact solver is
cheap: a bare king against a lone ROOK or QUEEN with the halfmove counter at 95-99.

Why this region makes the answer EXACT. The fifty-move draw falls at counter 100, so with the
counter at c the strong side has exactly (100 - c) half-moves — 1 to 5 — to mate. A minimax
limited to those plies is therefore not an approximation: a move that fails to mate inside the
window IS a draw, and a move that mates is a win. No deeper search can change either verdict.

So for each root: every legal move's TRUE result (win for the strong side, or draw) is decided
exactly; the engine's `go depth 16` and `go nodes 20000` answers are then compared against the best
true result. A HIT = the chosen move draws where another move wins, or vice versa.

Both colours are used as the strong side, and both are tested (the coordinator asked for the colour
case to be covered).
"""
import json
import os
import random
import sys
from functools import lru_cache

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


def strong_can_force_mate(board, strong, plies):
    """Exact: can `strong` force mate within `plies` half-moves? Memoised minimax.

    Returns True/False. `plies` is small (1..5 here) so this is fast and exact.
    """
    cache = {}

    def rec(b, left):
        key = (b.fen(), left)
        if key in cache:
            return cache[key]
        if b.is_checkmate():
            v = (b.turn != strong)          # strong wins iff the side to move is mated
            cache[key] = v
            return v
        if b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100:
            cache[key] = False              # a draw is not a win
            return False
        if left <= 0:
            cache[key] = False
            return False
        moves = list(b.legal_moves)
        if not moves:
            cache[key] = False
            return False
        if b.turn == strong:
            v = any(rec(_push(b, m), left - 1) for m in moves)
        else:
            v = all(rec(_push(b, m), left - 1) for m in moves)
        cache[key] = v
        return v

    return rec(board, plies)


def _push(b, m):
    c = b.copy()
    c.push(m)
    return c


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    return e


def make_positions(n, seed=SEED):
    """Bare king vs a lone R/Q, counter 95-99, positions where the window is genuinely 1-5."""
    rng = random.Random(seed)
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
        piece = rng.choice([chess.ROOK, chess.ROOK, chess.QUEEN])
        b.set_piece_at(rng.choice(rest), chess.Piece(piece, strong))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        hm = rng.randrange(95, 100)
        if b.is_check() or b.is_checkmate() or b.is_stalemate() or b.legal_moves.count() == 0:
            continue
        if b.is_insufficient_material():
            continue
        fen = b.fen().rsplit(" ", 2)[0] + " %d %d" % (hm, 60)
        out.append((fen, "white_strong" if strong == chess.WHITE else "black_strong"))
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    os.makedirs(outdir, exist_ok=True)
    e = eng(exe, os.path.join(outdir, "exact_raw.txt"))
    positions = make_positions(npos)
    R = {}
    hits = []
    for i, (fen, kind) in enumerate(positions):
        b = chess.Board(fen)
        strong = chess.WHITE if kind == "white_strong" else chess.BLACK
        window = 100 - b.halfmove_clock          # 1..5 half-moves to the draw
        true = {}
        for m in list(b.legal_moves):
            c = _push(b, m)
            true[m.uci()] = "win" if strong_can_force_mate(c, strong, window - 1) else "draw"
        # `true[m]` is "does the STRONG side force mate after move m". From the point of view of the
        # side to move, "win" is BAD (it loses) and "draw" is GOOD. A hit is therefore: there exists
        # a move where the mover DRAWS, and the engine picked one where it LOSES.
        mover_draws_available = any(v == "draw" for v in true.values())
        chosen = {}
        for name, go in (("depth16", "go depth 16"), ("nodes20k", "go nodes 20000")):
            e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
            e.position("position fen " + fen)
            chosen[name] = bestmove_of(e.go(go, timeout=200))
        # the engine plays for the STRONG side; a hit is choosing a draw when a win exists
        hit_names = []
        if mover_draws_available:
            for k, bm in chosen.items():
                if true.get(bm) == "win":
                    hit_names.append(k)   # engine walked into a forced mate it could have avoided
        R["%d" % i] = dict(fen=fen, kind=kind, window=window, true=true,
                           mover_draws=mover_draws_available, chosen=chosen, hits=hit_names)
        if hit_names:
            hits.append(i)
        if (i + 1) % 10 == 0:
            print("scanned %d/%d winnable %d hits %d" % (
                i + 1, len(positions), sum(1 for r in R.values() if r["mover_draws"]), len(hits)))
    e.close()
    rows = ["| pos | strong side | window (half-moves to the draw) | mover can save the draw | chosen d16 | chosen 20k | hit |",
            "|---|---|---|---|---|---|---|"]
    for i, (fen, kind) in enumerate(positions):
        r = R["%d" % i]
        rows.append("| %d | %s | %d | %s | %s | %s | %s |" % (
            i, kind, r["window"], r["mover_draws"], r["chosen"]["depth16"],
            r["chosen"]["nodes20k"], "YES" if r["hits"] else "no"))
    n_win = sum(1 for r in R.values() if r["mover_draws"])
    text = "\n".join(rows)
    text += ("\n\npositions: %d\nwhere the side to move could SAVE the draw: %d\n"
             "HITS (engine walked into a mate it could have avoided): %d\n"
             % (len(positions), n_win, len(hits)))
    for i in hits:
        r = R["%d" % i]
        text += "  hit %d (%s) `%s` window %d chosen %s\n" % (
            i, r["kind"], r["fen"], r["window"], r["chosen"])
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-700:])


if __name__ == "__main__":
    main()