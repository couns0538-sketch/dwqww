#pragma once

#include <cstdint>

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI CorrMargins (spin 0-1, default 0): correction-size pruning margins
// (forge/corr_margins.hpp, weights tune::Corr*Pct). Read once per iteration at
// the root, which then searches with the CorrMargins instance of the main
// search (Worker::search_corr_margins, src/search/alphabeta.inc); with 0 no
// node tests it and the search is the AL1 s198 search.
extern std::uint8_t corr_margins;

} // namespace forge::options
