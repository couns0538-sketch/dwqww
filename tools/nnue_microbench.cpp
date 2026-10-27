// S37 NNUE inference microbench + per-stage cost table. A tool with its own CMake target
// (forge_nnue_microbench); it links forge_core and times the engine's own functions, so the engine
// executable is unchanged by it.
//
// Corpus (deterministic): the 8 bench FENs of src/uci.cpp and the WAC300 EPD positions, then round-robin
// random walks of 1..8 plies from every root (64-bit LCG per root and walk), deduplicated by Zobrist key,
// until --positions positions (default 10,000). Every legal move of every position is an update pair.
//
// Stages (single thread; positions processed in chunks of 32 whose setup is not timed):
//   refresh          nnue::refresh(board, acc)                       full accumulator, both perspectives
//   dirty            nnue::dirty_pieces(board, move)                 piece changes of a move
//   update_quiet     nnue::update, 2 changes (quiet moves, non-capture promotions)
//   update_capture   nnue::update, 3 changes (captures, en passant, capture promotions)
//   update_castle    nnue::update, 4 changes (castling, generic loop)
//   output           nnue::evaluate(board, acc)                      SCReLU + 2H->1 affine, fused (engine code)
//   activation       replica: clamp + square of both perspectives into a buffer   } split of `output`;
//   affine           replica: 16-lane dot with w2, + b2, scale, truncate         } bit-exact vs nnue::evaluate
//   whole_refresh    Worker::static_evaluate with no valid accumulator: refresh + runtime PSQT + HCE + net
//   whole_update     Worker::static_evaluate of a child, parent valid: lazy update + HCE + net (search case)
//   whole_cached     Worker::static_evaluate with a valid accumulator: HCE + net
//   hce_uncached     Evaluator::evaluate_uncached (reference: HCE without caches)
// Timing: per pass, every stage's timed regions are summed twice: TSC ticks (rdtsc) and thread CPU time
// (Windows QueryThreadCycleTime, else CLOCK_THREAD_CPUTIME_ID), each minus its measured empty-region
// overhead; --repeats passes -> median and p90 of ns/call. Regions: one per stage per chunk of 32 positions
// (output/activation/affine walk the chunk 4 times on the hot accumulators); updates are grouped kind by
// kind, up to 32 parents per region, so even rare castling moves fill a region. A separate per-call pass
// (rdtsc around every call, overhead subtracted) gives the per-call median and p90; its resolution is the
// TSC step (about 10 ns on AMD Zen, whose TSC advances from a 100 MHz reference). Checks: replica == nnue::evaluate,
// incremental accumulator == refreshed accumulator (bitwise) and same eval, whole static eval ==
// clamp(evaluate_uncached + net); checksums for comparison with an independent harness (nnue_check.cpp).
//
// usage: forge_nnue_microbench (--wac WAC.epd | --fens FILE) [--positions N] [--repeats R]
//          [--call-repeats R2] [--dump-fens OUT] [--json OUT] [--check-only] [--label TEXT]

// The replica's code path follows the target macros as nnue.cpp sees them. Capture them before any include:
// GCC's intrinsic headers (x86intrin.h, used for rdtsc) re-define __AVX2__/__SSE__ via target pragmas even
// when they were undefined on the command line (the scalar build).
#if defined(__AVX2__)
#define MB_AVX2 1
#else
#define MB_AVX2 0
#endif
#if !MB_AVX2 && (defined(__SSE__) || defined(_M_X64) || defined(_M_AMD64))
#define MB_SSE 1
#else
#define MB_SSE 0
#endif

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#if (defined(__x86_64__) || defined(__i386__)) && __has_include(<x86intrin.h>)
#include <x86intrin.h>
#define MB_TSC 1
#else
#define MB_TSC 0
#endif
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <time.h>
#endif

#if __has_include("../src/nnue_weights.inc")
// A private copy of the compiled-in network (static arrays) for the activation/affine replica.
#include "../src/nnue_weights.inc"
#define MB_HAS_WEIGHTS 1
#else
#define MB_HAS_WEIGHTS 0
#endif
#if MB_AVX2
#include <immintrin.h>
#define MB_PATH "avx2"
#elif MB_SSE
#include <xmmintrin.h>
#define MB_PATH "sse"
#else
#define MB_PATH "scalar"
#endif

namespace forge {
// Same friendship the engine's tests use (tests/tests.cpp): reach Worker::static_evaluate and the stack.
struct SearcherTestProbe {
    static SearchStack* slot(Searcher& searcher, std::size_t index) { return &searcher.main_worker().stack_[index]; }
    static int static_eval(Searcher& searcher, const Board& board, SearchStack* ss) {
        return searcher.main_worker().static_evaluate(board, ss);
    }
};
} // namespace forge

