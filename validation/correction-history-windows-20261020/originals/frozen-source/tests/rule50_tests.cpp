// Original actual-Forge diagnostic. No copied or simulated search algorithm.
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"
#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>

namespace forge {
// Existing production friendship is also used by tests/tests.cpp.
struct SearcherTestProbe {
    static std::uint64_t visited(Searcher& searcher) { return searcher.main_worker().local_nodes_; }
    static int run(Searcher& searcher, Board board, int depth, int alpha, int beta) {
        auto& worker = searcher.main_worker();
        worker.clear(); // Reset every worker-local cache/history/stack; preserve TT only.
        worker.shared_.stop.store(false, std::memory_order_relaxed);
        worker.shared_.ponder_hit_ns.store(0, std::memory_order_relaxed);
        worker.all_workers_ = nullptr;
        worker.aborted_ = false;
        worker.local_nodes_ = 0;
        worker.nodes_.store(0, std::memory_order_relaxed);
        worker.node_limit_ = 0;
        worker.node_limit_specified_ = false;
        worker.hard_limit_ms_ = worker.soft_limit_ms_ = 0;
        worker.time_managed_ = worker.pondering_ = false;
        worker.start_ = std::chrono::steady_clock::now();
        worker.seldepth_ = 0;
        worker.root_history_index_ = board.history_size() - 1;
        auto* ss = &worker.stack_[5];
        ss->ply = 1; // Non-root search; same ply/window/depth in warm/cold calls.
        nnue::refresh(board, ss->accumulator);
        return depth == 0 ? worker.qsearch(board, ss, alpha, beta)
                          : worker.search(board, ss, depth, alpha, beta, false);
    }
};
}

forge::Board position(int clock) {
    forge::Board board;
    if (!board.set_fen("7k/8/8/8/8/8/8/K6R b - - " + std::to_string(clock) + " 80"))
        throw std::runtime_error("invalid FEN");
    return board;
}

void print_tt(forge::Searcher& searcher, const forge::Board& board) {
    const auto probe = searcher.transposition_table().probe(board.key());
    std::cout << "tt_hit=" << probe.hit << " score=" << probe.entry.score
              << " eval=" << probe.entry.eval << " depth=" << int(probe.entry.depth)
              << " bound=" << int(probe.entry.bound()) << '\n';
}

