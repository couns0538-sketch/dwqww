    const int target_rank = rank_of(to);
    if ((target_rank == 0 || target_rank == 7) &&
        piece_type(squares_[static_cast<std::size_t>(from)]) != King) {
        const Color promoter = target_rank == 7 ? White : Black;
        const Bitboard promoting_pawns =
            pieces(promoter, Pawn) & attacks::pawn(opposite(promoter), to) &
            ~(square_bb(from) | square_bb(captured_square));
        if (promoting_pawns != 0) {
            return promotion_recapture_exchange(*this, move, captured_square) >= threshold;
        }
    }
