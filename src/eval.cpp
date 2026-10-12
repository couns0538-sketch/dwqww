#include "forge/eval.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>

namespace forge {
namespace {

// Piece-square tables listed from White's point of view with rank 8 first,
// as in a printed diagram (PeSTO layout). Material is folded in.
constexpr std::array<int, 64> PawnMg{
      0,   0,   0,   0,   0,   0,   0,   0,
     98, 134,  61,  95,  68, 126,  34, -11,
     -6,   7,  26,  31,  65,  56,  25, -20,
    -14,  13,   6,  21,  23,  12,  17, -23,
    -27,  -2,  -5,  12,  17,   6,  10, -25,
    -26,  -4,  -4, -10,   3,   3,  33, -12,
    -35,  -1, -20, -23, -15,  24,  38, -22,
      0,   0,   0,   0,   0,   0,   0,   0,
};
constexpr std::array<int, 64> PawnEg{
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
};
constexpr std::array<int, 64> KnightMg{
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
};
constexpr std::array<int, 64> KnightEg{
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
};
constexpr std::array<int, 64> BishopMg{
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
};
constexpr std::array<int, 64> BishopEg{
    -14, -21, -11,  -8,  -7,  -9, -17, -24,
     -8,  -4,   7, -12,  -3, -13,  -4, -14,
      2,  -8,   0,  -1,  -2,   6,   0,   4,
     -3,   9,  12,   9,  14,  10,   3,   2,
     -6,   3,  13,  19,   7,  10,  -3,  -9,
    -12,  -3,   8,  10,  13,   3,  -7, -15,
    -14, -18,  -7,  -1,   4,  -9, -15, -27,
    -23,  -9, -23,  -5,  -9, -16,  -5, -17,
};
constexpr std::array<int, 64> RookMg{
     32,  42,  32,  51,  63,   9,  31,  43,
     27,  32,  58,  62,  80,  67,  26,  44,
     -5,  19,  26,  36,  17,  45,  61,  16,
    -24, -11,   7,  26,  24,  35,  -8, -20,
    -36, -26, -12,  -1,   9,  -7,   6, -23,
    -45, -25, -16, -17,   3,   0,  -5, -33,
    -44, -16, -20,  -9,  -1,  11,  -6, -71,
    -19, -13,   1,  17,  16,   7, -37, -26,
};
constexpr std::array<int, 64> RookEg{
     13,  10,  18,  15,  12,  12,   8,   5,
     11,  13,  13,  11,  -3,   3,   8,   3,
      7,   7,   7,   5,   4,  -3,  -5,  -3,
      4,   3,  13,   1,   2,   1,  -1,   2,
      3,   5,   8,   4,  -5,  -6,  -8, -11,
     -4,   0,  -5,  -1,  -7, -12,  -8, -16,
     -6,  -6,   0,   2,  -9,  -9, -11,  -3,
     -9,   2,   3,  -1,  -5, -13,   4, -20,
};
constexpr std::array<int, 64> QueenMg{
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
};
constexpr std::array<int, 64> QueenEg{
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
};
constexpr std::array<int, 64> KingMg{
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
};
constexpr std::array<int, 64> KingEg{
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
};

struct Psqt {
    std::array<std::array<Score, 64>, 7> table{};
    constexpr Psqt() {
        const std::array<const std::array<int, 64>*, 7> mg{nullptr, &PawnMg, &KnightMg, &BishopMg, &RookMg, &QueenMg, &KingMg};
        const std::array<const std::array<int, 64>*, 7> eg{nullptr, &PawnEg, &KnightEg, &BishopEg, &RookEg, &QueenEg, &KingEg};
        for (int type = Pawn; type <= King; ++type) {
            for (int square = 0; square < 64; ++square) {
                // Diagram index: rank 8 is row 0, so flip the rank of a1-based squares.
                const std::size_t diagram = static_cast<std::size_t>(square ^ 56);
                table[static_cast<std::size_t>(type)][static_cast<std::size_t>(square)] =
                    S(PieceValueMg[static_cast<std::size_t>(type)] + (*mg[static_cast<std::size_t>(type)])[diagram],
                      PieceValueEg[static_cast<std::size_t>(type)] + (*eg[static_cast<std::size_t>(type)])[diagram]);
            }
        }
    }
};
constexpr Psqt PSQT{};

// White-relative square lookup; black pieces mirror the rank.
[[nodiscard]] constexpr Score psqt(Color color, int type, int square) {
    return PSQT.table[static_cast<std::size_t>(type)][static_cast<std::size_t>(relative_square(color, square))];
}

constexpr std::array<Score, 9> KnightMobility{
    S(-50, -60), S(-25, -30), S(-8, -12), S(0, 0), S(6, 8), S(12, 14), S(16, 18), S(20, 22), S(22, 24)};
constexpr std::array<Score, 14> BishopMobility{
    S(-45, -50), S(-22, -25), S(-8, -10), S(2, 4), S(10, 12), S(16, 20), S(22, 26), S(26, 32),
    S(30, 36), S(33, 40), S(36, 43), S(38, 45), S(40, 47), S(42, 48)};
constexpr std::array<Score, 15> RookMobility{
    S(-40, -70), S(-20, -35), S(-10, -10), S(-5, 5), S(0, 18), S(4, 30), S(8, 40), S(12, 48),
    S(15, 55), S(18, 60), S(20, 65), S(22, 68), S(24, 71), S(25, 73), S(26, 75)};
constexpr std::array<Score, 28> QueenMobility{
    S(-30, -50), S(-15, -30), S(-8, -15), S(-4, -5), S(0, 5), S(3, 12), S(6, 18), S(9, 24),
    S(12, 30), S(14, 35), S(16, 40), S(18, 44), S(20, 48), S(21, 52), S(22, 55), S(23, 58),
    S(24, 61), S(25, 64), S(26, 66), S(27, 68), S(28, 70), S(29, 72), S(30, 74), S(30, 75),
    S(31, 76), S(31, 77), S(32, 78), S(32, 79)};

constexpr Score BishopPair = S(28, 55);
constexpr Score RookOpenFile = S(32, 10);
constexpr Score RookSemiOpenFile = S(14, 6);
constexpr Score RookOnSeventh = S(8, 22);
constexpr Score KnightOutpost = S(32, 14);
constexpr Score BishopOutpost = S(20, 8);
constexpr Score MinorBehindPawn = S(8, 2);
constexpr Score BishopPawnsSameColor = S(-3, -6);
constexpr Score QueenEarlyDevelopment = S(-6, 0);
constexpr Score Tempo = S(18, 8);

constexpr Score PawnIsolated = S(-10, -16);
constexpr Score PawnDoubled = S(-9, -22);
constexpr Score PawnBackward = S(-8, -12);
constexpr std::array<Score, 8> PawnConnected{
    S(0, 0), S(4, 2), S(8, 4), S(12, 8), S(22, 16), S(40, 32), S(70, 60), S(0, 0)};
constexpr Score PawnPhalanxBonus = S(5, 3);
constexpr std::array<Score, 8> PassedRank{
    S(0, 0), S(6, 12), S(10, 18), S(20, 36), S(42, 66), S(90, 120), S(140, 180), S(0, 0)};
constexpr std::array<int, 8> PassedKingProximityScale{0, 0, 1, 2, 5, 9, 14, 0};
constexpr Score PassedBlocked = S(-8, -20);
constexpr Score PassedUnstoppablePath = S(10, 40);
constexpr Score PassedSafePush = S(4, 14);

constexpr std::array<Score, 7> ThreatByMinor{S(0, 0), S(4, 18), S(28, 32), S(32, 36), S(56, 48), S(44, 36), S(0, 0)};
constexpr std::array<Score, 7> ThreatByRook{S(0, 0), S(2, 14), S(24, 30), S(24, 30), S(0, 20), S(40, 24), S(0, 0)};
constexpr Score ThreatByKing = S(12, 30);
constexpr Score ThreatByPawn = S(38, 28);
constexpr Score ThreatByPawnPush = S(14, 12);
constexpr Score HangingPiece = S(28, 20);
constexpr Score RestrictedPiece = S(3, 3);

constexpr std::array<int, 7> KingAttackWeight{0, 0, 2, 2, 3, 5, 0};
constexpr std::array<int, 100> SafetyTable{
      0,   0,   1,   2,   3,   5,   7,   9,  12,  15,
     18,  22,  26,  30,  35,  39,  44,  50,  56,  62,
     68,  75,  82,  85,  89,  97, 105, 113, 122, 131,
    140, 150, 169, 180, 191, 202, 213, 225, 237, 248,
    260, 272, 283, 295, 307, 319, 330, 342, 354, 366,
    377, 389, 401, 412, 424, 436, 448, 459, 471, 483,
    494, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500};
// Shelter: own pawn on a file near the king, indexed by rank distance 1..3; 0 means missing.
constexpr std::array<int, 4> ShelterByDistance{-24, 22, 12, 2};
// Storm: enemy pawn approaching the king, indexed by rank distance 1..3; 0 means none.
constexpr std::array<int, 4> StormByDistance{0, -6, -28, -14};
constexpr int KingFileOpenPenalty = -16;

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

template <Color Us>
Score evaluate_pawn_structure(const Board& board, Bitboard& passed_out) {
    constexpr Color Them = opposite(Us);
    const Bitboard own = board.pieces(Us, Pawn);
    const Bitboard enemy = board.pieces(Them, Pawn);
    const Bitboard own_attacks = pawn_attacks_bb(Us, own);
    const Bitboard enemy_attacks = pawn_attacks_bb(Them, enemy);
    Score score = 0;
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

        if ((own & forward) != 0) score += PawnDoubled;
        if (neighbours == 0) {
            score += PawnIsolated;
        } else if (supported == 0 && phalanx == 0) {
            // Backward: cannot be supported by a pawn advance and its stop square
            // is controlled by an enemy pawn.
            const Bitboard behind_or_level = ~attacks::forward_ranks(Us, square) & adjacent & own;
            if (behind_or_level == 0 && (enemy_attacks & square_bb(stop)) != 0) score += PawnBackward;
        }
        if (supported != 0 || phalanx != 0) {
            score += PawnConnected[static_cast<std::size_t>(rank)];
            if (phalanx != 0) score += PawnPhalanxBonus;
            if (popcount(supported) > 1) score += S(2, 2);
        }
        if ((attacks::passed_pawn_mask(Us, square) & enemy) == 0 && (own & forward) == 0) {
            passed |= square_bb(square);
        }
    }
    (void)own_attacks;
    passed_out = passed;
    return score;
}

template <Color Us>
Score evaluate_pieces(const Board& board, EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    const Bitboard own_pawns = board.pieces(Us, Pawn);
    const Bitboard enemy_pawns = board.pieces(Them, Pawn);
    const Bitboard occupied = board.occupied();
    const Bitboard outpost_ranks = Us == White ? (Rank4BB | Rank5BB | Rank6BB) : (Rank5BB | Rank4BB | Rank3BB);
    const Bitboard enemy_pawn_attacks = info.attacked_by[Them][Pawn];
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
    Score score = 0;

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
            case Knight: score += KnightMobility[static_cast<std::size_t>(mobility)]; break;
            case Bishop: score += BishopMobility[static_cast<std::size_t>(mobility)]; break;
            case Rook: score += RookMobility[static_cast<std::size_t>(mobility)]; break;
            default: score += QueenMobility[static_cast<std::size_t>(std::min(mobility, 27))]; break;
            }

