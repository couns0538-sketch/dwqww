// smp_lifecycle_tests.cpp - opus2 SMP pack (FORGE_SMP_LAYOUT=1): Searcher lifecycle in both TT modes, opus_smp_layout/
// SPEC.md 5.2. Own test code. Threads 1/2/4/8 (8 is oversubscribed on small machines: a smoke, not a scaling test):
//   depth- and node-limited searches, an infinite search stopped from another thread, ponder + ponderhit (with a stop
//   fallback), and between searches clear_hash / clear / resize_hash / set_threads / TT mode toggles. Every best move
//   must be legal; every case is time-bounded; Searchers are destroyed at scope end (helpers joined per search).
//   Threads 1 node identity: legacy shared, legacy exclusive (the UCI path) and lockless give the same nodes / move / score.
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#if !FORGE_SMP_LAYOUT
#error "smp_lifecycle_tests needs FORGE_SMP_LAYOUT=1 (CMake option FORGE_SMP_LAYOUT=ON)"
#endif

namespace {

using forge::Board;
using forge::Move;
using forge::SearchInfo;
using forge::SearchLimits;
using forge::Searcher;

int failures = 0;
void check(bool ok, const std::string& what) {
    if (!ok) {
        ++failures;
        if (failures <= 40) std::cout << "FAIL " << what << "\n";
    }
}

const std::vector<std::string> Fens = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8",
};

int env_int(const char* name, int fallback) {
    const char* v = std::getenv(name);
    return v == nullptr ? fallback : std::atoi(v);
}

bool is_legal_move(const Board& board, const Move& move) {
    for (const Move& m : board.legal_moves()) if (m == move) return true;
    return false;
}

double seconds_since(std::chrono::steady_clock::time_point t0) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
}

void expect_legal(const Board& board, const SearchInfo& info, const std::string& what) {
    check(is_legal_move(board, info.best_move), what + ": best move " + Board::move_to_uci(info.best_move) + " is legal");
}

void run_cases(bool lockless, int threads, int depth) {
    const std::string tag = std::string(lockless ? "lockless" : "legacy") + " T" + std::to_string(threads);
    Searcher s(16, threads);
    s.set_tt_lockless(lockless);
    check(s.transposition_table().lockless() == lockless, tag + ": mode set");
    for (std::size_t i = 0; i < Fens.size(); ++i) {
        Board board;
        if (!board.set_fen(Fens[i])) { check(false, tag + ": FEN " + Fens[i]); continue; }
        const std::string where = tag + " fen" + std::to_string(i);
        // A: depth-limited
        s.reset_stop();
        SearchLimits a; a.depth = depth;
        auto t0 = std::chrono::steady_clock::now();
        expect_legal(board, s.search(board, a), where + " depth");
        check(seconds_since(t0) < 120.0, where + " depth search bounded");
        // B: node-limited (every worker checks the shared node count on every node: the nodes_ cache-line path)
        s.reset_stop();
        SearchLimits b; b.nodes = 40000; b.nodes_specified = true;
        expect_legal(board, s.search(board, b), where + " nodes");
        // C: infinite, stopped from another thread
        s.reset_stop();
        SearchLimits c; c.infinite = true;
        t0 = std::chrono::steady_clock::now();
        std::thread stopper([&s]() { std::this_thread::sleep_for(std::chrono::milliseconds(40)); s.stop(); });
        const SearchInfo ci = s.search(board, c);
        stopper.join();
        expect_legal(board, ci, where + " infinite+stop");
        check(seconds_since(t0) < 30.0, where + " stop ended the infinite search");
        // D: ponder, ponderhit after 20 ms with movetime 60; stop fallback after 5 s if it is still running
        s.reset_stop();
        SearchLimits d; d.ponder = true; d.movetime_ms = 60;
        std::atomic<bool> done{false};
        std::atomic<bool> fallback_used{false};
        std::thread pinger([&]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
            s.ponderhit();
            const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
            while (!done.load(std::memory_order_acquire) && std::chrono::steady_clock::now() < deadline) {
                std::this_thread::sleep_for(std::chrono::milliseconds(5));
            }
            if (!done.load(std::memory_order_acquire)) { fallback_used.store(true); s.stop(); }
        });
        const SearchInfo di = s.search(board, d);
        done.store(true, std::memory_order_release);
        pinger.join();
        expect_legal(board, di, where + " ponder+ponderhit");
        check(!fallback_used.load(), where + " ponderhit ended the ponder search without the stop fallback");
    }
    // E: lifecycle operations between searches (all quiescent: search() joined its helpers)
    Board board;
    (void)board.set_fen(Fens[1]);
    SearchLimits l; l.depth = depth > 6 ? 6 : depth;
    s.reset_stop(); s.clear_hash(); expect_legal(board, s.search(board, l), tag + " after clear_hash");
    s.reset_stop(); s.resize_hash(1); expect_legal(board, s.search(board, l), tag + " after resize_hash(1)");
    s.reset_stop(); s.set_threads(threads == 1 ? 3 : 1); expect_legal(board, s.search(board, l), tag + " after set_threads");
    s.reset_stop(); s.set_tt_lockless(!lockless); expect_legal(board, s.search(board, l), tag + " after mode toggle");
    s.reset_stop(); s.set_tt_lockless(lockless); s.clear(); expect_legal(board, s.search(board, l), tag + " after toggle back + clear");
    s.reset_stop(); s.set_threads(threads); s.resize_hash(8); expect_legal(board, s.search(board, l), tag + " after resize_hash(8)");
    std::cout << tag << ": cases done\n";
}