namespace {

using namespace forge;
using Clock = std::chrono::steady_clock;
constexpr int H = nnue::HiddenSize;
constexpr std::size_t Chunk = 32;
constexpr int HotRepeats = 4;  // output / activation / affine: calls per position per region (hot accumulator)

inline void barrier() { std::atomic_signal_fence(std::memory_order_seq_cst); }

inline std::uint64_t tsc_begin() {
#if MB_TSC
    _mm_lfence();
    const std::uint64_t t = __rdtsc();
    _mm_lfence();
    return t;
#else
    return static_cast<std::uint64_t>(Clock::now().time_since_epoch().count());
#endif
}

inline std::uint64_t tsc_end() {
#if MB_TSC
    unsigned aux = 0;
    const std::uint64_t t = __rdtscp(&aux);
    _mm_lfence();
    return t;
#else
    return static_cast<std::uint64_t>(Clock::now().time_since_epoch().count());
#endif
}

// Thread CPU time in "cpu units": Windows thread cycles (QueryThreadCycleTime, TSC rate), else ns.
inline std::uint64_t thread_cpu() {
#if defined(_WIN32)
    ULONG64 cycles = 0;
    QueryThreadCycleTime(GetCurrentThread(), &cycles);
    return static_cast<std::uint64_t>(cycles);
#else
    timespec ts{};
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
    return static_cast<std::uint64_t>(ts.tv_sec) * 1000000000ULL + static_cast<std::uint64_t>(ts.tv_nsec);
#endif
}

struct Calibration {
    double tsc_per_ns = 1.0;   // rdtsc ticks per wall nanosecond
    double cpu_per_ns = 1.0;   // thread_cpu units per nanosecond
    double tsc_region_overhead = 0;   // ticks of an empty timed region
    double cpu_region_overhead = 0;   // cpu units of an empty timed region
    double tsc_call_overhead = 0;     // ticks of an empty per-call measurement
};

double median_of(std::vector<double> v) {
    if (v.empty()) return 0;
    const auto mid = v.begin() + static_cast<std::ptrdiff_t>(v.size() / 2);
    std::nth_element(v.begin(), mid, v.end());
    return *mid;
}

double quantile_of(std::vector<double> v, double q) {
    if (v.empty()) return 0;
    const auto k = static_cast<std::size_t>(std::min<double>(static_cast<double>(v.size() - 1), std::ceil(q * static_cast<double>(v.size())) - 1));
    std::nth_element(v.begin(), v.begin() + static_cast<std::ptrdiff_t>(k), v.end());
    return v[k];
}

Calibration calibrate() {
    Calibration c;
    // TSC rate against the steady clock over ~200 ms of busy waiting.
    const auto t0 = Clock::now();
    const std::uint64_t r0 = tsc_begin();
    while (Clock::now() - t0 < std::chrono::milliseconds(200)) {}
    const std::uint64_t r1 = tsc_end();
    const double ns = static_cast<double>(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - t0).count());
    c.tsc_per_ns = static_cast<double>(r1 - r0) / ns;
#if defined(_WIN32)
    c.cpu_per_ns = c.tsc_per_ns;  // QueryThreadCycleTime counts at the TSC rate
#else
    c.cpu_per_ns = 1.0;
#endif
    std::vector<double> tsc_regions;
    std::vector<double> cpu_regions;
    std::vector<double> calls;
    for (int i = 0; i < 2001; ++i) {
        const std::uint64_t c0 = thread_cpu();
        const std::uint64_t a = tsc_begin();
        barrier();
        const std::uint64_t b = tsc_end();
        const std::uint64_t c1 = thread_cpu();
        tsc_regions.push_back(static_cast<double>(b - a));
        cpu_regions.push_back(static_cast<double>(c1 - c0));
        const std::uint64_t x = tsc_begin();
        barrier();
        const std::uint64_t y = tsc_end();
        calls.push_back(static_cast<double>(y - x));
    }
    c.tsc_region_overhead = median_of(tsc_regions);
    c.cpu_region_overhead = median_of(cpu_regions);
    c.tsc_call_overhead = median_of(calls);
    return c;
}

// ---------------------------------------------------------------------------------------------- replica
#if MB_HAS_WEIGHTS
struct ReplicaWeights {
    alignas(64) std::array<float, 2 * H> w2{};
    float b2 = 0;
};

const ReplicaWeights& replica_weights() {
    static const ReplicaWeights weights = [] {
        ReplicaWeights w;
        for (std::size_t i = 0; i < 2 * static_cast<std::size_t>(H); ++i) w.w2[i] = static_cast<float>(NnueW2[i]) / nnue::OutputScale;
        w.b2 = static_cast<float>(NnueB2) / nnue::OutputScale;
        return w;
    }();
    return weights;
}
#endif