            const Bitboard zone_hits = attacks_bb & enemy_king_zone;
            if (zone_hits != 0) {
                ++info.king_attackers[Them];
                info.king_attack_units[Them] += KingAttackWeight[static_cast<std::size_t>(type)] * popcount(zone_hits);
            }

            if (type == Knight || type == Bishop) {
                const Bitboard bit = square_bb(square);
                if ((bit & outpost_ranks) != 0 && (bit & own_pawn_attacks) != 0 && (bit & enemy_pawn_attack_span) == 0) {
                    score += type == Knight ? KnightOutpost : BishopOutpost;
                }
                if ((pawn_push(Them, bit) & own_pawns) != 0) score += MinorBehindPawn;
                if (type == Bishop) {
                    const Bitboard same_color = (bit & DarkSquares) != 0 ? DarkSquares : LightSquares;
                    score += BishopPawnsSameColor * popcount(own_pawns & same_color);
                }
            } else if (type == Rook) {
                const int file = file_of(square);
                if ((own_pawns & file_bb(file)) == 0) {
                    score += (enemy_pawns & file_bb(file)) == 0 ? RookOpenFile : RookSemiOpenFile;
                }
                if (relative_rank(Us, square) == 6) {
                    const int enemy_king_rank = relative_rank(Us, info.king_square[Them]);
                    if (enemy_king_rank == 7 || (enemy_pawns & rank_bb(rank_of(square))) != 0) score += RookOnSeventh;
                }
            } else {
                if (relative_rank(Us, square) >= 2) {
                    const Bitboard home_minors = (board.pieces(Us, Knight) | board.pieces(Us, Bishop)) &
                                                 (Us == White ? Rank1BB : Rank8BB);
                    score += QueenEarlyDevelopment * popcount(home_minors);
                }
            }
        }
    }
    (void)enemy_pawn_attacks;
    return score;
}