void node_identity_threads1(int depth) {
    for (std::size_t i = 0; i < Fens.size(); ++i) {
        Board board;
        (void)board.set_fen(Fens[i]);
        SearchLimits limits; limits.depth = depth;
        Searcher shared_legacy(16, 1), exclusive_legacy(16, 1), lockless(16, 1);
        lockless.set_tt_lockless(true);
        const SearchInfo r1 = shared_legacy.search(board, limits, false, Searcher::TTAccess::Shared);
        const SearchInfo r2 = exclusive_legacy.search(board, limits, false, Searcher::TTAccess::Exclusive);
        const SearchInfo r3 = lockless.search(board, limits, false, Searcher::TTAccess::Exclusive);
        // A second (warm-table) search on the same searchers must agree as well.
        const SearchInfo w1 = shared_legacy.search(board, limits, false, Searcher::TTAccess::Shared);
        const SearchInfo w2 = exclusive_legacy.search(board, limits, false, Searcher::TTAccess::Exclusive);
        const SearchInfo w3 = lockless.search(board, limits, false, Searcher::TTAccess::Exclusive);
        const std::string where = "T1 identity fen" + std::to_string(i);
        check(r1.nodes == r2.nodes && r2.nodes == r3.nodes, where + ": nodes " + std::to_string(r1.nodes) + "/" + std::to_string(r2.nodes) + "/" + std::to_string(r3.nodes));
        check(r1.best_move == r2.best_move && r2.best_move == r3.best_move, where + ": best move");
        check(r1.score == r2.score && r2.score == r3.score, where + ": score");
        check(w1.nodes == w2.nodes && w2.nodes == w3.nodes, where + " warm: nodes " + std::to_string(w1.nodes) + "/" + std::to_string(w2.nodes) + "/" + std::to_string(w3.nodes));
        check(w1.best_move == w2.best_move && w2.best_move == w3.best_move && w1.score == w3.score, where + " warm: move/score");
        std::cout << where << ": nodes " << r1.nodes << " warm " << w1.nodes << " (shared / exclusive / lockless)\n";
    }
}

} // namespace

int main() {
    const int depth = env_int("FORGE_SMP_LIFECYCLE_DEPTH", 7);
    node_identity_threads1(env_int("FORGE_SMP_IDENTITY_DEPTH", 9));
    for (const bool lockless : {false, true}) {
        for (const int threads : {1, 2, 4, 8}) run_cases(lockless, threads, threads >= 4 ? depth - 1 : depth);
    }
    if (failures == 0) {
        std::cout << "All smp_lifecycle groups passed\n";
        return 0;
    }
    std::cout << failures << " smp_lifecycle failure(s)\n";
    return 1;
}
