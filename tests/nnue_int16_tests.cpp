// NnueInt16 tests (opus-sol-SA2). The integer path (int16 weights, int32
// accumulators) is checked against an independent scalar reference written from
// the number format, never from the engine's kernels:
//   A = b1 + sum w1[active], a = clamp(A, 0, 4096), q = (a*a + 1024) / 2048,
//   T = sum q*w2 (int64), cp = trunc(clamp((T / 2^25 + b2 / 4096) * 400 / 2.25)).
// Also: incremental == fresh accumulators along deterministic random playouts
// (captures, castling, en passant, promotions, null moves), the representation
// tag, the OFF path against a float emulation in the engine's lane order, and
// the float/int16 difference bound. Prints "FAIL: ..." and exits 1 on failure.
// R3 stack: the integer path is the build switch FORGE_NNUE_INT16; the CMake
// targets compile this test with their own copy of the NNUE sources and the switch.
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#if !FORGE_NNUE_INT16
#error "tests/nnue_int16_tests.cpp needs FORGE_NNUE_INT16=1 (R3 stack build switch)"
#endif

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#if defined(FORGE_NNUE_WEIGHTS)
#include FORGE_NNUE_WEIGHTS
#else
#include "../src/nnue_weights.inc"
#endif

namespace {

using namespace forge;
constexpr int H = nnue::HiddenSize;
int failures = 0;
int checks = 0;

void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) {
        ++failures;
        if (failures <= 20) std::printf("FAIL: %s\n", what.c_str());
    }
}

// ---------------------------------------------------------------- reference
int ref_feature(Color perspective, Piece piece, int square) {
    const int relative = color_of(piece) == perspective ? 0 : 1;
    const int type = piece_type(piece) - 1;
    const int sq = perspective == White ? square : (square ^ 56);
    return (relative * 6 + type) * 64 + sq;
}

std::vector<std::int64_t> ref_accumulator(const Board& board, Color perspective) {
    std::vector<std::int64_t> acc(static_cast<std::size_t>(H));
    for (int h = 0; h < H; ++h) acc[static_cast<std::size_t>(h)] = NnueB1[h];
    for (int square = 0; square < 64; ++square) {
        const Piece piece = board.piece_at(square);
        if (piece == Empty) continue;
        const std::size_t base = static_cast<std::size_t>(ref_feature(perspective, piece, square)) * H;
        for (int h = 0; h < H; ++h) acc[static_cast<std::size_t>(h)] += NnueW1[base + static_cast<std::size_t>(h)];
    }
    return acc;
}

int ref_evaluate_int(const Board& board) {
    const auto ours = ref_accumulator(board, board.side_to_move());
    const auto theirs = ref_accumulator(board, opposite(board.side_to_move()));
    std::int64_t total = 0;
    for (int h = 0; h < H; ++h) {
        const std::int64_t a = std::clamp<std::int64_t>(ours[static_cast<std::size_t>(h)], 0, 4096);
        const std::int64_t b = std::clamp<std::int64_t>(theirs[static_cast<std::size_t>(h)], 0, 4096);
        total += (a * a + 1024) / 2048 * NnueW2[h];
        total += (b * b + 1024) / 2048 * NnueW2[H + h];
    }
    const double logit = static_cast<double>(total) / 33554432.0 + static_cast<double>(NnueB2) / 4096.0;
    const double cp = logit * 400.0 / 2.25;
    return static_cast<int>(std::clamp(cp, -30000.0, 30000.0));
}

// The OFF path's arithmetic: grid-exact float accumulators, sixteen lane sums
// (lane j takes the units h with h % 16 == j), then one ordered tail.
int ref_evaluate_float(const Board& board) {
    const auto ours = ref_accumulator(board, board.side_to_move());
    const auto theirs = ref_accumulator(board, opposite(board.side_to_move()));
    float lanes[16] = {};
    for (int h = 0; h < H; h += 16) {
        for (int j = 0; j < 16; ++j) {
            const std::size_t i = static_cast<std::size_t>(h + j);
            const float a = std::min(std::max(static_cast<float>(ours[i]) / 4096.0F, 0.0F), 1.0F);
            const float b = std::min(std::max(static_cast<float>(theirs[i]) / 4096.0F, 0.0F), 1.0F);
            const float wa = static_cast<float>(NnueW2[i]) / 4096.0F;
            const float wb = static_cast<float>(NnueW2[static_cast<std::size_t>(H) + i]) / 4096.0F;
            lanes[j] += a * a * wa + b * b * wb;
        }
    }
    float out = static_cast<float>(NnueB2) / 4096.0F;
    for (const float lane : lanes) out += lane;
    const float cp = out * 400.0F / 2.25F;
    return static_cast<int>(std::clamp(cp, -30000.0F, 30000.0F));
}