template <Color Us>
Score evaluate_king(const Board& board, const EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    const int king = info.king_square[Us];
    const int king_file = file_of(king);
    const int king_rank = relative_rank(Us, king);
    const Bitboard own_pawns = board.pieces(Us, Pawn);
    const Bitboard enemy_pawns = board.pieces(Them, Pawn);
    Score score = 0;

    int shelter = 0;
    for (int file = std::max(0, king_file - 1); file <= std::min(7, king_file + 1); ++file) {
        const Bitboard file_mask = file_bb(file) & attacks::forward_ranks(Us, king);
        const Bitboard own = own_pawns & file_mask;
        const Bitboard enemy = enemy_pawns & file_mask;
        int own_distance = 0;
        if (own != 0) {
            const int nearest = Us == White ? lsb(own) : msb(own);
            own_distance = std::min(3, relative_rank(Us, nearest) - king_rank);
        }
        shelter += ShelterByDistance[static_cast<std::size_t>(own_distance)];
        if (enemy != 0) {
            const int nearest = Us == White ? lsb(enemy) : msb(enemy);
            const int distance = relative_rank(Us, nearest) - king_rank;
            if (distance <= 3) shelter += StormByDistance[static_cast<std::size_t>(std::max(1, distance))];
        }
        if (((own_pawns | enemy_pawns) & file_bb(file)) == 0) shelter += KingFileOpenPenalty;
    }
    score += S(shelter, 0);

    // King danger from pieces attacking the zone, requires at least two attackers
    // unless a queen participates.
    const int attackers = info.king_attackers[Us];
    if (attackers >= 2 || (attackers >= 1 && board.pieces(Them, Queen) != 0)) {
        int units = info.king_attack_units[Us];
        const Bitboard zone = info.king_zone[Us];
        const Bitboard weak = zone & info.attacked_by[Them][0] &
                              ~info.attacked_twice[Us] &
                              (~info.attacked_by[Us][0] | info.attacked_by[Us][King] | info.attacked_by[Us][Queen]);
        units += 2 * popcount(weak);
        // Safe checking squares.
        const Bitboard safe = ~board.occupied(Them) & (~info.attacked_by[Us][0] | (weak & info.attacked_twice[Them]));
        const Bitboard occ = board.occupied();
        const Bitboard rook_checks = attacks::rook(king, occ) & safe & info.attacked_by[Them][Rook];
        const Bitboard bishop_checks = attacks::bishop(king, occ) & safe & info.attacked_by[Them][Bishop];
        const Bitboard knight_checks = attacks::knight(king) & safe & info.attacked_by[Them][Knight];
        const Bitboard queen_checks = (attacks::rook(king, occ) | attacks::bishop(king, occ)) & safe & info.attacked_by[Them][Queen];
        units += 6 * popcount(rook_checks) + 4 * popcount(bishop_checks) + 5 * popcount(knight_checks) + 5 * popcount(queen_checks);
        if (board.pieces(Them, Queen) == 0) units /= 2;
        units -= shelter / 8;
        units = std::clamp(units, 0, 99);
        const int danger = SafetyTable[static_cast<std::size_t>(units)];
        score -= S(danger, danger / 6);
    }
    return score;
}

