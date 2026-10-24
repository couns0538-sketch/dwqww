#include "forge/nnue.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <memory>

// The output layer uses SSE min/max/mul/add directly: compilers may not turn a
// float clamp into min/max instructions without -ffast-math, which left the
// AVX2 builds with slow scalar code. SSE2 is part of every x86-64 target.
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#define FORGE_NNUE_SSE 1
#else
#define FORGE_NNUE_SSE 0
#endif

#ifndef FORGE_AVX512
#define FORGE_AVX512 0
#endif
#if FORGE_AVX512 && !defined(__AVX512F__)
#error "FORGE_AVX512=1 requires AVX-512F compiler support"
#endif

#if defined(__AVX2__) || FORGE_AVX512
#include <immintrin.h>
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

struct Weights {
    std::unique_ptr<float[]> w1;   // [InputCount][HiddenSize]
    alignas(32) std::array<float, HiddenSize> b1{};
    alignas(32) std::array<float, 2 * HiddenSize> w2{};
    float b2 = 0.0F;
};

const Weights& weights() {
    static const Weights instance = [] {
        Weights w;
        w.w1 = std::make_unique<float[]>(static_cast<std::size_t>(InputCount) * HiddenSize);
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

#if FORGE_AVX512
static_assert(HiddenSize % 16 == 0, "AVX-512 requires HiddenSize to be a multiple of 16");

inline void copy_accumulator(float* destination, const float* source) {
    for (int h = 0; h < HiddenSize; h += 16) {
        _mm512_storeu_ps(destination + h, _mm512_loadu_ps(source + h));
    }
}

// Keep one partial sum for each index modulo 16. Output-head selection can
// supply another w2/b2 pair without changing this arithmetic kernel.
inline float evaluate_avx512(const float* ours, const float* theirs, const float* w2, const float* b2) {
    const __m512 zero = _mm512_setzero_ps();
    const __m512 one = _mm512_set1_ps(1.0F);
    __m512 sums = zero;
    for (int h = 0; h < HiddenSize; h += 16) {
        const __m512 a = _mm512_min_ps(_mm512_max_ps(_mm512_loadu_ps(ours + h), zero), one);
        const __m512 b = _mm512_min_ps(_mm512_max_ps(_mm512_loadu_ps(theirs + h), zero), one);
        const __m512 a_term = _mm512_mul_ps(_mm512_mul_ps(a, a), _mm512_loadu_ps(w2 + h));
        const __m512 b_term = _mm512_mul_ps(_mm512_mul_ps(b, b), _mm512_loadu_ps(w2 + HiddenSize + h));
        const __m512 term = _mm512_add_ps(a_term, b_term);
        sums = _mm512_add_ps(sums, term);
    }
    alignas(64) float lanes[16];
    _mm512_storeu_ps(lanes, sums);
    float out = *b2;
    for (int j = 0; j < 16; ++j) out += lanes[j];
    return out;
}
#endif

inline void add_feature(std::array<float, HiddenSize>& acc, const float* column) {
#if FORGE_AVX512
    for (int h = 0; h < HiddenSize; h += 16) {
        _mm512_storeu_ps(acc.data() + h, _mm512_add_ps(_mm512_loadu_ps(acc.data() + h), _mm512_loadu_ps(column + h)));
    }
#else
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] += column[h];
#endif
}

inline void sub_feature(std::array<float, HiddenSize>& acc, const float* column) {
#if FORGE_AVX512
    for (int h = 0; h < HiddenSize; h += 16) {
        _mm512_storeu_ps(acc.data() + h, _mm512_sub_ps(_mm512_loadu_ps(acc.data() + h), _mm512_loadu_ps(column + h)));
    }
#else
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] -= column[h];
#endif
}

} // namespace

bool available() { return FORGE_HAS_NNUE != 0; }

bool residual() { return FORGE_HAS_NNUE != 0 && FORGE_NNUE_RESIDUAL != 0; }

void refresh(const Board& board, Accumulator& accumulator) {
    const Weights& w = weights();
    for (const Color perspective : {White, Black}) {
        auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
#if FORGE_AVX512
        copy_accumulator(acc.data(), w.b1.data());
#else
        acc = w.b1;
#endif
        Bitboard occupied = board.occupied();
        while (occupied != 0) {
            const int square = pop_lsb(occupied);
            const int index = feature_index(perspective, board.piece_at(square), square);
            add_feature(acc, w.w1.get() + static_cast<std::size_t>(index) * HiddenSize);
        }
    }
    accumulator.valid = true;
}

