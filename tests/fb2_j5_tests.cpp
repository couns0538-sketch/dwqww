// Unit tests of the FB2-J5 SmpV2 option. Usage: forge_fb2_j5_tests  (uses up to 3 threads for a few seconds)
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using namespace forge;

namespace {
int failures = 0;
int checks = 0;
void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) { ++failures; std::cout << "FAIL: " << what << '\n'; }
}

bool legal(const Board& b, const Move& m) {
    for (const Move& x : b.legal_moves()) if (x.from == m.from && x.to == m.to && x.promotion == m.promotion) return true;
    return false;
}

const char* kFens[] = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "2r3k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
};
} // namespace

int main() {
    // 1. the pure pieces
    {
        check(fb2::smp_depth_skew(0) == 0 && fb2::smp_depth_skew(1) == 1 && fb2::smp_depth_skew(2) == 0 && fb2::smp_depth_skew(3) == 1, "depth skew: odd helpers one ply ahead");
        check(fb2::smp_aspiration_multiplier(0) == 1 && fb2::smp_aspiration_multiplier(1) == 1 && fb2::smp_aspiration_multiplier(2) == 2
              && fb2::smp_aspiration_multiplier(4) == 3 && fb2::smp_aspiration_multiplier(6) == 1, "aspiration multiplier of even helpers cycles 2,3,1");
        SearchInfo main;
        main.depth = 10; main.score = 20; main.nodes = 1000; main.elapsed_ms = 50;
        main.best_move.from = 12; main.best_move.to = 28; main.pv = {main.best_move};
        SearchInfo deeper = main;
        deeper.depth = 11; deeper.score = 35; deeper.nodes = 700; deeper.elapsed_ms = 49; deeper.best_move.from = 6; deeper.best_move.to = 21; deeper.pv = {deeper.best_move};
        SearchInfo shallower = main;
        shallower.depth = 9; shallower.best_move.from = 1; shallower.best_move.to = 18; shallower.pv = {shallower.best_move};
        SearchInfo empty;
        empty.depth = 20;
        const SearchInfo pick = fb2::smp_select_result(main, {shallower, deeper, empty});
        check(pick.depth == 11 && pick.best_move.from == 6 && pick.score == 35, "select: deepest helper with a move wins");
        check(pick.nodes == 1000 && pick.elapsed_ms == 50, "select: node count and time stay the main thread's");
        const SearchInfo tie = fb2::smp_select_result(main, {shallower, main});
        check(tie.best_move.from == 12 && tie.depth == 10, "select: ties keep the main thread");
        const SearchInfo none = fb2::smp_select_result(main, {empty});
        check(none.best_move.from == 12, "select: a result without a move is ignored");
    }

    // 2. the option is inert at Threads 1 (identical node counts) and searches sanely at Threads 2 and 3
    {
        Searcher one(16, 1);
        for (const char* fen : kFens) {
            Board b;
            check(b.set_fen(fen), "fen");
            SearchLimits limits;
            limits.depth = 10;
            fb2::SmpV2 = false;
            one.clear();
            const SearchInfo off = one.search(b, limits, false, Searcher::TTAccess::Exclusive);
            fb2::SmpV2 = true;
            one.clear();
            const SearchInfo on = one.search(b, limits, false, Searcher::TTAccess::Exclusive);
            check(off.nodes == on.nodes && off.depth == on.depth && off.score == on.score, std::string("Threads 1: SmpV2 inert on ") + fen);
        }
        fb2::SmpV2 = false;
        for (int threads = 2; threads <= 3; ++threads) {
            Searcher s(16, threads);
            for (int on = 0; on < 2; ++on) {
                fb2::SmpV2 = on != 0;
                for (const char* fen : kFens) {
                    Board b;
                    (void)b.set_fen(fen);
                    SearchLimits limits;
                    limits.depth = 9;
                    s.clear();
                    const SearchInfo info = s.search(b, limits, false, Searcher::TTAccess::Shared);
                    check(!info.best_move.is_none() && legal(b, info.best_move), "Threads " + std::to_string(threads) + " SmpV2 " + std::to_string(on) + ": legal best move");
                    check(info.depth >= 9 && info.depth <= 10, "Threads " + std::to_string(threads) + " SmpV2 " + std::to_string(on) + ": depth 9 (or a helper's 10)");
                    check(info.score > -Infinite && info.score < Infinite, "finite score");
                    // node-limited search
                    SearchLimits nl;
                    nl.nodes = 20000;
                    nl.nodes_specified = true;
                    s.clear();
                    const SearchInfo n = s.search(b, nl, false, Searcher::TTAccess::Shared);
                    check(!n.best_move.is_none() && legal(b, n.best_move), "node-limited: legal best move");
                }
            }
            fb2::SmpV2 = false;
        }
    }

    // 3. with SmpV2 on and 3 threads, a mate in 1 is still found and reported with a mate score
    {
        Searcher s(16, 3);
        fb2::SmpV2 = true;
        Board b;
        (void)b.set_fen("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1");
        SearchLimits limits;
        limits.depth = 6;
        s.clear();
        const SearchInfo info = s.search(b, limits, false, Searcher::TTAccess::Shared);
        check(info.score >= MateValue - 2 && info.best_move.from == 0 && info.best_move.to == 56, "mate in 1 (Ra8#) with SmpV2 at 3 threads");
        fb2::SmpV2 = false;
    }

    std::cout << checks << " checks, " << failures << " failures\n";
    return failures == 0 ? 0 : 1;
}
