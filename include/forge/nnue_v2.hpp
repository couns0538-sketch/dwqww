#pragma once

// v2 networks, loaded from a file at run time: king-bucketed input layer (C4)
// and output buckets by piece count (C5). Used only when UCI NNUEKingBuckets
// or NNUEOutputBuckets is > 0 and a matching file is loaded with UCI NNUEFile
// (forge/search_options.hpp); with none of these options set the compiled-in
// network (forge/nnue.hpp) is used and nothing here runs. A request that cannot
// be honoured is an error, never a silent fall-back to the compiled-in network
// (see options::nnue_v2_problem and src/uci.cpp).
//
// Feature of piece `pc` on `square` for perspective p (own king on `ksq`):
//   r      = p == White ? square : square ^ 56       (rank flip, as forge/nnue.hpp)
//   kr     = p == White ? ksq : ksq ^ 56
//   flip   = (mirror flag && file_of(kr) >= 4) ? 7 : 0   (own king on files e-h)
//   bucket = king_bucket_map[kr]                     (64 entries, indexed before mirroring)
//   index  = bucket * 768 + ((colour(pc) == p ? 0 : 1) * 6 + type(pc) - 1) * 64 + (r ^ flip)
// With one bucket and no mirroring this is nnue::feature_index(). The output
// layer has the compiled-in architecture (SCReLU of the side-to-move and the
// opponent accumulators, one linear output) and the arithmetic of
// nnue::evaluate(); with output buckets (C5) the row of w2/b2 is
//   output bucket = output_bucket_map[popcount(occupied squares)]   (33 entries, kings included)
// The trainer's default map for N buckets puts n = pieces - 2 non-king pieces in
// bucket min(N - 1, n * N / 32): for N = 8 that is n / 4.
//
// File format v2 (little-endian), written by tools/nnue/forge_nnue_v2.py:
//   0   char[8] "FORGENN2"      8  u32 version = 2        12 u32 header_bytes = 160
//   16  u32 feature_set = 0     20 u32 inputs = 768       24 u32 hidden (= HiddenSize)
//   28  u32 king_buckets (1-32) 32 u32 output_buckets (1-16)  36 u32 flags (bit0 residual, bit1 mirror)
//   40  f32 weight_scale 4096   44 f32 output_scale 4096  48 f32 sigmoid_k 2.25
//   52  u8 king_bucket_map[64]  116 u8 output_bucket_map[33]   149 u8 reserved[11] = 0
//   160 i16 w1[king_buckets][768][hidden], i16 b1[hidden], i16 w2[output_buckets][2*hidden],
//       i16 b2[output_buckets], then u64 FNV-1a 64 of every preceding byte.
//
// Exactness: weights are de-quantised like the compiled-in net (int16 / 4096),
// so every accumulator value is an integer multiple of 2^-12 below 2^12 in
// magnitude and every float addition/subtraction on it is exact. Incremental
// updates, the refresh cache and a full refresh therefore give bit-identical
// accumulators whatever the order of the terms.
//
// Layout discipline: everything here is inline (an out-of-line copy is a COMDAT
// section) and the search code that uses it lives in .text.forge_v2, so the
// default build's .text is unchanged (see src/search/evaluation_v2.inc).

#include "forge/nnue.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <new>
#include <string>
#include <vector>

#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#define FORGE_NNUE_V2_SSE 1
#else
#define FORGE_NNUE_V2_SSE 0
#endif
#if defined(__AVX2__)
#include <immintrin.h>
#endif