bool same_integer(const nnue::Accumulator& x, const nnue::Accumulator& y) { return x.integer_values == y.integer_values; }
bool same_float(const nnue::Accumulator& x, const nnue::Accumulator& y) { return x.values == y.values; }

bool matches_reference(const Board& board, const nnue::Accumulator& acc) {
    for (const Color perspective : {White, Black}) {
        const auto expected = ref_accumulator(board, perspective);
        for (int h = 0; h < H; ++h)
            if (acc.integer_values[static_cast<std::size_t>(perspective)][static_cast<std::size_t>(h)] != expected[static_cast<std::size_t>(h)]) return false;
    }
    return true;
}

// ---------------------------------------------------------------- playouts
struct Rng {
    std::uint64_t state;
    std::uint64_t next() {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        return state;
    }
};

const std::array<const char*, 10> StartFens{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",            // promotions and capture-promotions
    "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",  // en passant
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",               // castling both sides
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",                       // bare kings
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
};

struct Stats {
    long long positions = 0;
    long long transitions = 0;
    long long nulls = 0;
    int max_float_int_diff = 0;
    long long differing = 0;
};

// One playout in the current mode. `integer` = expected representation.
void playout(const char* fen, Rng& rng, int plies, bool integer, Stats& stats) {
    Board board;
    if (!board.set_fen(fen)) {
        check(false, std::string("set_fen ") + fen);
        return;
    }
    nnue::Accumulator parent;
    nnue::refresh(board, parent);
    check(parent.valid && parent.integer == integer, std::string("refresh tag ") + fen);
    for (int ply = 0; ply <= plies; ++ply) {
        ++stats.positions;
        const int got = nnue::evaluate(board, parent);
        const int want_int = ref_evaluate_int(board);
        const int want_float = ref_evaluate_float(board);
        if (integer) {
            check(matches_reference(board, parent), "int32 accumulator != reference: " + board.fen());
            check(got == want_int, "int16 evaluate " + std::to_string(got) + " != reference " + std::to_string(want_int) + ": " + board.fen());
        } else {
            check(got == want_float, "float evaluate " + std::to_string(got) + " != float emulation " + std::to_string(want_float) + ": " + board.fen());
        }
        const int diff = std::abs(want_int - want_float);
        stats.max_float_int_diff = std::max(stats.max_float_int_diff, diff);
        if (diff != 0) ++stats.differing;
        if (ply == plies) break;
        const MoveList moves = board.legal_moves();
        if (moves.size() == 0) break;
        nnue::Accumulator child;
        if (!board.in_check() && rng.next() % 16 == 0) {
            NullUndo undo;
            nnue::DirtyPieces none;  // the search's null-move record: no changes
            nnue::update(parent, child, none);
            board.make_null_move(undo);
            ++stats.nulls;
        } else {
            const Move move = moves[static_cast<std::size_t>(rng.next() % moves.size())];
            const nnue::DirtyPieces dirty = nnue::dirty_pieces(board, move);
            nnue::update(parent, child, dirty);
            Undo undo;
            if (!board.make_move(move, undo)) {
                check(false, "legal move rejected: " + Board::move_to_uci(move));
                return;
            }
        }
        ++stats.transitions;
        nnue::Accumulator fresh;
        nnue::refresh(board, fresh);
        check(child.valid && child.integer == integer, "child tag after update: " + board.fen());
        check(integer ? same_integer(child, fresh) : same_float(child, fresh), "incremental != fresh: " + board.fen());
        parent = child;
    }
}

void run_playouts(bool integer, Stats& stats, std::uint64_t seed) {
    Rng rng{seed};
    for (const char* fen : StartFens)
        for (int game = 0; game < 12; ++game) playout(fen, rng, 48, integer, stats);
}

} // namespace

