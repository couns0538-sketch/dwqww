// Original Forge H256 runtime-int16 validation driver. No engine source copied.
// Usage: nnue_int16_parity [unique-positions=100000] [seed=20261024] [fens.txt]
// Compile against the actual candidate core, with the same hidden-size/FP flags.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include "../src/nnue_weights.inc"

namespace {
using namespace forge;
constexpr std::size_t H = static_cast<std::size_t>(nnue::HiddenSize);
using Exact = std::array<std::array<std::int64_t, H>, 2>;

struct Rng {
    std::uint64_t state;
    std::uint64_t next() {
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        return state * UINT64_C(2685821657736338717);
    }
};

struct Stats {
    std::uint64_t checked = 0, positions = 0, transitions = 0, nulls = 0;
    std::uint64_t castles = 0, ep = 0, quiet_promotions = 0, capture_promotions = 0;
    std::uint64_t fresh_lane_mismatches = 0, incremental_lane_mismatches = 0;
    std::uint64_t output_oracle_mismatches = 0, state_mismatches = 0;
    std::uint64_t parent_mismatches = 0, in_place_mismatches = 0;
    std::uint64_t net_sign_flips = 0, total_sign_flips = 0;
    std::uint64_t net_zero_changes = 0, total_zero_changes = 0, different = 0;
    std::int64_t minimum_lane = INT64_MAX, maximum_lane = INT64_MIN;
    std::uint64_t absolute_sum = 0;
    int maximum_cp = 0;
    std::vector<std::uint64_t> histogram = std::vector<std::uint64_t>(60001, 0);
    std::string first_failure, maximum_fen;
    std::unordered_set<std::string> seen;
    std::ofstream fens;
    std::uint64_t corpus_hash = UINT64_C(14695981039346656037);

