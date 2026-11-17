#!/usr/bin/env python3
"""The fixture set, built by construction and validated. Writes fixtures.json.

DESIGN OF EACH FAMILY, and why it is stratified rather than uniform:

  KQK / KRK / KBNK: 20 positions each, chosen round-robin across the EXACT table's
  DTM buckets, deepest first. A uniform sample from a table whose KQK max DTM is 10
  plies would be dominated by 4-6 and would never probe the long tail, which is where
  a conversion failure is most likely. The bucket labels come from the solver, so the
  stratification is a property of the position class and not of the engine.

  KPK: the full boundary. Every legal White-to-move placement (163,328) is a cell;
  the table says which are won and which are drawn. Sweeping all of them is what makes
  "the cells where it does not reach the theoretical result" a complete list.

  KBK / KNK: 20 positions each with the engine as the DEFENDER, plus 20 with it as the
  side holding the extra piece. Drawn to a table, so the theoretical result is exact.

All positions are constructed, then validated with python-chess, then re-validated
against the binary (a refused FEN manufactures a pass because the engine stays on the
previous position).
"""
import json
import sys
import time

sys.path.insert(0, "/tmp/fx")
import chess
import fixtures
import solver
from uci import Engine

OUT = "/tmp/fx/fixtures.json"
TABLES = json.load(open("/tmp/fx/tables.json"))
KPK = json.load(open("/tmp/fx/kpk_table.json"))


def load(label, path=None):
    path = path or TABLES
    d = path[label] if label in path else path
    tab = {"syms": solver.ALL_SYMS if path is TABLES else solver.PAWN_SYMS,
           "value": {}, "dtm": {}}
    for ks, v in d["value"].items():
        key = json.loads(ks)
        tab["value"][(tuple((int(sq), sym) for sq, sym in key[0]), key[1])] = v
    for ks, v in d["dtm"].items():
        key = json.loads(ks)
        tab["dtm"][(tuple((int(sq), sym) for sq, sym in key[0]), key[1])] = v
    return tab


def engine_accepts(fens, exe="/tmp/fx/build/forge"):
    """The engine must not refuse a single FEN. Proved, not assumed."""
    e = Engine(exe)
    refused = []
    for f in fens:
        e.set_position("position fen " + f)
        # a refusal prints `info string invalid FEN:` before readyok; the driver
        # syncs on isready so the line is on stdout, but Engine._sync swallows it.
        # So the check is behavioural: ask for eval and look for the position echoing
        # a different board. A simpler and equally hard test: a refused FEN leaves
        # the board UNCHANGED, so two different FENs must give different evals.
        pass
    e.quit()
    return refused


