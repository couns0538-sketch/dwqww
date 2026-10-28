#include "forge/nnue.hpp"
#include "forge/nnue_v2.hpp"
#ifdef FORGE_PROF
#include "forge/profile.hpp"
#endif

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <vector>
#if FORGE_NNUE_O2
#include <new>
#endif // FORGE_NNUE_O2
#if FORGE_NNUE_INT16
#include <atomic>
#include <cstdlib>
#include <iterator>
#include <limits>
#endif // FORGE_NNUE_INT16

// R3 stack: the O2 accumulator kernels (opus-O2) are compiled only with
// FORGE_NNUE_O2 (build switch, default off = the AL1 s198 loops). Both paths
// give bit-identical accumulators and outputs (opus_round1/O2/REPORT.md).
#if FORGE_NNUE_O2
// Kernel selection is compile-time only, and every path is bit-identical: each
// accumulator lane and each output partial sum sees the same float operations
// in the same order as the portable code (no FMA, no -ffast-math, no
// reassociation). FORGE_NNUE_FORCE_SCALAR selects the portable code on any
// target (used by the parity tests).
//
#endif // FORGE_NNUE_O2
// The output layer uses SSE min/max/mul/add directly: compilers may not turn a
// float clamp into min/max instructions without -ffast-math, which left the
// AVX2 builds with slow scalar code. SSE2 is part of every x86-64 target.
// (FORGE_NNUE_FORCE_SCALAR is honoured only with FORGE_NNUE_O2, as on opus-O2.)
#if (!FORGE_NNUE_O2 || !defined(FORGE_NNUE_FORCE_SCALAR)) && \
    (defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64))
#include <xmmintrin.h>
#define FORGE_NNUE_SSE 1
#else
#define FORGE_NNUE_SSE 0
#endif

#if (!FORGE_NNUE_O2 || !defined(FORGE_NNUE_FORCE_SCALAR)) && defined(__AVX2__)
#include <immintrin.h>
#define FORGE_NNUE_AVX2 1
#else
#define FORGE_NNUE_AVX2 0
#endif

#if FORGE_NNUE_O2
// Accumulator kernels (refresh/update): explicit AVX2 or SSE2 vectors, else the
// portable loops. AVX-512 targets keep the portable loops, which the compiler
// widens to 512 bits itself as it does for AL1 s198.
#if FORGE_NNUE_AVX2 && !defined(__AVX512F__)
#define FORGE_NNUE_KERNEL_AVX2 1
#else
#define FORGE_NNUE_KERNEL_AVX2 0
#endif
#if FORGE_NNUE_SSE && !defined(__AVX2__)
#define FORGE_NNUE_KERNEL_SSE2 1
#else
#define FORGE_NNUE_KERNEL_SSE2 0
#endif
#endif // FORGE_NNUE_O2

// FORGE_NNUE_WEIGHTS (compile flag, default unset = src/nnue_weights.inc): another
// network include file, e.g. an H512 net built with -DFORGE_NNUE_HIDDEN=512
// -DFORGE_NNUE_WEIGHTS='"path/to/net.inc"'. The include file's static_asserts
// reject a hidden width that differs from FORGE_NNUE_HIDDEN.
#if defined(FORGE_NNUE_WEIGHTS)
#include FORGE_NNUE_WEIGHTS
#define FORGE_HAS_NNUE 1
#elif __has_include("nnue_weights.inc")
#include "nnue_weights.inc"
#define FORGE_HAS_NNUE 1
#else
#define FORGE_HAS_NNUE 0
#endif
// Include files written before residual training existed carry no flag and
// hold stand-alone networks.
#ifndef FORGE_NNUE_RESIDUAL
#define FORGE_NNUE_RESIDUAL 0
#endif
#if FORGE_HAS_NNUE
static_assert(sizeof(NnueW1) / sizeof(NnueW1[0]) == static_cast<std::size_t>(forge::nnue::InputCount) * forge::nnue::HiddenSize,
              "nnue_weights.inc was trained for a different FORGE_NNUE_HIDDEN");
static_assert(sizeof(NnueB1) / sizeof(NnueB1[0]) == static_cast<std::size_t>(forge::nnue::HiddenSize), "nnue_weights.inc b1 size");
static_assert(sizeof(NnueW2) / sizeof(NnueW2[0]) == 2 * static_cast<std::size_t>(forge::nnue::HiddenSize), "nnue_weights.inc w2 size");
#endif

