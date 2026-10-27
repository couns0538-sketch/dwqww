#pragma once

#include <atomic>
#include <cstdint>

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

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
