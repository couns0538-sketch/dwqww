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
    alignas(32) std::array<std::array<float, HiddenSize>, 2> values{};
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

void refresh(const Board& board, Accumulator& accumulator);
void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty);
// Side-to-move evaluation in centipawns.
[[nodiscard]] int evaluate(const Board& board, const Accumulator& accumulator);

// Piece changes implied by a move about to be played on `board`.
[[nodiscard]] DirtyPieces dirty_pieces(const Board& board, const Move& move);

} // namespace forge::nnue
