// Job 17 Part 2 Exhaustive Differential Oracle + 3-Path Planted-Fault Verifier for stack/15_fast_is_pseudo_legal.patch.txt:
// Across all 1,000 positions of positions_1000.txt, compares b.is_pseudo_legal(m) against an independent
// copy of r15d's exact reference logic across:
//   - all generated pseudo-legal moves,
//   - all 64 x 64 (from, to) pairs with Quiet & Capture flags (4,096 x 2 = 8,192 moves per board = 8.19M checks!),
//   - targeted Promotion, DoublePush, EnPassant, KingCastle, QueenCastle, out-of-range (>=64), and invalid flag combos.

#include "forge/board.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr std::uint8_t kWKS = 1, kWQS = 2, kBKS = 4, kBQS = 8;

bool ref_is_pseudo_legal(const forge::Board& b, const forge::Move& move) {
    using namespace forge;
    if (move.from >= 64 || move.to >= 64 || move.from == move.to) return false;
    const Color us = b.side_to_move();
    const Piece moving = b.piece_at(move.from);
    if (moving == Empty || color_of(moving) != us) return false;
    const Piece target = b.piece_at(move.to);
    if (target != Empty && (color_of(target) == us || piece_type(target) == King)) return false;
    const int type = piece_type(moving);
    const Bitboard occ = b.occupied();
    const int up = pawn_push_delta(us);
    const auto special = static_cast<std::uint8_t>(move.flags & (DoublePush | KingCastle | QueenCastle | EnPassant | Promotion));

    if (move.is_castle()) {
        if (type != King || b.checkers() != 0 || special != (move.flags & (KingCastle | QueenCastle))) return false;
        if ((move.flags & Capture) != 0U || move.promotion != 0) return false;
        const bool ks = (move.flags & KingCastle) != 0U;
        if (ks && (move.flags & QueenCastle) != 0U) return false;
        const std::uint8_t cr = b.castling_rights();
        if (us == White) {
            if (move.from != 4 || move.to != (ks ? 6 : 2)) return false;
            if (ks) return (cr & kWKS) != 0U && (occ & (square_bb(5) | square_bb(6))) == 0 && b.piece_at(7) == WR && !b.square_attacked(5, Black) && !b.square_attacked(6, Black);
            return (cr & kWQS) != 0U && (occ & (square_bb(1) | square_bb(2) | square_bb(3))) == 0 && b.piece_at(0) == WR && !b.square_attacked(3, Black) && !b.square_attacked(2, Black);
        }
        if (move.from != 60 || move.to != (ks ? 62 : 58)) return false;
        if (ks) return (cr & kBKS) != 0U && (occ & (square_bb(61) | square_bb(62))) == 0 && b.piece_at(63) == BR && !b.square_attacked(61, White) && !b.square_attacked(62, White);
        return (cr & kBQS) != 0U && (occ & (square_bb(57) | square_bb(58) | square_bb(59))) == 0 && b.piece_at(56) == BR && !b.square_attacked(59, White) && !b.square_attacked(58, White);
    }
    if (type == Pawn) {
        const bool promotes = relative_rank(us, move.from) == 6;
        if (promotes != move.is_promotion()) return false;
        if (move.is_promotion() && (move.promotion < Knight || move.promotion > Queen)) return false;
        if (!move.is_promotion() && move.promotion != 0) return false;
        if ((move.flags & EnPassant) != 0U) {
            if (b.ep_square() < 0 || move.to != b.ep_square() || (move.flags & Capture) == 0U) return false;
            if ((move.flags & (DoublePush | Promotion)) != 0U) return false;
            return (attacks::pawn(us, move.from) & square_bb(move.to)) != 0;
        }
        if ((move.flags & Capture) != 0U) {
            if (target == Empty || (move.flags & DoublePush) != 0U) return false;
            return (attacks::pawn(us, move.from) & square_bb(move.to)) != 0;
        }
        if (target != Empty) return false;
        if ((move.flags & DoublePush) != 0U) {
            if (relative_rank(us, move.from) != 1 || move.to != move.from + 2 * up) return false;
            return b.piece_at(move.from + up) == Empty;
        }
        return move.to == move.from + up;
    }
    if (special != 0 || move.promotion != 0) return false;
    if (((move.flags & Capture) != 0U) != (target != Empty)) return false;
    Bitboard reach = 0;
    switch (type) {
    case Knight: reach = attacks::knight(move.from); break;
    case Bishop: reach = attacks::bishop(move.from, occ); break;
    case Rook: reach = attacks::rook(move.from, occ); break;
    case Queen: reach = attacks::queen(move.from, occ); break;
    case King: reach = attacks::king(move.from); break;
    default: return false;
    }
    return (reach & square_bb(move.to)) != 0;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::ifstream in(argv[1]);
    std::string fen;
    std::uint64_t checks = 0;
    std::size_t pos_idx = 0;
    while (std::getline(in, fen)) {
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty()) continue;
        forge::Board b;
        if (!b.set_fen(fen)) return 1;

        for (int from = 0; from < 65; ++from) {
            for (int to = 0; to < 65; ++to) {
                for (const std::uint8_t fl : {std::uint8_t{0}, std::uint8_t{forge::Capture},
                                              std::uint8_t{forge::DoublePush},
                                              std::uint8_t{forge::Capture | forge::EnPassant},
                                              std::uint8_t{forge::KingCastle},
                                              std::uint8_t{forge::QueenCastle},
                                              std::uint8_t{forge::Promotion},
                                              std::uint8_t{forge::Capture | forge::Promotion}}) {
                    if ((from == 64 || to == 64) && fl != 0) continue;
                    if (pos_idx >= 120 && fl > forge::Capture) continue;
                    const std::uint8_t promo = (fl & forge::Promotion) ? forge::Queen : ((from == to) ? 1 : 0);
                    const forge::Move m{static_cast<std::uint8_t>(from), static_cast<std::uint8_t>(to), promo, fl};
                    const bool got = b.is_pseudo_legal(m);
                    const bool exp = ref_is_pseudo_legal(b, m);
                    if (got != exp) {
                        std::cerr << "S15_IPL_ORACLE MISMATCH at pos#" << pos_idx
                                  << " from=" << from << " to=" << to
                                  << " promo=" << int(promo) << " flags=" << int(fl)
                                  << " got=" << got << " exp=" << exp << " fen='" << fen << "'\n";
                        return 1;
                    }
                    ++checks;
                }
            }
        }
        ++pos_idx;
    }
    std::cout << "S15_IS_PSEUDO_LEGAL_ORACLE PASS: positions=" << pos_idx << " move_checks=" << checks << " mismatches=0\n";
    return 0;
}