struct alignas(64) Activated {
    std::array<float, 2 * H> values{};
};

// Same operations and association as nnue::evaluate, split into two loops.
[[gnu::noinline]] void replica_activation(const Board& board, const nnue::Accumulator& acc, Activated& out) {
    const Color us = board.side_to_move();
    const float* ours = acc.values[static_cast<std::size_t>(us)].data();
    const float* theirs = acc.values[static_cast<std::size_t>(opposite(us))].data();
    float* dst = out.values.data();
#if MB_AVX2
    const __m256 zero = _mm256_setzero_ps();
    const __m256 one = _mm256_set1_ps(1.0F);
    for (int h = 0; h < H; h += 8) {
        const __m256 a = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(ours + h), zero), one);
        const __m256 b = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(theirs + h), zero), one);
        _mm256_store_ps(dst + h, _mm256_mul_ps(a, a));
        _mm256_store_ps(dst + H + h, _mm256_mul_ps(b, b));
    }
#elif MB_SSE
    const __m128 zero = _mm_setzero_ps();
    const __m128 one = _mm_set1_ps(1.0F);
    for (int h = 0; h < H; h += 4) {
        const __m128 a = _mm_min_ps(_mm_max_ps(_mm_load_ps(ours + h), zero), one);
        const __m128 b = _mm_min_ps(_mm_max_ps(_mm_load_ps(theirs + h), zero), one);
        _mm_store_ps(dst + h, _mm_mul_ps(a, a));
        _mm_store_ps(dst + H + h, _mm_mul_ps(b, b));
    }
#else
    // Same values as std::min(std::max(x, 0.0F), 1.0F) (incl. NaN), written on locals with restrict pointers
    // so that GCC emits maxss/minss as in nnue::evaluate's scalar loop instead of branches.
    const float* __restrict__ a_in = ours;
    const float* __restrict__ b_in = theirs;
    float* __restrict__ out_values = dst;
    for (int h = 0; h < H; ++h) {
        float a = a_in[h];
        float b = b_in[h];
        a = a < 0.0F ? 0.0F : a;
        b = b < 0.0F ? 0.0F : b;
        a = 1.0F < a ? 1.0F : a;
        b = 1.0F < b ? 1.0F : b;
        out_values[h] = a * a;
        out_values[H + h] = b * b;
    }
#endif
}

[[gnu::noinline]] int replica_affine(const Activated& in) {
#if MB_HAS_WEIGHTS
    const ReplicaWeights& w = replica_weights();
    constexpr int Lanes = 16;
    alignas(64) float lanes[Lanes];
    const float* x = in.values.data();
#if MB_AVX2
    __m256 sums[2] = {_mm256_setzero_ps(), _mm256_setzero_ps()};
    for (int h = 0; h < H; h += Lanes) {
        for (int k = 0; k < 2; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 8 * k);
            const __m256 term = _mm256_add_ps(_mm256_mul_ps(_mm256_load_ps(x + base), _mm256_load_ps(w.w2.data() + base)),
                                              _mm256_mul_ps(_mm256_load_ps(x + H + base), _mm256_load_ps(w.w2.data() + H + base)));
            sums[k] = _mm256_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 2; ++k) _mm256_store_ps(lanes + 8 * k, sums[k]);
#elif MB_SSE
    __m128 sums[4] = {_mm_setzero_ps(), _mm_setzero_ps(), _mm_setzero_ps(), _mm_setzero_ps()};
    for (int h = 0; h < H; h += Lanes) {
        for (int k = 0; k < 4; ++k) {
            const std::size_t base = static_cast<std::size_t>(h + 4 * k);
            const __m128 term = _mm_add_ps(_mm_mul_ps(_mm_load_ps(x + base), _mm_load_ps(w.w2.data() + base)),
                                           _mm_mul_ps(_mm_load_ps(x + H + base), _mm_load_ps(w.w2.data() + H + base)));
            sums[k] = _mm_add_ps(sums[k], term);
        }
    }
    for (int k = 0; k < 4; ++k) _mm_store_ps(lanes + 4 * k, sums[k]);
#else
    for (float& lane : lanes) lane = 0.0F;
    for (int h = 0; h < H; h += Lanes) {
        for (int j = 0; j < Lanes; ++j) {
            const std::size_t index = static_cast<std::size_t>(h + j);
            lanes[j] += x[index] * w.w2[index] + x[static_cast<std::size_t>(H) + index] * w.w2[static_cast<std::size_t>(H) + index];
        }
    }
#endif
    float out = w.b2;
    for (int j = 0; j < Lanes; ++j) out += lanes[j];
    const float centipawns = out * 400.0F / nnue::SigmoidK;
    return static_cast<int>(std::clamp(centipawns, -30000.0F, 30000.0F));
#else
    (void)in;
    return 0;
#endif
}

