#pragma once

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI SmpExactNodes (check, default false); acts only with Threads > 1.
// Resets every worker's published node count before the helper threads start
// (otherwise the main thread reads the previous search's counts until each
// helper has started: `go nodes N` can stop at once and the first info lines
// over-report nodes/nps), and reports the exact total after the helpers stop.
extern bool smp_exact_nodes;

} // namespace forge::options
