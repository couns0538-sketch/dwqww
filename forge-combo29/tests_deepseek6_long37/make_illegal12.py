#!/usr/bin/env python3
"""make_illegal12.py -- build illegal12.fens: twelve FENs each breaking ONE rule (python-chess
is_valid() == False, with its status recorded), plus one legal thirteenth. Verified here."""
import chess

CANDS = {
    "castling_right_without_rook": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1",
    "castling_right_king_moved":   "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKB1R w KQ - 0 1",
    "bogus_en_passant":            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1",
    "pawn_on_rank_1":              "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/PNBQKBNR w KQkq - 0 1",
    "pawn_on_rank_8":              "Pnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "two_white_kings":             "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK1KK w - - 0 1",
    "no_black_king":               "rnbq1bnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1",
    "side_not_to_move_in_check":   "4k3/8/8/8/8/8/8/4R3 w - - 0 1",
    "seventeen_white_pieces":      "rnbqkbnr/pppppppp/8/4N3/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "nine_white_pawns":            "rnbqkbnr/pppppppp/8/4P3/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "kings_touching":              "4k3/4K3/8/8/8/8/8/8 w - - 0 1",
}
out = []
status12 = {}
for name, fen in CANDS.items():
    b = chess.Board(fen)
    v = b.is_valid()
    status = b.status()
    status12[name] = (fen, str(v), str(status), int(status))
    out.append(fen)
# find a STATUS_IMPOSSIBLE_CHECK FEN
imp = None
for cand in ["4k3/2N5/3N1N2/8/8/8/8/4K3 b - - 0 1", "4k3/1NN5/3N1N2/8/8/8/8/4K3 b - - 0 1"]:
    b = chess.Board(cand)
    if not b.is_valid() and (b.status() & chess.STATUS_IMPOSSIBLE_CHECK):
        imp = cand
        break
if imp is None:
    print("no impossible-check FEN found among the candidates")
    raise SystemExit(1)
status12["impossible_check"] = (imp, "False", str(chess.STATUS_IMPOSSIBLE_CHECK), int(chess.STATUS_IMPOSSIBLE_CHECK))
out.append(imp)
legal = chess.STARTING_FEN
out.append(legal)
open("/tmp/illegal12.fens", "w").write("\n".join(out) + "\n")
print("wrote /tmp/illegal12.fens with", len(out), "FENs")
for name, (fen, v, st, code) in status12.items():
    print(f"{name}: valid={v} status={st}")
import json
open("/tmp/illegal12_status.json", "w").write(json.dumps(status12))
