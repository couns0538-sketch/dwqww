#pragma once

// R10: inference for Stockfish-format .nnue nets from the nnue-pytorch trainer of R6 (b2614500) with the K32H3^
// feature set, the trainer's HalfKAv2_hm family member: 32 horizontally mirrored king buckets x 3 material states
// x 704 piece-square planes (both kings share plane 10), an int8 feature transformer with int16 biases, a pairwise
// product activation, and 32 layer stacks (piece-count bucket x 4 + queen bucket) with linear + squared hidden
// activations and a skip output. Written from the trainer's export format and quantization rules; see
// opus_r10/IDEA_SOURCE.md. Off unless the UCI option EvalFileHalfKA names a net that loaded.

#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace forge::halfka {

constexpr int NumKingBuckets = 32;
constexpr int NumStates = 3;
constexpr int NumBuckets = NumKingBuckets * NumStates;    // 96 feature buckets per perspective
constexpr int PlanesPerBucket = 11 * 64;                  // 704
constexpr int NumFeatures = NumBuckets * PlanesPerBucket; // 67,584
constexpr int NumStacks = 32;
constexpr int MaxL1 = 4096;
constexpr int MaxL2 = 64;
constexpr int MaxL3 = 64;
constexpr std::uint32_t FileVersion = 0x6A448AFAU;
constexpr std::uint32_t FeatureHash = 0xAB005CEFU;        // K32H3

// Loads a net (replacing the current one); on failure the old state is kept and `error` says why.
[[nodiscard]] bool load(const std::string& path, std::string& error);
void unload();
[[nodiscard]] bool active();
[[nodiscard]] int l1();
[[nodiscard]] std::string description();   // "<file>: L1 x L2 x L3, hash ..."

// Feature bucket of a perspective: state * 32 + king bucket (state 2 = the opponent has a queen, 1 = otherwise any
// rook or queen on the board, 0 = none).
[[nodiscard]] int feature_bucket(const Board& board, Color perspective);
// Index of one piece's feature for a perspective whose king is on `king_square` (unoriented) and whose bucket is
// `bucket`.
[[nodiscard]] int feature_index(Color perspective, Piece piece, int square, int king_square, int bucket);
// Layer stack: (pieces - 1) / 4 * 4 + 2 * (side to move has a queen) + (the other side has a queen).
[[nodiscard]] int stack_index(const Board& board);

// Accumulator rows (int16, l1() values) of one perspective.
void refresh(const Board& board, Color perspective, std::int16_t* out);
// child = parent - removed + added features of one ply's `dirty` changes, in the bucket/orientation given (the
// caller makes sure it is the same for both ends of the path); parent may equal child (in place).
void apply(const std::int16_t* parent, std::int16_t* child, Color perspective, int king_square, int bucket,
           const nnue::DirtyPieces& dirty);

// Raw network output (the trainer's integer output value; centipawns * 16) and the evaluation in centipawns
// (raw / 16, truncated), side to move's view.
[[nodiscard]] std::int64_t evaluate_raw(const Board& board, const std::int16_t* white, const std::int16_t* black);
[[nodiscard]] int evaluate(const Board& board, const std::int16_t* white, const std::int16_t* black);

// Test hooks: force the scalar kernels (false = AVX2 when compiled in), and evaluate a board from scratch.
void set_force_scalar(bool on);
[[nodiscard]] bool simd_compiled();
[[nodiscard]] std::int64_t evaluate_fresh_raw(const Board& board);

// Per-worker accumulator storage, indexed like the search stack; valid flags and the (king square, state) each row
// was built for, so a descendant can be updated incrementally only from an ancestor with the same orientation.
class AccumulatorStack {
public:
    void ensure(int entries);   // (re)allocates for the loaded net's L1; invalidates everything
    void invalidate_all();
    [[nodiscard]] std::int16_t* row(int entry, Color c) { return data_.data() + (static_cast<std::size_t>(entry) * 2 + c) * stride_; }
    bool valid[2][1024]{};
    int king[2][1024]{};
    int bucket[2][1024]{};
    [[nodiscard]] int l1() const { return l1_; }

private:
    std::vector<std::int16_t> data_;
    std::size_t stride_ = 0;
    int l1_ = 0;
    int entries_ = 0;
};

} // namespace forge::halfka