namespace forge::nnue {

bool enabled = true;

namespace {

#if FORGE_NNUE_O2
// 64-byte aligned storage: every feature column (HiddenSize floats) starts on a
// cache-line boundary, so no vector load of a column straddles two lines.
struct AlignedDelete {
    void operator()(float* p) const { ::operator delete[](p, std::align_val_t{64}); }
};
using AlignedFloats = std::unique_ptr<float[], AlignedDelete>;

AlignedFloats aligned_zeros(std::size_t count) {
    AlignedFloats storage(static_cast<float*>(::operator new[](count * sizeof(float), std::align_val_t{64})));
    std::fill_n(storage.get(), count, 0.0F);
    return storage;
}

#endif // FORGE_NNUE_O2
struct Weights {
#if !FORGE_NNUE_O2
    std::unique_ptr<float[]> w1;   // [InputCount][HiddenSize]
    alignas(32) std::array<float, HiddenSize> b1{};
    alignas(32) std::array<float, 2 * HiddenSize> w2{};
#else  // FORGE_NNUE_O2
    AlignedFloats w1;   // [InputCount][HiddenSize]
    alignas(64) std::array<float, HiddenSize> b1{};
    alignas(64) std::array<float, 2 * HiddenSize> w2{};
#endif // FORGE_NNUE_O2
    float b2 = 0.0F;
};

const Weights& weights() {
    static const Weights instance = [] {
        Weights w;
#if !FORGE_NNUE_O2
        w.w1 = std::make_unique<float[]>(static_cast<std::size_t>(InputCount) * HiddenSize);
#else  // FORGE_NNUE_O2
        w.w1 = aligned_zeros(static_cast<std::size_t>(InputCount) * HiddenSize);
#endif // FORGE_NNUE_O2
#if FORGE_HAS_NNUE
        for (std::size_t i = 0; i < static_cast<std::size_t>(InputCount) * HiddenSize; ++i) {
            w.w1[i] = static_cast<float>(NnueW1[i]) / WeightScale;
        }
        for (std::size_t i = 0; i < HiddenSize; ++i) w.b1[i] = static_cast<float>(NnueB1[i]) / WeightScale;
        for (std::size_t i = 0; i < 2 * HiddenSize; ++i) w.w2[i] = static_cast<float>(NnueW2[i]) / OutputScale;
        w.b2 = static_cast<float>(NnueB2) / OutputScale;
#endif
        return w;
    }();
    return instance;
}

#if FORGE_NNUE_O2
inline const float* column(const Weights& w, Color perspective, Piece piece, int square) {
    return w.w1.get() + static_cast<std::size_t>(feature_index(perspective, piece, square)) * HiddenSize;
}

#endif // FORGE_NNUE_O2
inline void add_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] += column[h];
}

inline void sub_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] -= column[h];
}

#if FORGE_NNUE_O2
// One accumulator vector: the kernels below are written once against these
// helpers. Lanes never interact, so the vector width only changes how many
// lanes one instruction handles, never the operations a lane sees.
#if FORGE_NNUE_KERNEL_AVX2
using Vec = __m256;
constexpr int VecWidth = 8;
inline Vec vec_load(const float* p) { return _mm256_load_ps(p); }
inline void vec_store(float* p, Vec v) { _mm256_store_ps(p, v); }
inline Vec vec_add(Vec a, Vec b) { return _mm256_add_ps(a, b); }
inline Vec vec_sub(Vec a, Vec b) { return _mm256_sub_ps(a, b); }
#elif FORGE_NNUE_KERNEL_SSE2
using Vec = __m128;
constexpr int VecWidth = 4;
inline Vec vec_load(const float* p) { return _mm_load_ps(p); }
inline void vec_store(float* p, Vec v) { _mm_store_ps(p, v); }
inline Vec vec_add(Vec a, Vec b) { return _mm_add_ps(a, b); }
inline Vec vec_sub(Vec a, Vec b) { return _mm_sub_ps(a, b); }
#else
using Vec = float;
constexpr int VecWidth = 1;
inline Vec vec_load(const float* p) { return *p; }
inline void vec_store(float* p, Vec v) { *p = v; }
inline Vec vec_add(Vec a, Vec b) { return a + b; }
inline Vec vec_sub(Vec a, Vec b) { return a - b; }
#endif
static_assert(HiddenSize % VecWidth == 0, "HiddenSize must be a multiple of the vector width");

// Update kernels. Each lane takes the parent value and then applies the piece
// changes in DirtyPieces order (subtract a removal, add an addition), which is
// exactly what the generic copy-then-apply loop in update() computes. `out`
// may equal `in` (in-place update): every vector is read before it is written.

// Quiet moves and noncapturing promotions: (in - r) + a.
inline void apply_sub_add(float* out, const float* in, const float* r, const float* a) {
    for (int h = 0; h < HiddenSize; h += VecWidth)
        vec_store(out + h, vec_add(vec_sub(vec_load(in + h), vec_load(r + h)), vec_load(a + h)));
}

