// Astra R2 B1: regression of Forge FB2-J5's real deepest-helper selector.
// IDEA_SOURCE: the user's proven-result invariant and Forge's own J5 implementation;
// no algorithm, code, or tuned constants from another engine.
#include "forge/search_types.hpp"
#include "forge/syzygy.hpp"
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace forge::fb2 {
SearchInfo smp_select_result(const SearchInfo&, const std::vector<SearchInfo>&);
}
using namespace forge;
namespace {
int checks = 0, failures = 0;
void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) { ++failures; std::cout << "FAIL " << name << '\n'; }
}
SearchInfo info(int depth, int score, int index) {
    SearchInfo r;
    r.depth = depth; r.seldepth = depth + 2; r.score = score;
    r.best_move = Move{static_cast<std::uint8_t>(8 + index), static_cast<std::uint8_t>(24 + index), 0, DoublePush};
    r.ponder_move = Move{48, 40, 0, Quiet};
    r.pv = {r.best_move, r.ponder_move};
    r.nodes = static_cast<std::uint64_t>(index + 1) * 1000U;
    r.elapsed_ms = static_cast<std::uint64_t>(index + 1) * 20U;
    return r;
}
void expect(const SearchInfo& main, const std::vector<SearchInfo>& helpers,
            const SearchInfo& winner, const std::string& name) {
    const auto got = fb2::smp_select_result(main, helpers);
    check(got.best_move == winner.best_move && got.ponder_move == winner.ponder_move &&
          got.score == winner.score && got.depth == winner.depth && got.pv == winner.pv, name);
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
    syzygy::tb_scores = false;
    expect(tb_win, {ordinary}, ordinary, "without loaded TBs same numeric band uses ordinary ranking");
    auto main = info(12, 300, 0);
    expect(main, {ordinary}, ordinary, "ordinary deeper helper wins despite lower or higher score");
    expect(main, {info(12, 900, 1)}, main, "ordinary ties stay main even with higher score");
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
    std::cout << "smp_v2 selector: checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
