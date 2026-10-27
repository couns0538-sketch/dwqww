#pragma once

#include <string>

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI NNUEKingBuckets (spin 0-32, default 0) together with UCI NNUEFile
// (string): evaluate with a v2 network (king-bucketed input layer, see
// forge/nnue.hpp nnue::v2) loaded from NNUEFile. N > 0 selects the loaded net
// when it has exactly N king buckets.
//
// Fail-loud rule (no silent fall-back to the compiled-in network). The user
// requests a v2 net with a non-empty NNUEFile or NNUEKingBuckets > 0. A
// request that cannot be honoured (file missing or unreadable, wrong size, bad
// header or checksum, NNUEKingBuckets != the net's king buckets, including 0,
// NNUEKingBuckets > 0 without a loaded file) is an error: the UCI layer prints
// `info string ERROR NNUE v2: <reason>` at once, and if the request is still
// unsatisfied at the next `isready`, `go` or `bench` it prints the error again
// and exits with status 2. Not errors: `UseNNUE false` (every network off on
// purpose; the request is ignored while it lasts) and NNUEFile `<empty>` (clears
// the file part of the request). With no NNUE option set nothing new is printed
// and the engine is the AL1 s198 engine.
extern int nnue_king_buckets;

// UCI NNUEThreats (spin 0-1, default 0; O6; "true" / "false" are accepted as
// well): 1 = evaluate with a v2 net that has threat inputs (header feature_set
// bit 0; forge/nnue_v2.hpp ThreatFeatures), loaded with NNUEFile; with
// NNUEKingBuckets 0 that net must have one king bucket, with NNUEKingBuckets
// N > 0 exactly N. The header and the option must agree both ways: NNUEThreats 1
// with a net without threat inputs, and NNUEThreats 0 with a threat net, are
// fail-loud errors (rule above). NNUEThreats 1 is itself a v2 request (an error
// without a usable net); UseNNUE false still wins.
extern int nnue_threats;

// UCI NNUEPawnPairs (spin 0-1, default 0; O7; "true" / "false" accepted as
// well): 1 = evaluate with a v2 net that has pawn-pair inputs (header
// feature_set bit 1; forge/nnue_v2.hpp PawnPairFeatures). Same rules as
// NNUEThreats: with NNUEKingBuckets 0 a one-bucket net, the header bit and the
// option must agree both ways (fail-loud otherwise), it is a v2 request of its
// own, UseNNUE false wins. NNUEThreats and NNUEPawnPairs are independent: a net
// with both blocks needs both options.
extern int nnue_pawn_pairs;

// Derived switch read by Worker::static_evaluate: true while a v2 network is
// active. Written only by apply_nnue_v2().
extern bool nnue_v2;

// Re-selects the evaluation network after NNUEFile, NNUEKingBuckets or UseNNUE
// changed and returns whether a v2 network is now active. The caller clears
// the hash afterwards (stored static evals may belong to another network).
// `message` (optional) receives a one-line description of the state.
bool apply_nnue_v2(std::string* message);

// The fail-loud rule above: why the current v2 request cannot be honoured, or
// "" when it is honoured, when nothing is requested or when UseNNUE is false.
// `file` is the NNUEFile value ("" = none) and `load_error` why it did not
// load ("" = it loaded). Call after apply_nnue_v2().
std::string nnue_v2_problem(const std::string& file, const std::string& load_error);

} // namespace forge::options
