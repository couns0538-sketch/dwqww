import chess
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def mat(bd): return sum(V[p.piece_type]*(1 if p.color else -1) for p in bd.piece_map().values())  # black - white
print("turn:", "black" if b.turn==chess.BLACK else "white")
print("queen b6 attacked by white?", b.is_attacked_by(chess.WHITE, chess.B6),
      [chess.square_name(s) for s in b.attackers(chess.WHITE,chess.B6)])
print("knight a4 PINNED?", b.is_pinned(chess.WHITE, chess.A4))
# give white the move on the identical placement to test knight mobility
w=b.copy(stack=False); w.turn=chess.WHITE
print("a4b6 legal if it were White to move?", chess.Move.from_uci("a4b6") in w.legal_moves)
print("So the queen was ALREADY capturable on White's previous move.",
      "=> e6e5 did not create the threat; it failed to answer it." )
print()
print("material (black-white) at root:", mat(b))
for mv in ("e6e5","b6b4"):
    c=b.copy(); c.push_uci(mv)
    print(" after %s: material %+d, queen b6 attacked? %s" % (mv, mat(c), c.is_attacked_by(chess.WHITE,chess.B6) if c.piece_at(chess.B6) else "queen moved/absent"))
