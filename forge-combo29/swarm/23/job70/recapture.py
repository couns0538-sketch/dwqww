import chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN); b.push_uci("e6e5")
victim=b.piece_at(chess.B6); print("piece White takes on b6:",victim.symbol(),"value",V[victim.piece_type])
b.push_uci("a4b6")
print("\nBlack's candidate recaptures and WHAT THEY CAPTURE:")
for m in [x for x in b.legal_moves if b.is_capture(x)]:
    cap=b.piece_at(m.to_square)
    print("   %s captures %s on %s (value %d)"%(m.uci(),cap.symbol(),chess.square_name(m.to_square),V[cap.piece_type]))
best=None
for m in [x for x in b.legal_moves if x.uci()=="e5d4"]:
    cap=b.piece_at(m.to_square); best=V[cap.piece_type]
print("\nF129's arithmetic: 9 (queen) - 3 (a knight recapture) = +6")
print("Actual recapture e5d4 takes a %s, value %d -> 9 - %d = +%d"%(b.piece_at(chess.D4).symbol(),best,best,9-best))
print("\nF129 subtracted the value of a KNIGHT for a recapture that captures a PAWN.")
