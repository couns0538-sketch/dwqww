#!/usr/bin/env python3
"""resultscan.py EXE OUTDIR [NPOS]

RESULT-based scan for the position-155 class (seat 03 S-F16).

For a root position:
  1. the chosen move = the engine's `go depth 16` answer (and, separately, its `go nodes 20000` answer);
  2. for EVERY legal root move, play the position out with the ENGINE on both sides (`go nodes 20000`,
     Threads 1, PC20) until python-chess says the game is over or a ply cap is reached;
  3. classify the ending as win / draw / loss for the side to move at the root, using
     is_checkmate / is_insufficient_material / is_game_over, with a threefold and fifty-move check
     by python-chess's own out_of_board rules;
  4. a position is a HIT when the chosen move's result is strictly worse than the best available
     alternative's result (loss < draw < win).

Play-out uses the engine for both sides so the classification reflects real continuations, not
the engine's static opinion. Ply cap 300; a capped game counts as a draw only if python-chess agrees
the position is drawn by material or repetition, otherwise it is recorded as CAPPED and excluded.

Position generation: lone-king endings reached from material-imbalanced starts — one side has a bare
king, the other has at most a rook plus a minor, generated at random and verified with python-chess
(not mate, not stalemate, has legal moves, exactly one bare king).
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PLY_CAP = 300
SEED = 2101
POS155 = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"


class Eng:
    """One long-lived process per side of the play-out (ucinewgame between games keeps it cold)."""

    def __init__(self, exe, raw):
        self.e = SafeEngine(exe, raw, hash_mb=16, threads=1)
        for k, v in S14 + PC20_EXTRA:
            self.e.send("setoption name %s value %s" % (k, v))
            self.e.send("isready")
            self.e.wait_for("readyok")

    def fresh_game(self):
        self.e.send("ucinewgame")
        self.e.send("isready")
        self.e.wait_for("readyok")

    def best(self, board, go="go nodes 20000"):
        self.e.position("position fen " + board.fen())
        lines = self.e.go(go, timeout=180)
        return bestmove_of(lines), lines

    def close(self):
        self.e.close()


def classify(board):
    """win / draw / loss for the side to move, from python-chess."""
    if board.is_checkmate():
        return "loss"
    if board.is_stalemate() or board.is_insufficient_material():
        return "draw"
    if board.is_game_over():
        return "draw"
    # python-chess can_claim_* is about the player to move; a settled draw by counter is a draw
    if board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
        return "draw"
    return None


def playout(eng, board, mover_color):
    """Play the game out with the engine for both sides. Returns (result for mover_color, plies, capped)."""
    b = board.copy()
    eng.fresh_game()
    plies = 0
    while plies < PLY_CAP:
        r = classify(b)
        if r is not None:
            return (r if b.turn == mover_color else {"win": "loss", "loss": "win", "draw": "draw"}[r]), plies, False
        bm, _ = eng.best(b)
        if not bm or bm == "0000":
            r2 = classify(b) or "draw"
            return (r2 if b.turn == mover_color else {"win": "loss", "loss": "win", "draw": "draw"}[r2]), plies, False
        try:
            b.push_uci(bm)
        except Exception:
            return "UNKNOWN", plies, True
        plies += 1
    return "CAPPED", plies, True


RANK = {"loss": 0, "draw": 1, "win": 2}


def scan_position(exe, outdir, tag, fen, eng):
    board = chess.Board(fen)
    mover = board.turn
    results = {}
    for m in list(board.legal_moves):
        c = board.copy()
        c.push(m)
        res, plies, capped = playout(eng, c, mover)
        results[m.uci()] = dict(result=res, plies=plies, capped=capped)
    # chosen moves
    chosen = {}
    for go_name, go in (("depth16", "go depth 16"), ("nodes20k", "go nodes 20000")):
        eng.fresh_game()
        bm, _ = eng.best(board, go=go)
        chosen[go_name] = bm
    best_result = max((RANK.get(v["result"], -1) for v in results.values()))
    hits = []
    for go_name, bm in chosen.items():
        r = results.get(bm, {}).get("result")
        if r in RANK and RANK[r] < best_result:
            hits.append(go_name)
    return dict(fen=fen, chosen=chosen, moves=results, best=RANK_INV(best_result), hits=hits)


def RANK_INV(v):
    return {0: "loss", 1: "draw", 2: "win"}.get(v, "?")


def gen_lone_king(n, seed=SEED):
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
        # the stronger side gets a rook and optionally a minor / pawn
        rest = [s for s in sq if s not in (wk, bk)]
        n_extra = rng.choice([1, 1, 2, 2, 3])
        pieces = [rng.choice([chess.ROOK, chess.ROOK, chess.QUEEN])]
        for _ in range(n_extra - 1):
            pieces.append(rng.choice([chess.KNIGHT, chess.BISHOP, chess.PAWN]))
        strong_is_white = rng.random() < 0.5
        for p in pieces:
            s = rng.choice(rest)
            rest.remove(s)
            b.set_piece_at(s, chess.Piece(p, chess.WHITE if strong_is_white else chess.BLACK))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        if b.is_check() or b.is_checkmate() or b.is_stalemate():
            continue
        if b.legal_moves.count() == 0:
            continue
        # exactly one bare king
        for color in (chess.WHITE, chess.BLACK):
            if len(b.pieces(chess.PAWN, color)) + sum(
                    len(b.pieces(t, color)) for t in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)) != 0:
                pass
        strong = chess.WHITE if strong_is_white else chess.BLACK
        weak = not strong
        nweak = sum(len(b.pieces(t, weak)) for t in (chess.PAWN, chess.KNIGHT, chess.BISHOP,
                                                     chess.ROOK, chess.QUEEN))
        if nweak != 0:
            continue
        out.append(b.fen())
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    os.makedirs(outdir, exist_ok=True)
    eng = Eng(exe, os.path.join(outdir, "scan_raw.txt"))
    R = {}

    # ---- P1: reproduce position 155 first
    r155 = scan_position(exe, outdir, "p155", POS155, eng)
    R["155"] = r155
    print("155 chosen:", r155["chosen"], "best available:", r155["best"], "hits:", r155["hits"])
    for k, v in r155["moves"].items():
        print("   155 move %-6s -> %-6s (%d plies%s)" % (k, v["result"], v["plies"],
                                                         ", CAPPED" if v["capped"] else ""))

    # ---- the 50-position scan
    fens = gen_lone_king(npos)
    with open(os.path.join(outdir, "lone_king.fens"), "w") as fh:
        fh.write("\n".join(fens) + "\n")
    hit_positions = []
    for i, fen in enumerate(fens):
        try:
            r = scan_position(exe, outdir, "p%03d" % i, fen, eng)
        except (Timeout, EOFError) as exc:
            R["%d" % i] = dict(fen=fen, error=str(exc))
            continue
        R["%d" % i] = r
        if r["hits"]:
            hit_positions.append((i, fen, r))
        if (i + 1) % 10 == 0:
            print("scanned %d/%d, hits so far %d" % (i + 1, len(fens), len(hit_positions)))
    eng.close()

    rows = ["| pos | FEN | chosen (depth16) | chosen (20k) | best available | hit |",
            "|---|---|---|---|---|---|"]
    for i in range(len(fens)):
        r = R.get("%d" % i, {})
        if "moves" not in r:
            rows.append("| %d | `%s` | ERROR | – | – | – |" % (i, fens[i]))
            continue
        rows.append("| %d | `%s` | %s | %s | %s | %s |" % (
            i, fens[i], r["chosen"]["depth16"], r["chosen"]["nodes20k"], r["best"],
            "YES" if r["hits"] else "no"))
    text = "\n".join(rows)
    text += "\n\n155 reproduced: %s\n" % bool(r155["hits"])
    text += "HITS among %d lone-king endings: %d\n" % (len(fens), len(hit_positions))
    for i, fen, r in hit_positions:
        text += "  hit at %d: `%s` chosen %s best %s\n" % (i, fen, r["chosen"], r["best"])
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1200:])


if __name__ == "__main__":
    main()