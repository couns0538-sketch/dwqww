// Search-level checks for the clock plan: an empty reserve does not search,
// and fixed-depth / fixed-node searches keep the node counts measured before
// the change. Those counts are from Searcher at Hash 16 and Threads 1.

#include "forge/board.hpp"
#include "forge/clock_plan.hpp"
#include "forge/search.hpp"

#include <chrono>
#include <cstdint>
#include <iostream>
#include <string>
#include <thread>

namespace {

int failures = 0;

void fail(const std::string& message) {
    ++failures;
    std::cerr << "FAIL " << message << '\n';
}

[[nodiscard]] bool is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none()) return false;
    for (const forge::Move candidate : board.legal_moves()) {
        if (candidate == move) return true;
    }
    return false;
}

void expect_fixed(const char* label, const char* fen, int depth, std::uint64_t node_limit, bool nodes_specified,
                  std::uint64_t nodes, int out_depth, const char* move) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string(label) + " fen");
        return;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = depth;
    if (nodes_specified) {
        limits.nodes = node_limit;
        limits.nodes_specified = true;
    }
    const forge::SearchInfo info = searcher.search(board, limits, false);
    const std::string played = forge::Board::move_to_uci(info.best_move);
    if (info.nodes != nodes || info.depth != out_depth || played != move) {
        fail(std::string(label) + " nodes " + std::to_string(info.nodes) + " depth " + std::to_string(info.depth) +
             " move " + played);
    } else {
        std::cout << "PASS " << label << " nodes " << info.nodes << " move " << played << '\n';
    }
}

void expect_empty_clock(const char* label, const char* fen, std::int64_t time_ms, int overhead, int threads) {
    forge::Board board;
    if (!board.set_fen(fen)) {
        fail(std::string(label) + " fen");
        return;
    }
    forge::Searcher searcher(16, threads);
    forge::SearchLimits limits;
    limits.time_ms = time_ms;
    limits.move_overhead_ms = overhead;
    const auto started = std::chrono::steady_clock::now();
    const forge::SearchInfo info = searcher.search(board, limits, false);
    const auto wall_ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
    if (info.nodes > 2000 || info.depth > 1 || !is_legal(board, info.best_move)) {
        fail(std::string(label) + " nodes " + std::to_string(info.nodes) + " depth " + std::to_string(info.depth));
        return;
    }
    std::cout << "PASS " << label << " nodes " << info.nodes << " depth " << info.depth << " move "
              << forge::Board::move_to_uci(info.best_move) << " wall " << wall_ms << " ms\n";
}

void expect_live_clock(const char* label, std::int64_t time_ms, std::int64_t increment, int moves_to_go, int overhead) {
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) {
        fail(std::string(label) + " fen");
        return;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.time_ms = time_ms;
    limits.increment_ms = increment;
    limits.moves_to_go = moves_to_go;
    limits.move_overhead_ms = overhead;
    const forge::SearchInfo info = searcher.search(board, limits, false);
    if (info.nodes == 0 || info.depth <= 0 || info.depth >= 64 || !is_legal(board, info.best_move)) {
        fail(std::string(label) + " nodes " + std::to_string(info.nodes) + " depth " + std::to_string(info.depth));
        return;
    }
    std::cout << "PASS " << label << " nodes " << info.nodes << " depth " << info.depth << " move "
              << forge::Board::move_to_uci(info.best_move) << '\n';
}