// Captures, en passant and capturing promotions: ((in - r0) - r1) + a.
inline void apply_sub_sub_add(float* out, const float* in, const float* r0, const float* r1, const float* a) {
    for (int h = 0; h < HiddenSize; h += VecWidth)
        vec_store(out + h, vec_add(vec_sub(vec_sub(vec_load(in + h), vec_load(r0 + h)), vec_load(r1 + h)), vec_load(a + h)));
}

// Castling (king, then rook): (((in - r0) + a0) - r1) + a1.
inline void apply_sub_add_sub_add(float* out, const float* in, const float* r0, const float* a0, const float* r1,
                                  const float* a1) {
    for (int h = 0; h < HiddenSize; h += VecWidth)
        vec_store(out + h, vec_add(vec_sub(vec_add(vec_sub(vec_load(in + h), vec_load(r0 + h)), vec_load(a0 + h)),
                                           vec_load(r1 + h)),
                                   vec_load(a1 + h)));
}

// Refresh kernel: out = bias + columns[0] + columns[1] + ..., lane by lane in
// column order (the order in which AL1 s198 adds the pieces).
inline void accumulate_columns(float* out, const float* bias, const float* const* columns, std::size_t count) {
#if FORGE_NNUE_KERNEL_AVX2 || FORGE_NNUE_KERNEL_SSE2
    // Register-blocked: a block of Regs vectors stays in registers while every
    // column is added, instead of a load and a store per column and vector.
    constexpr int Regs = HiddenSize % (8 * VecWidth) == 0 ? 8 : HiddenSize % (4 * VecWidth) == 0 ? 4 : 1;
    for (int base = 0; base < HiddenSize; base += Regs * VecWidth) {
        Vec sums[Regs];
        for (int k = 0; k < Regs; ++k) sums[k] = vec_load(bias + base + k * VecWidth);
        for (std::size_t c = 0; c < count; ++c) {
            const float* source = columns[c] + base;
            for (int k = 0; k < Regs; ++k) sums[k] = vec_add(sums[k], vec_load(source + k * VecWidth));
        }
        for (int k = 0; k < Regs; ++k) vec_store(out + base + k * VecWidth, sums[k]);
    }
#else
    std::copy_n(bias, HiddenSize, out);
    for (std::size_t c = 0; c < count; ++c) {
        const float* source = columns[c];
        for (int h = 0; h < HiddenSize; ++h) out[h] += source[h];
    }
#endif
}

#endif // FORGE_NNUE_O2
} // namespace

#if FORGE_NNUE_INT16
// S-A2 NnueInt16 (build switch FORGE_NNUE_INT16, default off; UCI NnueInt16,
// default false): the integer path and the three hooks below. The hooks run
// before either accumulator variant (AL1 loops or the FORGE_NNUE_O2 kernels),
// which stay untouched.
#include "nnue_int16.inc"
#endif // FORGE_NNUE_INT16

bool available() { return FORGE_HAS_NNUE != 0; }

bool residual() { return FORGE_HAS_NNUE != 0 && FORGE_NNUE_RESIDUAL != 0; }

void refresh(const Board& board, Accumulator& accumulator) {
#ifdef FORGE_PROF
    prof::count(prof::Counter::NnueRefresh);
#endif

#if FORGE_NNUE_INT16
    if (int16_active()) {
        int16_detail::refresh_integer(board, accumulator);
        return;
    }
    accumulator.integer = false;
#endif // FORGE_NNUE_INT16
    const Weights& w = weights();
    for (const Color perspective : {White, Black}) {
#if !FORGE_NNUE_O2
        auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
        acc = w.b1;
#else  // FORGE_NNUE_O2
        std::array<const float*, 64> columns;
        std::size_t count = 0;
#endif // FORGE_NNUE_O2
        Bitboard occupied = board.occupied();
        while (occupied != 0) {
            const int square = pop_lsb(occupied);
#if !FORGE_NNUE_O2
            const int index = feature_index(perspective, board.piece_at(square), square);
            add_feature(acc, w.w1.get() + static_cast<std::size_t>(index) * HiddenSize);
#else  // FORGE_NNUE_O2
            columns[count++] = column(w, perspective, board.piece_at(square), square);
#endif // FORGE_NNUE_O2
        }
#if FORGE_NNUE_O2
        accumulate_columns(accumulator.values[static_cast<std::size_t>(perspective)].data(), w.b1.data(), columns.data(),
                           count);
#endif // FORGE_NNUE_O2
    }
    accumulator.valid = true;
}

