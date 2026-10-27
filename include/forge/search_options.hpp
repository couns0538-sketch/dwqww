#pragma once

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI CuckooRep (check, default false): upcoming-repetition draw bound. At
// every non-root node of the main and quiescence search whose alpha is below
// the draw score, Board::upcoming_repetition() asks whether the side to move
// can reach a search-level repetition draw with one reversible move; if so,
// the draw score is a lower bound for the node (src/search/cuckoo.inc). Read
// once per iteration at the root, which then searches with the CuckooRep
// instances of the search functions; with the option off no node tests it.
extern bool cuckoo_rep;

} // namespace forge::options
