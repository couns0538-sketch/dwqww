#pragma once

// NNUE v3 (job FB1): king-bucketed HalfKA inputs, a wider hidden layer with
// SCReLU, piece-count output buckets and int16 inference, loaded from a file at
// run time. Nothing here runs unless UCI NNUEArch is true and a v3 net is
// loaded with NNUEArchFile; with the option off the compiled-in network
// (forge/nnue.hpp) evaluates exactly as before.
//
// Feature of piece `pc` on `square` for perspective p (own king on `ksq`):
//   r      = p == White ? square : square ^ 56       (rank flip, as forge/nnue.hpp)
//   kr     = p == White ? ksq : ksq ^ 56
//   flip   = (mirror flag && file_of(kr) >= 4) ? 7 : 0   (own king on files e-h)
//   bucket = king_bucket_map[kr]                     (64 entries, indexed before mirroring)
//   index  = bucket * 768 + ((colour(pc) == p ? 0 : 1) * 6 + type(pc) - 1) * 64 + (r ^ flip)
// The 768 inputs per bucket include both kings (HalfKA). With one bucket and
// no mirroring this is nnue::feature_index().
//
// Quantisation (fixed by the engine, checked at load time):
//   accumulator = b1 + sum w1[feature]        int16, scale QA = 255 (1.0 == 255)
//   a = clamp(accumulator, 0, QA)             SCReLU input
//   sum = sum_h a_us[h]^2 * w2[ob][h] + a_them[h]^2 * w2[ob][H + h]      (int64)
//   out = sum / QA + b2[ob]                   units QA * QB, C++ truncating division
//   cp  = out * eval_scale / (QA * QB)        truncating division, then clamp +-30000
// Bounds that make the AVX2 kernel exact (int32 partial sums per lane, int64
// reduction) and the accumulators overflow-free: |w2| <= 127, hidden <= 1024,
// max|b1| + 32 * max|w1| <= 32767. The loader rejects nets outside them.
//
// Incremental evaluation (M2): one accumulator per ply in a per-worker stack.
// A ply whose accumulator is stale is rebuilt from the nearest valid ancestor
// by replaying the recorded piece changes; a perspective whose king key
// (bucket, flip) changed is refreshed through the per-worker cache, which
// holds for every (perspective, bucket, flip) the accumulator and the piece
// bitboards it was last refreshed with, so only the difference is applied.
// For an intermediate ply the piece bitboards are reconstructed from the
// current board by undoing the later plies' recorded changes.
//
// File format v3 (little-endian), written by tools/nnue/fable_nnue_v3.py:
//   0   char[8] "FORGENN3"      8  u32 version = 3        12 u32 header_bytes = 192
//   16  u32 inputs = 768        20 u32 hidden (32..1024, multiple of 32)
//   24  u32 king_buckets (1-32) 28 u32 output_buckets (1-16)
//   32  u32 flags (bit0 residual, bit1 mirror)
//   36  i32 qa = 255            40 i32 qb = 64           44 i32 eval_scale (1..10000)
//   48  u8 king_bucket_map[64]  112 u8 output_bucket_map[33] (index = min(pieces, 32))
//   145 u8 reserved[47] = 0
//   192 i16 w1[king_buckets][768][hidden], i16 b1[hidden], i16 w2[output_buckets][2*hidden],
//       i32 b2[output_buckets], then u64 FNV-1a 64 of every preceding byte.

#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace forge::nnue::v3 {

constexpr int InputsPerBucket = 768;
constexpr int MaxKingBuckets = 32;
constexpr int MaxOutputBuckets = 16;
constexpr int MinHidden = 32;
constexpr int MaxHidden = 1024;
constexpr int HeaderBytes = 192;
constexpr int QA = 255;
constexpr int QB = 64;
constexpr int MaxW2 = 127;
constexpr int MaxPieces = 32;
constexpr int MaxEvalScale = 10000;
constexpr std::uint32_t FlagResidual = 1U;
constexpr std::uint32_t FlagMirror = 2U;

struct KingKey {
    std::uint8_t bucket = 0;
    std::uint8_t flip = 0;   // 0, or 7 when the perspective's king stands on files e-h of a mirrored net
    [[nodiscard]] bool operator==(const KingKey&) const = default;
};

// 64-byte aligned int16 array.
class AlignedInt16 {
public:
    AlignedInt16() = default;
    AlignedInt16(const AlignedInt16&) = delete;
    AlignedInt16& operator=(const AlignedInt16&) = delete;
    ~AlignedInt16();
    void allocate(std::size_t count);
    [[nodiscard]] std::int16_t* data() const { return data_; }
    [[nodiscard]] std::size_t size() const { return size_; }

private:
    void release();
    std::int16_t* data_ = nullptr;
    std::size_t size_ = 0;
};

