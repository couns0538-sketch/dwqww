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
    bool valid = false;
};

// Per-worker state (M2 adds the king-bucket refresh cache): one accumulator per ply.
struct WorkerState {
    std::vector<Accumulator> stack;
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

// ---- feature set ----
[[nodiscard]] KingKey king_key(const Net& net, Color perspective, int king_square);
[[nodiscard]] int feature_index(KingKey key, Color perspective, Piece piece, int square);
[[nodiscard]] int output_bucket(const Net& net, const Board& board);
[[nodiscard]] inline const std::int16_t* column(const Net& net, int feature) {
    return net.w1.data() + static_cast<std::size_t>(feature) * static_cast<std::size_t>(net.hidden);
}

// ---- scalar reference path (M1) ----
void refresh_perspective(const Net& net, const Board& board, Color perspective, Accumulator& accumulator);
void refresh(const Net& net, const Board& board, Accumulator& accumulator);
// Output sum of the SCReLU layer (see the header comment), scalar reference.
[[nodiscard]] std::int64_t output_sum_scalar(const Net& net, const std::int16_t* ours, const std::int16_t* theirs, int bucket);
[[nodiscard]] int finish(const Net& net, std::int64_t sum, int bucket);
// Side-to-move network output in centipawns (the residual flag is the caller's business).
[[nodiscard]] int evaluate(const Net& net, const Board& board, const Accumulator& accumulator);
// Fresh accumulators + scalar output: the reference for tools and tests.
[[nodiscard]] int evaluate_reference(const Net& net, const Board& board);

// ---- file helpers shared with the tools ----
[[nodiscard]] std::uint64_t fnv1a64(const std::uint8_t* data, std::size_t size, std::uint64_t hash = 14695981039346656037ULL);
[[nodiscard]] std::size_t file_size_for(int hidden, int king_buckets, int output_buckets);

} // namespace forge::nnue::v3
