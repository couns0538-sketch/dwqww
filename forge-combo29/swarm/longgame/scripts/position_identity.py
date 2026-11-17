#!/usr/bin/env python3
"""POSITION IDENTITY: does the engine's own board after N moves equal the same position
loaded as a FEN?

This is a different question from determinism. Determinism asks "does the same command give
the same answer twice". Identity asks "is the board the engine built from a move list the
same board as the FEN for that position" -- the failure mode that would make every replay
silently analyse a position that is not the game's.

Method. For each ply of each game, build the board twice in the SAME engine:
  A. `position fen <game start> moves <prefix>`   (the replay form)
  B. `position fen <full FEN of that position>`   (the FEN form)
then send `go perft 3` on each and compare the COMPLETE move-by-move breakdown, not just the
total. Perft exercises piece placement, side to move, castling rights and en-passant, so a
byte-identical breakdown is a strong fingerprint of all four.

The FEN in B is built by hand, not by python-chess's `Board.fen()`, because that method
silently drops the ep square when no legal ep capture exists (brief rule 5). `force_ep_fen`
writes the ep square whenever the move list produced one.

What perft CANNOT see: the halfmove clock. It is covered separately by `halfmove_probe`,
which plants positions either side of the clock-100 boundary and checks the bail, because
that is the only place the clock changes the engine's answer.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
import chess

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")


def force_ep_fen(b):
    """Full FEN with the ep square kept whenever the move list set one."""
    ep = chess.square_name(b.ep_square) if b.ep_square is not None else "-"
    castling = b.castling_xfen() or "-"
    return f"{b.board_fen()} {b.turn and 'w' or 'b'} {castling} {ep} {b.halfmove_clock} {b.fullmove_number}"


def perft(eng, pos, depth=3):
    eng.send(pos)
    eng.send(f"go perft {depth}")
    lines = eng.read_until(lambda l: l.startswith("nodes ") and not l.startswith("info"))
    return tuple(lines)


def main():
    corpus = {g["id"]: g for g in json.load(open("evidence/games.json", encoding="utf-8"))["games"]}
    ids = json.load(open("evidence/divergence_sample.json", encoding="utf-8"))["games"]
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    eng = Engine(ENG)
    eng.uci(); eng.sync()
    rows, n, same, first_bad = [], 0, 0, None
    for gid in ids:
        g = corpus[gid]
        board = chess.Board(g["start_fen"])
        pre = []
        for k, mv in enumerate(g["moves"], 1):
            board.push(chess.Move.from_uci(mv))
            pre.append(mv)
            a = perft(eng, f"position fen {g['start_fen']} moves " + " ".join(pre), depth)
            b = perft(eng, f"position fen {force_ep_fen(board)}", depth)
            n += 1
            ok = a == b
            same += ok
            if not ok and first_bad is None:
                first_bad = {"game": gid, "ply": k, "fens": force_ep_fen(board),
                             "movelist_nodes": a[-1] if a else None,
                             "fen_nodes": b[-1] if b else None}
            rows.append({"game": gid, "ply": k, "identical": ok,
                         "nodes": a[-1] if a else None})
        if n % 1000 < len(g["moves"]):
            print(f"  ... {n} plies", flush=True)
    eng.quit()

    json.dump({"depth": depth, "plies": n, "identical": same, "first_mismatch": first_bad,
               "rows": rows}, open("evidence/position_identity.json", "w", encoding="utf-8"), indent=0)
    print(f"\nperft depth {depth}: {same}/{n} plies where the move-list board and the FEN "
          f"board produce a byte-identical perft breakdown")
    if first_bad:
        print("  FIRST MISMATCH:", first_bad)
    else:
        print("  no mismatch: position identity holds at every ply measured")


if __name__ == "__main__":
    main()