template <Color Us>
Score evaluate_threats(const Board& board, const EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    const Bitboard enemy_pieces = board.occupied(Them) & ~board.pieces(Them, King);
    const Bitboard enemy_non_pawns = enemy_pieces & ~board.pieces(Them, Pawn);
    Score score = 0;

    // Enemy pieces that are poorly defended relative to our attacks.
    const Bitboard strongly_protected = info.attacked_by[Them][Pawn] |
                                        (info.attacked_twice[Them] & ~info.attacked_twice[Us]);
    const Bitboard defended = enemy_non_pawns & strongly_protected;
    const Bitboard weak = enemy_pieces & ~strongly_protected & info.attacked_by[Us][0];

    if ((defended | weak) != 0) {
        Bitboard minor_targets = (defended | weak) & (info.attacked_by[Us][Knight] | info.attacked_by[Us][Bishop]);
        while (minor_targets != 0) {
            const int square = pop_lsb(minor_targets);
            score += ThreatByMinor[static_cast<std::size_t>(piece_type(board.piece_at(square)))];
        }
        Bitboard rook_targets = weak & info.attacked_by[Us][Rook];
        while (rook_targets != 0) {
            const int square = pop_lsb(rook_targets);
            score += ThreatByRook[static_cast<std::size_t>(piece_type(board.piece_at(square)))];
        }
        if ((weak & info.attacked_by[Us][King]) != 0) score += ThreatByKing;
        const Bitboard hanging = weak & (~info.attacked_by[Them][0] | (enemy_non_pawns & info.attacked_twice[Us]));
        score += HangingPiece * popcount(hanging);
    }

    // Pieces attacked by pawns, and pieces our safe pawn pushes would attack.
    const Bitboard safe_squares = ~info.attacked_by[Them][0] | info.attacked_by[Us][0];
    const Bitboard safe_pawns = board.pieces(Us, Pawn) & safe_squares;
    score += ThreatByPawn * popcount(pawn_attacks_bb(Us, safe_pawns) & enemy_non_pawns);

    const Bitboard empty = ~board.occupied();
    Bitboard pushes = pawn_push(Us, board.pieces(Us, Pawn)) & empty;
    pushes |= pawn_push(Us, pushes & (Us == White ? Rank3BB : Rank6BB)) & empty;
    pushes &= ~info.attacked_by[Them][Pawn] & safe_squares;
    score += ThreatByPawnPush * popcount(pawn_attacks_bb(Us, pushes) & enemy_non_pawns);

    // Squares our pieces are restricted from by enemy control.
    const Bitboard restricted = info.attacked_by[Them][0] & ~strongly_protected & info.attacked_by[Us][0];
    score += RestrictedPiece * popcount(restricted);
    return score;
}

