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

[[nodiscard]] constexpr int feature_index(Color perspective, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int relative_square = perspective == White ? square : square ^ 56;
    return (relative_color * 6 + type) * 64 + relative_square;
}

struct Accumulator {
#if !FORGE_NNUE_O2
    alignas(32) std::array<std::array<float, HiddenSize>, 2> values{};
#else  // FORGE_NNUE_O2
    // 64-byte aligned: every 512-bit (or 256-bit) access stays inside one cache line.
    alignas(64) std::array<std::array<float, HiddenSize>, 2> values{};
#endif // FORGE_NNUE_O2
#if FORGE_NNUE_INT16
    // NnueInt16 (OFF by default): int32 accumulators over the include file's
    // int16 weights. Separate storage keeps the float representation and
    // arithmetic of the OFF path intact; `integer` records which of the two
    // this accumulator holds and is inherited by every incremental child.
    alignas(32) std::array<std::array<std::int32_t, HiddenSize>, 2> integer_values{};
#endif // FORGE_NNUE_INT16
    bool valid = false;
#if FORGE_NNUE_INT16
    bool integer = false;
#endif // FORGE_NNUE_INT16
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

#if FORGE_NNUE_INT16
// NnueInt16 (UCI option, OFF by default): integer inference with the int16
// weights of the include file and int32 accumulators (the weights are int16,
// the accumulators are not). int16_available() is false when the compiled-in
// network fails the representability checks; set_int16(true) then leaves float
// inference active and returns false. The mode only affects refresh(): update()
// follows the parent's representation and evaluate() the accumulator's, so a
// mode change takes effect at the next root refresh (the next search).
// R3 stack: compiled only with the build switch FORGE_NNUE_INT16 (default off;
// the switch-off build is the previous stack binary). It applies to the
// compiled-in network only; a v2 net (forge/nnue_v2.hpp) keeps its float path.
[[nodiscard]] bool int16_available();
[[nodiscard]] bool int16_active();
[[nodiscard]] bool set_int16(bool requested);
#endif // FORGE_NNUE_INT16

#if FORGE_NNUE_O2
// The float kernels compiled into this O2 build, e.g. "accumulator avx512,
// output avx2" (R5B; the UCI layer prints it as an info string at "uci").
[[nodiscard]] const char* kernel_name();
#endif // FORGE_NNUE_O2

void refresh(const Board& board, Accumulator& accumulator);
void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty);
// Side-to-move evaluation in centipawns.
[[nodiscard]] int evaluate(const Board& board, const Accumulator& accumulator);

// Piece changes implied by a move about to be played on `board`.
[[nodiscard]] DirtyPieces dirty_pieces(const Board& board, const Move& move);

} // namespace forge::nnue
