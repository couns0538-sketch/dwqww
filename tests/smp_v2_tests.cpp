// Astra R2 B1: regression of Forge FB2-J5's real deepest-helper selector.
// IDEA_SOURCE: the user's proven-result invariant and Forge's own J5 implementation;
// no algorithm, code, or tuned constants from another engine.
#include "forge/search_types.hpp"
#ifdef FORGE_SMP_V2_NATIVE_TESTS
#include "forge/search.hpp"
#endif
#include "forge/syzygy.hpp"
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using namespace forge;
namespace {
int checks = 0, failures = 0;
void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) { ++failures; std::cout << "FAIL " << name << '\n'; }
}
SearchInfo info(int depth, int score, int index) {
    SearchInfo r;
    r.depth = depth; r.nominal_depth = depth; r.seldepth = depth + 2; r.score = score;
    r.best_move = Move{static_cast<std::uint8_t>(8 + index), static_cast<std::uint8_t>(24 + index), 0, DoublePush};
    r.ponder_move = Move{48, 40, 0, Quiet};
    r.pv = {r.best_move, r.ponder_move};
    r.nodes = static_cast<std::uint64_t>(index + 1) * 1000U;
    r.elapsed_ms = static_cast<std::uint64_t>(index + 1) * 20U;
    return r;
}
void expect(const SearchInfo& main, const std::vector<SearchInfo>& helpers,
            const SearchInfo& winner, const std::string& name, int depth_cap = 64) {
    const auto got = fb2::smp_select_result(main, helpers, depth_cap);
    check(got.best_move == winner.best_move && got.ponder_move == winner.ponder_move &&
          got.score == winner.score && got.depth == winner.depth &&
          got.nominal_depth == winner.nominal_depth && got.pv == winner.pv, name);
    check(got.nodes == main.nodes && got.elapsed_ms == main.elapsed_ms, name + ": preserve main accounting");
}
}
int main() {
    const auto mate = info(12, MateValue - 5, 0);
    auto ordinary = info(20, 1500, 1);
    expect(mate, {ordinary}, mate, "deeper ordinary helper cannot erase main mate");
    expect(mate, {info(20, MateValue - 9, 1)}, mate, "deeper longer mate cannot erase shorter mate");
    expect(mate, {info(12, MateValue - 3, 1)}, mate, "equal-depth mate does not replace main");
    expect(mate, {info(10, MateValue - 3, 1)}, mate, "shallower mate does not replace main");
    auto deeper_mate = info(13, mate.score, 1);
    expect(mate, {deeper_mate}, deeper_mate, "deeper equal proven mate is accepted");
    auto shorter_mate = info(13, MateValue - 3, 1);
    expect(mate, {shorter_mate}, shorter_mate, "deeper better proven mate is accepted");
    expect(mate, {shorter_mate, ordinary}, shorter_mate, "accepted proven helper remains protected from later helper");
    auto losing_mate = info(12, -MateValue + 5, 0);
    expect(losing_mate, {ordinary}, losing_mate, "main negative mate requires a deeper proven replacement");
    expect(losing_mate, {info(13, -MateValue + 3, 1)}, losing_mate, "deeper worse negative mate is rejected");
    auto longer_resistance = info(13, -MateValue + 9, 1);
    expect(losing_mate, {longer_resistance}, longer_resistance, "deeper better negative mate is accepted");
    syzygy::tb_scores = true;
    auto tb_win = info(12, syzygy::TbWin - 3, 0);
    expect(tb_win, {ordinary}, tb_win, "deeper ordinary helper cannot erase main TB win");
    expect(tb_win, {info(20, syzygy::TbWin - 8, 1)}, tb_win, "deeper lower TB win cannot replace");
    auto better_tb = info(13, syzygy::TbWin - 2, 1);
    expect(tb_win, {better_tb}, better_tb, "deeper better TB win accepted");
    expect(tb_win, {shorter_mate}, shorter_mate, "deeper mate improves TB win");
    auto boundary = info(12, syzygy::TbWinInMaxPly, 0);
    expect(boundary, {ordinary}, boundary, "lowest reserved TB winning score protected");
    auto tb_loss = info(12, -syzygy::TbWin + 3, 0);
    expect(tb_loss, {ordinary}, tb_loss, "deeper ordinary helper cannot erase main proven TB loss");
    expect(tb_loss, {info(20, -syzygy::TbWin + 2, 1)}, tb_loss, "deeper worse TB loss cannot replace");
    auto better_loss = info(13, -syzygy::TbWin + 4, 1);
    expect(tb_loss, {better_loss}, better_loss, "deeper equal-or-better proven TB loss accepted");
    auto negative_boundary = info(12, -syzygy::TbWinInMaxPly, 0);
    expect(negative_boundary, {ordinary}, negative_boundary, "negative TB boundary is protected");
    syzygy::tb_scores = false;
    expect(tb_loss, {ordinary}, ordinary, "without TBs negative numeric band uses ordinary ranking");
    expect(tb_win, {ordinary}, ordinary, "without loaded TBs same numeric band uses ordinary ranking");
    auto main = info(12, 300, 0);
    expect(main, {ordinary}, ordinary, "ordinary deeper helper wins despite lower or higher score");
    expect(main, {info(12, 900, 1)}, main, "ordinary ties stay main even with higher score");
    // Nominal depth is diagnostic metadata, not a replacement for the existing
    // capped actual-depth ranking. Preserve the selected worker's metadata.
    auto skewed = info(13, 900, 1);
    skewed.nominal_depth = 11;
    expect(main, {skewed}, skewed, "actual depth still ranks above higher nominal depth", 14);
    expect(main, {skewed}, main, "actual-depth cap still ties skewed helper with main", 12);
    // Requested-depth ranking: N+1 is useful helper work, not a deeper completed
    // result for deciding between workers that both completed the user's N.
    expect(main, {info(13, 900, 1)}, main, "requested N: main N ties helper N+1", 12);
    expect(mate, {shorter_mate}, mate, "requested N: better proven helper N+1 still ties main N", 12);
    const auto below_cap = info(11, 300, 0);
    const auto at_cap = info(12, 350, 1);
    expect(below_cap, {at_cap}, at_cap, "helper genuinely deeper below requested cap can win", 12);
    const auto above_cap = info(13, 350, 1);
    expect(below_cap, {above_cap, info(14, 400, 2)}, above_cap,
           "helpers over cap tie; first qualifying helper is retained", 12);
    auto below_mate = info(11, mate.score, 0);
    auto at_mate = info(12, mate.score, 1);
    expect(below_mate, {at_mate}, at_mate, "deeper equal proven result below cap accepted", 12);
    auto mate_one = info(1, MateValue - 1, 0);
    expect(mate_one, {info(2, MateValue - 1, 1)}, mate_one, "mate search depth cap preserves main", 1);
    for (int bad : {Infinite, ValueNone, -Infinite, std::numeric_limits<int>::min(), std::numeric_limits<int>::max()}) {
        expect(mate, {info(20, bad, 1)}, mate, "invalid sentinel cannot be proven " + std::to_string(bad));
        expect(main, {info(20, bad, 1)}, main, "invalid sentinel cannot replace ordinary " + std::to_string(bad));
    }
    ordinary.best_move = Move::none();
    expect(main, {ordinary}, main, "missing move ignored");
    ordinary = info(20, 1500, 1); ordinary.pv.clear();
    expect(main, {ordinary}, main, "empty PV ignored");
    ordinary = info(20, 1500, 1); ordinary.pv.front() = main.best_move;
    expect(main, {ordinary}, main, "inconsistent PV ignored");
    ordinary = info(20, 1500, 1); ordinary.restricted_root_empty = true;
    expect(main, {ordinary}, main, "empty restricted root ignored");
    auto restricted = main; restricted.restricted_root_empty = true;
    expect(restricted, {info(20, 1500, 1)}, restricted, "main empty root restriction is authoritative");
#ifdef FORGE_SMP_V2_NATIVE_TESTS
    fb2::requested.smp_v2 = true;
    for (const auto bundle : {fb2::Bundle::Off, fb2::Bundle::B1, fb2::Bundle::B2, fb2::Bundle::B3, fb2::Bundle::B4}) {
        fb2::apply_bundle(bundle);
        check(fb2::requested.smp_v2, "preset preserves independent SmpV2 option");
    }
    const auto snapshot = fb2::effective(fb2::requested, 0);
    fb2::requested.smp_v2 = false;
    check(snapshot.smp_v2, "per-search snapshot survives next pending option update");
    fb2::apply_bundle(fb2::Bundle::Off);
    // Exercise the production Worker directly with a bounded completed search:
    // helper diversification adds one actual ply to helper 1's nominal depth.
    const auto search_worker = [](int id, const Board& board, const SearchLimits& limits) {
        SharedSearchState shared(16);
        auto worker = std::make_unique<Worker>(shared, id);
        const std::vector<Worker*> workers{worker.get()};
        const SearchInfo result = worker->search(board, limits, false, workers);
        worker->end_search();
        return result;
    };
    SearchLimits depth_limits;
    depth_limits.depth = 3;
    depth_limits.fb2.smp_v2 = true;
    const auto helper_depth = search_worker(1, Board{}, depth_limits);
    check(helper_depth.depth == 4 && helper_depth.nominal_depth == 3,
          "completed helper records actual and nominal depths separately");
    const auto main_depth = search_worker(0, Board{}, depth_limits);
    check(main_depth.depth == 3 && main_depth.nominal_depth == 3,
          "completed main records equal actual and nominal depths");
    Board terminal;
    check(terminal.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), "nominal-depth terminal fixture parses");
    const auto terminal_depth = search_worker(1, terminal, depth_limits);
    check(terminal_depth.depth == 3 && terminal_depth.nominal_depth == 3,
          "terminal helper reports nominal depth without diversification");
    SearchLimits zero_limits = depth_limits;
    zero_limits.nodes_specified = true;
    zero_limits.nodes = 0;
    const auto zero_depth = search_worker(0, Board{}, zero_limits);
    check(zero_depth.depth == 0 && zero_depth.nominal_depth == 0,
          "zero-budget search has no completed nominal depth");
    // SmpV2 must not change the main worker's partial-iteration adoption policy.
    // Compare fresh ON/OFF searches, without pinning a particular move or score.
    for (const std::uint64_t cap : {100U, 500U, 1000U, 2000U, 5000U}) {
        SearchLimits limits; limits.nodes = cap; limits.nodes_specified = true;
        fb2::requested.smp_v2 = false;
        Searcher off_search(16, 1);
        const SearchInfo off = off_search.search(Board{}, limits);
        fb2::requested.smp_v2 = true;
        Searcher on_search(16, 1);
        const SearchInfo on = on_search.search(Board{}, limits);
        check(on.best_move == off.best_move && on.ponder_move == off.ponder_move && on.pv == off.pv &&
              on.score == off.score && on.depth == off.depth && on.nominal_depth == off.nominal_depth &&
              on.seldepth == off.seldepth && on.nodes == off.nodes,
              "Threads1 ON/OFF main behavior identical at node cap " + std::to_string(cap));
        std::cout << "main identity cap=" << cap << " OFF depth=" << off.depth << " score=" << off.score
                  << " move=" << Board::move_to_uci(off.best_move) << " ON depth=" << on.depth
                  << " score=" << on.score << " move=" << Board::move_to_uci(on.best_move) << '\n';
    }
    fb2::requested.smp_v2 = false;
#endif
    std::cout << "smp_v2 selector: checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
