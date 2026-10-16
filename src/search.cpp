#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <iostream>
#include <limits>

namespace forge {
namespace {

constexpr int Infinity = 32000;
constexpr int MateScore = 30000;
// Scores at or beyond this magnitude are mate scores; speculative pruning is
// disabled whenever a window touches them.
constexpr int MateBound = MateScore - 128;
// Sentinel static evaluation for in-check nodes, where no stand-pat exists.
constexpr int NoEval = -Infinity * 4;
constexpr std::array<int, 7> PieceValue{0, 100, 320, 330, 500, 900, 0};

// Late-move reduction amounts indexed by [depth][move index], both capped at 63.
struct LmrTable {
    std::array<std::array<int, 64>, 64> quiet{};
    LmrTable() {
        for (int depth = 1; depth < 64; ++depth) {
            for (int index = 1; index < 64; ++index) {
                const double value = 0.75 + std::log(static_cast<double>(depth)) *
                                                std::log(static_cast<double>(index)) / 2.25;
                quiet[static_cast<std::size_t>(depth)][static_cast<std::size_t>(index)] =
                    static_cast<int>(std::max(0.0, value));
            }
        }
    }
};
const LmrTable Lmr;
constexpr std::array<int, 7> MgValue{0, 82, 337, 365, 477, 1025, 0};
constexpr std::array<int, 7> EgValue{0, 94, 281, 297, 512, 936, 0};
constexpr std::array<int, 7> PhaseWeight{0, 0, 1, 1, 2, 4, 0};
constexpr std::array<int, 8> PassedMg{0, 5, 10, 20, 35, 60, 100, 0};
constexpr std::array<int, 8> PassedEg{0, 10, 20, 35, 60, 100, 160, 0};
constexpr int MaxPhase = 24;
// Piece-square tables from PeSTO's evaluation function (Ronald Friederich,
// published for free use on the Chess Programming Wiki). Rows run from rank 8
// down to rank 1, so a white piece on square s reads entry s ^ 56 and a black
// piece reads entry s. Material is added separately (MgValue/EgValue).
struct PieceSquare { std::array<int, 64> mg; std::array<int, 64> eg; };
constexpr std::array<PieceSquare, 7> Psqt{{
    PieceSquare{{}, {}},
    PieceSquare{{ // Pawn middlegame
           0,    0,    0,    0,    0,    0,    0,    0,
          98,  134,   61,   95,   68,  126,   34,  -11,
          -6,    7,   26,   31,   65,   56,   25,  -20,
         -14,   13,    6,   21,   23,   12,   17,  -23,
         -27,   -2,   -5,   12,   17,    6,   10,  -25,
         -26,   -4,   -4,  -10,    3,    3,   33,  -12,
         -35,   -1,  -20,  -23,  -15,   24,   38,  -22,
           0,    0,    0,    0,    0,    0,    0,    0,
    }, { // Pawn endgame
           0,    0,    0,    0,    0,    0,    0,    0,
         178,  173,  158,  134,  147,  132,  165,  187,
          94,  100,   85,   67,   56,   53,   82,   84,
          32,   24,   13,    5,   -2,    4,   17,   17,
          13,    9,   -3,   -7,   -7,   -8,    3,   -1,
           4,    7,   -6,    1,    0,   -5,   -1,   -8,
          13,    8,    8,   10,   13,    0,    2,   -7,
           0,    0,    0,    0,    0,    0,    0,    0,
    }},
    PieceSquare{{ // Knight middlegame
        -167,  -89,  -34,  -49,   61,  -97,  -15, -107,
         -73,  -41,   72,   36,   23,   62,    7,  -17,
         -47,   60,   37,   65,   84,  129,   73,   44,
          -9,   17,   19,   53,   37,   69,   18,   22,
         -13,    4,   16,   13,   28,   19,   21,   -8,
         -23,   -9,   12,   10,   19,   17,   25,  -16,
         -29,  -53,  -12,   -3,   -1,   18,  -14,  -19,
        -105,  -21,  -58,  -33,  -17,  -28,  -19,  -23,
    }, { // Knight endgame
         -58,  -38,  -13,  -28,  -31,  -27,  -63,  -99,
         -25,   -8,  -25,   -2,   -9,  -25,  -24,  -52,
         -24,  -20,   10,    9,   -1,   -9,  -19,  -41,
         -17,    3,   22,   22,   22,   11,    8,  -18,
         -18,   -6,   16,   25,   16,   17,    4,  -18,
         -23,   -3,   -1,   15,   10,   -3,  -20,  -22,
         -42,  -20,  -10,   -5,   -2,  -20,  -23,  -44,
         -29,  -51,  -23,  -15,  -22,  -18,  -50,  -64,
    }},
    PieceSquare{{ // Bishop middlegame
         -29,    4,  -82,  -37,  -25,  -42,    7,   -8,
         -26,   16,  -18,  -13,   30,   59,   18,  -47,
         -16,   37,   43,   40,   35,   50,   37,   -2,
          -4,    5,   19,   50,   37,   37,    7,   -2,
          -6,   13,   13,   26,   34,   12,   10,    4,
           0,   15,   15,   15,   14,   27,   18,   10,
           4,   15,   16,    0,    7,   21,   33,    1,
         -33,   -3,  -14,  -21,  -13,  -12,  -39,  -21,
    }, { // Bishop endgame
         -14,  -21,  -11,   -8,   -7,   -9,  -17,  -24,
          -8,   -4,    7,  -12,   -3,  -13,   -4,  -14,
           2,   -8,    0,   -1,   -2,    6,    0,    4,
          -3,    9,   12,    9,   14,   10,    3,    2,
          -6,    3,   13,   19,    7,   10,   -3,   -9,
         -12,   -3,    8,   10,   13,    3,   -7,  -15,
         -14,  -18,   -7,   -1,    4,   -9,  -15,  -27,
         -23,   -9,  -23,   -5,   -9,  -16,   -5,  -17,
    }},
    PieceSquare{{ // Rook middlegame
          32,   42,   32,   51,   63,    9,   31,   43,
          27,   32,   58,   62,   80,   67,   26,   44,
          -5,   19,   26,   36,   17,   45,   61,   16,
         -24,  -11,    7,   26,   24,   35,   -8,  -20,
         -36,  -26,  -12,   -1,    9,   -7,    6,  -23,
         -45,  -25,  -16,  -17,    3,    0,   -5,  -33,
         -44,  -16,  -20,   -9,   -1,   11,   -6,  -71,
         -19,  -13,    1,   17,   16,    7,  -37,  -26,
    }, { // Rook endgame
          13,   10,   18,   15,   12,   12,    8,    5,
          11,   13,   13,   11,   -3,    3,    8,    3,
           7,    7,    7,    5,    4,   -3,   -5,   -3,
           4,    3,   13,    1,    2,    1,   -1,    2,
           3,    5,    8,    4,   -5,   -6,   -8,  -11,
          -4,    0,   -5,   -1,   -7,  -12,   -8,  -16,
          -6,   -6,    0,    2,   -9,   -9,  -11,   -3,
          -9,    2,    3,   -1,   -5,  -13,    4,  -20,
    }},
    PieceSquare{{ // Queen middlegame
         -28,    0,   29,   12,   59,   44,   43,   45,
         -24,  -39,   -5,    1,  -16,   57,   28,   54,
         -13,  -17,    7,    8,   29,   56,   47,   57,
         -27,  -27,  -16,  -16,   -1,   17,   -2,    1,
          -9,  -26,   -9,  -10,   -2,   -4,    3,   -3,
         -14,    2,  -11,   -2,   -5,    2,   14,    5,
         -35,   -8,   11,    2,    8,   15,   -3,    1,
          -1,  -18,   -9,   10,  -15,  -25,  -31,  -50,
    }, { // Queen endgame
          -9,   22,   22,   27,   27,   19,   10,   20,
         -17,   20,   32,   41,   58,   25,   30,    0,
         -20,    6,    9,   49,   47,   35,   19,    9,
           3,   22,   24,   45,   57,   40,   57,   36,
         -18,   28,   19,   47,   31,   34,   39,   23,
         -16,  -27,   15,    6,    9,   17,   10,    5,
         -22,  -23,  -30,  -16,  -16,  -23,  -36,  -32,
         -33,  -28,  -22,  -43,   -5,  -32,  -20,  -41,
    }},
    PieceSquare{{ // King middlegame
         -65,   23,   16,  -15,  -56,  -34,    2,   13,
          29,   -1,  -20,   -7,   -8,   -4,  -38,  -29,
          -9,   24,    2,  -16,  -20,    6,   22,  -22,
         -17,  -20,  -12,  -27,  -30,  -25,  -14,  -36,
         -49,   -1,  -27,  -39,  -46,  -44,  -33,  -51,
         -14,  -14,  -22,  -46,  -44,  -30,  -15,  -27,
           1,    7,   -8,  -64,  -43,  -16,    9,    8,
         -15,   36,   12,  -54,    8,  -28,   24,   14,
    }, { // King endgame
         -74,  -35,  -18,  -18,  -11,   15,    4,  -17,
         -12,   17,   14,   17,   17,   38,   23,   11,
          10,   17,   23,   15,   20,   45,   44,   13,
          -8,   22,   24,   27,   26,   33,   26,    3,
         -18,   -4,   21,   24,   27,   23,    9,  -11,
         -19,   -3,   11,   21,   23,   16,    7,   -9,
         -27,  -11,    4,   13,   14,    4,   -5,  -17,
         -53,  -34,  -21,  -11,  -28,  -14,  -24,  -43,
    }},
}};
constexpr int abs_int(int value) { return value < 0 ? -value : value; }

int normalized_score_for_tt(int score, int ply) {
    if (score > MateScore - 128) return score + ply;
    if (score < -MateScore + 128) return score - ply;
    return score;
}

int score_from_tt(int score, int ply) {
    if (score > MateScore - 128) return score - ply;
    if (score < -MateScore + 128) return score + ply;
    return score;
}

bool same_move(const Move& a, const Move& b) {
    return a.from == b.from && a.to == b.to && a.promotion == b.promotion;
}

bool has_non_pawn_material(const Board& board, Color color) {
    if (color == White) return (board.pieces(WN) | board.pieces(WB) | board.pieces(WR) | board.pieces(WQ)) != 0;
    return (board.pieces(BN) | board.pieces(BB) | board.pieces(BR) | board.pieces(BQ)) != 0;
}

constexpr std::array<std::uint64_t, 64> make_knight_attacks() {
    std::array<std::uint64_t, 64> attacks{};
    constexpr std::array<int, 8> offsets{17, 15, 10, 6, -6, -10, -15, -17};
    for (int square = 0; square < 64; ++square) {
        const int file = square & 7;
        for (const int offset : offsets) {
            const int target = square + offset;
            if (target < 0 || target >= 64 || abs_int((target & 7) - file) > 2) continue;
            attacks[static_cast<std::size_t>(square)] |= 1ULL << target;
        }
    }
    return attacks;
}

constexpr auto KnightAttacks = make_knight_attacks();

constexpr std::array<std::uint64_t, 64> make_king_attacks() {
    std::array<std::uint64_t, 64> attacks{};
    constexpr std::array<int, 8> offsets{9, 8, 7, 1, -1, -7, -8, -9};
    for (int square = 0; square < 64; ++square) {
        const int file = square & 7;
        for (const int offset : offsets) {
            const int target = square + offset;
            if (target < 0 || target >= 64 || abs_int((target & 7) - file) > 1) continue;
            attacks[static_cast<std::size_t>(square)] |= 1ULL << target;
        }
    }
    return attacks;
}

constexpr auto KingAttacks = make_king_attacks();

// King safety: attack units accumulated by enemy pieces hitting the king zone
// (king square, its neighbours and the three squares beyond them), converted
// to a middlegame penalty once at least two pieces take part.
constexpr std::array<int, 7> KingAttackWeight{0, 0, 2, 2, 3, 5, 0};
constexpr std::array<int, 100> KingSafetyTable{
      0,   0,   1,   2,   3,   5,   7,   9,  12,  15,
     18,  22,  26,  30,  35,  39,  44,  50,  56,  62,
     68,  75,  82,  85,  89,  97, 105, 113, 122, 131,
    140, 150, 169, 180, 191, 202, 213, 225, 237, 248,
    260, 272, 283, 295, 307, 319, 330, 342, 354, 366,
    377, 389, 401, 412, 424, 436, 448, 459, 471, 483,
    494, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
};

constexpr std::array<int, 8> RayDirections{9, 7, -7, -9, 8, -8, 1, -1};

constexpr std::array<std::array<std::uint64_t, 8>, 64> make_ray_attacks() {
    std::array<std::array<std::uint64_t, 8>, 64> attacks{};
    for (int square = 0; square < 64; ++square) {
        for (std::size_t direction = 0; direction < RayDirections.size(); ++direction) {
            int from = square;
            while (true) {
                const int target = from + RayDirections[direction];
                if (target < 0 || target >= 64 || abs_int((target & 7) - (from & 7)) > 1) break;
                attacks[static_cast<std::size_t>(square)][direction] |= 1ULL << target;
                from = target;
            }
        }
    }
    return attacks;
}

constexpr auto RayAttacks = make_ray_attacks();

} // namespace

Searcher::Searcher(std::size_t hash_mb) {
    resize_hash(hash_mb);
    eval_cache_.resize(EvalCacheSize);
    pawn_cache_.resize(PawnCacheSize);
}

void Searcher::resize_hash(std::size_t hash_mb) {
    const std::size_t bytes = std::max<std::size_t>(1, hash_mb) * 1024U * 1024U;
    table_.assign(std::max<std::size_t>(1, bytes / sizeof(TTEntry)), TTEntry{});
    tt_mask_ = std::has_single_bit(table_.size()) ? table_.size() - 1U : 0U;
}

void Searcher::clear() {
    clear_hash();
    history_ = {};
    killers_ = {};
    countermoves_ = {};
}

void Searcher::clear_hash() {
    std::fill(table_.begin(), table_.end(), TTEntry{});
    std::fill(eval_cache_.begin(), eval_cache_.end(), EvalEntry{});
    std::fill(pawn_cache_.begin(), pawn_cache_.end(), PawnEntry{});
}

bool Searcher::is_search_repetition(const Board& board, std::size_t root_index) {
    const std::vector<std::uint64_t>& history = board.key_history();
    const std::size_t size = history.size();
    if (size < 3) return false;
    const std::uint64_t current = history[size - 1];
    const std::size_t reversible = std::min<std::size_t>(
        static_cast<std::size_t>(board.halfmove_clock()), size - 1);
    const std::size_t begin = size - 1 - reversible;
    int matches = 0;
    for (std::size_t i = size - 1; i-- > begin;) {
        if (history[i] != current) continue;
        // One earlier occurrence strictly inside the search tree is enough: the
        // opponent can always repeat, so the line is at best a draw.
        if (i > root_index) return true;
        if (++matches >= 2) return true;
    }
    return false;
}

int Searcher::hashfull_permille() const {
    const std::size_t sample = std::min<std::size_t>(1000, table_.size());
    if (sample == 0) return 0;
    const auto occupied = std::count_if(table_.begin(), table_.begin() + static_cast<std::ptrdiff_t>(sample),
                                        [](const TTEntry& entry) { return tt_depth(entry) >= 0; });
    return static_cast<int>(occupied * 1000 / static_cast<std::ptrdiff_t>(sample));
}

Searcher::PawnEntry Searcher::analyze_pawns(const Board& board) {
    PawnEntry result;
    result.key = board.pawn_key();
    result.valid = true;
    result.white_min_rank.fill(8);
    result.black_max_rank.fill(-1);
    auto add = [&](Color color, int mg, int eg) {
        const int sign = color == White ? 1 : -1;
        result.mg += sign * mg;
        result.eg += sign * eg;
    };

    std::uint64_t pawns = board.pieces(WP) | board.pieces(BP);
    while (pawns != 0) {
        const int square = static_cast<int>(std::countr_zero(pawns));
        pawns &= pawns - 1;
        const Piece piece = board.piece_at(square);
        const Color color = piece == WP ? White : Black;
        const int file = square & 7;
        const int rank = square >> 3;
        const std::size_t psq = static_cast<std::size_t>(color == White ? square ^ 56 : square);
        add(color, MgValue[1] + Psqt[1].mg[psq], EgValue[1] + Psqt[1].eg[psq]);
        ++result.by_file[static_cast<std::size_t>(color)][static_cast<std::size_t>(file)];
        if (color == White) result.white_min_rank[static_cast<std::size_t>(file)] =
            std::min(result.white_min_rank[static_cast<std::size_t>(file)], rank);
        else result.black_max_rank[static_cast<std::size_t>(file)] =
            std::max(result.black_max_rank[static_cast<std::size_t>(file)], rank);
    }
    for (int color_index = 0; color_index < 2; ++color_index) {
        const Color color = static_cast<Color>(color_index);
        for (int file = 0; file < 8; ++file) {
            const int count = result.by_file[static_cast<std::size_t>(color)][static_cast<std::size_t>(file)];
            if (count > 1) add(color, -14 * (count - 1), -20 * (count - 1));
        }
    }
    pawns = board.pieces(WP) | board.pieces(BP);
    while (pawns != 0) {
        const int square = static_cast<int>(std::countr_zero(pawns));
        pawns &= pawns - 1;
        const Color color = board.piece_at(square) == WP ? White : Black;
        const int file = square & 7;
        const int rank = square >> 3;
        const int relative_rank = color == White ? rank : 7 - rank;
        const auto& own_files = result.by_file[static_cast<std::size_t>(color)];
        const bool left_empty = file == 0 || own_files[static_cast<std::size_t>(file - 1)] == 0;
        const bool right_empty = file == 7 || own_files[static_cast<std::size_t>(file + 1)] == 0;
        if (left_empty && right_empty) add(color, -12, -16);
        bool passed = true;
        for (int adjacent = std::max(0, file - 1); adjacent <= std::min(7, file + 1); ++adjacent) {
            if (color == White && result.black_max_rank[static_cast<std::size_t>(adjacent)] > rank) passed = false;
            if (color == Black && result.white_min_rank[static_cast<std::size_t>(adjacent)] < rank) passed = false;
        }
        if (passed) add(color, PassedMg[static_cast<std::size_t>(relative_rank)],
                        PassedEg[static_cast<std::size_t>(relative_rank)]);
    }
    return result;
}

int Searcher::evaluate(const Board& board) {
    return evaluate_with_pawns(board, analyze_pawns(board));
}

int Searcher::evaluate_with_pawns(const Board& board, const PawnEntry& pawns) {
    const auto& pawns_by_file = pawns.by_file;
    std::array<int, 2> bishops{};
    std::array<int, 2> king_square{-1, -1};
    int mg_score = pawns.mg;
    int eg_score = pawns.eg;
    int phase = 0;

    auto add = [&](Color color, int mg, int eg) {
        const int sign = color == White ? 1 : -1;
        mg_score += sign * mg;
        eg_score += sign * eg;
    };
    const std::uint64_t white_occupied = board.occupied(White);
    const std::uint64_t black_occupied = board.occupied(Black);
    const std::uint64_t all_occupied = white_occupied | black_occupied;
    auto attack_set = [&](int square, int type) {
        if (type == 2) return KnightAttacks[static_cast<std::size_t>(square)];
        std::uint64_t attacks = 0;
        const int begin = type == 4 ? 4 : 0;
        const int end = type == 3 ? 4 : 8;
        for (int index = begin; index < end; ++index) {
            std::uint64_t ray = RayAttacks[static_cast<std::size_t>(square)]
                                         [static_cast<std::size_t>(index)];
            const std::uint64_t blockers = ray & all_occupied;
            if (blockers != 0) {
                const int blocker_square = RayDirections[static_cast<std::size_t>(index)] > 0
                    ? static_cast<int>(std::countr_zero(blockers))
                    : 63 - static_cast<int>(std::countl_zero(blockers));
                ray &= ~RayAttacks[static_cast<std::size_t>(blocker_square)]
                                  [static_cast<std::size_t>(index)];
            }
            attacks |= ray;
        }
        return attacks;
    };
    // King zones are needed while scanning the attacking pieces, so locate the
    // kings first.
    std::array<std::uint64_t, 2> king_zone{};
    for (int color_index = 0; color_index < 2; ++color_index) {
        const std::uint64_t king_bit = board.pieces(color_index == 0 ? WK : BK);
        if (king_bit == 0) continue;
        const int king = static_cast<int>(std::countr_zero(king_bit));
        const std::uint64_t ring = KingAttacks[static_cast<std::size_t>(king)] | king_bit;
        king_zone[static_cast<std::size_t>(color_index)] =
            ring | (color_index == 0 ? ring << 8U : ring >> 8U);
    }
    std::array<int, 2> king_attack_units{};
    std::array<int, 2> king_attackers{};

    for (int color_index = 0; color_index < 2; ++color_index) {
        const Color color = static_cast<Color>(color_index);
        for (int type = 2; type <= 6; ++type) {
            const Piece piece = static_cast<Piece>((color == White ? 0 : 6) + type);
            std::uint64_t remaining = board.pieces(piece);
            while (remaining != 0) {
                const int square = static_cast<int>(std::countr_zero(remaining));
                remaining &= remaining - 1;
                const int file = square & 7;
                const std::size_t psq = static_cast<std::size_t>(color == White ? square ^ 56 : square);
                const PieceSquare& table = Psqt[static_cast<std::size_t>(type)];
                const int mg = MgValue[static_cast<std::size_t>(type)] + table.mg[psq];
                const int eg = EgValue[static_cast<std::size_t>(type)] + table.eg[psq];
                if (type == 3) ++bishops[static_cast<std::size_t>(color)];
                if (type == 6) king_square[static_cast<std::size_t>(color)] = square;
                phase += PhaseWeight[static_cast<std::size_t>(type)];
                add(color, mg, eg);

                if (type <= 5) {
                    const std::uint64_t attacks = attack_set(square, type);
                    const std::uint64_t own = color == White ? white_occupied : black_occupied;
                    const int moves = std::popcount(attacks & ~own);
                    const int mg_weight = type == 2 ? 4 : (type == 3 ? 5 : (type == 4 ? 2 : 1));
                    const int eg_weight = type == 2 ? 3 : (type == 3 ? 4 : (type == 4 ? 3 : 2));
                    add(color, moves * mg_weight, moves * eg_weight);
                    const std::size_t defender = static_cast<std::size_t>(opposite(color));
                    const int zone_hits = std::popcount(attacks & king_zone[defender]);
                    if (zone_hits > 0) {
                        ++king_attackers[defender];
                        king_attack_units[defender] += zone_hits * KingAttackWeight[static_cast<std::size_t>(type)];
                    }
                    if (type == 4 && pawns_by_file[static_cast<std::size_t>(color)][static_cast<std::size_t>(file)] == 0) {
                        const Color enemy = opposite(color);
                        const bool open = pawns_by_file[static_cast<std::size_t>(enemy)][static_cast<std::size_t>(file)] == 0;
                        add(color, open ? 20 : 10, open ? 12 : 6);
                    }
                }
            }
        }
    }

    for (int color_index = 0; color_index < 2; ++color_index) {
        const Color color = static_cast<Color>(color_index);
        if (bishops[static_cast<std::size_t>(color)] >= 2) add(color, 30, 45);

        const int king = king_square[static_cast<std::size_t>(color)];
        if (king >= 0) {
            const int king_file = king & 7;
            const int king_rank = king >> 3;
            const int direction = color == White ? 1 : -1;
            int shelter = 0;
            for (int file = std::max(0, king_file - 1); file <= std::min(7, king_file + 1); ++file) {
                for (int step = 1; step <= 2; ++step) {
                    const int rank = king_rank + direction * step;
                    if (rank < 0 || rank >= 8) continue;
                    const Piece expected = color == White ? WP : BP;
                    if (board.piece_at(rank * 8 + file) == expected) {
                        shelter += step == 1 ? 12 : 6;
                        break;
                    }
                }
            }
            add(color, shelter, 0);
        }
        if (king_attackers[static_cast<std::size_t>(color)] >= 2) {
            const int units = std::min(king_attack_units[static_cast<std::size_t>(color)], 99);
            add(color, -KingSafetyTable[static_cast<std::size_t>(units)], 0);
        }
    }

    phase = std::min(phase, MaxPhase);
    int score = (mg_score * phase + eg_score * (MaxPhase - phase)) / MaxPhase;
    score += board.side_to_move() == White ? 10 : -10;
    return board.side_to_move() == White ? score : -score;
}

int Searcher::evaluate_cached(const Board& board) {
    EvalEntry& entry = eval_cache_[eval_index(board.key())];
    if (entry.valid && entry.key == board.key()) return entry.score;
    PawnEntry& pawn_entry = pawn_cache_[pawn_index(board.pawn_key())];
    if (!pawn_entry.valid || pawn_entry.key != board.pawn_key()) pawn_entry = analyze_pawns(board);
    const int score = evaluate_with_pawns(board, pawn_entry);
    entry.key = board.key();
    entry.score = static_cast<std::int16_t>(score);
    entry.valid = true;
    return score;
}

std::uint64_t Searcher::elapsed_budget_ms() const {
    auto budget_start = start_;
    if (pondering_) {
        const std::int64_t hit_ns = ponder_hit_ns_.load(std::memory_order_relaxed);
        if (hit_ns == 0) return 0; // Opponent's clock is still running.
        budget_start = std::chrono::steady_clock::time_point(
            std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                std::chrono::nanoseconds(hit_ns)));
    }
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - budget_start).count();
    return elapsed > 0 ? static_cast<std::uint64_t>(elapsed) : 0U;
}

