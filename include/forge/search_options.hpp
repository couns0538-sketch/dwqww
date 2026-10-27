#pragma once

#include <cstdint>

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI CorrHistPlus (spin 0-7, default 0): extra correction-history keys, a
// bitmask of forge::corrplus::{Continuation = 1, MinorPiece = 2, NonPawn = 4}
// (forge/correction_plus.hpp). 0 keeps the AL1 s198 pawn + material
// correction only; each bit is meant to be gated on its own. One byte so that
// the default-path test in the hot corrected_eval is a single compare with
// memory that needs no register.
extern std::uint8_t corr_hist_plus;

} // namespace forge::options
