#include "forge/search_types.hpp"
#include "forge/syzygy.hpp"
namespace forge::syzygy { bool tb_scores = false; }
namespace forge::fb2 {
[[gnu::cold]] SearchInfo smp_select_result(const SearchInfo& main, const std::vector<SearchInfo>& helpers) {
    if (main.restricted_root_empty) return main;
    const auto valid_score = [](int score) { return score >= -MateValue && score <= MateValue; };
    const auto proven = [&](int score) {
        return valid_score(score) && (is_mate_score(score) ||
               (syzygy::tb_scores && score >= syzygy::TbWinInMaxPly));
    };
    const SearchInfo* best = &main;
    for (const auto& helper : helpers) {
        if (helper.best_move.is_none() || helper.pv.empty() || helper.pv.front() != helper.best_move ||
            helper.restricted_root_empty || helper.depth <= best->depth || !valid_score(helper.score)) continue;
        // Depth alone cannot erase a proven score, even after one helper has been selected.
        if (proven(best->score) && (!proven(helper.score) || helper.score < best->score)) continue;
        best = &helper;
    }
    SearchInfo result = *best;
    result.nodes = main.nodes;
    result.elapsed_ms = main.elapsed_ms;
    return result;
}

}