int main() {
    using namespace forge;
    int failures = 0;
    auto check = [&](bool condition, const char* message) {
        std::cout << (condition ? "PASS " : "FAIL ") << message << '\n';
        if (!condition) ++failures;
    };
    auto low = position(0), near = position(99);
    for (int clock : {89, 90, 98, 99, 100}) {
        Searcher warm(4, 1), cold(4, 1);
        const int learned = SearcherTestProbe::run(warm, low, 0, -Infinite, Infinite);
        auto board = position(clock);
        const auto seeded = warm.transposition_table().probe(board.key());
        check(seeded.hit && seeded.entry.bound() == BoundExact && learned < -1,
              "seed is a genuine exact low-clock qsearch bound");
        const int cached = SearcherTestProbe::run(warm, board, 0, -1, 0);
        const auto visited = SearcherTestProbe::visited(warm);
        const int fresh = SearcherTestProbe::run(cold, board, 0, -1, 0);
        std::cout << "clock=" << clock << " warm=" << cached << " cold=" << fresh
                  << " warm_nodes=" << visited << '\n';
        check(cached == fresh, "targeted fixture warm/cold scores agree");
        if (clock == 89) check(visited == 1 && cached == learned, "eligible below90 direct TT cutoff remains enabled");
        if (clock == 90 || clock == 98 || clock == 99)
            check(visited > 1, "near50 guarded qsearch actually visits evasions");
        if (clock >= 99) check(cached == 0 && fresh == 0, "one-ply or already-terminal rule50 draw stays exact");
    }
    Board mate;
    check(mate.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 100 80"), "mate FEN parses");
    Searcher mate_search(4, 1);
    check(SearcherTestProbe::run(mate_search, mate, 0, -Infinite, Infinite) <= -MateInMaxPly,
          "checkmate on halfmove100 takes precedence");

    // Legal capture resets clock and retains a rook: not an insufficient-material draw.
    Board capture;
    check(capture.set_fen("7k/7R/8/8/8/8/8/KR6 b - - 99 80"), "capture fixture parses");
    const auto capture_move = capture.parse_uci("h8h7");
    check(capture_move.has_value(), "resetting king capture is legal");
    if (capture_move) {
        Undo undo;
        (void)capture.make_move(*capture_move, undo);
        check(capture.halfmove_clock() == 0 && !capture.is_insufficient_material(), "capture resets clock with material remaining");
        Searcher searcher(4, 1);
        check(SearcherTestProbe::run(searcher, capture, 0, -Infinite, Infinite) > 0,
              "reset capture child is evaluated rather than forced to rule50 draw");
    }
    Board pawn;
    check(pawn.set_fen("7k/8/8/8/8/8/1P6/K5R1 w - - 99 80"), "pawn fixture parses");
    const auto pawn_move = pawn.parse_uci("b2b3");
    check(pawn_move.has_value(), "resetting pawn move is legal");
    if (pawn_move) {
        Undo undo;
        (void)pawn.make_move(*pawn_move, undo);
        check(pawn.halfmove_clock() == 0, "pawn move resets rule50 clock");
        Searcher searcher(4, 1);
        check(SearcherTestProbe::run(searcher, pawn, 0, -Infinite, Infinite) < 0,
              "reset pawn child is evaluated rather than forced to rule50 draw");
    }

    // The original one-line current-clock guard failed these reverse paths.
    // Genuine near-limit draw bounds must not override these low-clock searches.
    Searcher reverse(4, 1), reverse_cold(4, 1);
    const int draw_seed = SearcherTestProbe::run(reverse, near, 0, -Infinite, Infinite);
    const int reverse_cached = SearcherTestProbe::run(reverse, low, 0, -1, 0);
    const int reverse_fresh = SearcherTestProbe::run(reverse_cold, low, 0, -1, 0);
    std::cout << "reverse_q_direct high99_seed=" << draw_seed << " low0_warm="
              << reverse_cached << " low0_cold=" << reverse_fresh << '\n';
    check(draw_seed == 0 && reverse_cached == reverse_fresh && reverse_cached < -1,
          "near-limit draw does not override low-clock direct qsearch");
    Board quiet_low, quiet_high;
    check(quiet_low.set_fen("7k/8/8/8/8/8/8/KR6 w - - 0 80") &&
          quiet_high.set_fen("7k/8/8/8/8/8/8/KR6 w - - 99 80"), "quiet eval-substitution fixtures parse");
    Searcher eval_warm(4, 1), eval_cold(4, 1);
    const int quiet_seed = SearcherTestProbe::run(eval_warm, quiet_high, 1, -Infinite, Infinite);
    print_tt(eval_warm, quiet_low);
    const int cached_eval = SearcherTestProbe::run(eval_warm, quiet_low, 0, -Infinite, Infinite);
    const int fresh_eval = SearcherTestProbe::run(eval_cold, quiet_low, 0, -Infinite, Infinite);
    std::cout << "reverse_q_score_as_eval high99_main_seed=" << quiet_seed
              << " low0_pv_q_warm=" << cached_eval << " low0_pv_q_cold=" << fresh_eval << '\n';
    check(quiet_seed == 0 && cached_eval == fresh_eval && cached_eval > 0,
          "near-limit draw does not replace low-clock PV static evaluation");

    Searcher same_context(4, 1);
    check(SearcherTestProbe::run(same_context, near, 0, -Infinite, Infinite) == 0,
          "same-context fixture learns genuine near-limit draw");
    const int same_score = SearcherTestProbe::run(same_context, near, 0, -1, 0);
    check(same_score == 0 && SearcherTestProbe::visited(same_context) == 1,
          "matching near-limit qsearch score remains reusable");
    std::cout << "targeted_regression_failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}