void update(const Accumulator& parent, Accumulator& child, const DirtyPieces& dirty) {
    const Weights& w = weights();
    // Quiet moves (including noncapturing promotions) remove one feature and
    // add one. Keep each lane's subtraction-then-addition order while avoiding
    // a full copy and two separate read/write passes over the child.
    if (dirty.count == 2 && !dirty.changes[0].add && dirty.changes[1].add) {
        for (const Color perspective : {White, Black}) {
            const auto& source = parent.values[static_cast<std::size_t>(perspective)];
            auto& destination = child.values[static_cast<std::size_t>(perspective)];
            const PieceChange& removed = dirty.changes[0];
            const PieceChange& added = dirty.changes[1];
            const float* removed_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, removed.piece, removed.square)) * HiddenSize;
            const float* added_column = w.w1.get() +
                static_cast<std::size_t>(feature_index(perspective, added.piece, added.square)) * HiddenSize;
#if FORGE_AVX512
            for (int h = 0; h < HiddenSize; h += 16) {
                const __m512 after_remove = _mm512_sub_ps(_mm512_loadu_ps(source.data() + h), _mm512_loadu_ps(removed_column + h));
                _mm512_storeu_ps(destination.data() + h, _mm512_add_ps(after_remove, _mm512_loadu_ps(added_column + h)));
            }
#else
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = (source[index] - removed_column[index]) + added_column[index];
            }
#endif
        }
        child.valid = true;
        return;
    }
    // Captures remove the mover and captured piece before adding the mover
    // (or promoted piece). Preserve both intermediate subtractions per lane.
    if (dirty.count == 3 && !dirty.changes[0].add && !dirty.changes[1].add && dirty.changes[2].add) {
        for (const Color perspective : {White, Black}) {
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
#if FORGE_AVX512
            for (int h = 0; h < HiddenSize; h += 16) {
                const __m512 after_remove0 = _mm512_sub_ps(_mm512_loadu_ps(source.data() + h), _mm512_loadu_ps(removed0_column + h));
                const __m512 after_remove1 = _mm512_sub_ps(after_remove0, _mm512_loadu_ps(removed1_column + h));
                _mm512_storeu_ps(destination.data() + h, _mm512_add_ps(after_remove1, _mm512_loadu_ps(added_column + h)));
            }
#else
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = ((source[index] - removed0_column[index]) - removed1_column[index]) + added_column[index];
            }
#endif
        }
        child.valid = true;
        return;
    }
    for (const Color perspective : {White, Black}) {
        auto& acc = child.values[static_cast<std::size_t>(perspective)];
#if FORGE_AVX512
        copy_accumulator(acc.data(), parent.values[static_cast<std::size_t>(perspective)].data());
#else
        acc = parent.values[static_cast<std::size_t>(perspective)];
#endif
        for (int i = 0; i < dirty.count; ++i) {
            const PieceChange& change = dirty.changes[static_cast<std::size_t>(i)];
            const int index = feature_index(perspective, change.piece, change.square);
            const float* column = w.w1.get() + static_cast<std::size_t>(index) * HiddenSize;
            if (change.add) add_feature(acc, column);
            else sub_feature(acc, column);
        }
    }
    child.valid = true;
}

int evaluate(const Board& board, const Accumulator& accumulator) {
    const Weights& w = weights();
    const Color us = board.side_to_move();
    const auto& ours = accumulator.values[static_cast<std::size_t>(us)];
    const auto& theirs = accumulator.values[static_cast<std::size_t>(opposite(us))];
#if FORGE_AVX512
    const float out = evaluate_avx512(ours.data(), theirs.data(), w.w2.data(), &w.b2);
#else
    // Sixteen independent partial sums (lane j takes the hidden units with
    // index % 16 == j, in increasing order) and then one ordered sum: the
    // association is fixed by the source, so every target (SSE, AVX2, AVX-512,
    // the scalar fallback) produces bit-identical results without -ffast-math.
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
#endif
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
