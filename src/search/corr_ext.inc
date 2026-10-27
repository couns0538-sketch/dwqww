// Search module: helpers of the CorrExt instance of the main search (UCI
// CorrExt; the extension rule itself is in forge/corr_ext.hpp).
// Compiled as part of src/search.cpp (included exactly once), right before the
// second inclusion of alphabeta.inc.

namespace forge {

namespace {

// The late-move pruning threshold of tune.inc, as a copy for the CorrExt
// instance. The AL1 s198 lmp_threshold() keeps its single call site in the
// default Worker::search: with a second caller GCC would inline it in a later
// pass, and that alone changes the code layout of the default search.
[[nodiscard]] int lmp_threshold_corr_ext(int depth, bool improving) {
    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / 2;
}

} // namespace

} // namespace forge