void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {
#if FORGE_NNUE_INT16
    if (parent.integer) {
        int16_detail::update_integer(parent, child, dirty);
        return;
    }
    child.integer = false;
#endif // FORGE_NNUE_INT16
    const Weights& w = weights();
#if FORGE_NNUE_O2
    const auto& changes = dirty.changes;
#endif // FORGE_NNUE_O2
    // Quiet moves (including noncapturing promotions) remove one feature and
#if !FORGE_NNUE_O2
    // add one. Keep each lane's subtraction-then-addition order while avoiding
    // a full copy and two separate read/write passes over the child.
    if (dirty.count == 2 && !dirty.changes[0].add && dirty.changes[1].add) {
#else  // FORGE_NNUE_O2
    // add one; captures remove two (mover and captured piece) before adding
    // the mover or promoted piece; castling moves the king, then the rook.
    // One pass per lane keeps every intermediate subtraction and addition of
    // the generic loop below, without a full copy and a pass per change.
    if (dirty.count == 2 && !changes[0].add && changes[1].add) {
        for (const Color perspective : {White, Black}) {
            const std::size_t side = static_cast<std::size_t>(perspective);
            apply_sub_add(child.values[side].data(), parent.values[side].data(),
                          column(w, perspective, changes[0].piece, changes[0].square),
                          column(w, perspective, changes[1].piece, changes[1].square));
        }
        child.valid = true;
        return;
    }
    if (dirty.count == 3 && !changes[0].add && !changes[1].add && changes[2].add) {
#endif // FORGE_NNUE_O2
        for (const Color perspective : {White, Black}) {
#if !FORGE_NNUE_O2
            const auto& source = parent.values[static_cast<std::size_t>(perspective)];
            auto& destination = child.values[static_cast<std::size_t>(perspective)];
            const PieceChange& removed = dirty.changes[0];
            const PieceChange& added = dirty.changes[1];
            const float* removed_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed.piece, removed.square)) * HiddenSize;
            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = (source[index] - removed_column[index]) + added_column[index];
            }
#else  // FORGE_NNUE_O2
            const std::size_t side = static_cast<std::size_t>(perspective);
            apply_sub_sub_add(child.values[side].data(), parent.values[side].data(),
                              column(w, perspective, changes[0].piece, changes[0].square),
                              column(w, perspective, changes[1].piece, changes[1].square),
                              column(w, perspective, changes[2].piece, changes[2].square));
#endif // FORGE_NNUE_O2
        }
        child.valid = true;
        return;
    }
#if !FORGE_NNUE_O2
    // Captures remove the mover and captured piece before adding the mover
    // (or promoted piece). Preserve both intermediate subtractions per lane.
    if (dirty.count == 3 && !dirty.changes[0].add && !dirty.changes[1].add && dirty.changes[2].add) {
#else  // FORGE_NNUE_O2
    if (dirty.count == 4 && !changes[0].add && changes[1].add && !changes[2].add && changes[3].add) {
#endif // FORGE_NNUE_O2
        for (const Color perspective : {White, Black}) {
#if !FORGE_NNUE_O2
            const auto& source = parent.values[static_cast<std::size_t>(perspective)];
            auto& destination = child.values[static_cast<std::size_t>(perspective)];
            const PieceChange& removed0 = dirty.changes[0];
            const PieceChange& removed1 = dirty.changes[1];
            const PieceChange& added = dirty.changes[2];
            const float* removed0_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed0.piece, removed0.square)) * HiddenSize;
            const float* removed1_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed1.piece, removed1.square)) * HiddenSize;
            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = ((source[index] - removed0_column[index]) - removed1_column[index]) + added_column[index];
            }
#else  // FORGE_NNUE_O2
            const std::size_t side = static_cast<std::size_t>(perspective);
            apply_sub_add_sub_add(child.values[side].data(), parent.values[side].data(),
                                  column(w, perspective, changes[0].piece, changes[0].square),
                                  column(w, perspective, changes[1].piece, changes[1].square),
                                  column(w, perspective, changes[2].piece, changes[2].square),
                                  column(w, perspective, changes[3].piece, changes[3].square));
#endif // FORGE_NNUE_O2
        }
        child.valid = true;
        return;
    }
#if FORGE_NNUE_O2
    // Null moves (no change) and any other change list: copy, then apply each
    // change in order.
#endif // FORGE_NNUE_O2
    for (const Color perspective : {White, Black}) {
        auto& acc = child.values[static_cast<std::size_t>(perspective)];
        acc = parent.values[static_cast<std::size_t>(perspective)];
        for (int i = 0; i < dirty.count; ++i) {
#if !FORGE_NNUE_O2
            const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
            const int index = feature_index(perspective, change.piece, change.square);
            const float* column = w.w1.get() + static_cast<std::size_t>(index) * HiddenSize;
            if (change.add) add_feature(acc, column);
            else sub_feature(acc, column);
#else  // FORGE_NNUE_O2
            const PieceChange& change = changes[static_cast<std::size_t>(i)];
            const float* feature = column(w, perspective, change.piece, change.square);
            if (change.add) add_feature(acc, feature);
            else sub_feature(acc, feature);
#endif // FORGE_NNUE_O2
        }
    }
    child.valid = true;
}