    void fail(const Board& board, const char* reason) {
        if (first_failure.empty()) first_failure = std::string(reason) + ": " + board.fen();
    }
};

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

std::string position_key(const Board& board) {
    std::string fen = board.fen();
    std::size_t end = 0;
    for (int i = 0; i < 4; ++i) {
        end = fen.find(' ', end);
        if (end == std::string::npos) return fen;
        if (i != 3) ++end;
    }
    return fen.substr(0, end);
}

Exact exact_lanes(const Board& board) {
    Exact result{};
    for (std::size_t perspective = 0; perspective < 2; ++perspective) {
        for (std::size_t h = 0; h < H; ++h) result[perspective][h] = NnueB1[h];
        for (int square = 0; square < 64; ++square) {
            const Piece piece = board.piece_at(square);
            if (piece == Empty) continue;
            // Independent feature-index derivation, not the candidate helper.
            const std::size_t relative_color = color_of(piece) == static_cast<Color>(perspective) ? 0 : 1;
            const std::size_t type = static_cast<std::size_t>(piece_type(piece) - 1);
            const std::size_t relative_square = static_cast<std::size_t>(perspective == White ? square : square ^ 56);
            const std::size_t feature = (relative_color * 6 + type) * 64 + relative_square;
            for (std::size_t h = 0; h < H; ++h)
                result[perspective][h] += NnueW1[feature * H + h];
        }
    }
    return result;
}

int exact_integer_output(const Board& board, const Exact& exact) {
    const std::size_t us = static_cast<std::size_t>(board.side_to_move());
    std::int64_t total = 0;
    for (std::size_t side = 0; side < 2; ++side) {
        const std::size_t perspective = side == 0 ? us : 1 - us;
        for (std::size_t h = 0; h < H; ++h) {
            const std::int64_t a = std::clamp<std::int64_t>(exact[perspective][h], 0, 4096);
            const std::int64_t square = (a * a + 1024) / 2048;
            total += square * NnueW2[side * H + h];
        }
    }
    const double output = static_cast<double>(total) / 33554432.0 + static_cast<double>(NnueB2) / 4096.0;
    const double cp = output * 400.0 / 2.25;
    return static_cast<int>(std::clamp(cp, -30000.0, 30000.0));
}

bool same_active(const nnue::Accumulator& a, const nnue::Accumulator& b) {
    if (a.valid != b.valid || a.integer != b.integer) return false;
    for (std::size_t perspective = 0; perspective < 2; ++perspective)
        for (std::size_t h = 0; h < H; ++h) {
            if (a.integer) {
                if (a.integer_values[perspective][h] != b.integer_values[perspective][h]) return false;
            } else if (std::bit_cast<std::uint32_t>(a.values[perspective][h]) !=
                       std::bit_cast<std::uint32_t>(b.values[perspective][h])) return false;
        }
    return true;
}

void refresh_pair(const Board& board, nnue::Accumulator& floating, nnue::Accumulator& integer) {
    (void)nnue::set_int16(false);
    require(!nnue::int16_active(), "OFF request did not select float");
    nnue::refresh(board, floating);
    require(nnue::set_int16(true) && nnue::int16_active(), "int16 backend unavailable");
    nnue::refresh(board, integer);
}

void check(const Board& board, const nnue::Accumulator& floating,
           const nnue::Accumulator& integer, Stats& stats, std::uint64_t target) {
    ++stats.checked;
    nnue::Accumulator fresh_float, fresh_integer;
    refresh_pair(board, fresh_float, fresh_integer);
    if (!floating.valid || floating.integer || !integer.valid || !integer.integer ||
        !fresh_float.valid || fresh_float.integer || !fresh_integer.valid || !fresh_integer.integer) {
        ++stats.state_mismatches;
        stats.fail(board, "wrong accumulator validity or backend tag");
    }
    const Exact exact = exact_lanes(board);
    bool incremental_bad = false, fresh_bad = false;
    for (std::size_t perspective = 0; perspective < 2; ++perspective)
        for (std::size_t h = 0; h < H; ++h) {
            const auto wanted = exact[perspective][h];
            stats.minimum_lane = std::min(stats.minimum_lane, wanted);
            stats.maximum_lane = std::max(stats.maximum_lane, wanted);
            incremental_bad |= integer.integer_values[perspective][h] != wanted ||
                !std::isfinite(floating.values[perspective][h]) ||
                static_cast<double>(floating.values[perspective][h]) * 4096.0 != static_cast<double>(wanted);
            fresh_bad |= fresh_integer.integer_values[perspective][h] != wanted ||
                !std::isfinite(fresh_float.values[perspective][h]) ||
                static_cast<double>(fresh_float.values[perspective][h]) * 4096.0 != static_cast<double>(wanted);
        }
    if (incremental_bad) { ++stats.incremental_lane_mismatches; stats.fail(board, "incremental lane oracle mismatch"); }
    if (fresh_bad) { ++stats.fresh_lane_mismatches; stats.fail(board, "refreshed lane oracle mismatch"); }
    const int int_cp = nnue::evaluate(board, integer);
    const int float_cp = nnue::evaluate(board, floating);
    if (int_cp != exact_integer_output(board, exact) || int_cp != nnue::evaluate(board, fresh_integer) ||
        float_cp != nnue::evaluate(board, fresh_float)) {
        ++stats.output_oracle_mismatches;
        stats.fail(board, "output oracle or refresh evaluation mismatch");
    }
    if (stats.positions >= target || !stats.seen.insert(position_key(board)).second) return;
    ++stats.positions;
    const int difference = std::abs(int_cp - float_cp);
    stats.absolute_sum += static_cast<std::uint64_t>(difference);
    ++stats.histogram[static_cast<std::size_t>(std::min(difference, 60000))];
    stats.different += difference != 0;
    stats.net_sign_flips += (int_cp > 0 && float_cp < 0) || (int_cp < 0 && float_cp > 0);
    stats.net_zero_changes += (int_cp == 0) != (float_cp == 0);
    const int hand = Evaluator::evaluate_uncached(board);
    const int full_int = std::clamp(hand + int_cp, -MateInMaxPly + 1, MateInMaxPly - 1);
    const int full_float = std::clamp(hand + float_cp, -MateInMaxPly + 1, MateInMaxPly - 1);
    stats.total_sign_flips += (full_int > 0 && full_float < 0) || (full_int < 0 && full_float > 0);
    stats.total_zero_changes += (full_int == 0) != (full_float == 0);
    if (difference > stats.maximum_cp) { stats.maximum_cp = difference; stats.maximum_fen = board.fen(); }
    const std::string fen = board.fen();
    for (const unsigned char byte : fen) stats.corpus_hash = (stats.corpus_hash ^ byte) * UINT64_C(1099511628211);
    stats.corpus_hash = (stats.corpus_hash ^ static_cast<unsigned char>('\n')) * UINT64_C(1099511628211);
    if (stats.fens.is_open()) stats.fens << fen << '\n';
}

void transition(const Board& board_after, const nnue::DirtyPieces& dirty,
                nnue::Accumulator& floating, nnue::Accumulator& integer, Stats& stats, bool in_place) {
    const nnue::Accumulator saved_float = floating, saved_integer = integer;
    nnue::Accumulator next_float, next_integer;
    nnue::update(floating, next_float, dirty);
    nnue::update(integer, next_integer, dirty);
    ++stats.transitions;
    if (!same_active(floating, saved_float) || !same_active(integer, saved_integer)) {
        ++stats.parent_mismatches;
        stats.fail(board_after, "update mutated its distinct parent");
    }
    if (in_place) {
        nnue::Accumulator alias_float = saved_float, alias_integer = saved_integer;
        nnue::update(alias_float, alias_float, dirty);
        nnue::update(alias_integer, alias_integer, dirty);
        if (!same_active(alias_float, next_float) || !same_active(alias_integer, next_integer)) {
            ++stats.in_place_mismatches;
            stats.fail(board_after, "in-place update differs from distinct update");
        }
    }
    floating = next_float;
    integer = next_integer;
}

constexpr std::array<const char*, 12> starts{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
    "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
    "4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
};

void record_move(Move move, Stats& stats) {
    stats.castles += move.is_castle();
    stats.ep += (move.flags & EnPassant) != 0U;
    stats.quiet_promotions += move.is_promotion() && !move.is_capture();
    stats.capture_promotions += move.is_promotion() && move.is_capture();
}

void special_cases(Stats& stats, std::uint64_t target) {
    for (const char* fen : starts) {
        Board board;
        require(board.set_fen(fen), "special FEN rejected");
        nnue::Accumulator base_float, base_integer;
        refresh_pair(board, base_float, base_integer);
        check(board, base_float, base_integer, stats, target);
        for (const Move move : board.legal_moves()) {
            const auto dirty = nnue::dirty_pieces(board, move);
            Undo undo;
            require(board.make_move(move, undo), "special legal move rejected");
            auto floating = base_float, integer = base_integer;
            transition(board, dirty, floating, integer, stats, true);
            record_move(move, stats);
            check(board, floating, integer, stats, target);
            board.unmake_move(move, undo);
        }
        if (!board.in_check()) {
            NullUndo undo;
            board.make_null_move(undo);
            auto floating = base_float, integer = base_integer;
            transition(board, nnue::DirtyPieces{}, floating, integer, stats, true);
            ++stats.nulls;
            check(board, floating, integer, stats, target);
            board.unmake_null_move(undo);
        }
    }
}
} // namespace