namespace forge::nnue::v2 {

constexpr int MaxKingBuckets = 32;
constexpr int MaxOutputBuckets = 16;
constexpr int MaxWorkers = 256;       // refresh caches are per worker id (Threads max)
constexpr int HeaderBytes = 160;

struct KingKey {
    int bucket = 0;
    int flip = 0;     // 0, or 7 when the perspective's king stands on files e-h of a mirrored net
    [[nodiscard]] bool operator==(const KingKey&) const = default;
};

// 64-byte aligned float array.
class AlignedFloats {
public:
    AlignedFloats() = default;
    AlignedFloats(const AlignedFloats&) = delete;
    AlignedFloats& operator=(const AlignedFloats&) = delete;
    ~AlignedFloats() { release(); }
    void allocate(std::size_t count) {
        release();
        data_ = static_cast<float*>(::operator new(count * sizeof(float), std::align_val_t{64}));
        size_ = count;
        std::fill(data_, data_ + count, 0.0F);
    }
    [[nodiscard]] float* data() const { return data_; }
    [[nodiscard]] std::size_t size() const { return size_; }

private:
    void release() {
        if (data_ != nullptr) ::operator delete(data_, std::align_val_t{64});
        data_ = nullptr;
        size_ = 0;
    }
    float* data_ = nullptr;
    std::size_t size_ = 0;
};

// Piece bitboards indexed by Piece code (index 0 unused).
using Pieces = std::array<Bitboard, 13>;

// Per-worker accumulator cache: for each (perspective, bucket, flip) the
// accumulator of the last piece placement refreshed under that key.
struct RefreshCache {
    struct Entry {
        alignas(64) std::array<float, HiddenSize> values;
        Pieces pieces;
    };
    std::vector<Entry> entries;   // index ((perspective * king_buckets + bucket) * 2 + (flip != 0))
};

struct Net {
    std::string path;
    int king_buckets = 1;
    int output_buckets = 1;
    bool mirror = false;
    bool residual = false;
    std::uint64_t checksum = 0;
    std::array<std::uint8_t, 64> king_map{};
    std::array<std::uint8_t, 33> output_map{};
    AlignedFloats w1;   // [king_buckets][InputCount][HiddenSize]
    AlignedFloats b1;   // [HiddenSize]
    AlignedFloats w2;   // [output_buckets][2 * HiddenSize]
    std::vector<float> b2;   // [output_buckets]
    // Per worker id; slot i is created and used only by the worker with id i.
    mutable std::array<std::unique_ptr<RefreshCache>, MaxWorkers> caches;
};

struct Description {
    std::string path;
    int king_buckets = 1;
    int output_buckets = 1;
    bool mirror = false;
    bool residual = false;
    std::uint64_t checksum = 0;
    std::array<std::uint8_t, 33> output_bucket_map{};
};

// ---- loading and selection (src/nnue.cpp; must not run during a search) ----
// Loads a v2 file. The previously loaded net is unloaded first, so after a
// failed load no net is loaded (the engine never evaluates with a net other
// than the one last requested). The file size is checked (seek to the end)
// before anything is allocated: a file smaller than a header, larger than the
// largest valid v2 file or of another size than its header implies is
// rejected after reading at most the 160 header bytes.
[[nodiscard]] bool load(const std::string& path, std::string* error);
void unload();
[[nodiscard]] const Net* loaded();
// Size in bytes of a v2 file with these counts (header + weights + checksum).
[[nodiscard]] std::uint64_t file_bytes(int king_buckets, int output_buckets);
// Bytes of its file the last load() read (0, the header only, or the whole file).
[[nodiscard]] std::uint64_t last_load_bytes_read();
// "<path> king buckets N output buckets M hidden H mirrored|unmirrored residual|stand-alone fnv1a X".
[[nodiscard]] std::string summary(const Net& net);
// Makes the loaded net the active one if its architecture matches the options:
// king_buckets > 0 needs exactly that many king buckets (0: one unmirrored
// bucket), output_buckets > 0 exactly that many output buckets (0: one), and at
// least one of them must be > 0. Returns the active net (nullptr: the
// compiled-in network); message gets a one-line state.
const Net* select(int king_buckets, int output_buckets, std::string* message);
[[nodiscard]] Description describe(const Net& net);
// Allocates the refresh cache of one worker (on first use).
[[nodiscard]] RefreshCache& make_cache(const Net& net, int worker_id);

// The net the search evaluates with (nullptr: the compiled-in network).
extern const Net* active_net;
[[nodiscard]] inline const Net* active() { return active_net; }

// ---- evaluation kernels ----
[[nodiscard]] inline KingKey king_key(const Net& net, Color perspective, int king_square) {
    const int relative = perspective == White ? king_square : king_square ^ 56;
    return {net.king_map[static_cast<std::size_t>(relative)], net.mirror && (relative & 7) >= 4 ? 7 : 0};
}

[[nodiscard]] inline int feature(Color perspective, KingKey key, Piece piece, int square) {
    const int relative_color = color_of(piece) == perspective ? 0 : 1;
    const int relative_square = (perspective == White ? square : square ^ 56) ^ key.flip;
    return key.bucket * InputCount + (relative_color * 6 + piece_type(piece) - 1) * 64 + relative_square;
}

[[nodiscard]] inline const float* column(const Net& net, Color perspective, KingKey key, Piece piece, int square) {
    return net.w1.data() + static_cast<std::size_t>(feature(perspective, key, piece, square)) * HiddenSize;
}

[[nodiscard]] inline Pieces pieces_of(const Board& board) {
    Pieces pieces{};
    for (int code = WP; code <= BK; ++code) pieces[static_cast<std::size_t>(code)] = board.pieces(static_cast<Piece>(code));
    return pieces;
}

// Takes back the piece changes of one move (`dirty`) on a piece placement.
inline void undo(Pieces& pieces, const DirtyPieces& dirty) {
    for (int i = 0; i < dirty.count; ++i) {
        const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
        Bitboard& bb = pieces[static_cast<std::size_t>(change.piece)];
        if (change.add) bb &= ~square_bb(change.square);
        else bb |= square_bb(change.square);
    }
}

[[nodiscard]] inline RefreshCache& cache(const Net& net, int worker_id) {
    const std::unique_ptr<RefreshCache>& slot = net.caches[static_cast<std::size_t>(std::clamp(worker_id, 0, MaxWorkers - 1))];
    if (slot == nullptr) [[unlikely]] return make_cache(net, worker_id);
    return *slot;
}

// dst = src - sub[0] - ... + add[0] + ... (exact; any order gives the same bits).
template <int Subs, int Adds>
inline void apply_columns(const float* src, float* dst, const float* const* sub, const float* const* add) {
    for (int h = 0; h < HiddenSize; ++h) {
        float value = src[h];
        for (int i = 0; i < Subs; ++i) value -= sub[i][h];
        for (int i = 0; i < Adds; ++i) value += add[i][h];
        dst[h] = value;
    }
}

// Accumulator of one perspective from scratch (reference implementation).
inline void refresh(const Net& net, const Board& board, Color perspective, float* values) {
    const KingKey key = king_key(net, perspective, board.king_square(perspective));
    std::copy(net.b1.data(), net.b1.data() + HiddenSize, values);
    Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        const float* col = column(net, perspective, key, board.piece_at(square), square);
        for (int h = 0; h < HiddenSize; ++h) values[h] += col[h];
    }
}

