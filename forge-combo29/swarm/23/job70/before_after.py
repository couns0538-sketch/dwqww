import chess
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
print("QUEEN on b6 attacked before e6e5?", b.is_attacked_by(chess.WHITE, chess.B6))
print("white attackers of b6:", [chess.square_name(s) for s in b.attackers(chess.WHITE,chess.B6)])
print("a4b6 legal BEFORE e6e5?", chess.Move.from_uci("a4b6") in b.legal_moves)
b2=b.copy(); b2.push_uci("e6e5")
print("a4b6 legal AFTER e6e5?", chess.Move.from_uci("a4b6") in b2.legal_moves)
print()
# Material if white just takes the queen NOW (before black moves) - i.e. was the queen already lost?
b3=b.copy(); b3.push_uci("a4b6")
print("if white played a4b6 immediately (before any black move): material black-white =",
      sum({1:1,2:3,3:3,4:5,5:9}.get(p.piece_type,0)*(1 if p.color else -1) for p in b3.piece_map().values()))