// ---------------------------------------------------------------------------------------------- corpus
constexpr std::array<const char*, 8> BenchFens{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
};

Board board_from(const std::string& fen) {
    Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) throw std::runtime_error("invalid FEN '" + fen + "': " + error);
    return board;
}

std::vector<Board> load_roots(const std::string& wac) {
    std::vector<Board> roots;
    for (const char* fen : BenchFens) roots.push_back(board_from(fen));
    std::ifstream in(wac, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open " + wac);
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream fields(line);
        std::string a, b, c, d;
        if (!(fields >> a >> b >> c >> d)) continue;
        roots.push_back(board_from(a + ' ' + b + ' ' + c + ' ' + d + " 0 1"));
    }
    return roots;
}

std::vector<Board> build_corpus(const std::vector<Board>& roots, std::size_t count) {
    std::vector<Board> corpus;
    std::unordered_set<std::uint64_t> seen;
    auto add = [&](const Board& board) {
        if (corpus.size() < count && seen.insert(board.key()).second) corpus.push_back(board);
    };
    for (const Board& root : roots) add(root);
    for (std::uint64_t walk = 1; corpus.size() < count; ++walk) {
        if (walk > 100000) throw std::runtime_error("corpus generation does not converge");
        for (std::size_t r = 0; r < roots.size() && corpus.size() < count; ++r) {
            std::uint64_t state = (static_cast<std::uint64_t>(r) + 1) * 0x9E3779B97F4A7C15ULL ^ walk * 0xD1B54A32D192ED03ULL;
            Board board = roots[r];
            const int plies = 1 + static_cast<int>((walk - 1) % 8);
            bool alive = true;
            for (int p = 0; p < plies; ++p) {
                const MoveList moves = board.legal_moves();
                if (moves.empty()) { alive = false; break; }
                state = state * 6364136223846793005ULL + 1442695040888963407ULL;
                Undo undo;
                (void)board.make_move(moves[static_cast<std::size_t>((state >> 33U) % moves.size())], undo);
            }
            if (alive && board.has_legal_move()) add(board);
        }
    }
    return corpus;
}

std::vector<Board> load_fens(const std::string& path, std::size_t count) {
    std::vector<Board> corpus;
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open " + path);
    std::string line;
    while (corpus.size() < count && std::getline(in, line)) {
        std::string fen = line.substr(0, line.find('|'));
        while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\r')) fen.pop_back();
        if (!fen.empty()) corpus.push_back(board_from(fen));
    }
    return corpus;
}

// ---------------------------------------------------------------------------------------------- stages
enum Stage {
    Refresh, Dirty, UpdateQuiet, UpdateCapture, UpdateCastle, Output, Activation, Affine,
    WholeRefresh, WholeUpdate, WholeCached, HceUncached, StageCount
};
constexpr std::array<const char*, StageCount> StageNames{
    "refresh", "dirty", "update_quiet", "update_capture", "update_castle", "output", "activation", "affine",
    "whole_refresh", "whole_update", "whole_cached", "hce_uncached"};

int update_kind(const nnue::DirtyPieces& dirty) {
    if (dirty.count == 2 && !dirty.changes[0].add && dirty.changes[1].add) return UpdateQuiet;
    if (dirty.count == 3 && !dirty.changes[0].add && !dirty.changes[1].add && dirty.changes[2].add) return UpdateCapture;
    return UpdateCastle;
}

struct Pair {
    std::size_t parent = 0;
    Move move{};
    nnue::DirtyPieces dirty{};
    int kind = UpdateQuiet;
};

struct Totals {
    std::array<double, StageCount> tsc{};
    std::array<double, StageCount> cpu{};
    std::array<std::uint64_t, StageCount> calls{};
};

struct Bench {
    const std::vector<Board>& corpus;
    std::vector<std::vector<Pair>> pairs;     // per position
    std::vector<std::vector<Board>> children; // per position, same order as pairs
    std::vector<std::array<std::uint64_t, StageCount>> kind_count;  // per position: moves per update kind
    Searcher searcher{1, 1};
    Calibration cal;
    std::int64_t sink = 0;
    std::vector<nnue::Accumulator> parent_acc = std::vector<nnue::Accumulator>(Chunk);  // per chunk position
    nnue::Accumulator child_acc{};
    std::vector<Activated> activated = std::vector<Activated>(Chunk);

    explicit Bench(const std::vector<Board>& positions) : corpus(positions) {
        pairs.resize(corpus.size());
        children.resize(corpus.size());
        kind_count.resize(corpus.size());
        for (std::size_t i = 0; i < corpus.size(); ++i) {
            for (const Move move : corpus[i].legal_moves()) {
                Pair pair;
                pair.parent = i;
                pair.move = move;
                pair.dirty = nnue::dirty_pieces(corpus[i], move);
                pair.kind = update_kind(pair.dirty);
                ++kind_count[i][static_cast<std::size_t>(pair.kind)];
                pairs[i].push_back(pair);
                Board child = corpus[i];
                Undo undo;
                (void)child.make_move(move, undo);
                children[i].push_back(child);
            }
        }
    }

