#pragma once

#include "forge/board.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

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

[[nodiscard]] constexpr int feature_index(Color perspective, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int relative_square = perspective == White ? square : square ^ 56;
    return (relative_color * 6 + type) * 64 + relative_square;
}

struct Accumulator {
#if FORGE_SPD_NNUE_ZMM
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

// Empty path, or "<empty>", restores the compiled-in net. A FORGENET file is
// 8-byte magic, uint32 version 1, uint32 hidden size, then little-endian
// int16 W1, B1, W2 and one int16 B2. A wrong magic, version or size leaves
// the current net in place and writes the reason into error.
[[nodiscard]] bool load_file(std::string_view path, std::string& error);

void refresh(const Board& board, Accumulator& accumulator);
void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty);
// Side-to-move evaluation in centipawns.
[[nodiscard]] int evaluate(const Board& board, const Accumulator& accumulator);

// Piece changes implied by a move about to be played on `board`.
[[nodiscard]] DirtyPieces dirty_pieces(const Board& board, const Move& move);

} // namespace forge::nnue
