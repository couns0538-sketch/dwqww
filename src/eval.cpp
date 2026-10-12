#include "forge/eval.hpp"
#include "forge/eval_params.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>

namespace forge {
namespace {

using namespace params;

constexpr std::array<int, 8> PassedKingProximityScale{0, 0, 1, 2, 5, 9, 14, 0};
constexpr std::array<int, 7> KingAttackWeight{0, 0, 2, 2, 3, 5, 0};

// Accumulates parameter contributions, optionally recording coefficients.
template <bool Trace>
struct Accumulator {
    Score score = 0;
    EvalTrace* trace = nullptr;

    template <Color Us>
    void add(int index, int count = 1) {
        const Score value = table[static_cast<std::size_t>(index)] * count;
        score += Us == White ? value : -value;
        if constexpr (Trace) {
            trace->coefficients[static_cast<std::size_t>(index)] =
                static_cast<std::int16_t>(trace->coefficients[static_cast<std::size_t>(index)] + (Us == White ? count : -count));
        }
    }
};

struct EvalInfo {
    std::array<std::array<Bitboard, 7>, 2> attacked_by{};
    std::array<Bitboard, 2> attacked_twice{};
    std::array<Bitboard, 2> mobility_area{};
    std::array<Bitboard, 2> king_zone{};
    std::array<int, 2> king_square{};
    std::array<int, 2> king_attackers{};
    std::array<int, 2> king_attack_units{};
    std::array<Bitboard, 2> passed{};
};

template <bool Trace, Color Us>
void evaluate_pawn_structure(const Board& board, Accumulator<Trace>& acc, Bitboard& passed_out) {
    constexpr Color Them = opposite(Us);
    const Bitboard own = board.pieces(Us, Pawn);
    const Bitboard enemy = board.pieces(Them, Pawn);
    const Bitboard enemy_attacks = pawn_attacks_bb(Them, enemy);
    Bitboard passed = 0;
    Bitboard pawns = own;
    while (pawns != 0) {
        const int square = pop_lsb(pawns);
        const int rank = relative_rank(Us, square);
        const Bitboard adjacent = attacks::adjacent_files(square);
        const Bitboard neighbours = own & adjacent;
        const Bitboard phalanx = neighbours & rank_bb(rank_of(square));
        const Bitboard supported = own & attacks::pawn(Them, square);
        const Bitboard forward = attacks::forward_file(Us, square);
        const int stop = square + pawn_push_delta(Us);

        if ((own & forward) != 0) acc.template add<Us>(PawnDoubled);
        if (neighbours == 0) {
            acc.template add<Us>(PawnIsolated);
        } else if (supported == 0 && phalanx == 0) {
            // Backward: no pawn can ever support it and its stop square is
            // controlled by an enemy pawn.
            const Bitboard behind_or_level = ~attacks::forward_ranks(Us, square) & adjacent & own;
            if (behind_or_level == 0 && (enemy_attacks & square_bb(stop)) != 0) acc.template add<Us>(PawnBackward);
        }
        if (supported != 0 || phalanx != 0) {
            acc.template add<Us>(PawnConnected + rank);
            if (phalanx != 0) acc.template add<Us>(PawnPhalanx);
            if (popcount(supported) > 1) acc.template add<Us>(PawnDoubleSupport);
        }
        if ((attacks::passed_pawn_mask(Us, square) & enemy) == 0 && (own & forward) == 0) {
            passed |= square_bb(square);
        }
    }
    passed_out = passed;
}

template <bool Trace, Color Us>
void evaluate_pieces(const Board& board, Accumulator<Trace>& acc, EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    const Bitboard own_pawns = board.pieces(Us, Pawn);
    const Bitboard enemy_pawns = board.pieces(Them, Pawn);
    const Bitboard occupied = board.occupied();
    const Bitboard outpost_ranks = Us == White ? (Rank4BB | Rank5BB | Rank6BB) : (Rank5BB | Rank4BB | Rank3BB);
    const Bitboard own_pawn_attacks = info.attacked_by[Us][Pawn];
    const Bitboard enemy_king_zone = info.king_zone[Them];
    // Squares that enemy pawns can never attack: outposts.
    Bitboard enemy_pawn_attack_span = 0;
    {
        Bitboard ep = enemy_pawns;
        while (ep != 0) {
            const int sq = pop_lsb(ep);
            enemy_pawn_attack_span |= attacks::passed_pawn_mask(Them, sq) & ~attacks::forward_file(Them, sq);
        }
    }

    for (int type = Knight; type <= Queen; ++type) {
        Bitboard pieces = board.pieces(Us, static_cast<PieceType>(type));
        while (pieces != 0) {
            const int square = pop_lsb(pieces);
            Bitboard attacks_bb = 0;
            switch (type) {
            case Knight: attacks_bb = attacks::knight(square); break;
            case Bishop:
                // X-ray through own queens so batteries count as mobility.
                attacks_bb = attacks::bishop(square, occupied ^ board.pieces(Us, Queen));
                break;
            case Rook:
                attacks_bb = attacks::rook(square, occupied ^ board.pieces(Us, Queen) ^ board.pieces(Us, Rook));
                break;
            default: attacks_bb = attacks::queen(square, occupied); break;
            }
            info.attacked_twice[Us] |= info.attacked_by[Us][0] & attacks_bb;
            info.attacked_by[Us][0] |= attacks_bb;
            info.attacked_by[Us][static_cast<std::size_t>(type)] |= attacks_bb;

            const int mobility = popcount(attacks_bb & info.mobility_area[Us]);
            switch (type) {
            case Knight: acc.template add<Us>(KnightMobility + mobility); break;
            case Bishop: acc.template add<Us>(BishopMobility + mobility); break;
            case Rook: acc.template add<Us>(RookMobility + mobility); break;
            default: acc.template add<Us>(QueenMobility + std::min(mobility, 27)); break;
            }

            const Bitboard zone_hits = attacks_bb & enemy_king_zone;
            if (zone_hits != 0) {
                ++info.king_attackers[Them];
                info.king_attack_units[Them] += KingAttackWeight[static_cast<std::size_t>(type)] * popcount(zone_hits);
            }

            if (type == Knight || type == Bishop) {
                const Bitboard bit = square_bb(square);
                if ((bit & outpost_ranks) != 0 && (bit & own_pawn_attacks) != 0 && (bit & enemy_pawn_attack_span) == 0) {
                    acc.template add<Us>(type == Knight ? KnightOutpost : BishopOutpost);
                }
                if ((pawn_push(Them, bit) & own_pawns) != 0) acc.template add<Us>(MinorBehindPawn);
                if (type == Bishop) {
                    const Bitboard same_color = (bit & DarkSquares) != 0 ? DarkSquares : LightSquares;
                    acc.template add<Us>(BishopPawnsSameColor, popcount(own_pawns & same_color));
                }
            } else if (type == Rook) {
                const int file = file_of(square);
                if ((own_pawns & file_bb(file)) == 0) {
                    acc.template add<Us>((enemy_pawns & file_bb(file)) == 0 ? RookOpenFile : RookSemiOpenFile);
                }
                if (relative_rank(Us, square) == 6) {
                    const int enemy_king_rank = relative_rank(Us, info.king_square[Them]);
                    if (enemy_king_rank == 7 || (enemy_pawns & rank_bb(rank_of(square))) != 0) acc.template add<Us>(RookOnSeventh);
                }
            } else if (relative_rank(Us, square) >= 2) {
                const Bitboard home_minors = (board.pieces(Us, Knight) | board.pieces(Us, Bishop)) &
                                             (Us == White ? Rank1BB : Rank8BB);
                acc.template add<Us>(QueenEarlyDevelopment, popcount(home_minors));
            }
        }
    }
}

template <bool Trace, Color Us>
void evaluate_king(const Board& board, Accumulator<Trace>& acc, const EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    const int king = info.king_square[Us];
    const int king_file = file_of(king);
    const int king_rank = relative_rank(Us, king);
    const Bitboard own_pawns = board.pieces(Us, Pawn);
    const Bitboard enemy_pawns = board.pieces(Them, Pawn);

    int shelter = 0;
    auto shelter_term = [&](int index) {
        acc.template add<Us>(index);
        shelter += mg_value(table[static_cast<std::size_t>(index)]);
    };
    for (int file = std::max(0, king_file - 1); file <= std::min(7, king_file + 1); ++file) {
        const Bitboard file_mask = file_bb(file) & attacks::forward_ranks(Us, king);
        const Bitboard own = own_pawns & file_mask;
        const Bitboard enemy = enemy_pawns & file_mask;
        int own_distance = 0;
        if (own != 0) {
            const int nearest = Us == White ? lsb(own) : msb(own);
            own_distance = std::min(3, relative_rank(Us, nearest) - king_rank);
        }
        shelter_term(ShelterDistance + own_distance);
        if (enemy != 0) {
            const int nearest = Us == White ? lsb(enemy) : msb(enemy);
            const int distance = relative_rank(Us, nearest) - king_rank;
            if (distance <= 3) shelter_term(StormDistance + std::max(1, distance));
        }
        if (((own_pawns | enemy_pawns) & file_bb(file)) == 0) shelter_term(KingFileOpen);
    }

    // King danger from pieces attacking the zone; requires two attackers
    // unless a queen participates.
    const int attackers = info.king_attackers[Us];
    if (attackers >= 2 || (attackers >= 1 && board.pieces(Them, Queen) != 0)) {
        int units = info.king_attack_units[Us];
        const Bitboard zone = info.king_zone[Us];
        const Bitboard weak = zone & info.attacked_by[Them][0] & ~info.attacked_twice[Us] &
                              (~info.attacked_by[Us][0] | info.attacked_by[Us][King] | info.attacked_by[Us][Queen]);
        units += 2 * popcount(weak);
        const Bitboard safe = ~board.occupied(Them) & (~info.attacked_by[Us][0] | (weak & info.attacked_twice[Them]));
        const Bitboard occ = board.occupied();
        const Bitboard rook_rays = attacks::rook(king, occ);
        const Bitboard bishop_rays = attacks::bishop(king, occ);
        const Bitboard rook_checks = rook_rays & safe & info.attacked_by[Them][Rook];
        const Bitboard bishop_checks = bishop_rays & safe & info.attacked_by[Them][Bishop];
        const Bitboard knight_checks = attacks::knight(king) & safe & info.attacked_by[Them][Knight];
        const Bitboard queen_checks = (rook_rays | bishop_rays) & safe & info.attacked_by[Them][Queen];
        units += 6 * popcount(rook_checks) + 4 * popcount(bishop_checks) + 5 * popcount(knight_checks) +
                 5 * popcount(queen_checks);
        if (board.pieces(Them, Queen) == 0) units /= 2;
        units -= shelter / 8;
        units = std::clamp(units, 0, 99);
        acc.template add<Us>(KingDanger + units, -1);
    }
}

template <bool Trace, Color Us>
void evaluate_threats(const Board& board, Accumulator<Trace>& acc, const EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    const Bitboard enemy_pieces = board.occupied(Them) & ~board.pieces(Them, King);
    const Bitboard enemy_non_pawns = enemy_pieces & ~board.pieces(Them, Pawn);

    // Enemy pieces that are poorly defended relative to our attacks.
    const Bitboard strongly_protected = info.attacked_by[Them][Pawn] | (info.attacked_twice[Them] & ~info.attacked_twice[Us]);
    const Bitboard defended = enemy_non_pawns & strongly_protected;
    const Bitboard weak = enemy_pieces & ~strongly_protected & info.attacked_by[Us][0];

    if ((defended | weak) != 0) {
        Bitboard minor_targets = (defended | weak) & (info.attacked_by[Us][Knight] | info.attacked_by[Us][Bishop]);
        while (minor_targets != 0) {
            const int square = pop_lsb(minor_targets);
            acc.template add<Us>(ThreatByMinor + piece_type(board.piece_at(square)));
        }
        Bitboard rook_targets = weak & info.attacked_by[Us][Rook];
        while (rook_targets != 0) {
            const int square = pop_lsb(rook_targets);
            acc.template add<Us>(ThreatByRook + piece_type(board.piece_at(square)));
        }
        if ((weak & info.attacked_by[Us][King]) != 0) acc.template add<Us>(ThreatByKing);
        const Bitboard hanging = weak & (~info.attacked_by[Them][0] | (enemy_non_pawns & info.attacked_twice[Us]));
        acc.template add<Us>(HangingPiece, popcount(hanging));
    }

    // Pieces attacked by safe pawns, and pieces our safe pawn pushes would attack.
    const Bitboard safe_squares = ~info.attacked_by[Them][0] | info.attacked_by[Us][0];
    const Bitboard safe_pawns = board.pieces(Us, Pawn) & safe_squares;
    acc.template add<Us>(ThreatByPawn, popcount(pawn_attacks_bb(Us, safe_pawns) & enemy_non_pawns));

    const Bitboard empty = ~board.occupied();
    Bitboard pushes = pawn_push(Us, board.pieces(Us, Pawn)) & empty;
    pushes |= pawn_push(Us, pushes & (Us == White ? Rank3BB : Rank6BB)) & empty;
    pushes &= ~info.attacked_by[Them][Pawn] & safe_squares;
    acc.template add<Us>(ThreatByPawnPush, popcount(pawn_attacks_bb(Us, pushes) & enemy_non_pawns));

    // Squares our pieces are restricted from by enemy control.
    const Bitboard restricted = info.attacked_by[Them][0] & ~strongly_protected & info.attacked_by[Us][0];
    acc.template add<Us>(RestrictedPiece, popcount(restricted));
}

template <bool Trace, Color Us>
void evaluate_passed(const Board& board, Accumulator<Trace>& acc, const EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    Bitboard passed = info.passed[Us];
    const Bitboard occupied = board.occupied();
    while (passed != 0) {
        const int square = pop_lsb(passed);
        const int rank = relative_rank(Us, square);
        acc.template add<Us>(PassedRank + rank);
        const int scale = PassedKingProximityScale[static_cast<std::size_t>(rank)];
        if (scale == 0) continue;
        const int stop = square + pawn_push_delta(Us);
        const int own_king_distance = std::min(5, square_distance(info.king_square[Us], stop));
        const int enemy_king_distance = std::min(5, square_distance(info.king_square[Them], stop));
        acc.template add<Us>(PassedEnemyKingDistance, enemy_king_distance * scale);
        acc.template add<Us>(PassedOwnKingDistance, own_king_distance * scale);
        if ((occupied & square_bb(stop)) != 0) {
            acc.template add<Us>(PassedBlocked);
        } else {
            const Bitboard path = attacks::forward_file(Us, square);
            const bool path_free = (path & occupied) == 0;
            const bool path_safe = (path & info.attacked_by[Them][0] & ~info.attacked_by[Us][0]) == 0;
            if (path_free && path_safe) acc.template add<Us>(PassedUnstoppablePath, scale / 4 + 1);
            if ((square_bb(stop) & info.attacked_by[Them][0]) == 0) acc.template add<Us>(PassedSafePush, scale / 4 + 1);
        }
    }
}

int scale_factor(const Board& board, int eg) {
    const Color strong = eg > 0 ? White : Black;
    const Color weak = opposite(strong);
    const Bitboard strong_pawns = board.pieces(strong, Pawn);
    auto non_pawn = [&](Color c) {
        return PieceValueMg[Knight] * popcount(board.pieces(c, Knight)) + PieceValueMg[Bishop] * popcount(board.pieces(c, Bishop)) +
               PieceValueMg[Rook] * popcount(board.pieces(c, Rook)) + PieceValueMg[Queen] * popcount(board.pieces(c, Queen));
    };
    const int strong_non_pawn = non_pawn(strong);
    const int weak_non_pawn = non_pawn(weak);

    // No pawns and at most a minor piece ahead: almost certainly drawn.
    if (strong_pawns == 0 && strong_non_pawn - weak_non_pawn <= PieceValueMg[Bishop]) {
        return strong_non_pawn < PieceValueMg[Rook] ? 0 : 12;
    }
    // Opposite coloured bishops.
    const Bitboard white_bishops = board.pieces(White, Bishop);
    const Bitboard black_bishops = board.pieces(Black, Bishop);
    if (popcount(white_bishops) == 1 && popcount(black_bishops) == 1 &&
        ((white_bishops & DarkSquares) != 0) != ((black_bishops & DarkSquares) != 0)) {
        const bool only_bishops = (board.pieces(Knight) | board.pieces(Rook) | board.pieces(Queen)) == 0;
        if (only_bishops) return 32 + 4 * popcount(strong_pawns);
        return 48 + 2 * popcount(strong_pawns);
    }
    // Few pawns for the stronger side make conversions harder.
    return std::min(64, 44 + 5 * popcount(strong_pawns));
}

template <bool Trace>
int evaluate_position(const Board& board, Evaluator::PawnEntry* cache, EvalTrace* trace) {
    EvalInfo info{};
    Accumulator<Trace> acc;
    acc.trace = trace;
    int phase = 0;

    for (int type = Pawn; type <= King; ++type) {
        Bitboard white = board.pieces(White, static_cast<PieceType>(type));
        Bitboard black = board.pieces(Black, static_cast<PieceType>(type));
        phase += PhaseValue[static_cast<std::size_t>(type)] * (popcount(white) + popcount(black));
        while (white != 0) acc.template add<White>(Psqt + (type - 1) * 64 + pop_lsb(white));
        while (black != 0) acc.template add<Black>(Psqt + (type - 1) * 64 + flip_square(pop_lsb(black)));
    }
    phase = std::min(phase, MaxPhase);

    if (!Trace && cache != nullptr && cache->valid && cache->key == board.pawn_key()) {
        acc.score += cache->score;
        info.passed = cache->passed;
    } else {
        Accumulator<Trace> pawn_acc;
        pawn_acc.trace = trace;
        Bitboard white_passed = 0;
        Bitboard black_passed = 0;
        evaluate_pawn_structure<Trace, White>(board, pawn_acc, white_passed);
        evaluate_pawn_structure<Trace, Black>(board, pawn_acc, black_passed);
        acc.score += pawn_acc.score;
        info.passed = {white_passed, black_passed};
        if (!Trace && cache != nullptr) {
            cache->key = board.pawn_key();
            cache->score = pawn_acc.score;
            cache->passed = info.passed;
            cache->valid = true;
        }
    }

    info.king_square = {board.king_square(White), board.king_square(Black)};
    for (const Color color : {White, Black}) {
        const std::size_t c = static_cast<std::size_t>(color);
        const Bitboard pawns = board.pieces(color, Pawn);
        const Bitboard pawn_attacks = pawn_attacks_bb(color, pawns);
        const Bitboard king_attacks = attacks::king(info.king_square[c]);
        info.attacked_by[c][Pawn] = pawn_attacks;
        info.attacked_by[c][King] = king_attacks;
        const Bitboard double_pawn = color == White ? shift_north_east(pawns) & shift_north_west(pawns)
                                                    : shift_south_east(pawns) & shift_south_west(pawns);
        info.attacked_twice[c] = double_pawn | (pawn_attacks & king_attacks);
        info.attacked_by[c][0] = pawn_attacks | king_attacks;
        info.king_zone[c] = attacks::king_zone(info.king_square[c]);
    }
    for (const Color color : {White, Black}) {
        const Color them = opposite(color);
        const std::size_t c = static_cast<std::size_t>(color);
        const Bitboard own_pawns = board.pieces(color, Pawn);
        const Bitboard blocked_pawns = own_pawns & pawn_push(them, board.occupied());
        const Bitboard low_ranks = color == White ? (Rank2BB | Rank3BB) : (Rank7BB | Rank6BB);
        info.mobility_area[c] = ~(info.attacked_by[static_cast<std::size_t>(them)][Pawn] | board.pieces(color, King) |
                                  board.pieces(color, Queen) | (own_pawns & (blocked_pawns | low_ranks)));
    }

    evaluate_pieces<Trace, White>(board, acc, info);
    evaluate_pieces<Trace, Black>(board, acc, info);
    evaluate_king<Trace, White>(board, acc, info);
    evaluate_king<Trace, Black>(board, acc, info);
    evaluate_threats<Trace, White>(board, acc, info);
    evaluate_threats<Trace, Black>(board, acc, info);
    evaluate_passed<Trace, White>(board, acc, info);
    evaluate_passed<Trace, Black>(board, acc, info);

    if (popcount(board.pieces(White, Bishop)) >= 2) acc.template add<White>(BishopPair);
    if (popcount(board.pieces(Black, Bishop)) >= 2) acc.template add<Black>(BishopPair);
    if (board.side_to_move() == White) acc.template add<White>(Tempo);
    else acc.template add<Black>(Tempo);

    const int mg = mg_value(acc.score);
    int eg = eg_value(acc.score);
    const int scale = scale_factor(board, eg);
    eg = eg * scale / 64;
    const int tapered = (mg * phase + eg * (MaxPhase - phase)) / MaxPhase;
    if constexpr (Trace) {
        trace->phase = phase;
        trace->scale = scale;
        trace->side_to_move = board.side_to_move();
        trace->white_eval = tapered;
    }
    return board.side_to_move() == White ? tapered : -tapered;
}

} // namespace

Evaluator::Evaluator() : pawn_cache_(PawnCacheSize) {}

void Evaluator::clear() {
    std::fill(pawn_cache_.begin(), pawn_cache_.end(), PawnEntry{});
}

int Evaluator::evaluate(const Board& board) {
    PawnEntry& entry = pawn_cache_[static_cast<std::size_t>(board.pawn_key()) & (PawnCacheSize - 1U)];
    return evaluate_position<false>(board, &entry, nullptr);
}

int Evaluator::evaluate_uncached(const Board& board) {
    return evaluate_position<false>(board, nullptr, nullptr);
}

int evaluate_traced(const Board& board, EvalTrace& trace) {
    trace = EvalTrace{};
    (void)evaluate_position<true>(board, nullptr, &trace);
    return trace.white_eval;
}

} // namespace forge
