#pragma once

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

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