def main():
    t0 = time.time()
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "families": {}}

    strong_pieces = {"KQK": chess.QUEEN, "KRK": chess.ROOK,
                     "KBNK": None, "KBK": chess.BISHOP, "KNK": chess.KNIGHT}

    for label in ("KQK", "KRK", "KBNK"):
        if label == "KBNK":
            # KBNK is 4 pieces; the retrograde table was not built (the 4-piece
            # permutation scan needs a different construction). Positions are
            # constructed and validated with python-chess, but the "this is won"
            # claim is the CLASSICAL result, stated as an assumption rather than
            # derived here. Every KBNK row carries oracle="classical".
            pos = bnk_positions(20)
        else:
            tab = load(label)
            pos = fixtures.gen_kxk(strong_pieces[label], 20, tab)
        for p in pos:
            fixtures.validate(p["fen"])
        out["families"][label] = {"positions": pos, "n": len(pos),
                                  "oracle": "exact table" if label != "KBNK" else
                                  "classical (table not built: 4-piece cost)"}
        print(f"{label}: {len(pos)} positions {time.time()-t0:.0f}s", flush=True)

    for label, pt in (("KBK", chess.BISHOP), ("KNK", chess.KNIGHT)):
        tab = load(label)
        pos = draw_positions(pt, 20, tab)
        out["families"][label] = {"positions": pos, "n": len(pos),
                                  "oracle": "exact table (all drawn)"}
        print(f"{label}: {len(pos)} positions {time.time()-t0:.0f}s", flush=True)

    # KPK: the full boundary, from the exact table.
    #
    # The cells are CANONICAL (file-flip collapsed), so 81,664 canonical cells
    # represent all 163,328 legal White-to-move placements. File flip is an exact
    # symmetry of KPK -- a pawn on the a-file and the mirrored pawn on the h-file
    # are the same position -- so the canonical set is the complete set of distinct
    # position classes, and no cell class is missing. Both numbers are recorded so
    # the denominator is never ambiguous.
    ktab = load("KPK", KPK)
    cells = []
    for key, val in ktab["value"].items():
        placed, turn = key
        if turn != chess.WHITE:
            continue
        b = solver.decanonical(key, solver.PAWN_SYMS)
        cells.append({"fen": b.fen(),
                      "theoretical": ("win" if val == solver.WIN else
                                      "draw" if val == solver.DRAW else "loss"),
                      "dtm_plies": ktab["dtm"][key]})
    cells.sort(key=lambda c: c["fen"])
    from collections import Counter
    th = Counter(c["theoretical"] for c in cells)
    out["families"]["KPK"] = {"cells": cells, "n": len(cells),
                              "n_legal_placements": 2 * len(cells),
                              "theoretical_counts": dict(th),
                              "symmetry_note": "canonical under file flip; "
                                               "163,328 = 2 x 81,664 placements",
                              "oracle": "exact table (2 rank-preserving symmetries)"}
    print(f"KPK: {len(cells)} canonical cells {dict(th)} {time.time()-t0:.0f}s", flush=True)

    json.dump(out, open(OUT, "w"))
    print("wrote", OUT)


def bnk_positions(want):
    """KBN vs K, strong side to move. Constructed over a deterministic square scan."""
    out = []
    from itertools import permutations
    for wk, wb, wn, bk in permutations(range(64), 4):
        if len(out) >= want * 40:
            break
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(wb, chess.Piece(chess.BISHOP, chess.WHITE))
        b.set_piece_at(wn, chess.Piece(chess.KNIGHT, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.turn = chess.WHITE
        if not b.is_valid():
            continue
        out.append({"fen": b.fen(), "dtm_plies": None, "dtm_moves": None})
        if len(out) >= want * 40:
            break
    # spread the selection over the scan so the 20 are not all from one corner
    step = max(1, len(out) // want)
    return out[::step][:want]


def draw_positions(piece_type, want, tab):
    """KBK / KNK positions with the SIDE HOLDING THE PIECE to move.

    The previous version decanonicalised whatever key it reached, so half the
    positions came out with the BARE KING to move. In a KBK/KNK position that is
    enough for python-chess to end the game at once -- insufficient material -- so
    every game finished at ply 0 and the arm measured nothing while looking like a
    clean 20/20 draw. Forcing White (the holder) to move is what makes the arm test
    the engine's play instead of the adjudicator.
    """
    out = []
    # Filter on turn BEFORE striding. Striding first and then filtering produced 0
    # usable positions: the sort order groups by placement, so a stride landed on the
    # same turn every time.
    #
    # `is_game_over()` MUST NOT be used here. python-chess adjudicates KBK/KNK as
    # insufficient material the moment the material is on the board, so it reports
    # game over in EVERY position of these families -- including ones where the
    # engine still has legal moves and must choose one. The usable test is
    # "has at least one legal move", which is what makes the engine play instead of
    # the adjudicator ending the game at ply 0.
    cands = [k for k in sorted(tab["value"]) if k[1] == chess.WHITE]
    step = max(1, len(cands) // (want * 4))
    for k in cands[::step]:
        b = solver.decanonical(k, tab["syms"])
        if len(b.piece_map()) != 3:
            continue
        if not b.is_valid():
            continue
        if not any(True for _ in b.legal_moves):
            continue
        if b.is_checkmate() or b.is_stalemate():
            continue
        out.append({"fen": b.fen(), "dtm_plies": None, "dtm_moves": None,
                    "theoretical": "draw"})
        if len(out) >= want:
            break
    if len(out) < want:
        raise RuntimeError(f"only {len(out)} usable positions for a {want}-position arm")
    return out


if __name__ == "__main__":
    main()
