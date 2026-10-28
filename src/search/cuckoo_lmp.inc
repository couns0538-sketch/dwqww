// Search module: the late-move pruning threshold of tune.inc, as a copy for the
// CuckooRep instance of the main search (UCI CuckooRep). Compiled as part of
// src/search.cpp (included exactly once), right before the second inclusion of
// alphabeta.inc. The AL1 s198 lmp_threshold() keeps its single call site in the
// default Worker::search: with a second caller GCC inlines it in a later pass,
// which shifts the SSA numbering of the default search, swaps the operands of
// one comparison and changes its block layout (found in job O5,
// opus_round1/O5/logs/codegen_second_instance_investigation.log on opus-O5).

namespace forge {

namespace {

[[nodiscard]] int lmp_threshold_cuckoo(int depth, bool improving) {
    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / 2;
}

} // namespace

} // namespace forge