struct Net {
    std::string path;
    int hidden = 0;
    int king_buckets = 1;
    int output_buckets = 1;
    int eval_scale = 400;
    bool mirror = false;
    bool residual = false;
    std::uint64_t checksum = 0;
    std::uint64_t generation = 0;    // increases with every successful load (cache identity)
    std::array<std::uint8_t, 64> king_map{};
    std::array<std::uint8_t, 33> output_map{};
    AlignedInt16 w1;                 // [king_buckets][InputsPerBucket][hidden]
    AlignedInt16 b1;                 // [hidden]
    AlignedInt16 w2;                 // [output_buckets][2 * hidden]
    std::vector<std::int32_t> b2;    // [output_buckets]
    int max_abs_w1 = 0;
    int max_abs_b1 = 0;
    int max_abs_w2 = 0;
};

struct Accumulator {
    alignas(64) std::array<std::array<std::int16_t, MaxHidden>, 2> values{};
    std::array<KingKey, 2> keys{};
    std::array<std::uint8_t, 2> king_sq{};
    bool valid = false;
};

// Piece bitboards indexed by Piece code (index 0 unused).
using Pieces = std::array<Bitboard, 13>;

// Per-worker accumulator cache: for each (perspective, bucket, flip) the
// accumulator of the last piece placement refreshed under that key.
struct RefreshCache {
    struct Entry {
        alignas(64) std::array<std::int16_t, MaxHidden> values{};
        Pieces pieces{};
    };
    std::vector<Entry> entries;   // index ((perspective * king_buckets + bucket) * 2 + (flip != 0))
    std::uint64_t generation = 0;
    std::uint64_t refreshes = 0;  // statistics (tests)
    std::uint64_t columns = 0;
};

// Per-worker state: one accumulator per stack index (ply + 4) and the cache.
struct WorkerState {
    std::vector<Accumulator> stack;
    RefreshCache cache;
    std::uint64_t generation = 0;
    void invalidate() { for (Accumulator& acc : stack) acc.valid = false; }
};

// ---- loading and selection (must not run during a search) ----
// Loads a v3 file. On failure nothing stays loaded (no silent fallback) and
// *error names the reason.
[[nodiscard]] bool load(const std::string& path, std::string* error);
void unload();
[[nodiscard]] const Net* loaded();
[[nodiscard]] std::string describe(const Net& net);
// UCI NNUEArch request; the v3 path evaluates only when requested and a net is loaded.
extern bool requested;
[[nodiscard]] inline bool active() { return requested && loaded() != nullptr; }
// Non-empty when NNUEArch is requested but no v3 net is usable (the fail-loud rule).
[[nodiscard]] std::string problem();
void set_problem(const std::string& text);
// Kernels: the search uses the best one compiled in (AVX-512 BW, else AVX2, else scalar); the others stay
// available for the equality tests (scalar == AVX2 == AVX-512).
enum class Kernel { Scalar, Avx2, Avx512 };
[[nodiscard]] const char* kernel_name();
[[nodiscard]] const char* kernel_name(Kernel kernel);
[[nodiscard]] Kernel best_kernel();
[[nodiscard]] bool kernel_available(Kernel kernel);

// ---- feature set ----
[[nodiscard]] KingKey king_key(const Net& net, Color perspective, int king_square);
[[nodiscard]] int feature_index(KingKey key, Color perspective, Piece piece, int square);
[[nodiscard]] int output_bucket(const Net& net, const Board& board);
[[nodiscard]] inline const std::int16_t* column(const Net& net, int feature) {
    return net.w1.data() + static_cast<std::size_t>(feature) * static_cast<std::size_t>(net.hidden);
}
[[nodiscard]] Pieces pieces_of(const Board& board);

// ---- scalar reference path (M1; the oracle for the tests and tools) ----
void refresh_perspective(const Net& net, const Board& board, Color perspective, Accumulator& accumulator);
void refresh(const Net& net, const Board& board, Accumulator& accumulator);
[[nodiscard]] std::int64_t output_sum_scalar(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket);
[[nodiscard]] int finish(const Net& net, std::int64_t sum, int bucket);
// Fresh accumulators + scalar output.
[[nodiscard]] int evaluate_reference(const Net& net, const Board& board);