bool Searcher::should_stop() {
    if (stop_.load(std::memory_order_relaxed)) return true;
    if (node_limit_specified_ && nodes_ >= node_limit_) return true;
    if (time_limit_ms_ != 0 && (nodes_ & time_check_mask_) == 0U) {
        if (pondering_ && ponder_hit_ns_.load(std::memory_order_relaxed) == 0) return false;
        if (elapsed_budget_ms() >= time_limit_ms_) return true;
    }
    return false;
}

bool Searcher::abort_if_stopped() {
    if (!should_stop()) return false;
    aborted_ = true;
    return true;
}

int Searcher::move_score(const Board& board, const Move& move, const Move& tt_move,
                         const Move& counter_move, int ply, bool in_quiescence) const {
    if (same_move(move, tt_move)) return 2'000'000;
    if ((move.flags & Promotion) != 0U) {
        const int victim = move.is_capture()
            ? ((move.flags & EnPassant) != 0U ? 1 : piece_type(board.piece_at(move.to)))
            : 0;
        // Queen promotions are tactical; underpromotions are almost never best.
        if (move.promotion == 5) return 1'100'000 + victim * 16;
        return -2'000'000 + PieceValue[move.promotion] + victim * 16;
    }
    if (move.is_capture()) {
        const int victim = (move.flags & EnPassant) != 0U ? 1 : piece_type(board.piece_at(move.to));
        const int attacker = piece_type(board.piece_at(move.from));
        // Captures that lose material by static exchange are tried after the
        // quiet moves. Quiescence prunes them outright, so it skips the SEE.
        if (!in_quiescence && PieceValue[static_cast<std::size_t>(victim)] <
                                  PieceValue[static_cast<std::size_t>(attacker)] &&
            board.static_exchange(move) < 0) {
            return -1'000'000 + victim * 16 - attacker;
        }
        return 1'000'000 + victim * 16 - attacker;
    }
    const std::size_t index = static_cast<std::size_t>(std::min(ply, 127));
    if (same_move(move, killers_[index][0])) return 800'000;
    if (same_move(move, killers_[index][1])) return 700'000;
    if (same_move(move, counter_move)) return 600'000;
    return history_[static_cast<std::size_t>(board.side_to_move())][move.from][move.to];
}