    // One timed region: sums TSC ticks and thread CPU into `totals` for `stage`.
    template <typename F>
    void region(Totals& totals, int stage, std::uint64_t calls, F&& body) {
        const std::uint64_t c0 = thread_cpu();
        const std::uint64_t t0 = tsc_begin();
        barrier();
        body();
        barrier();
        const std::uint64_t t1 = tsc_end();
        const std::uint64_t c1 = thread_cpu();
        totals.tsc[static_cast<std::size_t>(stage)] += static_cast<double>(t1 - t0) - cal.tsc_region_overhead;
        totals.cpu[static_cast<std::size_t>(stage)] += static_cast<double>(c1 - c0) - cal.cpu_region_overhead;
        totals.calls[static_cast<std::size_t>(stage)] += calls;
    }

    // per_call: nullptr for the region pass; else every call is timed on its own into per_call[stage].
    void pass(Totals& totals, std::vector<std::vector<double>>* per_call) {
        auto timed = [&](int stage, auto&& call) {
            if (per_call == nullptr) {
                call();
                return;
            }
            const std::uint64_t a = tsc_begin();
            barrier();
            call();
            barrier();
            const std::uint64_t b = tsc_end();
            (*per_call)[static_cast<std::size_t>(stage)].push_back(static_cast<double>(b - a) - cal.tsc_call_overhead);
        };
        auto run = [&](int stage, std::uint64_t calls, auto&& body) {
            if (per_call == nullptr) region(totals, stage, calls, body);
            else body();
        };
        for (std::size_t begin = 0; begin < corpus.size(); begin += Chunk) {
            const std::size_t end = std::min(corpus.size(), begin + Chunk);
            const auto n = static_cast<std::uint64_t>(end - begin);
            run(Refresh, n, [&] {
                for (std::size_t i = begin; i < end; ++i) timed(Refresh, [&] { nnue::refresh(corpus[i], parent_acc[i - begin]); });
            });
            std::uint64_t moves = 0;
            for (std::size_t i = begin; i < end; ++i) moves += pairs[i].size();
            run(Dirty, moves, [&] {
                for (std::size_t i = begin; i < end; ++i) {
                    for (const Pair& pair : pairs[i]) {
                        timed(Dirty, [&] {
                            const nnue::DirtyPieces d = nnue::dirty_pieces(corpus[i], pair.move);
                            sink += d.count;
                        });
                    }
                }
            });
            // Cheap stages on hot accumulators: the chunk is walked HotRepeats times per region.
            run(Output, n * HotRepeats, [&] {
                for (int rep = 0; rep < HotRepeats; ++rep) {
                    for (std::size_t i = begin; i < end; ++i) timed(Output, [&] { sink += nnue::evaluate(corpus[i], parent_acc[i - begin]); });
                }
            });
            run(Activation, n * HotRepeats, [&] {
                for (int rep = 0; rep < HotRepeats; ++rep) {
                    for (std::size_t i = begin; i < end; ++i) {
                        timed(Activation, [&] { replica_activation(corpus[i], parent_acc[i - begin], activated[i - begin]); });
                    }
                }
            });
            run(Affine, n * HotRepeats, [&] {
                for (int rep = 0; rep < HotRepeats; ++rep) {
                    for (std::size_t i = begin; i < end; ++i) timed(Affine, [&] { sink += replica_affine(activated[i - begin]); });
                }
            });
            // Whole static evaluation through the search's own entry point. Parent k uses stack slot 5 + 2k
            // (ply 0), its children slot 6 + 2k (ply 1).
            run(WholeRefresh, n, [&] {
                for (std::size_t i = begin; i < end; ++i) {
                    timed(WholeRefresh, [&] {
                        SearchStack* ss = SearcherTestProbe::slot(searcher, 5 + 2 * (i - begin));
                        ss->ply = 0;
                        (ss - 1)->accumulator.valid = false;
                        ss->accumulator.valid = false;
                        ss->runtime_psqt.valid = false;
                        sink += SearcherTestProbe::static_eval(searcher, corpus[i], ss);
                    });
                }
            });
            run(WholeCached, n, [&] {
                for (std::size_t i = begin; i < end; ++i) {
                    timed(WholeCached, [&] {
                        sink += SearcherTestProbe::static_eval(searcher, corpus[i], SearcherTestProbe::slot(searcher, 5 + 2 * (i - begin)));
                    });
                }
            });
            run(WholeUpdate, moves, [&] {
                for (std::size_t i = begin; i < end; ++i) {
                    SearchStack* child = SearcherTestProbe::slot(searcher, 6 + 2 * (i - begin));
                    for (std::size_t j = 0; j < pairs[i].size(); ++j) {
                        timed(WholeUpdate, [&] {
                            child->ply = 1;
                            child->dirty = pairs[i][j].dirty;
                            child->accumulator.valid = false;
                            child->runtime_psqt.valid = false;
                            sink += SearcherTestProbe::static_eval(searcher, children[i][j], child);
                        });
                    }
                }
            });
            run(HceUncached, n, [&] {
                for (std::size_t i = begin; i < end; ++i) timed(HceUncached, [&] { sink += Evaluator::evaluate_uncached(corpus[i]); });
            });
        }
        // Incremental updates, kind by kind: groups of up to Chunk parents that have a move of the kind (parent
        // accumulators refreshed untimed), then one region with all their moves of that kind (castling is rare).
        for (const int kind : {UpdateQuiet, UpdateCapture, UpdateCastle}) {
            std::vector<std::size_t> group;
            auto flush = [&] {
                if (group.empty()) return;
                std::uint64_t calls = 0;
                for (std::size_t g = 0; g < group.size(); ++g) {
                    nnue::refresh(corpus[group[g]], parent_acc[g]);
                    calls += kind_count[group[g]][static_cast<std::size_t>(kind)];
                }
                run(kind, calls, [&] {
                    for (std::size_t g = 0; g < group.size(); ++g) {
                        for (const Pair& pair : pairs[group[g]]) {
                            if (pair.kind != kind) continue;
                            timed(kind, [&] { nnue::update(parent_acc[g], child_acc, pair.dirty); });
                        }
                    }
                });
                group.clear();
            };
            for (std::size_t i = 0; i < corpus.size(); ++i) {
                if (kind_count[i][static_cast<std::size_t>(kind)] == 0) continue;
                group.push_back(i);
                if (group.size() == Chunk) flush();
            }
            flush();
        }
        sink += static_cast<std::int64_t>(child_acc.values[0][0] * 4096.0F);
    }
};

