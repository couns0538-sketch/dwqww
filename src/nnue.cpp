#include "forge/nnue.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <memory>
#include <new>

// Kernel selection is compile-time only, and every path is bit-identical: each
// accumulator lane and each output partial sum sees the same float operations
// in the same order as the portable code (no FMA, no -ffast-math, no
// reassociation). FORGE_NNUE_FORCE_SCALAR selects the portable code on any
// target (used by the parity tests).
//
// The output layer uses SSE min/max/mul/add directly: compilers may not turn a
// float clamp into min/max instructions without -ffast-math, which left the
// AVX2 builds with slow scalar code. SSE2 is part of every x86-64 target.
#if !defined(FORGE_NNUE_FORCE_SCALAR) && (defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64))
#include <xmmintrin.h>
#define FORGE_NNUE_SSE 1
#else
#define FORGE_NNUE_SSE 0
#endif

#if !defined(FORGE_NNUE_FORCE_SCALAR) && defined(__AVX2__)
#include <immintrin.h>
#define FORGE_NNUE_AVX2 1
#else
#define FORGE_NNUE_AVX2 0
#endif

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

#if __has_include("nnue_weights.inc")
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

struct Weights {
    AlignedFloats w1;   // [InputCount][HiddenSize]
    alignas(64) std::array<float, HiddenSize> b1{};
    alignas(64) std::array<float, 2 * HiddenSize> w2{};
    float b2 = 0.0F;
};

const Weights& weights() {
    static const Weights instance = [] {
        Weights w;
        w.w1 = aligned_zeros(static_cast<std::size_t>(InputCount) * HiddenSize);
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

inline const float* column(const Weights& w, Color perspective, Piece piece, int square) {
    return w.w1.get() + static_cast<std::size_t>(feature_index(perspective, piece, square)) * HiddenSize;
}

inline void add_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] += column[h];
}

inline void sub_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] -= column[h];
}

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

} // namespace

bool available() { return FORGE_HAS_NNUE != 0; }

bool residual() { return FORGE_HAS_NNUE != 0 && FORGE_NNUE_RESIDUAL != 0; }

void refresh(const Board& board, Accumulator& accumulator) {
    const Weights& w = weights();
    for (const Color perspective : {White, Black}) {
        std::array<const float*, 64> columns;
        std::size_t count = 0;
        Bitboard occupied = board.occupied();
        while (occupied != 0) {
            const int square = pop_lsb(occupied);
            columns[count++] = column(w, perspective, board.piece_at(square), square);
        }
        accumulate_columns(accumulator.values[static_cast<std::size_t>(perspective)].data(), w.b1.data(), columns.data(),
                           count);
    }
    accumulator.valid = true;
}

void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {
    const Weights& w = weights();
    const auto& changes = dirty.changes;
    // Quiet moves (including noncapturing promotions) remove one feature and
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
        for (const Color perspective : {White, Black}) {
            const std::size_t side = static_cast<std::size_t>(perspective);
            apply_sub_sub_add(child.values[side].data(), parent.values[side].data(),
                              column(w, perspective, changes[0].piece, changes[0].square),
                              column(w, perspective, changes[1].piece, changes[1].square),
                              column(w, perspective, changes[2].piece, changes[2].square));
        }
        child.valid = true;
        return;
    }
    if (dirty.count == 4 && !changes[0].add && changes[1].add && !changes[2].add && changes[3].add) {
        for (const Color perspective : {White, Black}) {
            const std::size_t side = static_cast<std::size_t>(perspective);
            apply_sub_add_sub_add(child.values[side].data(), parent.values[side].data(),
                                  column(w, perspective, changes[0].piece, changes[0].square),
                                  column(w, perspective, changes[1].piece, changes[1].square),
                                  column(w, perspective, changes[2].piece, changes[2].square),
                                  column(w, perspective, changes[3].piece, changes[3].square));
        }
        child.valid = true;
        return;
    }
    // Null moves (no change) and any other change list: copy, then apply each
    // change in order.
    for (const Color perspective : {White, Black}) {
        auto& acc = child.values[static_cast<std::size_t>(perspective)];
        acc = parent.values[static_cast<std::size_t>(perspective)];
        for (int i = 0; i < dirty.count; ++i) {
            const PieceChange& change = changes[static_cast<std::size_t>(i)];
            const float* feature = column(w, perspective, change.piece, change.square);
            if (change.add) add_feature(acc, feature);
            else sub_feature(acc, feature);
        }
    }
    child.valid = true;
}

int evaluate(const Board& board, const Accumulator& accumulator) {
    const Weights& w = weights();
    const Color us = board.side_to_move();
    const auto& ours = accumulator.values[static_cast<std::size_t>(us)];
    const auto& theirs = accumulator.values[static_cast<std::size_t>(opposite(us))];
    // Sixteen independent partial sums (lane j takes the hidden units with
    // index % 16 == j, in increasing order) and then one ordered sum: the
    // association is fixed by the source, so every target (SSE, AVX2, the
    // scalar fallback) produces bit-identical results without -ffast-math.
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
