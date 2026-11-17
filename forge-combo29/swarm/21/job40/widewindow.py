#!/usr/bin/env python3
"""widewindow.py EXE OUTDIR [NPOS]

The exact drawn-root scan pushed to a WIDER counter window: counters 85-94, where the fifty-move
draw is 6-15 half-moves away.

A plain minimax explodes at 15 plies, so the solver is:
  - window-bounded: only (100 - counter) plies are ever searched, because a mate that does not land
    inside the window IS a draw;
  - alpha-beta with a transposition table keyed by (fen, plies_left);
  - node-capped: a position that hits the cap is UNDECIDED and is never counted as a hit.

Result per root move: "win" (the strong side forces mate inside the window), "draw" (it does not),
or "UNDECIDED". For the side to move, "win" means it LOSES. A HIT = there is a move where the side
to move saves the draw, and the engine chose one where it loses.
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
NODE_CAP = 40000


class Solver:
    def __init__(self, cap=NODE_CAP):
        self.cap = cap
        self.nodes = 0
        self.tt = {}
        self.capped = False

    def reset(self):
        self.nodes = 0
        self.capped = False
        self.tt = {}

    def forces_mate(self, b, strong, left):
        """True if `strong` forces mate within `left` half-moves. Sets self.capped on a cut-off."""
        if self.capped:
            return False
        self.nodes += 1
        if self.nodes > self.cap:
            self.capped = True
            return False
        key = (b.board_fen(), b.turn, b.halfmove_clock, left)
        if key in self.tt:
            return self.tt[key]
        if b.is_checkmate():
            v = b.turn != strong
            self.tt[key] = v
            return v
        if b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100:
            self.tt[key] = False
            return False
        if left <= 0:
            self.tt[key] = False
            return False
        moves = list(b.legal_moves)
        if not moves:
            self.tt[key] = False
            return False
        if b.turn == strong:
            for m in moves:
                c = b.copy(); c.push(m)
                if self.forces_mate(c, strong, left - 1):
                    self.tt[key] = True
                    return True
                if self.capped:
                    return False
            self.tt[key] = False
            return False
        else:
            for m in moves:
                c = b.copy(); c.push(m)
                if not self.forces_mate(c, strong, left - 1):
                    self.tt[key] = False
                    return False
                if self.capped:
                    return False
            self.tt[key] = True
            return True


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    return e


def make_positions(n, seed=SEED):
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
        hm = rng.randrange(85, 95)
        if b.is_check() or b.is_checkmate() or b.is_stalemate() or b.legal_moves.count() == 0:
            continue
        if b.is_insufficient_material():
            continue
        out.append((b.fen().rsplit(" ", 2)[0] + " %d %d" % (hm, 60),
                    "white_strong" if strong == chess.WHITE else "black_strong"))
    return out


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    os.makedirs(outdir, exist_ok=True)
    e = eng(exe, os.path.join(outdir, "wide_raw.txt"))
    positions = make_positions(npos)
    solver = Solver()
    R = {}
    hits, decided_pos, undecided_pos = [], 0, 0
    total_pairs = total_decided = 0
    for i, (fen, kind) in enumerate(positions):
        b = chess.Board(fen)
        strong = chess.WHITE if kind == "white_strong" else chess.BLACK
        window = 100 - b.halfmove_clock
        true = {}
        for m in list(b.legal_moves):
            c = b.copy(); c.push(m)
            solver.reset()
            won = solver.forces_mate(c, strong, window - 1)
            total_pairs += 1
            if solver.capped:
                true[m.uci()] = "UNDECIDED"
            else:
                true[m.uci()] = "win" if won else "draw"
                total_decided += 1
        decided = {k: v for k, v in true.items() if v != "UNDECIDED"}
        chosen = {}
        for name, go in (("depth16", "go depth 16"), ("nodes20k", "go nodes 20000")):
            e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
            e.position("position fen " + fen)
            chosen[name] = bestmove_of(e.go(go, timeout=200))
        can_save = any(v == "draw" for v in decided.values())
        hit_names = []
        if can_save:
            decided_pos += 1
            for k, bm in chosen.items():
                if decided.get(bm) == "win":
                    hit_names.append(k)
        else:
            undecided_pos += 1
        R["%d" % i] = dict(fen=fen, kind=kind, window=window, true=true,
                           can_save=can_save, chosen=chosen, hits=hit_names,
                           decided_moves=len(decided), total_moves=len(true))
        if hit_names:
            hits.append(i)
        if (i + 1) % 10 == 0:
            print("%d/%d decided_pairs %d/%d hits %d" % (
                i + 1, len(positions), total_decided, total_pairs, len(hits)))
    e.close()
    rows = ["| pos | strong side | window | moves decided | mover can save draw | chosen d16 | chosen 20k | hit |",
            "|---|---|---|---|---|---|---|---|"]
    for i, (fen, kind) in enumerate(positions):
        r = R["%d" % i]
        rows.append("| %d | %s | %d | %d/%d | %s | %s | %s | %s |" % (
            i, kind, r["window"], r["decided_moves"], r["total_moves"], r["can_save"],
            r["chosen"]["depth16"], r["chosen"]["nodes20k"], "YES" if r["hits"] else "no"))
    text = "\n".join(rows)
    frac = 100.0 * total_decided / total_pairs if total_pairs else 0
    text += ("\n\npositions: %d\nmove-pairs decided: %d of %d (%.1f %%)\n"
             "positions where the mover could save the draw: %d\n"
             "HITS: %d\n" % (len(positions), total_decided, total_pairs, frac, decided_pos, len(hits)))
    for i in hits:
        r = R["%d" % i]
        text += "  hit %d (%s) `%s` window %d chosen %s\n" % (
            i, r["kind"], r["fen"], r["window"], r["chosen"])
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-900:])


if __name__ == "__main__":
    main()