template <Color Us>
Score evaluate_passed(const Board& board, const EvalInfo& info) {
    constexpr Color Them = opposite(Us);
    Score score = 0;
    Bitboard passed = info.passed[Us];
    const Bitboard occupied = board.occupied();
    while (passed != 0) {
        const int square = pop_lsb(passed);
        const int rank = relative_rank(Us, square);
        score += PassedRank[static_cast<std::size_t>(rank)];
        const int scale = PassedKingProximityScale[static_cast<std::size_t>(rank)];
        if (scale == 0) continue;
        const int stop = square + pawn_push_delta(Us);
        const int own_king_distance = std::min(5, square_distance(info.king_square[Us], stop));
        const int enemy_king_distance = std::min(5, square_distance(info.king_square[Them], stop));
        score += S(0, (enemy_king_distance * 5 - own_king_distance * 2) * scale);
        if ((occupied & square_bb(stop)) != 0) {
            score += PassedBlocked;
        } else {
            const Bitboard path = attacks::forward_file(Us, square);
            const bool path_free = (path & occupied) == 0;
            const bool path_safe = (path & info.attacked_by[Them][0] & ~info.attacked_by[Us][0]) == 0;
            if (path_free && path_safe) {
                score += S(mg_value(PassedUnstoppablePath) * scale / 4, eg_value(PassedUnstoppablePath) * scale / 4);
            }
            if ((square_bb(stop) & info.attacked_by[Them][0]) == 0) {
                score += S(mg_value(PassedSafePush) * scale / 4, eg_value(PassedSafePush) * scale / 4);
            }
        }
    }
    return score;
}

int scale_factor(const Board& board, int eg) {
    const Color strong = eg > 0 ? White : Black;
    const Color weak = opposite(strong);
    const Bitboard strong_pawns = board.pieces(strong, Pawn);
    const int strong_non_pawn =
        PieceValueMg[Knight] * popcount(board.pieces(strong, Knight)) + PieceValueMg[Bishop] * popcount(board.pieces(strong, Bishop)) +
        PieceValueMg[Rook] * popcount(board.pieces(strong, Rook)) + PieceValueMg[Queen] * popcount(board.pieces(strong, Queen));
    const int weak_non_pawn =
        PieceValueMg[Knight] * popcount(board.pieces(weak, Knight)) + PieceValueMg[Bishop] * popcount(board.pieces(weak, Bishop)) +
        PieceValueMg[Rook] * popcount(board.pieces(weak, Rook)) + PieceValueMg[Queen] * popcount(board.pieces(weak, Queen));

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

} // namespace

Evaluator::Evaluator() : pawn_cache_(PawnCacheSize) {}

