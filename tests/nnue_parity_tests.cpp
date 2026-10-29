// NNUE parity harness (O2). Compares the current nnue::refresh / update /
// evaluate with lock_ref, a verbatim copy of the AL1 s198 (294dbed)
// src/nnue.cpp implementation (opus_round1/O2/verify_lock_ref.py checks the
// copy), bit for bit: every accumulator float as its bit pattern and every
// evaluate() result, on
//   - random make/unmake walks: legal moves and null moves, back-tracking to a
//     lower ply as a search does; every visited position is compared after an
//     incremental update, and regularly after a full refresh;
//   - in-place updates (parent == child), part of the update() contract;
//   - FEN files (--fens: one FEN per line, extra " | ..." fields ignored, the
//     5_nnue forge_text_sample format), each refreshed and used as a walk root;
//   - .pos files (--pos: the 5_nnue v3b record format; the synthetic boards
//     are made acceptable to Board::set_fen first, see pos_record_fen);
//   - synthetic accumulators with SCReLU edge values for evaluate().
// The last lines are the counts and a digest over every compared output.
// Build this test for each kernel target (portable code with
// -DFORGE_NNUE_FORCE_SCALAR, SSE2, AVX2, the compiler-widened AVX-512 build):
// the digest must be the same for all of them.
// usage: forge_nnue_parity_tests [--walk-positions N] [--synthetic N]
//        [--fens FILE]... [--pos FILE]... [--pos-limit N]
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// ---- BEGIN verbatim AL1 s198 src/nnue.cpp lines 8-20 ----
// The output layer uses SSE min/max/mul/add directly: compilers may not turn a
// float clamp into min/max instructions without -ffast-math, which left the
// AVX2 builds with slow scalar code. SSE2 is part of every x86-64 target.
#if defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64)
#include <xmmintrin.h>
#define FORGE_NNUE_SSE 1
#else
#define FORGE_NNUE_SSE 0
#endif

#if defined(__AVX2__)
#include <immintrin.h>
#endif
// ---- END verbatim ----

#if __has_include("../src/nnue_weights.inc")
#include "../src/nnue_weights.inc"
#define FORGE_HAS_NNUE 1
#else
#define FORGE_HAS_NNUE 0
#endif

// The AL1 s198 implementation, unchanged, as the oracle.
namespace forge::nnue::lock_ref {

// ---- BEGIN verbatim AL1 s198 src/nnue.cpp lines 46-76 ----
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

inline void add_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] += column[h];
}

inline void sub_feature(std::array<float, HiddenSize>& acc, const float* column) {
    for (int h = 0; h < HiddenSize; ++h) acc[static_cast<std::size_t>(h)] -= column[h];
}
// ---- END verbatim ----

// ---- BEGIN verbatim AL1 s198 src/nnue.cpp lines 84-216 ----
void refresh(const Board& board, Accumulator& accumulator) {
    const Weights& w = weights();
    for (const Color perspective : {White, Black}) {
        auto& acc = accumulator.values[static_cast<std::size_t>(perspective)];
        acc = w.b1;
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
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = (source[index] - removed_column[index]) + added_column[index];
            }
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
            for (int h = 0; h < HiddenSize; ++h) {
                const std::size_t index = static_cast<std::size_t>(h);
                destination[index] = ((source[index] - removed0_column[index]) - removed1_column[index]) + added_column[index];
            }
        }
        child.valid = true;
        return;
    }
    for (const Color perspective : {White, Black}) {
        auto& acc = child.values[static_cast<std::size_t>(perspective)];
        acc = parent.values[static_cast<std::size_t>(perspective)];
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
    const float centipawns = out * 400.0F / SigmoidK;
    return static_cast<int>(std::clamp(centipawns, -30000.0F, 30000.0F));
}
// ---- END verbatim ----

} // namespace forge::nnue::lock_ref