int evaluate(const Board& board, const Accumulator& accumulator) {
#ifdef FORGE_PROF
    prof::count(prof::Counter::NnueForward);
#endif

#if FORGE_NNUE_INT16
    if (accumulator.integer) return int16_detail::evaluate_integer(board, accumulator);
#endif // FORGE_NNUE_INT16
    const Weights& w = weights();
    const Color us = board.side_to_move();
    const auto& ours = accumulator.values[static_cast<std::size_t>(us)];
    const auto& theirs = accumulator.values[static_cast<std::size_t>(opposite(us))];
    // Sixteen independent partial sums (lane j takes the hidden units with
    // index % 16 == j, in increasing order) and then one ordered sum: the
#if !FORGE_NNUE_O2
    // association is fixed by the source, so every target (SSE, AVX2, AVX-512,
    // the scalar fallback) produces bit-identical results without -ffast-math.
#else  // FORGE_NNUE_O2
    // association is fixed by the source, so every target (SSE, AVX2, the
    // scalar fallback) produces bit-identical results without -ffast-math.
#endif // FORGE_NNUE_O2
    constexpr int Lanes = 16;
    static_assert(HiddenSize % Lanes == 0, "HiddenSize must be a multiple of the lane count");
    alignas(64) float lanes[Lanes];
#if FORGE_NNUE_AVX2
    const __m256 zero = _mm256_setzero_ps();
    const __m256 one = _mm256_set1_ps(1.0F);
    __m256 sums[2] = {zero, zero};
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int k = 0; k < 2; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 8 * k);
            const __m256 a = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(ours.data() + base), zero), one);
            const __m256 b = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(theirs.data() + base), zero), one);
            const __m256 term = _mm256_add_ps(_mm256_mul_ps(_mm256_mul_ps(a, a), _mm256_load_ps(w.w2.data() + base)),
                                            _mm256_mul_ps(_mm256_mul_ps(b, b), _mm256_load_ps(w.w2.data() + HiddenSize + base)));
            sums[k] = _mm256_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 2; ++k) _mm256_store_ps(lanes + 8 * k, sums[k]);
#elif FORGE_NNUE_SSE
    const __m128 zero = _mm_setzero_ps();
    const __m128 one = _mm_set1_ps(1.0F);
    __m128 sums[4] = {zero, zero, zero, zero};
    for (int h = 0; h < HiddenSize; h += Lanes) {
        for (int k = 0; k < 4; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 4 * k);
            const __m128 a = _mm_min_ps(_mm_max_ps(_mm_load_ps(ours.data() + base), zero), one);
            const __m128 b = _mm_min_ps(_mm_max_ps(_mm_load_ps(theirs.data() + base), zero), one);
            const __m128 term = _mm_add_ps(_mm_mul_ps(_mm_mul_ps(a, a), _mm_load_ps(w.w2.data() + base)),
                                           _mm_mul_ps(_mm_mul_ps(b, b), _mm_load_ps(w.w2.data() + HiddenSize + base)));
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
            lanes[j] += a * a * w.w2[index] + b * b * w.w2[static_cast<std::size_t>(HiddenSize) + index];
        }
    }
#endif
    float out = w.b2;
    for (int j = 0; j < Lanes; ++j) out += lanes[j];
    const float centipawns = out * 400.0F / SigmoidK;
    return static_cast<int>(std::clamp(centipawns, -30000.0F, 30000.0F));
}

DirtyPieces dirty_pieces(const Board& board, const Move& move) {
    DirtyPieces dirty;
    const Color us = board.side_to_move();
    const Piece moved = board.piece_at(move.from);
    const Piece captured = board.captured_piece(move);
    dirty.remove(moved, move.from);
    if (captured != Empty) {
        const int captured_square = (move.flags & EnPassant) != 0U ? move.to - pawn_push_delta(us) : move.to;
        dirty.remove(captured, captured_square);
    }
    dirty.add(move.is_promotion() ? make_piece(us, move.promotion) : moved, move.to);
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        const int rook_from = us == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
        const int rook_to = us == White ? (king_side ? 5 : 3) : (king_side ? 61 : 59);
        dirty.remove(make_piece(us, Rook), rook_from);
        dirty.add(make_piece(us, Rook), rook_to);
    }
    return dirty;
}

} // namespace forge::nnue