// Accumulator of one perspective for the placement `pieces` (own king on
// `king_square`) through the cache: only the difference to the cached
// placement under the same key is applied; the entry is updated.
inline void refresh_cached(const Net& net, RefreshCache& cache, const Pieces& pieces, int king_square,
                           Color perspective, float* values) {
    const KingKey key = king_key(net, perspective, king_square);
    RefreshCache::Entry& entry = cache.entries[(static_cast<std::size_t>(perspective) * static_cast<std::size_t>(net.king_buckets) +
                                                static_cast<std::size_t>(key.bucket)) * 2U + (key.flip != 0 ? 1U : 0U)];
    // At most one removal and one addition per square.
    std::array<const float*, 64> sub;
    std::array<const float*, 64> add;
    int subs = 0;
    int adds = 0;
    for (int code = WP; code <= BK; ++code) {
        const Piece piece = static_cast<Piece>(code);
        const Bitboard now = pieces[static_cast<std::size_t>(code)];
        Bitboard removed = entry.pieces[static_cast<std::size_t>(code)] & ~now;
        Bitboard added = now & ~entry.pieces[static_cast<std::size_t>(code)];
        while (removed != 0) sub[static_cast<std::size_t>(subs++)] = column(net, perspective, key, piece, pop_lsb(removed));
        while (added != 0) add[static_cast<std::size_t>(adds++)] = column(net, perspective, key, piece, pop_lsb(added));
        entry.pieces[static_cast<std::size_t>(code)] = now;
    }
    constexpr int Chunk = 64;
    static_assert(HiddenSize % Chunk == 0, "HiddenSize must be a multiple of the refresh chunk");
    for (int h0 = 0; h0 < HiddenSize; h0 += Chunk) {
        float chunk[Chunk];
        for (int k = 0; k < Chunk; ++k) chunk[k] = entry.values[static_cast<std::size_t>(h0 + k)];
        for (int i = 0; i < subs; ++i) {
            const float* col = sub[static_cast<std::size_t>(i)] + h0;
            for (int k = 0; k < Chunk; ++k) chunk[k] -= col[k];
        }
        for (int i = 0; i < adds; ++i) {
            const float* col = add[static_cast<std::size_t>(i)] + h0;
            for (int k = 0; k < Chunk; ++k) chunk[k] += col[k];
        }
        for (int k = 0; k < Chunk; ++k) {
            entry.values[static_cast<std::size_t>(h0 + k)] = chunk[k];
            values[h0 + k] = chunk[k];
        }
    }
}