std::uint64_t fnv(std::uint64_t hash, std::int64_t value) {
    for (int i = 0; i < 8; ++i) {
        hash ^= static_cast<std::uint64_t>(value >> (8 * i)) & 0xFFU;
        hash *= 0x100000001B3ULL;
    }
    return hash;
}

struct Checks {
    std::uint64_t positions = 0, pairs = 0;
    std::uint64_t replica_mismatch = 0, acc_mismatch = 0, update_eval_mismatch = 0;
    std::uint64_t whole_refresh_mismatch = 0, whole_update_mismatch = 0, whole_cached_mismatch = 0;
    std::int64_t net_sum = 0, hce_sum = 0, total_sum = 0, child_net_sum = 0;
    std::uint64_t net_hash = 0xCBF29CE484222325ULL, total_hash = 0xCBF29CE484222325ULL;
};

Checks run_checks(Bench& bench) {
    Checks c;
    nnue::Accumulator parent, child, fresh;
    Activated activated;
    for (std::size_t i = 0; i < bench.corpus.size(); ++i) {
        const Board& board = bench.corpus[i];
        nnue::refresh(board, parent);
        const int net = nnue::evaluate(board, parent);
        const int hce = Evaluator::evaluate_uncached(board);
        const int total = nnue::residual() ? std::clamp(hce + net, -MateInMaxPly + 1, MateInMaxPly - 1) : net;
        replica_activation(board, parent, activated);
        if (replica_affine(activated) != net && MB_HAS_WEIGHTS) ++c.replica_mismatch;
        SearchStack* ss = SearcherTestProbe::slot(bench.searcher, 5);
        ss->ply = 0;
        (ss - 1)->accumulator.valid = false;
        ss->accumulator.valid = false;
        ss->runtime_psqt.valid = false;
        if (SearcherTestProbe::static_eval(bench.searcher, board, ss) != total) ++c.whole_refresh_mismatch;
        if (SearcherTestProbe::static_eval(bench.searcher, board, ss) != total) ++c.whole_cached_mismatch;
        c.net_sum += net;
        c.hce_sum += hce;
        c.total_sum += total;
        c.net_hash = fnv(c.net_hash, net);
        c.total_hash = fnv(c.total_hash, total);
        ++c.positions;
        SearchStack* child_ss = SearcherTestProbe::slot(bench.searcher, 6);
        for (std::size_t j = 0; j < bench.pairs[i].size(); ++j) {
            const Board& child_board = bench.children[i][j];
            nnue::update(parent, child, bench.pairs[i][j].dirty);
            nnue::refresh(child_board, fresh);
            if (std::memcmp(child.values.data(), fresh.values.data(), sizeof(child.values)) != 0) ++c.acc_mismatch;
            const int child_net = nnue::evaluate(child_board, fresh);
            if (nnue::evaluate(child_board, child) != child_net) ++c.update_eval_mismatch;
            const int child_total = nnue::residual()
                ? std::clamp(Evaluator::evaluate_uncached(child_board) + child_net, -MateInMaxPly + 1, MateInMaxPly - 1) : child_net;
            child_ss->ply = 1;
            child_ss->dirty = bench.pairs[i][j].dirty;
            child_ss->accumulator.valid = false;
            child_ss->runtime_psqt.valid = false;
            if (SearcherTestProbe::static_eval(bench.searcher, child_board, child_ss) != child_total) ++c.whole_update_mismatch;
            c.child_net_sum += child_net;
            ++c.pairs;
        }
    }
    return c;
}