// ---------------------------------------------------------------------------
// v2 networks (forge/nnue_v2.hpp): loading and selection, all cold.
// This translation unit is linked before search.cpp; the functions above keep
// their code and addresses because nothing here is placed in .text (cold
// functions go to .text.unlikely, which the PE linker puts after every
// object's .text) and nothing here calls the local helpers above.
namespace forge::nnue::v2 {

// Constant-initialised: no dynamic initialisation or exit-time code.
const Net* active_net = nullptr;

namespace {

Net* loaded_net = nullptr;   // owned; deleted by load() / unload()
std::uint64_t last_bytes_read = 0;   // bytes of its file the last load() read

constexpr std::uint32_t FlagResidual = 1U;
constexpr std::uint32_t FlagMirror = 2U;
constexpr char Magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'N', '2'};

[[gnu::cold]] std::uint32_t read_u32(const unsigned char* bytes, std::size_t offset) {
    return static_cast<std::uint32_t>(bytes[offset]) | static_cast<std::uint32_t>(bytes[offset + 1]) << 8U |
           static_cast<std::uint32_t>(bytes[offset + 2]) << 16U | static_cast<std::uint32_t>(bytes[offset + 3]) << 24U;
}

[[gnu::cold]] float read_f32(const unsigned char* bytes, std::size_t offset) {
    const std::uint32_t bits = read_u32(bytes, offset);
    float value = 0.0F;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

[[gnu::cold]] std::int16_t read_i16(const unsigned char* bytes, std::size_t offset) {
    return static_cast<std::int16_t>(static_cast<std::uint16_t>(bytes[offset] | (bytes[offset + 1] << 8U)));
}

[[gnu::cold]] std::uint64_t fnv1a64(const unsigned char* data, std::size_t size) {
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= data[i];
        hash *= 0x100000001b3ULL;
    }
    return hash;
}

[[gnu::cold]] bool fail(std::string* error, const std::string& text) {
    if (error != nullptr) *error = text;
    return false;
}

} // namespace

[[gnu::cold]] std::uint64_t file_bytes(int king_buckets, int output_buckets, std::uint32_t feature_set) {
    const std::uint64_t w1 = static_cast<std::uint64_t>(king_buckets) * InputCount * HiddenSize;
    const std::uint64_t wt = (feature_set & FeatureSetThreats) != 0U ? static_cast<std::uint64_t>(ThreatFeatures) * HiddenSize : 0U;
    const std::uint64_t wp = (feature_set & FeatureSetPawnPairs) != 0U ? static_cast<std::uint64_t>(PawnPairFeatures) * HiddenSize : 0U;
    const std::uint64_t w2 = static_cast<std::uint64_t>(output_buckets) * 2U * HiddenSize;
    return static_cast<std::uint64_t>(HeaderBytes) + 2U * (w1 + wt + wp + HiddenSize + w2 + static_cast<std::uint64_t>(output_buckets)) + 8U;
}

[[gnu::cold]] std::uint64_t last_load_bytes_read() { return last_bytes_read; }