namespace {

using forge::nnue::Accumulator;
using forge::nnue::DirtyPieces;
using forge::nnue::HiddenSize;

struct Stats {
    std::uint64_t positions = 0;    // evaluate() comparisons on real positions
    std::uint64_t updates = 0;      // incremental updates compared
    std::uint64_t refreshes = 0;    // full refreshes compared
    std::uint64_t in_place = 0;     // in-place updates compared
    std::uint64_t quiet = 0, captures = 0, en_passant = 0, promotions = 0, capture_promotions = 0, castles = 0,
                  null_moves = 0;
    std::uint64_t synthetic = 0;
    std::uint64_t fens = 0, pos_used = 0, pos_skipped = 0;
    std::uint64_t digest = 14695981039346656037ULL;   // FNV-1a over every compared output
} stats;

std::uint64_t random_state = 0x0b2c0de5eed0f00dULL;
std::uint64_t next_random() {   // splitmix64
    std::uint64_t z = (random_state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

void mix(std::uint32_t word) {
    for (int shift = 0; shift < 32; shift += 8) {
        stats.digest ^= (word >> shift) & 255U;
        stats.digest *= 1099511628211ULL;
    }
}

[[noreturn]] void fail(const std::string& what) { throw std::runtime_error(what); }

void compare_accumulators(const Accumulator& now, const Accumulator& ref, const char* what, const forge::Board& board) {
    for (std::size_t side = 0; side < 2; ++side) {
        for (std::size_t h = 0; h < static_cast<std::size_t>(HiddenSize); ++h) {
            const auto a = std::bit_cast<std::uint32_t>(now.values[side][h]);
            const auto b = std::bit_cast<std::uint32_t>(ref.values[side][h]);
            if (a != b) {
                char detail[96];
                std::snprintf(detail, sizeof detail, " side %zu lane %zu: %08x vs lock %08x", side, h,
                              static_cast<unsigned>(a), static_cast<unsigned>(b));
                fail(std::string(what) + detail + " in " + board.fen());
            }
            // Exactness invariant (REPORT.md): every accumulator value is an
            // integer multiple of 2^-12 well inside the float significand, so
            // no addition or subtraction producing it was ever rounded.
            const float scaled = std::ldexp(now.values[side][h], 12);
            if (scaled != std::trunc(scaled) || std::fabs(scaled) >= 0x1p23F)
                fail(std::string(what) + ": accumulator value is not an exact multiple of 2^-12 in " + board.fen());
            mix(a);
        }
    }
    if (now.valid != ref.valid || !now.valid) fail(std::string(what) + ": valid flag differs in " + board.fen());
}

void compare_evaluate(const forge::Board& board, const Accumulator& now, const Accumulator& ref) {
    const int a = forge::nnue::evaluate(board, now);
    const int b = forge::nnue::lock_ref::evaluate(board, ref);
    if (a != b) fail("evaluate " + std::to_string(a) + " vs lock " + std::to_string(b) + " in " + board.fen());
    mix(static_cast<std::uint32_t>(a));
    ++stats.positions;
}

void compare_refresh(const forge::Board& board) {
    Accumulator now;
    Accumulator ref;
    for (auto& side : now.values) side.fill(-0x1.fffffep10F);   // catch lanes a kernel does not write
    forge::nnue::refresh(board, now);
    forge::nnue::lock_ref::refresh(board, ref);
    compare_accumulators(now, ref, "refresh", board);
    compare_evaluate(board, now, ref);
    ++stats.refreshes;
}

void classify(const forge::Board& board, const forge::Move& move) {
    if (move.is_castle()) ++stats.castles;
    else if ((move.flags & forge::EnPassant) != 0U) ++stats.en_passant;
    else if (move.is_promotion()) ++(board.captured_piece(move) != forge::Empty ? stats.capture_promotions : stats.promotions);
    else if (board.captured_piece(move) != forge::Empty) ++stats.captures;
    else ++stats.quiet;
}

struct Frame {
    Accumulator now;
    Accumulator ref;
    forge::Move move{};
    forge::Undo undo{};
    forge::NullUndo null_undo{};
    bool null_move = false;
};

constexpr std::size_t MaxWalkPly = 160;

// Random walk from `fen` comparing `budget` incrementally updated positions.
void walk(const std::string& fen, std::uint64_t budget) {
    forge::Board board;
    if (!board.set_fen(fen)) fail("walk root rejected: " + fen);
    std::vector<Frame> stack(MaxWalkPly + 1);
    forge::nnue::refresh(board, stack[0].now);
    forge::nnue::lock_ref::refresh(board, stack[0].ref);
    compare_accumulators(stack[0].now, stack[0].ref, "root refresh", board);
    compare_evaluate(board, stack[0].now, stack[0].ref);
    std::size_t ply = 0;
    const auto pop = [&]() {
        const Frame& frame = stack[ply];
        if (frame.null_move) board.unmake_null_move(frame.null_undo);
        else board.unmake_move(frame.move, frame.undo);
        --ply;
    };
    for (std::uint64_t done = 0; done < budget;) {
        const std::uint64_t r = next_random();
        // Back-track like a search returning from a subtree.
        if (ply > 0 && (r % 8 == 0 || ply == MaxWalkPly)) {
            for (std::size_t back = 1 + (r >> 8) % std::min<std::size_t>(ply, 6); back > 0; --back) pop();
            continue;
        }
        Frame& parent = stack[ply];
        Frame& child = stack[ply + 1];
        DirtyPieces dirty;
        if (ply > 0 && !board.in_check() && !stack[ply].null_move && (r >> 16) % 16 == 0) {
            board.make_null_move(child.null_undo);
            child.null_move = true;
            ++stats.null_moves;
        } else {
            const auto moves = board.legal_moves();
            if (moves.empty()) {
                if (ply == 0) break;
                pop();
                continue;
            }
            // Castles, en passant and promotions are rare in random play: on half
            // of the steps take one of them whenever the position has any.
            std::size_t pick = static_cast<std::size_t>((r >> 20) % moves.size());
            if ((r >> 48) % 2 == 0) {
                std::size_t special = 0;
                for (const forge::Move candidate : moves)
                    special += candidate.is_castle() || candidate.is_promotion() || (candidate.flags & forge::EnPassant) != 0U;
                if (special != 0) {
                    std::size_t target = static_cast<std::size_t>((r >> 52) % special);
                    for (pick = 0;; ++pick) {
                        const forge::Move candidate = moves[pick];
                        if ((candidate.is_castle() || candidate.is_promotion() || (candidate.flags & forge::EnPassant) != 0U) &&
                            target-- == 0)
                            break;
                    }
                }
            }
            const forge::Move move = moves[pick];
            dirty = forge::nnue::dirty_pieces(board, move);
            classify(board, move);
            child.move = move;
            child.null_move = false;
            if (!board.make_move(move, child.undo)) fail("legal move rejected in " + board.fen());
        }
        ++ply;
        for (auto& side : child.now.values) side.fill(-0x1.fffffep10F);
        child.now.valid = false;
        child.ref.valid = false;
        forge::nnue::update(parent.now, child.now, dirty);
        forge::nnue::lock_ref::update(parent.ref, child.ref, dirty);
        compare_accumulators(child.now, child.ref, "update", board);
        compare_evaluate(board, child.now, child.ref);
        ++stats.updates;
        ++done;
        if ((r >> 32) % 4 == 0) {
            Accumulator in_place = parent.now;
            forge::nnue::update(in_place, in_place, dirty);
            compare_accumulators(in_place, child.ref, "in-place update", board);
            ++stats.in_place;
        }
        if ((r >> 40) % 32 == 0) compare_refresh(board);
    }
}

// Every legal move sequence of `depth` plies from `board` (a perft walk), so
// each castle, en passant capture and promotion near a fixture is covered.
void exhaustive(forge::Board& board, const Accumulator& parent_now, const Accumulator& parent_ref, int depth) {
    for (const forge::Move move : board.legal_moves()) {
        const DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
        classify(board, move);
        forge::Undo undo;
        if (!board.make_move(move, undo)) fail("legal move rejected in " + board.fen());
        Accumulator now;
        Accumulator ref;
        for (auto& side : now.values) side.fill(-0x1.fffffep10F);
        forge::nnue::update(parent_now, now, dirty);
        forge::nnue::lock_ref::update(parent_ref, ref, dirty);
        compare_accumulators(now, ref, "exhaustive update", board);
        compare_evaluate(board, now, ref);
        ++stats.updates;
        if (depth > 1) exhaustive(board, now, ref, depth - 1);
        board.unmake_move(move, undo);
    }
}

std::string trim(std::string_view text) {
    const auto begin = text.find_first_not_of(" \t\r\n");
    if (begin == std::string_view::npos) return {};
    const auto end = text.find_last_not_of(" \t\r\n");
    return std::string(text.substr(begin, end - begin + 1));
}

std::vector<std::string> read_fens(const std::string& path) {
    std::ifstream in(path);
    if (!in) fail("cannot open " + path);
    std::vector<std::string> fens;
    for (std::string line; std::getline(in, line);) {
        const std::string fen = trim(std::string_view(line).substr(0, line.find('|')));
        if (!fen.empty() && fen[0] != '#') fens.push_back(fen);
    }
    return fens;
}

// A v3b .pos board (64 nibbles: 0 empty, 1..6 white P N B R Q K, 7..12 black)
// made acceptable to Board::set_fen, deterministically: pawns on the first or
// last rank are dropped, each side keeps its lowest-square king (a missing or
// adjacent king goes to the first empty square not next to the other king),
// and excess pawns / promoted pieces are dropped from the highest squares.
// The side to move is the record's, or the other one if that is the only
// legal choice; boards that fit neither are skipped (and counted).
std::string pos_record_fen(const std::uint8_t* packed, bool black_to_move, bool flip_side) {
    std::array<int, 64> code{};
    for (int square = 0; square < 64; ++square) {
        const int value = (packed[square >> 1] >> ((square & 1) * 4)) & 15;
        code[static_cast<std::size_t>(square)] = value <= 12 ? value : 0;
    }
    for (int square = 0; square < 64; ++square) {
        const int value = code[static_cast<std::size_t>(square)];
        if ((value == 1 || value == 7) && (square < 8 || square >= 56)) code[static_cast<std::size_t>(square)] = 0;
    }
    const auto adjacent = [](int a, int b) { return std::max(std::abs(a % 8 - b % 8), std::abs(a / 8 - b / 8)) <= 1; };
    std::array<int, 2> king{-1, -1};
    for (int square = 0; square < 64; ++square) {
        for (int color = 0; color < 2; ++color) {
            if (code[static_cast<std::size_t>(square)] != 6 + 6 * color) continue;
            if (king[static_cast<std::size_t>(color)] < 0) king[static_cast<std::size_t>(color)] = square;
            else code[static_cast<std::size_t>(square)] = 0;
        }
    }
    for (int color = 0; color < 2; ++color) {
        int& own = king[static_cast<std::size_t>(color)];
        const int other = king[static_cast<std::size_t>(1 - color)];
        if (own >= 0 && !(other >= 0 && adjacent(own, other))) continue;
        if (own >= 0) code[static_cast<std::size_t>(own)] = 0;
        own = -1;
        for (int square = 0; square < 64 && own < 0; ++square) {
            if (code[static_cast<std::size_t>(square)] == 0 && !(other >= 0 && adjacent(square, other))) {
                own = square;
                code[static_cast<std::size_t>(square)] = 6 + 6 * color;
            }
        }
        if (own < 0) return {};
    }
    for (int color = 0; color < 2; ++color) {
        const int offset = 6 * color;
        const auto count = [&](int type) {
            return static_cast<int>(std::count(code.begin(), code.end(), type + offset));
        };
        const auto drop_highest = [&](int type) {
            for (int square = 63; square >= 0; --square) {
                if (code[static_cast<std::size_t>(square)] == type + offset) {
                    code[static_cast<std::size_t>(square)] = 0;
                    return;
                }
            }
        };
        while (count(1) > 8) drop_highest(1);
        for (;;) {
            const int promoted = std::max(0, count(2) - 2) + std::max(0, count(3) - 2) + std::max(0, count(4) - 2) +
                                 std::max(0, count(5) - 1);
            if (promoted <= 8 - count(1)) break;
            drop_highest(count(5) > 1 ? 5 : count(4) > 2 ? 4 : count(3) > 2 ? 3 : 2);
        }
    }
    static constexpr std::string_view Letters = ".PNBRQKpnbrqk";
    std::string fen;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const int value = code[static_cast<std::size_t>(rank * 8 + file)];
            if (value == 0) {
                ++empty;
                continue;
            }
            if (empty != 0) fen += static_cast<char>('0' + empty);
            empty = 0;
            fen += Letters[static_cast<std::size_t>(value)];
        }
        if (empty != 0) fen += static_cast<char>('0' + empty);
        if (rank != 0) fen += '/';
    }
    fen += (black_to_move != flip_side) ? " b - - 0 1" : " w - - 0 1";
    return fen;
}

void check_pos_file(const std::string& path, std::uint64_t limit) {
    std::ifstream in(path, std::ios::binary);
    if (!in) fail("cannot open " + path);
    std::vector<char> raw((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    if (raw.size() < 16 || std::string_view(raw.data(), 4) != "FPOS") fail(path + ": not a v3b .pos file");
    std::uint64_t n = 0;
    for (int i = 0; i < 8; ++i) n |= static_cast<std::uint64_t>(static_cast<unsigned char>(raw[static_cast<std::size_t>(8 + i)])) << (8 * i);
    if (raw.size() != 16 + 35 * n) fail(path + ": size does not match the record count");
    const auto* boards = reinterpret_cast<const std::uint8_t*>(raw.data() + 16);
    const auto* meta = reinterpret_cast<const std::uint8_t*>(raw.data() + 16 + 34 * n);
    forge::Board board;
    for (std::uint64_t i = 0; i < std::min(n, limit); ++i) {
        const bool black = (meta[i] & 1U) != 0U;
        std::string fen = pos_record_fen(boards + 32 * i, black, false);
        if (fen.empty() || !board.set_fen(fen)) {
            fen = pos_record_fen(boards + 32 * i, black, true);
            if (fen.empty() || !board.set_fen(fen)) {
                ++stats.pos_skipped;
                continue;
            }
        }
        compare_refresh(board);
        ++stats.pos_used;
        if (i % 16 == 0) walk(fen, 8);   // a few updates on unusual material too
    }
}

// Synthetic accumulators: SCReLU edge values (negative, signed zero, the
// smallest denormal, values next to the clamp at 1.0) and random finite ones.
void check_synthetic(std::uint64_t samples) {
    constexpr std::array<float, 8> Edges{-2.0F, -0.0F, 0.0F, 0x1p-149F, 0x1.fffffep-1F, 1.0F, 0x1.000002p0F, 2.0F};
    forge::Board white;
    forge::Board black;
    if (!white.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1") ||
        !black.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"))
        fail("synthetic fixtures rejected");
    Accumulator acc;
    acc.valid = true;
    for (std::uint64_t sample = 0; sample < samples; ++sample) {
        for (auto& side : acc.values) {
            for (float& value : side) {
                const std::uint64_t word = next_random();
                value = sample < samples / 100 ? Edges[static_cast<std::size_t>((word >> 32U) % Edges.size())]
                                               : static_cast<float>(static_cast<int>((word >> 32U) % 16385U) - 8192) / 4096.0F;
            }
        }
        const forge::Board& board = sample % 2 == 0 ? white : black;
        const int a = forge::nnue::evaluate(board, acc);
        const int b = forge::nnue::lock_ref::evaluate(board, acc);
        if (a != b) fail("synthetic evaluate " + std::to_string(a) + " vs lock " + std::to_string(b));
        mix(static_cast<std::uint32_t>(a));
        ++stats.synthetic;
    }
}

std::uint64_t parse_count(std::string_view text) {
    std::uint64_t value = 0;
    const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
    if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) fail("bad number: " + std::string(text));
    return value;
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (!forge::nnue::available()) {
            std::cout << "SKIP: no network compiled in\n";
            return 0;
        }
        std::uint64_t walk_positions = 1000000;
        std::uint64_t synthetic = 100000;
        std::uint64_t pos_limit = ~0ULL;
        std::vector<std::string> fen_files;
        std::vector<std::string> pos_files;
        for (int i = 1; i < argc; ++i) {
            const std::string_view option = argv[i];
            if (i + 1 >= argc) fail("missing value for " + std::string(option));
            const std::string value = argv[++i];
            if (option == "--walk-positions") walk_positions = parse_count(value);
            else if (option == "--synthetic") synthetic = parse_count(value);
            else if (option == "--pos-limit") pos_limit = parse_count(value);
            else if (option == "--fens") fen_files.push_back(value);
            else if (option == "--pos") pos_files.push_back(value);
            else fail("unknown option " + std::string(option));
        }
        // Walk roots: castles, en passant, promotions (quiet and capturing) for
        // both colours within the first plies (all 3-ply sequences are checked
        // exhaustively), then the FEN files.
        std::vector<std::string> roots{
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
            "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
            "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
            "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
            "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
            "4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1",
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 5",
            "r3k2r/pppq1ppp/2npbn2/2b1p3/2B1P3/2NPBN2/PPPQ1PPP/R3K2R b KQkq - 4 8",
        };
        const std::size_t fixtures = roots.size();
        forge::Board board;
        for (const std::string& fen : roots) {
            if (!board.set_fen(fen)) fail("fixture rejected: " + fen);
            Accumulator now;
            Accumulator ref;
            forge::nnue::refresh(board, now);
            forge::nnue::lock_ref::refresh(board, ref);
            exhaustive(board, now, ref, 3);
        }
        for (const std::string& path : fen_files) {
            for (const std::string& fen : read_fens(path)) {
                if (!board.set_fen(fen)) fail("FEN rejected: " + fen);
                compare_refresh(board);
                ++stats.fens;
                roots.push_back(fen);
            }
        }
        // A quarter of the walk budget goes to the fixtures (castles, en passant
        // and promotions for both colours), the rest to the FEN-file roots.
        const std::uint64_t fixture_budget = roots.size() == fixtures ? walk_positions : walk_positions / 4;
        for (std::size_t i = 0; i < roots.size(); ++i) {
            const bool fixture = i < fixtures;
            const std::uint64_t total = fixture ? fixture_budget : walk_positions - fixture_budget;
            const std::size_t count = fixture ? fixtures : roots.size() - fixtures;
            const std::size_t index = fixture ? i : i - fixtures;
            walk(roots[i], total / count + (index < total % count ? 1U : 0U));
        }
        for (const std::string& path : pos_files) check_pos_file(path, pos_limit);
        check_synthetic(synthetic);
        std::cout << "positions " << stats.positions << " (updates " << stats.updates << ", refreshes " << stats.refreshes
                  << ", in-place " << stats.in_place << ")\n"
                  << "moves: quiet " << stats.quiet << " captures " << stats.captures << " en-passant " << stats.en_passant
                  << " promotions " << stats.promotions << " capture-promotions " << stats.capture_promotions
                  << " castles " << stats.castles << " null " << stats.null_moves << '\n'
                  << "fens " << stats.fens << " pos used " << stats.pos_used << " skipped " << stats.pos_skipped
                  << " synthetic evaluations " << stats.synthetic << '\n';
#if defined(FORGE_NNUE_FORCE_SCALAR)
        const char* target = "portable (FORGE_NNUE_FORCE_SCALAR)";
#elif defined(__AVX512F__) && FORGE_NNUE_O2
        const char* target = "AVX-512 (O2 512-bit accumulator kernels, R5B; AVX2 output layer)";
#elif defined(__AVX512F__)
        const char* target = "AVX-512 target (portable kernels, compiler-widened; AVX2 output layer)";
#elif defined(__AVX2__)
        const char* target = "AVX2";
#elif defined(__SSE2__) || defined(_M_X64) || defined(_M_AMD64)
        const char* target = "SSE2";
#else
        const char* target = "portable";
#endif
        char digest[17];
        std::snprintf(digest, sizeof digest, "%016llx", static_cast<unsigned long long>(stats.digest));
        std::cout << "kernels " << target << "\ndigest " << digest << "\nPASS: new == AL1 s198 bit for bit\n";
        if (stats.positions < walk_positions) fail("fewer positions compared than requested");
        return 0;
    } catch (const std::exception& error) {
        std::cout << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
