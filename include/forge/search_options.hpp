#pragma once

#include <atomic>
#include <cstdint>

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

// UCI CorrHistPlus (spin 0-7, default 0): extra correction-history keys, a
// bitmask of forge::corrplus::{Continuation = 1, MinorPiece = 2, NonPawn = 4}
// (forge/correction_plus.hpp). 0 keeps the AL1 s198 pawn + material
// correction only; each bit is meant to be gated on its own. One byte so that
// the default-path test in the hot corrected_eval is a single compare with
// memory that needs no register.
extern std::uint8_t corr_hist_plus;

// UCI HardDeadline (spin 0-1000 ms, default 0 = off). When N > 0, every search
// with a clock or movetime gets a watchdog thread that sleeps until the hard
// time limit + N ms (ponder searches: counted from ponderhit). If the search has
// not answered by then, the watchdog stops it and sends `bestmove` with the best
// move of the last completed iteration (published by the main worker), so a
// starved or delayed search thread cannot make the engine miss its deadline.
extern int hard_deadline_ms;

// HardDeadline runtime slot: best move (low 32 bits) and ponder move (high 32
// bits) of the main worker's last completed iteration, packed so the pair is
// consistent (forge::pack_move). Process-wide and constant-initialised (no
// constructor code): one UCI search runs at a time; the UCI thread resets it to
// 0 before each clocked search, the main worker writes it, the watchdog reads it.
extern std::atomic<std::uint64_t> published_moves;

} // namespace forge::options