[[gnu::cold]] bool load(const std::string& path, std::string* error) {
    // Whatever happens below, the previously loaded net is gone: after a failed load no net is
    // loaded, so the engine cannot evaluate with a net other than the one last requested.
    unload();
    last_bytes_read = 0;
    std::ifstream file(path, std::ios::binary);
    if (!file) return fail(error, "cannot open " + path);
    // The file size comes first (seek to the end): nothing is allocated or read before the size is
    // known to be the one the header implies.
    file.seekg(0, std::ios::end);
    const std::streamoff end = file.tellg();
    if (!file || end < 0) return fail(error, "cannot determine the size of " + path);
    const auto size = static_cast<std::uint64_t>(end);
    const std::uint64_t largest = file_bytes(MaxKingBuckets, MaxOutputBuckets, FeatureSetThreats | FeatureSetPawnPairs);
    if (size < static_cast<std::uint64_t>(HeaderBytes) + 8U) {
        return fail(error, "file too short for a v2 net (" + std::to_string(size) + " bytes)");
    }
    if (size > largest) {
        return fail(error, "file too large for a v2 net (" + std::to_string(size) + " bytes; the largest valid v2 file has " +
                               std::to_string(largest) + ")");
    }
    std::array<unsigned char, HeaderBytes> header{};
    file.seekg(0, std::ios::beg);
    file.read(reinterpret_cast<char*>(header.data()), HeaderBytes);
    if (!file) return fail(error, "cannot read the header of " + path);
    last_bytes_read = HeaderBytes;
    const unsigned char* bytes = header.data();
    if (std::memcmp(bytes, Magic, sizeof(Magic)) != 0) return fail(error, "bad magic (not a FORGENN2 file)");
    if (read_u32(bytes, 8) != 2U) return fail(error, "unsupported version " + std::to_string(read_u32(bytes, 8)));
    if (read_u32(bytes, 12) != static_cast<std::uint32_t>(HeaderBytes)) return fail(error, "unexpected header size");
    const std::uint32_t feature_set = read_u32(bytes, 16);
    if ((feature_set & ~(FeatureSetThreats | FeatureSetPawnPairs)) != 0U) return fail(error, "unsupported feature set " + std::to_string(feature_set));
    if (read_u32(bytes, 20) != static_cast<std::uint32_t>(InputCount)) return fail(error, "inputs per bucket must be 768");
    if (read_u32(bytes, 24) != static_cast<std::uint32_t>(HiddenSize)) {
        return fail(error, "hidden size " + std::to_string(read_u32(bytes, 24)) + " != engine hidden size " +
                               std::to_string(HiddenSize) + " (FORGE_NNUE_HIDDEN)");
    }
    const std::uint32_t king_buckets = read_u32(bytes, 28);
    const std::uint32_t output_buckets = read_u32(bytes, 32);
    const std::uint32_t flags = read_u32(bytes, 36);
    if (king_buckets < 1U || king_buckets > static_cast<std::uint32_t>(MaxKingBuckets)) return fail(error, "king buckets out of range 1-32");
    if (output_buckets < 1U || output_buckets > static_cast<std::uint32_t>(MaxOutputBuckets)) {
        return fail(error, "output buckets " + std::to_string(output_buckets) + " not supported (max " +
                               std::to_string(MaxOutputBuckets) + ")");
    }
    if ((flags & ~(FlagResidual | FlagMirror)) != 0U) return fail(error, "unknown flag bits");
    if (read_f32(bytes, 40) != WeightScale || read_f32(bytes, 44) != OutputScale || read_f32(bytes, 48) != SigmoidK) {
        return fail(error, "quantisation scales / sigmoid K differ from the engine's (4096, 4096, 2.25)");
    }
    for (std::size_t i = 0; i < 64; ++i) {
        if (bytes[52 + i] >= king_buckets) return fail(error, "king bucket map entry out of range");
    }
    for (std::size_t i = 0; i < 33; ++i) {
        if (bytes[116 + i] >= output_buckets) return fail(error, "output bucket map entry out of range");
    }
    for (std::size_t i = 149; i < static_cast<std::size_t>(HeaderBytes); ++i) {
        if (bytes[i] != 0U) return fail(error, "reserved header bytes are not zero");
    }
    const bool threats = (feature_set & FeatureSetThreats) != 0U;
    const bool pawn_pairs = (feature_set & FeatureSetPawnPairs) != 0U;   // O7
    const std::size_t w1_count = static_cast<std::size_t>(king_buckets) * InputCount * HiddenSize;
    const std::size_t wt_count = threats ? static_cast<std::size_t>(ThreatFeatures) * HiddenSize : 0U;
    const std::size_t wp_count = pawn_pairs ? static_cast<std::size_t>(PawnPairFeatures) * HiddenSize : 0U;
    const std::size_t w2_count = static_cast<std::size_t>(output_buckets) * 2U * HiddenSize;
    const std::uint64_t expected = file_bytes(static_cast<int>(king_buckets), static_cast<int>(output_buckets), feature_set);
    if (size != expected) {
        return fail(error, "file size " + std::to_string(size) + " bytes does not match the " + std::to_string(expected) +
                               " bytes implied by its header (" + std::to_string(king_buckets) + " king buckets, " +
                               std::to_string(output_buckets) + " output buckets, hidden " + std::to_string(HiddenSize) +
                               (threats ? ", threat inputs" : "") + (pawn_pairs ? ", pawn-pair inputs" : "") + "); the weights were not read");
    }
    // Only now are the weight blocks allocated and read.
    std::vector<unsigned char> all(static_cast<std::size_t>(expected));
    std::copy(header.begin(), header.end(), all.begin());
    file.read(reinterpret_cast<char*>(all.data() + HeaderBytes), static_cast<std::streamsize>(expected - HeaderBytes));
    if (!file) return fail(error, "cannot read the weights of " + path);
    last_bytes_read = expected;
    bytes = all.data();
    std::uint64_t stored = 0;
    for (std::size_t i = 8; i-- > 0;) stored = (stored << 8U) | bytes[all.size() - 8U + i];
    const std::uint64_t checksum = fnv1a64(bytes, all.size() - 8U);
    if (stored != checksum) return fail(error, "checksum mismatch (file damaged)");

    auto net = std::make_unique<Net>();
    net->path = path;
    net->king_buckets = static_cast<int>(king_buckets);
    net->output_buckets = static_cast<int>(output_buckets);
    net->mirror = (flags & FlagMirror) != 0U;
    net->residual = (flags & FlagResidual) != 0U;
    net->threats = threats;
    net->pawn_pairs = pawn_pairs;
    net->checksum = checksum;
    std::copy(bytes + 52, bytes + 116, net->king_map.begin());
    std::copy(bytes + 116, bytes + 149, net->output_map.begin());
    net->w1.allocate(w1_count);
    if (threats) net->wt.allocate(wt_count);
    if (pawn_pairs) net->wp.allocate(wp_count);
    net->b1.allocate(HiddenSize);
    net->w2.allocate(w2_count);
    net->b2.assign(output_buckets, 0.0F);
    std::size_t offset = static_cast<std::size_t>(HeaderBytes);
    // Same de-quantisation as the compiled-in network (weights(): int / scale).
    for (std::size_t i = 0; i < w1_count; ++i, offset += 2) net->w1.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < wt_count; ++i, offset += 2) net->wt.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < wp_count; ++i, offset += 2) net->wp.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < HiddenSize; ++i, offset += 2) net->b1.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;
    for (std::size_t i = 0; i < w2_count; ++i, offset += 2) net->w2.data()[i] = static_cast<float>(read_i16(bytes, offset)) / OutputScale;
    for (std::size_t i = 0; i < output_buckets; ++i, offset += 2) net->b2[i] = static_cast<float>(read_i16(bytes, offset)) / OutputScale;

    loaded_net = net.release();
    return true;
}