// Incremental update of one perspective whose king key did not change.
inline void update(const Net& net, Color perspective, KingKey key, const float* parent, float* child,
                   const DirtyPieces& dirty) {
    std::array<const float*, 4> sub{};
    std::array<const float*, 4> add{};
    int subs = 0;
    int adds = 0;
    for (int i = 0; i < dirty.count; ++i) {
        const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
        const float* col = column(net, perspective, key, change.piece, change.square);
        if (change.add) add[static_cast<std::size_t>(adds++)] = col;
        else sub[static_cast<std::size_t>(subs++)] = col;
    }
    if (subs == 1 && adds == 1) apply_columns<1, 1>(parent, child, sub.data(), add.data());
    else if (subs == 2 && adds == 1) apply_columns<2, 1>(parent, child, sub.data(), add.data());
    else if (subs == 2 && adds == 2) apply_columns<2, 2>(parent, child, sub.data(), add.data());
    else {
        apply_columns<0, 0>(parent, child, sub.data(), add.data());
        for (int i = 0; i < subs; ++i) apply_columns<1, 0>(child, child, &sub[static_cast<std::size_t>(i)], add.data());
        for (int i = 0; i < adds; ++i) apply_columns<0, 1>(child, child, sub.data(), &add[static_cast<std::size_t>(i)]);
    }
}

// Output bucket of a position: by the number of pieces on the board (C5).
[[nodiscard]] inline int output_bucket(const Net& net, const Board& board) {
    return net.output_map[static_cast<std::size_t>(std::min(popcount(board.occupied()), 32))];
}

// Network output before the conversion to centipawns; nnue::evaluate()'s arithmetic.
[[nodiscard]] inline float output(const Net& net, const Board& board, const Accumulator& accumulator) {
    const Color us = board.side_to_move();
    const auto& ours = accumulator.values[static_cast<std::size_t>(us)];
    const auto& theirs = accumulator.values[static_cast<std::size_t>(opposite(us))];
    const std::size_t bucket = static_cast<std::size_t>(output_bucket(net, board));
    const float* w2 = net.w2.data() + bucket * 2U * HiddenSize;
    constexpr int Lanes = 16;
    static_assert(HiddenSize % Lanes == 0, "HiddenSize must be a multiple of the lane count");
    alignas(64) float lanes[Lanes];
#if defined(__AVX2__)
    const __m256 zero = _mm256_setzero_ps();
    const __m256 one = _mm256_set1_ps(1.0F);
    __m256 sums[2] = {zero, zero};
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int k = 0; k < 2; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 8 * k);
            const __m256 a = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(ours.data() + base), zero), one);
            const __m256 b = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(theirs.data() + base), zero), one);
            const __m256 term = _mm256_add_ps(_mm256_mul_ps(_mm256_mul_ps(a, a), _mm256_load_ps(w2 + base)),
                                            _mm256_mul_ps(_mm256_mul_ps(b, b), _mm256_load_ps(w2 + HiddenSize + base)));
            sums[k] = _mm256_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 2; ++k) _mm256_store_ps(lanes + 8 * k, sums[k]);
#elif FORGE_NNUE_V2_SSE
    const __m128 zero = _mm_setzero_ps();
    const __m128 one = _mm_set1_ps(1.0F);
    __m128 sums[4] = {zero, zero, zero, zero};
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int k = 0; k < 4; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 4 * k);
            const __m128 a = _mm_min_ps(_mm_max_ps(_mm_load_ps(ours.data() + base), zero), one);
            const __m128 b = _mm_min_ps(_mm_max_ps(_mm_load_ps(theirs.data() + base), zero), one);
            const __m128 term = _mm_add_ps(_mm_mul_ps(_mm_mul_ps(a, a), _mm_load_ps(w2 + base)),
                                           _mm_mul_ps(_mm_mul_ps(b, b), _mm_load_ps(w2 + HiddenSize + base)));
            sums[k] = _mm_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 4; ++k) _mm_store_ps(lanes + 4 * k, sums[k]);
#else
    for (float& lane : lanes) lane = 0.0F;
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int j = 0; j < Lanes; ++j) {
            const std::size_t index = static_cast<std::size_t>(h + j);
            const float a = std::min(std::max(ours[index], 0.0F), 1.0F);
            const float b = std::min(std::max(theirs[index], 0.0F), 1.0F);
            lanes[j] += a * a * w2[index] + b * b * w2[static_cast<std::size_t>(HiddenSize) + index];
        }
    }
#endif
    float out = net.b2[bucket];
    for (int j = 0; j < Lanes; ++j) out += lanes[j];
    return out;
}

// Side-to-move evaluation in centipawns.
[[nodiscard]] inline int evaluate(const Net& net, const Board& board, const Accumulator& accumulator) {
    const float centipawns = output(net, board, accumulator) * 400.0F / SigmoidK;
    return static_cast<int>(std::clamp(centipawns, -30000.0F, 30000.0F));
}

} // namespace forge::nnue::v2