void Searcher::order_moves(const Board& board, MoveList& moves, const Move& tt_move,
                           const Move& counter_move, int ply, bool in_quiescence) const {
    std::array<int, 256> scores;
    if (moves.size() > scores.size()) return;
    for (std::size_t i = 0; i < moves.size(); ++i) {
        scores[i] = move_score(board, moves[i], tt_move, counter_move, ply, in_quiescence);
    }
    for (std::size_t i = 1; i < moves.size(); ++i) {
        const Move move = moves[i];
        const int score = scores[i];
        std::size_t j = i;
        while (j > 0 && scores[j - 1] < score) {
            moves[j] = moves[j - 1];
            scores[j] = scores[j - 1];
            --j;
        }
        moves[j] = move;
        scores[j] = score;
    }
}

std::vector<Move> Searcher::extract_pv(Board board, int depth) const {
    std::vector<Move> pv;
    pv.reserve(static_cast<std::size_t>(depth));
    std::vector<std::uint64_t> seen;
    seen.reserve(static_cast<std::size_t>(depth));
    for (int ply = 0; ply < depth; ++ply) {
        if (std::find(seen.begin(), seen.end(), board.key()) != seen.end()) break;
        seen.push_back(board.key());
        const std::uint64_t key = tt_key(board);
        const TTEntry& entry = table_[tt_index(key)];
        if (entry.key != key || entry.move.from == entry.move.to) break;
        const auto legal = board.legal_moves();
        const auto found = std::find_if(legal.begin(), legal.end(), [&](const Move& move) {
            return same_move(move, entry.move);
        });
        if (found == legal.end()) break;
        pv.push_back(*found);
        Undo undo;
        (void)board.make_move(*found, undo);
        if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) break;
    }
    return pv;
}

