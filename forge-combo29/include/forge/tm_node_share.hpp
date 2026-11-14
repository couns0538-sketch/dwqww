#pragma once

#include <cstdint>

namespace forge {

// One finished clock iteration, with timings the caller already chose.
// best_nodes is the current best root move. root_nodes is the sum of the
// per-root-move counters (not the whole tree).
struct NodeShareTiming {
    std::int64_t soft_ms = 0;
    std::int64_t hard_ms = 0;
    std::int64_t elapsed_ms = 0;
    std::uint64_t best_nodes = 0;
    std::uint64_t root_nodes = 0;
};

// soft_ms is the soft target after the node-share scale.
// reached means elapsed_ms has met that target. Search still multiplies the
// target by its older stability factor before it stops.
struct NodeShareTimingDecision {
    std::int64_t soft_ms = 0;
    bool reached = false;
};

// Lengthen the soft target when the best root move holds under half of the
// root nodes, shorten it when the move holds more than half, and leave a tie
// alone. The scale is linear in thousandths of the node share:
// 0% -> 3/2 of soft, 50% -> soft, 100% -> 1/2 of soft.
// A positive result is at least 1 ms. When hard_ms is positive the result is
// also at most hard_ms, so a lengthened target cannot pass the hard limit.
// A non-positive soft_ms is unchanged and is not treated as reached.
[[nodiscard]] constexpr NodeShareTimingDecision decide_node_share_timing(NodeShareTiming in) noexcept {
    NodeShareTimingDecision out;
    if (in.soft_ms <= 0) {
        out.soft_ms = in.soft_ms;
        out.reached = false;
        return out;
    }
    std::int64_t numer = 1000;
    if (in.root_nodes > 0) {
        constexpr std::uint64_t kShareScale = 1000;
        const bool dominant = in.best_nodes >= in.root_nodes || in.best_nodes > (UINT64_MAX / kShareScale);
        const std::uint64_t share = dominant ? kShareScale : (in.best_nodes * kShareScale) / in.root_nodes;
        numer = static_cast<std::int64_t>(kShareScale) + (500 - static_cast<std::int64_t>(share));
    }
    const std::int64_t whole = in.soft_ms / 1000;
    const std::int64_t part = in.soft_ms % 1000;
    std::int64_t adjusted = whole * numer + (part * numer) / 1000;
    if (adjusted < 1) adjusted = 1;
    if (in.hard_ms > 0 && adjusted > in.hard_ms) adjusted = in.hard_ms;
    out.soft_ms = adjusted;
    out.reached = in.elapsed_ms >= adjusted;
    return out;
}

}  // namespace forge