std::string json_escape(const std::string& text) {
    std::string out;
    for (const char ch : text) {
        if (ch == '"' || ch == '\\') out += '\\';
        out += ch;
    }
    return out;
}

} // namespace

int main(int argc, char** argv) {
    std::string wac, fens, dump, json, label;
    std::size_t positions = 10000;
    int repeats = 15;
    int call_repeats = 2;
    bool check_only = false;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            auto next = [&]() -> std::string {
                if (i + 1 >= argc) throw std::runtime_error("missing value for " + arg);
                return argv[++i];
            };
            if (arg == "--wac") wac = next();
            else if (arg == "--fens") fens = next();
            else if (arg == "--positions") positions = static_cast<std::size_t>(std::stoul(next()));
            else if (arg == "--repeats") repeats = std::stoi(next());
            else if (arg == "--call-repeats") call_repeats = std::stoi(next());
            else if (arg == "--dump-fens") dump = next();
            else if (arg == "--json") json = next();
            else if (arg == "--label") label = next();
            else if (arg == "--check-only") check_only = true;
            else throw std::runtime_error("unknown option " + arg);
        }
        if (wac.empty() == fens.empty()) throw std::runtime_error("give exactly one of --wac FILE or --fens FILE");
        if (!nnue::available()) throw std::runtime_error("no network compiled in");
        if (repeats < 1 || call_repeats < 0 || positions < 1) throw std::runtime_error("bad counts");
    } catch (const std::exception& error) {
        std::cerr << "nnue_microbench: " << error.what() << '\n';
        return 2;
    }

    const std::vector<Board> corpus = fens.empty() ? build_corpus(load_roots(wac), positions) : load_fens(fens, positions);
    if (!dump.empty()) {
        std::ofstream out(dump, std::ios::binary);
        for (const Board& board : corpus) out << board.fen() << '\n';
    }
    Bench bench(corpus);
    const Checks checks = run_checks(bench);
    const bool pass = checks.replica_mismatch == 0 && checks.acc_mismatch == 0 && checks.update_eval_mismatch == 0 &&
                      checks.whole_refresh_mismatch == 0 && checks.whole_update_mismatch == 0 && checks.whole_cached_mismatch == 0;
    std::uint64_t w2_hash = 0xCBF29CE484222325ULL;
#if MB_HAS_WEIGHTS
    for (const std::int16_t v : NnueW2) w2_hash = fnv(w2_hash, v);
    w2_hash = fnv(w2_hash, NnueB2);