void Evaluator::clear() {
    std::fill(pawn_cache_.begin(), pawn_cache_.end(), PawnEntry{});
}

int Evaluator::evaluate(const Board& board) {
    PawnEntry& entry = pawn_cache_[static_cast<std::size_t>(board.pawn_key()) & (PawnCacheSize - 1U)];
    return evaluate_impl(board, &entry);
}

int Evaluator::evaluate_uncached(const Board& board) {
    Evaluator evaluator;
    return evaluator.evaluate_impl(board, nullptr);
}

int Evaluator::evaluate_impl(const Board& board, PawnEntry* cache) {
    EvalInfo info{};
    Score score = 0;
    int phase = 0;

    for (int type = Pawn; type <= King; ++type) {
        Bitboard white = board.pieces(White, static_cast<PieceType>(type));
        Bitboard black = board.pieces(Black, static_cast<PieceType>(type));
        phase += PhaseValue[static_cast<std::size_t>(type)] * (popcount(white) + popcount(black));
        while (white != 0) score += psqt(White, type, pop_lsb(white));
        while (black != 0) score -= psqt(Black, type, pop_lsb(black));
    }
    phase = std::min(phase, MaxPhase);

    if (cache != nullptr && cache->valid && cache->key == board.pawn_key()) {
        score += cache->score;
        info.passed = cache->passed;
    } else {
        Bitboard white_passed = 0;
        Bitboard black_passed = 0;
        const Score pawn_score = evaluate_pawn_structure<White>(board, white_passed) -
                                 evaluate_pawn_structure<Black>(board, black_passed);
        score += pawn_score;
        info.passed = {white_passed, black_passed};
        if (cache != nullptr) {
            cache->key = board.pawn_key();
            cache->score = pawn_score;
            cache->passed = info.passed;
            cache->valid = true;
        }
    }

    info.king_square = {board.king_square(White), board.king_square(Black)};
    for (const Color color : {White, Black}) {
        const Color them = opposite(color);
        const std::size_t c = static_cast<std::size_t>(color);
        const Bitboard pawns = board.pieces(color, Pawn);
        const Bitboard pawn_attacks = pawn_attacks_bb(color, pawns);
        const Bitboard king_attacks = attacks::king(info.king_square[c]);
        info.attacked_by[c][Pawn] = pawn_attacks;
        info.attacked_by[c][King] = king_attacks;
        // Squares attacked by two pawns, or by a pawn and the king.
        const Bitboard double_pawn = color == White
            ? shift_north_east(pawns) & shift_north_west(pawns)
            : shift_south_east(pawns) & shift_south_west(pawns);
        info.attacked_twice[c] = double_pawn | (pawn_attacks & king_attacks);
        info.attacked_by[c][0] = pawn_attacks | king_attacks;
        info.king_zone[c] = attacks::king_zone(info.king_square[c]);
        (void)them;
    }
    for (const Color color : {White, Black}) {
        const Color them = opposite(color);
        const std::size_t c = static_cast<std::size_t>(color);
        const Bitboard own_pawns = board.pieces(color, Pawn);
        const Bitboard blocked_pawns = own_pawns & pawn_push(them, board.occupied());
        const Bitboard low_ranks = color == White ? (Rank2BB | Rank3BB) : (Rank7BB | Rank6BB);
        info.mobility_area[c] = ~(info.attacked_by[static_cast<std::size_t>(them)][Pawn] |
                                  board.pieces(color, King) | board.pieces(color, Queen) |
                                  (own_pawns & (blocked_pawns | low_ranks)));
    }

    score += evaluate_pieces<White>(board, info) - evaluate_pieces<Black>(board, info);
    score += evaluate_king<White>(board, info) - evaluate_king<Black>(board, info);
    score += evaluate_threats<White>(board, info) - evaluate_threats<Black>(board, info);
    score += evaluate_passed<White>(board, info) - evaluate_passed<Black>(board, info);

    if (popcount(board.pieces(White, Bishop)) >= 2) score += BishopPair;
    if (popcount(board.pieces(Black, Bishop)) >= 2) score -= BishopPair;
    score += board.side_to_move() == White ? Tempo : -Tempo;

    const int mg = mg_value(score);
    int eg = eg_value(score);
    eg = eg * scale_factor(board, eg) / 64;
    const int tapered = (mg * phase + eg * (MaxPhase - phase)) / MaxPhase;
    return board.side_to_move() == White ? tapered : -tapered;
}

} // namespace forge