int main(int argc, char** argv) {
    try {
        const std::uint64_t target = argc > 1 ? std::stoull(argv[1]) : 100000;
        const std::uint64_t seed = argc > 2 ? std::stoull(argv[2]) : 20261024;
        require(target > 0 && target <= 10000000, "position count out of range");
        require(seed != 0, "seed must be nonzero");
        require(nnue::available() && nnue::int16_available(), "compiled net/int16 unavailable");
        Stats stats;
        stats.seen.reserve(static_cast<std::size_t>(target * 2));
        if (argc > 3) {
            stats.fens.open(argv[3], std::ios::binary);
            require(stats.fens.is_open(), "cannot open FEN output");
        }
        special_cases(stats, target);
        Rng rng{seed};
        while (stats.positions < target) {
            Board board;
            // Half of the games start normally; the rest add material/EP/promotion diversity.
            const std::size_t fixture = (rng.next() & 1U) == 0 ? 0 : static_cast<std::size_t>(rng.next() % starts.size());
            require(board.set_fen(starts[fixture]), "walk FEN rejected");
            nnue::Accumulator floating, integer;
            refresh_pair(board, floating, integer);
            for (int ply = 0; ply < 240 && stats.positions < target; ++ply) {
                check(board, floating, integer, stats, target);
                const MoveList moves = board.legal_moves();
                if (moves.empty() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) break;
                const Move move = moves[static_cast<std::size_t>(rng.next() % moves.size())];
                const auto dirty = nnue::dirty_pieces(board, move);
                Undo undo;
                require(board.make_move(move, undo), "walk legal move rejected");
                transition(board, dirty, floating, integer, stats, stats.transitions % 257 == 0);
                record_move(move, stats);
            }
        }
        if (stats.fens.is_open()) { stats.fens.flush(); require(stats.fens.good(), "FEN output write failed"); }
        const std::uint64_t p99_rank = (stats.positions * 99 + 99) / 100;
        std::uint64_t cumulative = 0;
        int p99 = 0;
        for (std::size_t i = 0; i < stats.histogram.size(); ++i) {
            cumulative += stats.histogram[i];
            if (cumulative >= p99_rank) { p99 = static_cast<int>(i); break; }
        }
        const double mean = static_cast<double>(stats.absolute_sum) / static_cast<double>(stats.positions);
        const bool clean = stats.fresh_lane_mismatches == 0 && stats.incremental_lane_mismatches == 0 &&
            stats.output_oracle_mismatches == 0 && stats.state_mismatches == 0 && stats.parent_mismatches == 0 &&
            stats.in_place_mismatches == 0;
        const bool coverage = stats.castles >= 4 && stats.ep >= 2 && stats.quiet_promotions >= 8 &&
            stats.capture_promotions >= 8 && stats.nulls >= 2;
        const bool passed = clean && coverage && mean <= 2.0 && stats.maximum_cp <= 30;
        std::cout << std::setprecision(12)
            << "{\n  \"result\": \"" << (passed ? "PASS" : "FAIL") << "\",\n"
            << "  \"seed\": " << seed << ",\n  \"unique_four_field_positions\": " << stats.positions
            << ",\n  \"state_checks\": " << stats.checked << ",\n  \"transitions\": " << stats.transitions
            << ",\n  \"mean_abs_cp\": " << mean << ",\n  \"max_abs_cp\": " << stats.maximum_cp
            << ",\n  \"p99_abs_cp\": " << p99 << ",\n  \"different\": " << stats.different
            << ",\n  \"raw_net_strict_sign_flips\": " << stats.net_sign_flips
            << ",\n  \"full_static_strict_sign_flips\": " << stats.total_sign_flips
            << ",\n  \"raw_net_zero_vs_nonzero\": " << stats.net_zero_changes
            << ",\n  \"full_static_zero_vs_nonzero\": " << stats.total_zero_changes
            << ",\n  \"fresh_lane_mismatches\": " << stats.fresh_lane_mismatches
            << ",\n  \"incremental_lane_mismatches\": " << stats.incremental_lane_mismatches
            << ",\n  \"output_oracle_mismatches\": " << stats.output_oracle_mismatches
            << ",\n  \"state_mismatches\": " << stats.state_mismatches
            << ",\n  \"parent_mismatches\": " << stats.parent_mismatches
            << ",\n  \"in_place_mismatches\": " << stats.in_place_mismatches
            << ",\n  \"minimum_lane\": " << stats.minimum_lane
            << ",\n  \"maximum_lane\": " << stats.maximum_lane
            << ",\n  \"castles\": " << stats.castles << ",\n  \"en_passant\": " << stats.ep
            << ",\n  \"quiet_promotions\": " << stats.quiet_promotions
            << ",\n  \"capture_promotions\": " << stats.capture_promotions
            << ",\n  \"null_moves\": " << stats.nulls
            << ",\n  \"coverage_pass\": " << (coverage ? "true" : "false")
            << ",\n  \"fen_stream_fnv1a64\": \"" << std::hex << stats.corpus_hash << std::dec << "\",\n"
            << "  \"maximum_fen\": \"" << stats.maximum_fen << "\",\n"
            << "  \"first_failure\": \"" << stats.first_failure << "\"\n}\n";
        (void)nnue::set_int16(false);
        return passed ? 0 : 1;
    } catch (const std::exception& error) {
        std::cerr << "nnue_int16_parity: " << error.what() << '\n';
        return 2;
    }
}