#endif
    std::ostringstream head;
    head << "{\"tool\":\"forge_nnue_microbench\",\"label\":\"" << json_escape(label) << "\",\"path\":\"" << MB_PATH
         << "\",\"hidden\":" << H << ",\"residual\":" << (nnue::residual() ? "true" : "false") << ",\"net_w2_b2_fnv\":\""
         << std::hex << w2_hash << std::dec << "\",\"positions\":" << checks.positions << ",\"pairs\":" << checks.pairs
         << ",\"checks\":{\"replica_mismatch\":" << checks.replica_mismatch << ",\"accumulator_mismatch\":" << checks.acc_mismatch
         << ",\"update_eval_mismatch\":" << checks.update_eval_mismatch << ",\"whole_refresh_mismatch\":" << checks.whole_refresh_mismatch
         << ",\"whole_update_mismatch\":" << checks.whole_update_mismatch << ",\"whole_cached_mismatch\":" << checks.whole_cached_mismatch
         << ",\"pass\":" << (pass ? "true" : "false") << "},\"checksums\":{\"net_sum\":" << checks.net_sum << ",\"hce_sum\":" << checks.hce_sum
         << ",\"total_sum\":" << checks.total_sum << ",\"child_net_sum\":" << checks.child_net_sum << ",\"net_fnv\":\"" << std::hex
         << checks.net_hash << "\",\"total_fnv\":\"" << checks.total_hash << std::dec << "\"}";
    std::cout << "checks: " << (pass ? "PASS" : "FAIL") << " positions " << checks.positions << " pairs " << checks.pairs
              << " | replica " << checks.replica_mismatch << " acc " << checks.acc_mismatch << " update_eval " << checks.update_eval_mismatch
              << " whole(refresh/update/cached) " << checks.whole_refresh_mismatch << "/" << checks.whole_update_mismatch << "/"
              << checks.whole_cached_mismatch << " mismatches\nchecksums: net_sum " << checks.net_sum << " hce_sum " << checks.hce_sum
              << " total_sum " << checks.total_sum << " child_net_sum " << checks.child_net_sum << " net_fnv " << std::hex << checks.net_hash
              << " total_fnv " << checks.total_hash << std::dec << " (path " << MB_PATH << ", w2/b2 fnv " << std::hex << w2_hash << std::dec << ")"
              << std::endl;
    if (check_only) {
        if (!json.empty()) std::ofstream(json, std::ios::binary) << head.str() << "}\n";
        return pass ? 0 : 1;
    }

    bench.cal = calibrate();
    std::vector<std::array<double, StageCount>> tsc_ns(static_cast<std::size_t>(repeats));
    std::vector<std::array<double, StageCount>> cpu_ns(static_cast<std::size_t>(repeats));
    Totals warm;
    bench.pass(warm, nullptr);  // warm-up pass (caches, pawn hash), not reported
    Totals counts;
    for (int r = 0; r < repeats; ++r) {
        Totals totals;
        bench.pass(totals, nullptr);
        if (r == 0) counts = totals;
        for (std::size_t s = 0; s < StageCount; ++s) {
            const double calls = static_cast<double>(std::max<std::uint64_t>(1, totals.calls[s]));
            tsc_ns[static_cast<std::size_t>(r)][s] = totals.tsc[s] / bench.cal.tsc_per_ns / calls;
            cpu_ns[static_cast<std::size_t>(r)][s] = totals.cpu[s] / bench.cal.cpu_per_ns / calls;
        }
    }
    std::vector<std::vector<double>> per_call(StageCount);
    for (int r = 0; r < call_repeats; ++r) {
        Totals unused;
        bench.pass(unused, &per_call);
    }
    std::ostringstream body;
    body << std::fixed << std::setprecision(2) << ",\"repeats\":" << repeats << ",\"call_repeats\":" << call_repeats
         << ",\"tsc_ghz\":" << bench.cal.tsc_per_ns << ",\"overhead\":{\"tsc_region_ticks\":" << bench.cal.tsc_region_overhead
         << ",\"cpu_region_units\":" << bench.cal.cpu_region_overhead << ",\"tsc_call_ticks\":" << bench.cal.tsc_call_overhead
         << "},\"stages\":{";
    std::cout << std::fixed << std::setprecision(1) << "\nstage            calls/pass   cpu ns/call med  p90 |  tsc ns/call med  p90 |"
              << " per-call ns med  p90  (" << MB_PATH << ", " << repeats << " passes, TSC " << std::setprecision(3)
              << bench.cal.tsc_per_ns << " GHz)\n" << std::setprecision(1);
    for (std::size_t s = 0; s < StageCount; ++s) {
        std::vector<double> c, t, p;
        for (int r = 0; r < repeats; ++r) {
            c.push_back(cpu_ns[static_cast<std::size_t>(r)][s]);
            t.push_back(tsc_ns[static_cast<std::size_t>(r)][s]);
        }
        for (const double ticks : per_call[s]) p.push_back(ticks / bench.cal.tsc_per_ns);
        const double cm = median_of(c), c9 = quantile_of(c, 0.9), tm = median_of(t), t9 = quantile_of(t, 0.9);
        const double pm = median_of(p), p9 = quantile_of(p, 0.9);
        std::cout << std::left << std::setw(16) << StageNames[s] << std::right << std::setw(11) << counts.calls[s] << std::setw(12) << cm
                  << std::setw(8) << c9 << " |" << std::setw(11) << tm << std::setw(8) << t9 << " |" << std::setw(11) << pm << std::setw(8)
                  << p9 << '\n';
        body << (s ? "," : "") << '"' << StageNames[s] << "\":{\"calls_per_pass\":" << counts.calls[s] << ",\"cpu_ns_median\":" << cm
             << ",\"cpu_ns_p90\":" << c9 << ",\"tsc_ns_median\":" << tm << ",\"tsc_ns_p90\":" << t9 << ",\"call_ns_median\":" << pm
             << ",\"call_ns_p90\":" << p9 << ",\"call_samples\":" << p.size() << '}';
    }
    body << "},\"sink\":" << bench.sink << "}\n";
    std::cout << std::flush;
    if (!json.empty()) std::ofstream(json, std::ios::binary) << head.str() << body.str();
    return pass ? 0 : 1;
}
