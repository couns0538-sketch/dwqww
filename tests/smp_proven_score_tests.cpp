// IDEA_SOURCE: Owner A2; Forge's own SMP selector and Syzygy score contract.
#include "forge/search.hpp"
#include "forge/syzygy.hpp"
#include <iostream>
#include <vector>
#ifndef FORGE_TEST_BASE_REPRO
namespace forge {
struct SearcherTestProbe {
    static void select(Searcher& s, SearchInfo& main, const std::vector<SearchInfo>& helpers) {
        s.select_best_thread(main, helpers, false);
    }
};
}
#endif
using namespace forge;
int main() {
    int failures = 0;
    auto check = [&](bool value, const char* name) {
        std::cout << (value ? "PASS " : "FAIL ") << name << '\n';
        failures += !value;
    };
    auto info = [](int depth, int score, int which) {
        Board board; const auto moves = board.legal_moves();
        SearchInfo r; r.depth = depth; r.score = score;
        r.best_move = moves[which]; r.pv = {r.best_move};
        return r;
    };
    auto main = info(10, syzygy::TbWin - 4, 0);
    auto weaker = info(15, 100, 1);
    syzygy::tb_scores = true;
#ifndef FORGE_TEST_BASE_REPRO
    check(!options::smp_protect_proven_score, "option defaults OFF");
    check(better_thread_result(weaker, main), "OFF retains original deeper-result ranking");
    options::smp_protect_proven_score = true;
#endif
    check(!better_thread_result(weaker, main), "deeper ordinary helper cannot replace a TB win");
    check(!better_thread_result(weaker, info(10, syzygy::TbWinInMaxPly, 0)), "inclusive TB boundary protected");
    check(better_thread_result(weaker, info(10, syzygy::TbWinInMaxPly - 1, 0)), "below TB boundary stays ordinary");
    check(better_thread_result(info(8, syzygy::TbWin - 2, 1), main), "higher proven TB win beats deeper lower TB win");
    check(!better_thread_result(info(18, main.score, 1), main), "equal proven TB score retains winner");

    check(!better_thread_result(info(15, syzygy::TbWin - 5, 1), main), "lower TB win cannot replace higher TB win");
    check(better_thread_result(info(8, MateValue - 5, 1), main), "mate can replace TB win");
    check(!better_thread_result(weaker, info(10, MateValue - 5, 0)), "main mate stays protected");
    check(better_thread_result(info(15, 10, 1), info(10, 100, 0)), "ordinary depth preference unchanged");
    syzygy::tb_scores = false;
    check(better_thread_result(weaker, main), "without loaded TBs the reserved band keeps original semantics");
#ifndef FORGE_TEST_BASE_REPRO
    syzygy::tb_scores = true;
    Searcher searcher(1, 1);
    main.nodes = 12345; main.elapsed_ms = 678;
    const auto original = main;
    auto lower_tb = info(18, syzygy::TbWin - 6, 2);
    SearcherTestProbe::select(searcher, main, {SearchInfo{}, weaker, lower_tb});
    check(main.best_move == original.best_move && main.score == original.score &&
          main.depth == original.depth && main.pv == original.pv &&
          main.nodes == original.nodes && main.elapsed_ms == original.elapsed_ms, "actual selector preserves main proven win and metadata across helpers");
    auto ordinary = info(12, 200, 0);
    SearcherTestProbe::select(searcher, ordinary, {SearchInfo{}, original, weaker});
    check(ordinary.best_move == original.best_move && ordinary.score == original.score,
          "TB helper survives later deeper ordinary helper");
    auto mate = info(8, MateValue - 3, 2);
    SearcherTestProbe::select(searcher, main, {SearchInfo{}, mate, weaker});
    check(main.best_move == mate.best_move && main.score == mate.score && main.pv == mate.pv,
          "actual selector accepts stronger mate and rejects later weaker helper");
    check(main.nodes == 12345 && main.elapsed_ms == 678, "selection preserves main accounting");
    auto invalid = info(20, MateValue - 1, 1); invalid.pv.clear();
    SearcherTestProbe::select(searcher, main, {SearchInfo{}, invalid});
    check(main.best_move == mate.best_move && main.score == mate.score, "invalid helper ignored");
    options::smp_protect_proven_score = false;
#endif
    syzygy::tb_scores = false;
    std::cout << "failures=" << failures << '\n';
    return failures ? 1 : 0;
}
