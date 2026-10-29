#include "forge/search_types.hpp"
namespace forge::syzygy { bool tb_scores = false; }
namespace forge::fb2 {
SearchInfo smp_select_result(const SearchInfo& main, const std::vector<SearchInfo>& helpers) {
    SearchInfo best = main;
    for (const SearchInfo& h : helpers) {
        if (h.best_move.is_none() || h.pv.empty()) continue;
        if (h.depth > best.depth) {
            const std::uint64_t nodes = best.nodes;
            const std::uint64_t elapsed = best.elapsed_ms;
            best = h;
            best.nodes = nodes;            // the reported node count and time stay the main thread's totals
            best.elapsed_ms = elapsed;
        }
    }
    return best;
}
}