[[gnu::cold]] void unload() {
    if (active_net == loaded_net) active_net = nullptr;
    delete loaded_net;
    loaded_net = nullptr;
}

[[gnu::cold]] const Net* loaded() { return loaded_net; }

[[gnu::cold]] std::string summary(const Net& net) {
    std::ostringstream out;
    out << net.path << " king buckets " << net.king_buckets << " output buckets " << net.output_buckets << " hidden "
        << HiddenSize << (net.mirror ? " mirrored" : " unmirrored") << (net.residual ? " residual" : " stand-alone")
        << (net.threats ? " threat inputs" : "") << (net.pawn_pairs ? " pawn-pair inputs" : "") << " fnv1a " << std::hex << std::setw(16) << std::setfill('0') << net.checksum;
    return out.str();
}

[[gnu::cold]] const Net* select(int king_buckets, int output_buckets, std::string* message) {
    active_net = nullptr;
    std::string text;
    const std::string options = "NNUEKingBuckets " + std::to_string(std::max(king_buckets, 0)) +
                                ", NNUEOutputBuckets " + std::to_string(std::max(output_buckets, 0));
    if (king_buckets <= 0 && output_buckets <= 0) {
        text = "off (NNUEKingBuckets 0, NNUEOutputBuckets 0): compiled-in network";
    } else if (loaded_net == nullptr) {
        text = options + " needs a v2 net (NNUEFile)";
    } else if (king_buckets > 0 ? loaded_net->king_buckets != king_buckets
                                : (loaded_net->king_buckets != 1 || loaded_net->mirror)) {
        text = options + " does not match the loaded net (" + std::to_string(loaded_net->king_buckets) +
               (loaded_net->mirror ? " mirrored" : "") + " king buckets)";
    } else if (output_buckets > 0 ? loaded_net->output_buckets != output_buckets : loaded_net->output_buckets != 1) {
        text = options + " does not match the loaded net (" + std::to_string(loaded_net->output_buckets) +
               " output buckets)";
    } else {
        active_net = loaded_net;
        text = "active: " + summary(*loaded_net);
    }
    if (message != nullptr) *message = text;
    return active_net;
}

[[gnu::cold]] Description describe(const Net& net) {
    Description d;
    d.path = net.path;
    d.king_buckets = net.king_buckets;
    d.output_buckets = net.output_buckets;
    d.mirror = net.mirror;
    d.residual = net.residual;
    d.threats = net.threats;
    d.pawn_pairs = net.pawn_pairs;
    d.checksum = net.checksum;
    d.output_bucket_map = net.output_map;
    return d;
}

[[gnu::cold]] RefreshCache& make_cache(const Net& net, int worker_id) {
    std::unique_ptr<RefreshCache>& slot = net.caches[static_cast<std::size_t>(std::clamp(worker_id, 0, MaxWorkers - 1))];
    if (slot == nullptr) {
        auto cache = std::make_unique<RefreshCache>();
        cache->entries.resize(static_cast<std::size_t>(2 * net.king_buckets * 2));
        for (RefreshCache::Entry& entry : cache->entries) {
            std::copy(net.b1.data(), net.b1.data() + HiddenSize, entry.values.begin());
            entry.pieces.fill(0);
        }
        slot = std::move(cache);
    }
    return *slot;
}

} // namespace forge::nnue::v2
