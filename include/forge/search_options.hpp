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

// UCI SmpBestThread (check, default false); acts only with Threads > 1.
// Reports the best move, ponder move, PV and score of the worker with the
// deepest completed iteration (ties: higher score) instead of always thread 0.
extern bool smp_best_thread;

// UCI LocklessTT (check, default false). The transposition table is probed and
// written without its striped locks: each entry is two 64-bit atomic words and
// the first carries the key tag mixed with a hash of all data bits, so a read
// that combines two writes fails the key check and counts as a miss
// (src/search/tt_lockless.inc). Read once per search by Searcher::search;
// changing it clears the table. Same table contents and rules as the locked
// table, so a search with Threads=1 is unchanged.
extern bool lockless_tt;
// Syzygy tablebases (job C1). The master switch is UCI SyzygyPath (string,
// default empty = no tables, forge/syzygy.hpp); the two options below only act
// while tables are loaded.
// UCI SyzygyProbeDepth (spin 1-10, default 1): positions with as many pieces
// as the largest loaded tables are probed inside the search only at this
// remaining depth or more (fewer pieces: at every depth).
extern int syzygy_probe_depth;
// UCI Syzygy50MoveRule (check, default true): cursed wins and blessed losses
// (decided only beyond the 50-move rule) count as draws.
extern bool syzygy_50_move_rule;

} // namespace forge::options