int main() {
    std::printf("NnueInt16 tests: HiddenSize %d, network available %d\n", H, static_cast<int>(nnue::available()));
    check(nnue::available(), "a network is compiled in");

    // Representability: the engine's verdict equals this test's own bound.
    std::int64_t largest_lane = 0;
    std::int64_t largest_column = 0;
    for (int h = 0; h < H; ++h) {
        std::int64_t lane = std::abs(static_cast<std::int64_t>(NnueB1[h]));
        for (int f = 0; f < nnue::InputCount; ++f) {
            const std::int64_t m = std::abs(static_cast<std::int64_t>(NnueW1[static_cast<std::size_t>(f) * H + static_cast<std::size_t>(h)]));
            lane += m;
            largest_column = std::max(largest_column, m);
        }
        largest_lane = std::max(largest_lane, lane);
    }
    const bool representable = largest_lane + 4 * largest_column < (std::int64_t{1} << 24);
    std::printf("lane bound %lld + 4 * %lld = %lld (< 2^24: %d; int32 headroom x%lld)\n",
                static_cast<long long>(largest_lane), static_cast<long long>(largest_column),
                static_cast<long long>(largest_lane + 4 * largest_column), static_cast<int>(representable),
                static_cast<long long>(2147483647LL / (largest_lane + 4 * largest_column)));
    check(nnue::int16_available() == representable, "int16_available() agrees with the independent bound");
    check(nnue::int16_available(), "the compiled-in network is int16-representable");

    // Default OFF: float accumulators, float evaluation unchanged.
    check(!nnue::int16_active(), "NnueInt16 is OFF by default");
    Stats off;
    run_playouts(false, off, 0x9E3779B97F4A7C15ULL);

    // ON: integer accumulators and evaluation equal the reference exactly.
    check(nnue::set_int16(true), "set_int16(true) activates");
    check(nnue::int16_active(), "int16_active() after set_int16(true)");
    Stats on;
    run_playouts(true, on, 0xD1B54A32D192ED03ULL);

    // The representation follows the parent, not the current mode.
    Board start;
    check(start.set_fen(StartFens[1]), "set_fen kiwipete");
    const Move move = start.legal_moves()[0];
    const nnue::DirtyPieces dirty = nnue::dirty_pieces(start, move);
    nnue::Accumulator int_parent;
    nnue::refresh(start, int_parent);  // ON
    check(nnue::set_int16(false) == false && !nnue::int16_active(), "set_int16(false) deactivates");
    nnue::Accumulator float_parent;
    nnue::refresh(start, float_parent);  // OFF
    check(!float_parent.integer && int_parent.integer, "refresh follows the mode");
    nnue::Accumulator child;
    nnue::update(int_parent, child, dirty);
    check(child.integer, "an integer parent gives an integer child while OFF");
    (void)nnue::set_int16(true);
    nnue::update(float_parent, child, dirty);  // reuses an integer-tagged child object
    check(!child.integer, "a float parent gives a float child while ON");
    (void)nnue::set_int16(false);
    nnue::Accumulator again;
    nnue::refresh(start, again);
    check(!again.integer && same_float(again, float_parent) &&
          nnue::evaluate(start, again) == ref_evaluate_float(start), "OFF again: float accumulator and evaluation unchanged");

    std::printf("OFF: %lld positions, %lld transitions (%lld null), float evaluate == float emulation\n",
                off.positions, off.transitions, off.nulls);
    std::printf("ON:  %lld positions, %lld transitions (%lld null), int16 evaluate == integer reference, incremental == fresh\n",
                on.positions, on.transitions, on.nulls);
    // Analytic float/int16 bound for this net (Sol's FEASIBILITY.md): square rounding moves each q by at
    // most 0.5, plus a conservative bound on the float path's rounding (36 roundings per term);
    // truncation toward zero then gives at most ceil(bound) cp.
    double sum_abs_w2 = 0.0;
    for (int i = 0; i < 2 * H; ++i) sum_abs_w2 += std::abs(static_cast<double>(NnueW2[i]));
    const double u = std::ldexp(1.0, -24);
    const double gamma36 = 36.0 * u / (1.0 - 36.0 * u);
    const double real_bound = (0.5 * sum_abs_w2 / 33554432.0 + gamma36 * (sum_abs_w2 + std::abs(static_cast<double>(NnueB2))) / 4096.0) * 400.0 / 2.25;
    const int bound = static_cast<int>(std::ceil(real_bound));
    const int max_diff = std::max(off.max_float_int_diff, on.max_float_int_diff);
    std::printf("float vs int16 (references): max |diff| %d cp (analytic bound %.4f -> %d cp), %lld + %lld positions differ\n",
                max_diff, real_bound, bound, off.differing, on.differing);
    check(max_diff <= bound, "float/int16 difference within the analytic bound");
    check(on.positions > 4000 && on.transitions > 4000 && on.nulls > 50, "playouts cover enough positions and null moves");
    if (failures == 0) {
        std::printf("PASS: %d checks\n", checks);
        return 0;
    }
    std::printf("%d of %d checks failed\n", failures, checks);
    return 1;
}
