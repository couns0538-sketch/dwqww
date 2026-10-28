// Search module: helpers of the CorrMargins instance of the main search
// (UCI CorrMargins; the margins themselves are in forge/corr_margins.hpp).
// Compiled as part of src/search.cpp (included exactly once), right before the
// second inclusion of alphabeta.inc.

namespace forge {

namespace {

// The late-move pruning threshold of tune.inc, as a copy for the CorrMargins
// instance. The AL1 s198 lmp_threshold() keeps its single call site in the
// default Worker::search: with a second caller GCC would inline it in a later
// pass, and that alone changes the code layout of the default search.
[[nodiscard]] int lmp_threshold_corr_margins(int depth, bool improving) {
    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / 2;
}

} // namespace

} // namespace forge