// ---- fast path (M2): kernels, cache, incremental update ----
// Output sum with the best compiled kernel; equals output_sum_scalar.
[[nodiscard]] std::int64_t output_sum(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket);
[[nodiscard]] std::int64_t output_sum_with(Kernel kernel, const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket);
void add_column_with(Kernel kernel, std::int16_t* acc, const std::int16_t* col, int hidden, bool add);
void apply_changes_with(Kernel kernel, const Net& net, const std::int16_t* source, std::int16_t* destination, KingKey key,
                        Color perspective, const DirtyPieces& dirty);
// Side-to-move network output in centipawns from a valid accumulator (fast kernel).
[[nodiscard]] int evaluate(const Net& net, const Board& board, const Accumulator& accumulator);
// Prepares `state` for `net` (stack size, cache entries); cheap when already prepared.
void prepare(const Net& net, WorkerState& state, int stack_size);
// destination = source with the recorded changes applied under `key` (both arrays hold `hidden` values).
void apply_changes(const Net& net, const std::int16_t* source, std::int16_t* destination, KingKey key, Color perspective,
                   const DirtyPieces& dirty);
// Accumulator of `perspective` for the placement `pieces` (own king on `king_square`), through the cache.
void refresh_from_pieces(const Net& net, RefreshCache& cache, const Pieces& pieces, Color perspective, int king_square,
                         std::int16_t* destination);
// Both perspectives of `board` through the cache; marks the accumulator valid.
void refresh_cached(const Net& net, RefreshCache& cache, const Board& board, Accumulator& accumulator);
// Rebuilds state.stack[k] from state.stack[k - 1] (valid) with dirty_of(k); `board` is the position at
// stack index `top` (>= k) and dirty_of(j) the changes that led to index j, for j in (k, top].
template <class DirtyOf>
void replay_ply(const Net& net, WorkerState& state, int k, const Board& board, int top, DirtyOf&& dirty_of) {
    const Accumulator& parent = state.stack[static_cast<std::size_t>(k - 1)];
    Accumulator& child = state.stack[static_cast<std::size_t>(k)];
    const DirtyPieces& dirty = dirty_of(k);
    for (const Color p : {White, Black}) {
        const auto pi = static_cast<std::size_t>(p);
        int king_square = parent.king_sq[pi];
        for (int i = 0; i < dirty.count; ++i) {
            const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
            if (change.add && change.piece == make_piece(p, King)) king_square = change.square;
        }
        const KingKey key = king_key(net, p, king_square);
        child.king_sq[pi] = static_cast<std::uint8_t>(king_square);
        child.keys[pi] = key;
        if (key == parent.keys[pi]) {
            apply_changes(net, parent.values[pi].data(), child.values[pi].data(), key, p, dirty);
        } else {
            // The king changed bucket or side: rebuild this perspective from the
            // placement at index k, reconstructed by undoing the later plies.
            Pieces pieces = pieces_of(board);
            for (int j = top; j > k; --j) {
                const DirtyPieces& later = dirty_of(j);
                for (int i = 0; i < later.count; ++i) {
                    const PieceChange& change = later.changes[static_cast<std::size_t>(i)];
                    if (change.add) pieces[static_cast<std::size_t>(change.piece)] &= ~square_bb(change.square);
                    else pieces[static_cast<std::size_t>(change.piece)] |= square_bb(change.square);
                }
            }
            refresh_from_pieces(net, state.cache, pieces, p, king_square, child.values[pi].data());
        }
    }
    child.valid = true;
}
// Makes state.stack[index] valid for `board` (the position at that index): walks back to the nearest
// valid ancestor (index >= 4 is the search root) and replays, or refreshes through the cache.
template <class DirtyOf>
void make_valid(const Net& net, WorkerState& state, int index, const Board& board, DirtyOf&& dirty_of) {
    if (state.stack[static_cast<std::size_t>(index)].valid) return;
    int ancestor = index - 1;
    while (ancestor >= 4 && !state.stack[static_cast<std::size_t>(ancestor)].valid) --ancestor;
    if (ancestor < 4) {
        refresh_cached(net, state.cache, board, state.stack[static_cast<std::size_t>(index)]);
        return;
    }
    for (int k = ancestor + 1; k <= index; ++k) replay_ply(net, state, k, board, index, dirty_of);
}

// ---- file helpers shared with the tools ----
[[nodiscard]] std::uint64_t fnv1a64(const std::uint8_t* data, std::size_t size, std::uint64_t hash = 14695981039346656037ULL);
[[nodiscard]] std::size_t file_size_for(int hidden, int king_buckets, int output_buckets);

} // namespace forge::nnue::v3
