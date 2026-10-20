// Rare target-only LVA exchange path. The ordinary threshold SEE is unchanged.
// Pawn promotions add material immediately and change the next victim's value.
int promotion_recapture_exchange(const Board& board, const Move& move, int captured_square) {
    const Color us = board.side_to_move();
    const int from = move.from;
    const int to = move.to;
    std::array<int, 64> gain{};
    gain[0] = SeeValue[static_cast<std::size_t>(piece_type(board.piece_at(captured_square)))];
    int victim = SeeValue[static_cast<std::size_t>(piece_type(board.piece_at(from)))];
    if (move.is_promotion()) {
        gain[0] += SeeValue[move.promotion] - SeeValue[Pawn];
        victim = SeeValue[move.promotion];
    }

    Bitboard occupancy = (board.occupied() ^ square_bb(from) ^ square_bb(captured_square)) | square_bb(to);
    Color stm = us;
    Bitboard attackers = board.attackers_to(to, occupancy);
    const Bitboard diagonals = board.pieces(Bishop) | board.pieces(Queen);
    const Bitboard lines = board.pieces(Rook) | board.pieces(Queen);
    std::size_t depth = 0;
    // Each accepted recapture consumes a distinct occupied origin; a king ends
    // the exchange. The bound also makes every gain write fit for any board.
    while (depth + 1 < gain.size()) {
        stm = opposite(stm);
        attackers &= occupancy;
        Bitboard stm_attackers = attackers & board.occupied(stm);
        const Bitboard king_attackers = stm_attackers & board.pieces(stm, King);
        if ((stm_attackers & ~king_attackers) != 0) {
            const Color enemy = opposite(stm);
            const int king = board.king_square(stm);
            const Bitboard live = occupancy & ~square_bb(to);
            const Bitboard queens = board.pieces(enemy, Queen) & live;
            bool checked =
                (attacks::pawn(stm, king) & board.pieces(enemy, Pawn) & live) != 0 ||
                (attacks::knight(king) & board.pieces(enemy, Knight) & live) != 0 ||
                (attacks::king(king) & board.pieces(enemy, King) & live) != 0;
            Bitboard pinners =
                (attacks::bishop(king, 0) & ((board.pieces(enemy, Bishop) & live) | queens)) |
                (attacks::rook(king, 0) & ((board.pieces(enemy, Rook) & live) | queens));
            Bitboard forbidden = 0;
            while (!checked && pinners != 0) {
                const int pinner = pop_lsb(pinners);
                const Bitboard blockers = attacks::between(king, pinner) & occupancy;
                if (blockers == 0) checked = true;
                else if (!more_than_one(blockers)) forbidden |= blockers;
            }
            stm_attackers = checked ? king_attackers : stm_attackers & ~forbidden;
        }
        if (stm_attackers == 0) break;

        Bitboard bb = 0;
        PieceType attacker_type = NoPieceType;
        if ((bb = stm_attackers & board.pieces(stm, Pawn)) != 0) {
            attacker_type = Pawn;
        } else if ((bb = stm_attackers & board.pieces(stm, Knight)) != 0) {
            attacker_type = Knight;
        } else if ((bb = stm_attackers & board.pieces(stm, Bishop)) != 0) {
            attacker_type = Bishop;
        } else if ((bb = stm_attackers & board.pieces(stm, Rook)) != 0) {
            attacker_type = Rook;
        } else if ((bb = stm_attackers & board.pieces(stm, Queen)) != 0) {
            attacker_type = Queen;
        } else {
            // Preserve source16's geometric king-defender test. A king capture
            // is terminal, and a defended target permits no king capture.
            if ((attackers & ~board.occupied(stm)) != 0) break;
            const std::size_t next = depth + 1;
            gain[next] = victim - gain[depth];
            depth = next;
            break;
        }

        const bool promotes = attacker_type == Pawn && rank_of(to) == (stm == White ? 7 : 0);
        const int promotion_gain = promotes ? SeeValue[Queen] - SeeValue[Pawn] : 0;
        const std::size_t next = depth + 1;
        gain[next] = victim + promotion_gain - gain[depth];
        depth = next;
        victim = promotes ? SeeValue[Queen] : SeeValue[static_cast<std::size_t>(attacker_type)];

        occupancy ^= square_bb(lsb(bb));
        if (attacker_type == Pawn || attacker_type == Bishop) {
            attackers |= attacks::bishop(to, occupancy) & diagonals;
        } else if (attacker_type == Rook) {
            attackers |= attacks::rook(to, occupancy) & lines;
        } else if (attacker_type == Queen) {
            attackers |= (attacks::bishop(to, occupancy) & diagonals) | (attacks::rook(to, occupancy) & lines);
        }
    }
    while (depth != 0) {
        gain[depth - 1] = std::min(gain[depth - 1], -gain[depth]);
        --depth;
    }
    return gain[0];
}

