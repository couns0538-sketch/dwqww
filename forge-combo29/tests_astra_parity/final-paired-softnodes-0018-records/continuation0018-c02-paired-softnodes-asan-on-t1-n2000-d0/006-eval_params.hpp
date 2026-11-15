#pragma once

#include "forge/eval.hpp"

#include <array>

namespace forge::params {

// Every tunable evaluation term has an index into one flat parameter table.
// The layout is shared by the evaluator and the Texel tuner.
enum Index : int {
    Psqt = 0,                              // 6 piece types x 64 squares, white-relative
    KnightMobility = Psqt + 6 * 64,        // 9
    BishopMobility = KnightMobility + 9,   // 14
    RookMobility = BishopMobility + 14,    // 15
    QueenMobility = RookMobility + 15,     // 28
    BishopPair = QueenMobility + 28,
    RookOpenFile,
    RookSemiOpenFile,
    RookOnSeventh,
    KnightOutpost,
    BishopOutpost,
    MinorBehindPawn,
    BishopPawnsSameColor,
    QueenEarlyDevelopment,
    Tempo,
    PawnIsolated,
    PawnDoubled,
    PawnBackward,
    PawnConnected,                         // 8, by relative rank
    PawnPhalanx = PawnConnected + 8,
    PawnDoubleSupport,
    PassedRank,                            // 8, by relative rank
    PassedBlocked = PassedRank + 8,
    PassedUnstoppablePath,
    PassedSafePush,
    PassedEnemyKingDistance,
    PassedOwnKingDistance,
    ThreatByMinor,                         // 7, by attacked piece type
    ThreatByRook = ThreatByMinor + 7,      // 7
    ThreatByKing = ThreatByRook + 7,
    ThreatByPawn,
    ThreatByPawnPush,
    HangingPiece,
    RestrictedPiece,
    ShelterDistance,                       // 4: missing, then rank distance 1..3
    StormDistance = ShelterDistance + 4,   // 4: unused, then rank distance 1..3
    KingFileOpen = StormDistance + 4,
    KingDanger,                            // 100, by attack units
    KnightPawnAdjust = KingDanger + 100,   // 9, by own pawn count
    RookPawnAdjust = KnightPawnAdjust + 9, // 9, by own pawn count
    RookBehindOwnPasser = RookPawnAdjust + 9,
    RookBehindEnemyPasser,
    Space,                                 // per safe central square, scaled by piece count
    BishopLongDiagonal,
    WeakQueen,
    WeakUnopposedPawn,
    KingPawnDistance,                      // per square of distance to the nearest own pawn
    Count
};

using Table = std::array<Score, Count>;

// Live parameter table used by the evaluator. Tools may modify it before
// evaluating; the engine never writes to it.
extern Table table;

[[nodiscard]] Table defaults();
[[nodiscard]] const char* name(int index);

// Integer weights composing the king-danger index; adjustable by tools.
struct KingSafetyWeights {
    int knight = 2;
    int bishop = 2;
    int rook = 3;
    int queen = 5;
    int weak_square = 2;
    int rook_check = 6;
    int bishop_check = 4;
    int knight_check = 5;
    int queen_check = 5;
    int shelter_divisor = 4;
};
extern KingSafetyWeights king_safety;

} // namespace forge::params

namespace forge {

// Linear decomposition of one evaluation: coefficient[i] is the number of
// times parameter i applied for White minus the number of times for Black.
struct EvalTrace {
    std::array<std::int16_t, params::Count> coefficients{};
    int phase = 0;
    int scale = 64;
    Color side_to_move = White;
    int white_eval = 0;
};

// Evaluation with a full coefficient trace, from White's point of view.
[[nodiscard]] int evaluate_traced(const Board& board, EvalTrace& trace);

} // namespace forge