int Searcher::quiescence(Board& board, int ply, int alpha, int beta) {
    if (abort_if_stopped()) return 0;
    if (ply >= 127) return evaluate_cached(board);
    seldepth_ = std::max(seldepth_, ply);
    ++nodes_;
    const bool checked = board.in_check(board.side_to_move());
    if (is_search_repetition(board, root_index_) || board.halfmove_clock() >= 100) {
        if (!checked || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
    if (board.is_insufficient_material()) return 0;
    alpha = std::max(alpha, -MateScore + ply);
    beta = std::min(beta, MateScore - ply - 1);
    if (alpha >= beta) return alpha;
    const int original_alpha = alpha;
    const std::uint64_t qkey = tt_key(board);
    TTEntry& qentry = table_[tt_index(qkey)];
    Move qtt_move{};
    const std::uint8_t qcontext = current_tt_context(board);
    if (qentry.key == qkey) {
        qtt_move = qentry.move;
        if (tt_depth(qentry) == 0 && tt_context(qentry) == qcontext) {
            const int tt_score = score_from_tt(qentry.score, ply);
            const Bound bound = tt_bound(qentry);
            if (bound == Exact) return tt_score;
            if (bound == Lower && tt_score >= beta) return tt_score;
            if (bound == Upper && tt_score <= alpha) return tt_score;
        }
    }
    const int stand_pat = evaluate_cached(board);
    if (!checked) {
        if (stand_pat >= beta && beta <= 0) return beta;
    }

    auto moves = board.legal_moves(!checked);
    if (checked && moves.empty()) return -MateScore + ply;
    if (!checked) {
        if (stand_pat >= beta) {
            if (moves.empty() && !board.has_legal_move()) return 0;
            return beta;
        }
        alpha = std::max(alpha, stand_pat);
        if (moves.empty()) {
            // A favorable stalemate can raise alpha from stand-pat even though
            // its exact game-theoretic score is zero.  We only need the more
            // expensive quiet-legal-move probe when zero might change the
            // window result: either the window straddles zero, or stand-pat
            // improved alpha above the caller's original lower bound.
            if ((original_alpha < 0 || alpha > original_alpha) &&
                !board.has_legal_move()) {
                return 0;
            }
            return alpha;
        }
    }
    order_moves(board, moves, qtt_move, Move{}, ply, true);
    Move best_move{};
    for (const Move move : moves) {
        if (!checked && (move.flags & Promotion) == 0U) {
            // Delta pruning: even winning the victim outright cannot reach alpha.
            const int victim = (move.flags & EnPassant) != 0U ? 1 : piece_type(board.piece_at(move.to));
            if (stand_pat + PieceValue[static_cast<std::size_t>(victim)] + 200 <= alpha) continue;
            // Captures that clearly lose material by static exchange are not
            // searched; near-equal trades such as bishop-for-knight remain.
            if (board.static_exchange(move) < -20) continue;
        }
        Undo undo;
        (void)board.make_move(move, undo);
        const int score = -quiescence(board, ply + 1, -beta, -alpha);
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score >= beta) {
            if (tt_depth(qentry) <= 0) {
                qentry.key = qkey;
                qentry.move = move;
                qentry.score = static_cast<std::int16_t>(std::clamp(normalized_score_for_tt(beta, ply), -32767, 32767));
                set_tt_meta(qentry, 0, Lower, qcontext);
            }
            return beta;
        }
        if (score > alpha) { alpha = score; best_move = move; }
    }
    if (tt_depth(qentry) <= 0) {
        qentry.key = qkey;
        qentry.move = best_move;
        qentry.score = static_cast<std::int16_t>(std::clamp(normalized_score_for_tt(alpha, ply), -32767, 32767));
        set_tt_meta(qentry, 0, alpha <= original_alpha ? Upper : Exact, qcontext);
    }
    return alpha;
}

int Searcher::alpha_beta(Board& board, int depth, int ply, int alpha, int beta,
                         bool allow_null, Move previous_move) {
    if (abort_if_stopped()) return 0;
    if (ply >= 127) return evaluate_cached(board);
    seldepth_ = std::max(seldepth_, ply);
    if (depth <= 0) return quiescence(board, ply, alpha, beta);
    ++nodes_;
    if (is_search_repetition(board, root_index_) || board.halfmove_clock() >= 100) {
        if (!board.in_check(board.side_to_move()) || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
    if (board.is_insufficient_material()) return 0;
    alpha = std::max(alpha, -MateScore + ply);
    beta = std::min(beta, MateScore - ply - 1);
    if (alpha >= beta) return alpha;
    const int original_alpha = alpha;
    const std::uint64_t key = tt_key(board);
    TTEntry& entry = table_[tt_index(key)];
    Move tt_move{};
    const std::uint8_t context = current_tt_context(board);
    if (entry.key == key) {
        tt_move = entry.move;
        if (ply > 0 && tt_depth(entry) >= depth && tt_context(entry) == context) {
            const int tt_score = score_from_tt(entry.score, ply);
            const Bound bound = tt_bound(entry);
            if (bound == Exact) return tt_score;
            if (bound == Lower && tt_score >= beta) return tt_score;
            if (bound == Upper && tt_score <= alpha) return tt_score;
        }
    }

    const bool root = ply == 0;
    const bool pv_node = beta - alpha > 1;
    const bool checked = board.in_check(board.side_to_move());
    const int static_eval = checked ? NoEval : evaluate_cached(board);
    eval_stack_[static_cast<std::size_t>(ply)] = static_eval;
    // The side to move is "improving" when its static evaluation is better than
    // two plies ago; pruning is more cautious when it is not.
    const bool improving = !checked &&
        (ply < 2 || eval_stack_[static_cast<std::size_t>(ply - 2)] == NoEval ||
         static_eval > eval_stack_[static_cast<std::size_t>(ply - 2)]);
    const bool mate_window = alpha <= -MateBound || beta >= MateBound;

    // Whole-node pruning is skipped without non-pawn material: pawn endings are
    // zugzwang-prone and the only realistic stalemate contexts, and neither
    // heuristic generates moves before claiming a bound.
    if (!pv_node && !checked && !mate_window && has_non_pawn_material(board, board.side_to_move())) {
        // Reverse futility pruning: the static evaluation is so far above beta
        // that a shallow search is very unlikely to fall below it.
        if (depth <= 8 && static_eval - (improving ? 55 : 80) * depth >= beta) {
            ++reverse_futility_cutoffs_;
            return beta;
        }
        // Null-move pruning: giving the opponent a free move still fails high.
        if (allow_null && depth >= 3 && static_eval >= beta) {
            ++null_tries_;
            NullUndo null_undo;
            board.make_null_move(null_undo);
            const int reduction = 3 + depth / 3 + std::min(3, (static_eval - beta) / 200);
            const int null_depth = std::max(0, depth - 1 - reduction);
            const int null_score = -alpha_beta(board, null_depth, ply + 1,
                                               -beta, -beta + 1, false, Move{});
            board.unmake_null_move(null_undo);
            if (aborted_) return 0;
            if (null_score >= beta) {
                if (depth < 10) {
                    ++null_cutoffs_;
                    return beta;
                }
                // Deep nodes verify the cutoff with a reduced regular search.
                const int verification = alpha_beta(board, depth - 1 - reduction, ply, alpha, beta,
                                                    false, previous_move);
                if (aborted_) return 0;
                if (verification >= beta) {
                    ++null_cutoffs_;
                    return beta;
                }
            }
        }
    }
    // Internal iterative reduction: without a hash move, a deep node is searched
    // one ply shallower; the re-search at the next iteration has a hash move.
    if (!root && depth >= 4 && tt_move.from == tt_move.to && !checked) --depth;

    auto moves = board.legal_moves();
    // Classify the actual chess position before restricting the root move set.
    if (moves.empty()) return checked ? -MateScore + ply : 0;
    if (root && root_restricted_) {
        std::size_t write = 0;
        for (const Move move : moves) {
            const bool allowed = std::any_of(root_moves_.begin(), root_moves_.end(),
                                             [&](const Move& candidate) { return same_move(move, candidate); });
            if (allowed) moves[write++] = move;
        }
        moves.resize(write);
        // An empty searchmoves intersection is a command restriction, not mate.
        if (moves.empty()) return 0;
    }
    const Move counter_move = previous_move.from == previous_move.to
        ? Move{} : countermoves_[previous_move.from][previous_move.to];
    order_moves(board, moves, tt_move, counter_move, ply, false);
    const std::size_t us = static_cast<std::size_t>(board.side_to_move());
    const std::size_t killer_index = static_cast<std::size_t>(std::min(ply, 127));
    Move best_move{};
    std::array<Move, 256> quiets_searched;
    std::size_t quiet_count = 0;
    int move_index = 0;
    // Quiet moves are pruned only after a move has been searched, never in PV
    // nodes, never in check, and never while the side to move is being mated.
    const bool prune_quiets = !pv_node && !checked && alpha > -MateBound;
    const int lmp_threshold = (3 + depth * depth) / (improving ? 1 : 2);
    const int futility_margin = 100 + 120 * depth;
    for (const Move move : moves) {
        const bool quiet = !move.is_capture() && (move.flags & Promotion) == 0U;
        const bool late_prunable = prune_quiets && quiet && move_index > 0;
        Undo undo;
        (void)board.make_move(move, undo);
        const bool gives_check = board.in_check(board.side_to_move());
        // Quiet non-checking moves are pruned when they are very late at shallow
        // depth (late-move pruning) or when the static evaluation is too far
        // below alpha for a quiet move to recover (futility pruning).
        if (late_prunable && !gives_check &&
            ((depth <= 8 && move_index >= lmp_threshold) ||
             (depth <= 6 && static_eval + futility_margin <= alpha))) {
            board.unmake_move(move, undo);
            ++move_index;
            continue;
        }
        // Check extension, bounded so perpetual-check lines cannot explode.
        const int new_depth = depth - 1 + ((gives_check && ply < 2 * root_depth_) ? 1 : 0);
        int score;
        if (move_index == 0) {
            score = -alpha_beta(board, new_depth, ply + 1, -beta, -alpha, true, move);
        } else {
            int reduction = 0;
            if (depth >= 3 && move_index >= (pv_node ? 3 : 2) && quiet && !checked && !gives_check) {
                reduction = Lmr.quiet[static_cast<std::size_t>(std::min(depth, 63))]
                                     [static_cast<std::size_t>(std::min(move_index, 63))];
                if (pv_node) --reduction;
                if (!improving) ++reduction;
                if (same_move(move, killers_[killer_index][0]) ||
                    same_move(move, killers_[killer_index][1]) || same_move(move, counter_move)) {
                    --reduction;
                }
                reduction -= std::clamp(history_[us][move.from][move.to] / 4096, -2, 2);
                reduction = std::clamp(reduction, 0, new_depth - 1);
            }
            score = -alpha_beta(board, new_depth - reduction, ply + 1, -alpha - 1, -alpha, true, move);
            if (reduction > 0 && score > alpha) {
                score = -alpha_beta(board, new_depth, ply + 1, -alpha - 1, -alpha, true, move);
            }
            if (pv_node && score > alpha && score < beta) {
                score = -alpha_beta(board, new_depth, ply + 1, -beta, -alpha, true, move);
            }
        }
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score > alpha) {
            alpha = score;
            best_move = move;
            if (alpha >= beta) {
                if (quiet) {
                    if (!same_move(killers_[killer_index][0], move)) {
                        killers_[killer_index][1] = killers_[killer_index][0];
                        killers_[killer_index][0] = move;
                    }
                    int& history = history_[us][move.from][move.to];
                    const int bonus = std::min(depth * depth, 400);
                    history += bonus - history * bonus / 16384;
                    for (std::size_t i = 0; i < quiet_count; ++i) {
                        const Move failed = quiets_searched[i];
                        int& failed_history = history_[us][failed.from][failed.to];
                        failed_history -= bonus + failed_history * bonus / 16384;
                    }
                    if (previous_move.from != previous_move.to) {
                        countermoves_[previous_move.from][previous_move.to] = move;
                    }
                }
                break;
            }
        }
        if (quiet && quiet_count < quiets_searched.size()) quiets_searched[quiet_count++] = move;
        ++move_index;
    }

    if (!aborted_ && root) root_best_move_ = best_move;
    if (!aborted_ && !(root && root_restricted_)) {
        // A fail-low has no best move; keep the previous hash move for ordering.
        if (best_move.from == best_move.to && entry.key == key) best_move = entry.move;
        entry.key = key;
        entry.move = best_move;
        entry.score = static_cast<std::int16_t>(std::clamp(normalized_score_for_tt(alpha, ply), -32767, 32767));
        set_tt_meta(entry, std::min(depth, 127),
                    alpha <= original_alpha ? Upper : (alpha >= beta ? Lower : Exact), context);
    }
    return alpha;
}

SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info) {
    for (auto& color_history : history_) {
        for (auto& row : color_history) {
            for (int& value : row) value /= 2;
        }
    }
    nodes_ = 0;
    seldepth_ = 0;
    root_depth_ = 0;
    root_index_ = board.key_history().empty() ? 0 : board.key_history().size() - 1;
    eval_stack_.fill(NoEval);
    pondering_ = limits.ponder;
    root_moves_ = limits.search_moves;
    root_restricted_ = limits.search_moves_specified;
    null_tries_ = 0;
    null_cutoffs_ = 0;
    reverse_futility_cutoffs_ = 0;
    node_limit_ = limits.nodes;
    node_limit_specified_ = limits.nodes_specified || limits.nodes != 0;
    const std::int64_t move_overhead_ms = std::max<std::int64_t>(0, limits.move_overhead_ms);
    if (limits.infinite) {
        time_limit_ms_ = 0;
    } else if (limits.movetime_ms >= 0) {
        const std::int64_t movetime_ms = limits.movetime_ms;
        time_limit_ms_ = static_cast<std::uint64_t>(
            std::max<std::int64_t>(1, movetime_ms - move_overhead_ms));
    } else if (limits.time_ms >= 0) {
        const std::int64_t time_ms = limits.time_ms;
        const std::int64_t moves_to_go = std::max<std::int64_t>(1, limits.moves_to_go);
        const std::int64_t increment_ms = std::max<std::int64_t>(0, limits.increment_ms);
        const std::int64_t share = time_ms / moves_to_go;
        const std::int64_t budget = std::min(time_ms / 2, share + increment_ms * 3 / 4);
        time_limit_ms_ = static_cast<std::uint64_t>(
            std::max<std::int64_t>(1, std::min(time_ms, budget) - move_overhead_ms));
    } else {
        time_limit_ms_ = 0;
    }
    // A fixed movetime is spent fully; a game clock stops starting new iterations
    // once half of the hard budget has elapsed, since the next iteration would
    // rarely finish before the hard limit anyway.
    soft_limit_ms_ = limits.time_ms >= 0 && limits.movetime_ms < 0 && !limits.infinite
        ? std::max<std::uint64_t>(1, time_limit_ms_ / 2) : time_limit_ms_;
    time_check_mask_ = time_limit_ms_ <= 10 ? 0U : (time_limit_ms_ <= 100 ? 31U : 255U);
    start_ = std::chrono::steady_clock::now();
    SearchInfo result;
    if (root_restricted_) {
        const auto legal_root = board.legal_moves();
        result.restricted_root_empty = !legal_root.empty() &&
            std::none_of(legal_root.begin(), legal_root.end(), [&](const Move& legal) {
                return std::any_of(root_moves_.begin(), root_moves_.end(),
                                   [&](const Move& requested) { return same_move(legal, requested); });
            });
        if (result.restricted_root_empty && emit_info) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info string searchmoves restriction has no legal root moves" << std::endl;
        }
    }
    const int mate_moves = std::clamp(limits.mate_moves, 0, 32);
    const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
    const int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);
    for (int depth = 1; depth <= max_depth; ++depth) {
        aborted_ = false;
        root_depth_ = depth;
        std::vector<Move> pv;
        int alpha = -Infinity;
        int beta = Infinity;
        int delta = 25;
        if (depth >= 4 && result.depth > 0 && std::abs(result.score) < MateBound) {
            alpha = std::max(-Infinity, result.score - delta);
            beta = std::min(Infinity, result.score + delta);
        }
        int score = 0;
        // Aspiration window: widen progressively around the previous score until
        // the result lands strictly inside the window.
        while (true) {
            root_best_move_ = Move{};
            score = alpha_beta(board, depth, 0, alpha, beta);
            if (aborted_) break;
            if (score > alpha && score < beta) break;
            if (should_stop()) {
                aborted_ = true;
                break;
            }
            if (std::abs(score) >= MateBound) {
                alpha = -Infinity;
                beta = Infinity;
            } else if (score <= alpha) {
                beta = (alpha + beta) / 2;
                alpha = std::max(-Infinity, score - delta);
            } else {
                beta = std::min(Infinity, score + delta);
            }
            delta += delta / 2;
        }
        if (aborted_) break;
        if (root_restricted_) {
            if (root_best_move_.from != root_best_move_.to) {
                const bool root_allowed = std::any_of(
                    root_moves_.begin(), root_moves_.end(),
                    [&](const Move& allowed) { return same_move(root_best_move_, allowed); });
                if (root_allowed) {
                    const auto legal = board.legal_moves();
                    const auto found = std::find_if(legal.begin(), legal.end(), [&](const Move& move) {
                        return same_move(move, root_best_move_);
                    });
                    if (found != legal.end()) {
                        pv.push_back(*found);
                        Board child = board;
                        Undo undo;
                        (void)child.make_move(*found, undo);
                        std::vector<Move> child_pv = extract_pv(child, depth - 1);
                        pv.insert(pv.end(), child_pv.begin(), child_pv.end());
                    }
                }
            }
        } else {
            const std::vector<Move> tt_pv = extract_pv(board, depth);
            if (!tt_pv.empty()) pv = tt_pv;
        }
        const Move previous_best = result.best_move;
        result.score = score;
        result.depth = depth;
        result.pv = pv;
        result.best_move = pv.empty() ? Move{} : pv.front();
        const bool best_changed = depth > 1 && !same_move(previous_best, result.best_move);
        result.nodes = nodes_;
        result.seldepth = seldepth_;
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        if (emit_info) {
            const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
            std::cout << "info depth " << depth << " score ";
            if (std::abs(score) > MateScore - 128) {
                const int mate = (MateScore - std::abs(score) + 1) / 2;
                std::cout << "mate " << (score >= 0 ? mate : -mate);
            } else {
                std::cout << "cp " << score;
            }
            const std::uint64_t nps = result.elapsed_ms > 0 ? nodes_ * 1000U / result.elapsed_ms : 0;
            std::cout << " seldepth " << seldepth_ << " nodes " << nodes_ << " nps " << nps
                      << " hashfull " << hashfull_permille() << " time " << result.elapsed_ms << " pv";
            for (const Move move : pv) std::cout << ' ' << Board::move_to_uci(move);
            std::cout << std::endl;
        }
        if (limits.mate_moves > 0 && std::abs(score) > MateScore - 128 &&
            MateScore - std::abs(score) <= mate_depth) break;
        if (should_stop()) break;
        if (soft_limit_ms_ != 0 && !(pondering_ && ponder_hit_ns_.load(std::memory_order_relaxed) == 0)) {
            // An unstable best move earns extra time, up to the hard limit.
            const std::uint64_t soft = best_changed
                ? std::min(time_limit_ms_, soft_limit_ms_ + soft_limit_ms_ / 2) : soft_limit_ms_;
            if (elapsed_budget_ms() >= soft) break;
        }
    }
    result.nodes = nodes_;
    result.seldepth = seldepth_;
    result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count());
    if (result.best_move.from == result.best_move.to) {
        auto moves = board.legal_moves();
        if (root_restricted_) {
            std::size_t write = 0;
            for (const Move move : moves) {
                const bool allowed = std::any_of(
                    root_moves_.begin(), root_moves_.end(),
                    [&](const Move& candidate) { return same_move(move, candidate); });
                if (allowed) moves[write++] = move;
            }
            moves.resize(write);
        }
        if (!moves.empty()) result.best_move = moves.front();
    }
    return result;
}

} // namespace forge
