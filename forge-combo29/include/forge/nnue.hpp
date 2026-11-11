#pragma once

#include "forge/board.hpp"

#include <array>
#include <cstdint>

namespace forge::nnue {

// Architecture: for each colour's perspective, 768 piece-square inputs feed a
// HiddenSize accumulator (incrementally updated); SCReLU of the side-to-move
// and opponent accumulators is combined by a single linear output. The shipped
// network (src/nnue_weights.inc) is a residual correction added to the
// hand-crafted evaluation; see nnue::residual().
constexpr int InputCount = 768;
#ifndef FORGE_NNUE_HIDDEN
#define FORGE_NNUE_HIDDEN 128
#endif
constexpr int HiddenSize = FORGE_NNUE_HIDDEN;
constexpr float WeightScale = 4096.0F;   // quantisation of w1 / b1 in the include file
constexpr float OutputScale = 4096.0F;   // quantisation of w2 / b2
constexpr float SigmoidK = 2.25F;        // network output is in sigmoid units of K/400 per centipawn

// Build switch (default 0 = the lock code): 1 = the output layer runs one
// AVX-512 register of 16 lanes per 16 hidden units (lane j = h mod 16, the
// same per-lane order and the same final reduction as the 16-lane design in
// src/nnue.cpp), with separate multiply and add. Needs __AVX512F__.
#ifndef FORGE_SPD_NNUE_ZMM
#define FORGE_SPD_NNUE_ZMM 0
#endif

// Build switch (default 0 = the lock code; nothing of it is compiled): 1 adds
// the int8 inference path behind the UCI option NnueInt8Vnni (default 0 = the
// float path). Scheme and bounds: opus_nnue_int8_vnni/QUANT_SCHEME.md, BOUNDS.md.
#ifndef FORGE_NNUE_INT8_VNNI
#define FORGE_NNUE_INT8_VNNI 0
#endif

// JOB D build switches (fair_eval/build_fair.ps1). All default 0 = the lock code, nothing of them compiled.
//   FORGE_NNUE_INT8_DEFAULT 1  the int8 path is on at start (the UCI option's default follows it)
//   FORGE_NNUE_V2 1            compiles the v2 net path (UCI EvalFileV2, forge/nnue_v2.hpp)
//   FORGE_NNUE_V2_HOT 1        the v2 evaluation is this build's main path: no cold section / noinline / unlikely
//   FORGE_FAIR_DIAG 1          diagnostic UCI commands evalfens / evalbench (never in a measured exe)
#ifndef FORGE_NNUE_INT8_DEFAULT
#define FORGE_NNUE_INT8_DEFAULT 0
#endif
#ifndef FORGE_NNUE_V2
#define FORGE_NNUE_V2 0
#endif
#ifndef FORGE_NNUE_V2_HOT
#define FORGE_NNUE_V2_HOT 0
#endif
//   FORGE_NNUE_V2_FAST         bit mask, 0 = the v2 code as ported. Every bit keeps the evaluation bit-identical.
//                              1 = 512-bit output kernel (needs FORGE_SPD_NNUE_ZMM and AVX-512F)
//                              2 = both perspectives of a non-king move updated in one fused pass (as nnue::update)
//                              4 = a cached refresh that would apply more columns than a refresh from scratch
//                                  starts from the bias instead
#ifndef FORGE_NNUE_V2_FAST
#define FORGE_NNUE_V2_FAST 0
#endif
#ifndef FORGE_FAIR_DIAG
#define FORGE_FAIR_DIAG 0
#endif

[[nodiscard]] constexpr int feature_index(Color perspective, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int relative_square = perspective == White ? square : square ^ 56;
    return (relative_color * 6 + type) * 64 + relative_square;
}

struct Accumulator {
#if FORGE_NNUE_INT8_VNNI
    // NnueInt8Vnni=1 keeps int16 values (1/256 units) in the same storage; the
    // float array stays the first member, so size, alignment and the float path
    // are unchanged. Each mode reads only what it wrote (root refresh per search).
    union {
        alignas(64) std::array<std::array<float, HiddenSize>, 2> values{};
        std::array<std::array<std::int16_t, HiddenSize>, 2> ivalues;
    };
#elif FORGE_SPD_NNUE_ZMM
    // 64-byte alignment: the output kernel loads whole 512-bit registers.
    alignas(64) std::array<std::array<float, HiddenSize>, 2> values{};
#else
    alignas(32) std::array<std::array<float, HiddenSize>, 2> values{};
#endif
    bool valid = false;
};

struct PieceChange {
    Piece piece = Empty;
    std::uint8_t square = 0;
    bool add = false;
};

struct DirtyPieces {
    std::array<PieceChange, 4> changes{};
    int count = 0;
    void remove(Piece piece, int square) { changes[static_cast<std::size_t>(count++)] = {piece, static_cast<std::uint8_t>(square), false}; }
    void add(Piece piece, int square) { changes[static_cast<std::size_t>(count++)] = {piece, static_cast<std::uint8_t>(square), true}; }
};

// Whether a network is compiled into this binary.
[[nodiscard]] bool available();
// Whether the compiled-in network is a residual correction that the engine
// adds to the hand-crafted evaluation (false when no network is compiled in).
[[nodiscard]] bool residual();
// Runtime switch (UCI option); only effective when available().
extern bool enabled;
#if FORGE_NNUE_INT8_VNNI
// Runtime switch of the int8 path (UCI NnueInt8Vnni; false = the float path).
extern bool int8_vnni;
// Scalar int8 reference of evaluate() for an accumulator built with int8_vnni
// set, and the int32 L1 sums behind it (scalar reference and the used kernel).
[[nodiscard]] int evaluate_int8_scalar(const Board& board, const Accumulator& accumulator);
[[nodiscard]] std::int32_t int8_l1_sum_scalar(const Board& board, const Accumulator& accumulator);
[[nodiscard]] std::int32_t int8_l1_sum(const Board& board, const Accumulator& accumulator);
#endif

void refresh(const Board& board, Accumulator& accumulator);
void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty);
// Side-to-move evaluation in centipawns.
[[nodiscard]] int evaluate(const Board& board, const Accumulator& accumulator);

// Piece changes implied by a move about to be played on `board`.
[[nodiscard]] DirtyPieces dirty_pieces(const Board& board, const Move& move);

} // namespace forge::nnue