void expect_ponder_then_stop() {
    forge::Board board;
    if (!board.set_fen(forge::Board::StandardStartFen)) {
        fail("ponder fen");
        return;
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.ponder = true;
    limits.time_ms = 0;
    limits.move_overhead_ms = 10;
    forge::SearchInfo info;
    std::thread worker([&]() { info = searcher.search(board, limits, false); });
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(500);
    while (searcher.main_worker().nodes() == 0 && std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    const std::uint64_t before = searcher.main_worker().nodes();
    if (before == 0) {
        searcher.stop();
        worker.join();
        fail("ponder with an empty reserve never started");
        return;
    }
    searcher.ponderhit();
    worker.join();
    if (info.nodes == 0 || !is_legal(board, info.best_move)) {
        fail("ponderhit on an empty reserve did not finish a search");
        return;
    }
    std::cout << "PASS ponder empty reserve nodes " << info.nodes << " move "
              << forge::Board::move_to_uci(info.best_move) << '\n';
}

} // namespace

int main() {
    const forge::ClockPlan live = forge::plan_clock_budget(
        100000, 1000, 0, 10, forge::tune::TmSoftDivisor, forge::tune::TmIncrementPercent, forge::tune::TmHardPercent,
        forge::tune::TmHardSoftMultiple);
    const forge::ClockPlan pinned =
        forge::plan_clock_budget(100000, 1000, 0, 10, 22, 75, 60, 5);
    if (live.soft_ms != pinned.soft_ms || live.hard_ms != pinned.hard_ms || live.reserve_empty != pinned.reserve_empty) {
        fail("tune defaults no longer match 22/75/60/5");
    } else if (forge::tune::TmSoftDivisor != 22 || forge::tune::TmIncrementPercent != 75 ||
               forge::tune::TmHardPercent != 60 || forge::tune::TmHardSoftMultiple != 5) {
        fail("tune initializers drifted");
    } else {
        std::cout << "PASS tune defaults 22/75/60/5\n";
    }

    constexpr const char* start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    constexpr const char* kiwi = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";

    expect_fixed("start-depth-5", start, 5, 0, false, 1001, 5, "c2c4");
    expect_fixed("start-depth-8", start, 8, 0, false, 4099, 8, "d2d4");
    expect_fixed("kiwi-depth-6", kiwi, 6, 0, false, 2279, 6, "e2a6");
    expect_fixed("start-nodes-20000", start, 64, 20000, true, 20000, 10, "d2d4");
    expect_fixed("kiwi-nodes-12000", kiwi, 64, 12000, true, 12000, 7, "d5e6");
    expect_fixed("start-nodes-0", start, 64, 0, true, 0, 0, "a2a3");

    expect_empty_clock("wtime-0-overhead-10", start, 0, 10, 1);
    expect_empty_clock("wtime-5-overhead-50-threads-4", kiwi, 5, 50, 4);
    expect_empty_clock("wtime-10-overhead-10", start, 10, 10, 1);
    expect_empty_clock("wtime-9-overhead-10", start, 9, 10, 1);
    expect_empty_clock("wtime-0-overhead-0", start, 0, 0, 1);
    expect_empty_clock("wtime-0-overhead-10-threads-8", kiwi, 0, 10, 8);

    expect_live_clock("wtime-80", 80, 0, 0, 10);
    expect_live_clock("wtime-100-inc-2000", 100, 2000, 0, 10);
    expect_live_clock("wtime-300-mtg-5", 300, 0, 5, 10);

    forge::Searcher reused(16, 1);
    {
        forge::Board board;
        (void)board.set_fen(start);
        forge::SearchLimits dead;
        dead.time_ms = 0;
        dead.move_overhead_ms = 10;
        const forge::SearchInfo info = reused.search(board, dead, false);
        if (info.nodes > 2000 || info.depth > 1 || !is_legal(board, info.best_move)) {
            fail("reused searcher empty clock nodes " + std::to_string(info.nodes) + " depth " +
                 std::to_string(info.depth));
        }
    }
    reused.clear();
    {
        forge::Board board;
        (void)board.set_fen(start);
        forge::SearchLimits depth;
        depth.depth = 8;
        const forge::SearchInfo info = reused.search(board, depth, false);
        if (info.nodes != 4099 || forge::Board::move_to_uci(info.best_move) != "d2d4") {
            fail("depth search after an empty clock changed nodes to " + std::to_string(info.nodes));
        } else {
            std::cout << "PASS depth after empty clock nodes " << info.nodes << '\n';
        }
    }

    expect_ponder_then_stop();

    if (failures != 0) {
        std::cerr << failures << " guard failures\n";
        return 1;
    }
    std::cout << "PASS clock guard\n";
    return 0;
}
