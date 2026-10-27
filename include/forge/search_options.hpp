#pragma once

#include <string>

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI NNUEKingBuckets (spin 0-32, default 0) together with UCI NNUEFile
// (string): evaluate with a v2 network (king-bucketed input layer, see
// forge/nnue.hpp nnue::v2) loaded from NNUEFile. N > 0 selects the loaded net
// when it has exactly N king buckets; 0, no file or a mismatch keeps the
// compiled-in network.
extern int nnue_king_buckets;

// Derived switch read by Worker::static_evaluate: true while a v2 network is
// active. Written only by apply_nnue_v2().
extern bool nnue_v2;

// Re-selects the evaluation network after NNUEFile, NNUEKingBuckets or UseNNUE
// changed and returns whether a v2 network is now active. The caller clears
// the hash afterwards (stored static evals may belong to another network).
// `message` (optional) receives a one-line description of the state.
bool apply_nnue_v2(std::string* message);

} // namespace forge::options
