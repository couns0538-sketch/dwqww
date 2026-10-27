// Search translation unit.
//
// The search is split into modules under src/search/ (one concern per file).
// They are compiled together as this single translation unit, each included
// exactly once below, so that
//   - the build recipe is unchanged: CMakeLists.txt, 2_build/build_windows.ps1
//     and the PC gate scripts still compile the same eight .cpp files, and
//   - the generated code keeps the AL1 s198 shape: the modules are included in
//     the order the functions had in the former single-file search.cpp, small
//     helpers are header-inline, and the Worker data layout is unchanged
//     (forge/thread_data.hpp), so the hot functions are emitted with the same
//     code and placement (see opus_round1/O3/REPORT.md, NPS section).
// Public interfaces: forge/search.hpp (Worker, Searcher), forge/search_types.hpp,
// forge/tt.hpp, forge/history.hpp, forge/thread_data.hpp, forge/search_tune.hpp.
#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <optional>

#include "search/tune.inc"        // tunable constants, LMR / LMP tables
#include "search/options.inc"     // runtime search options (all OFF by default)
#include "search/scores.inc"      // mate scores and their TT encoding
#include "search/uci_info.inc"    // UCI info output (score formatting)
#include "search/tt.inc"          // transposition table
#include "search/movepicker.hpp"  // staged move picker
#include "search/worker.inc"      // per-thread state lifecycle
#include "search/evaluation.inc"  // static evaluation glue, correction history
#include "search/timeman.hpp"     // time budgets and the soft stop rule (inline)
#include "search/checks.inc"      // per-node clock / node / stop checks, draws
#include "search/history.inc"     // move-ordering history scoring and updates
#include "search/qsearch.inc"     // quiescence search
#include "search/alphabeta.inc"   // main alpha-beta search
#include "search/iterative.inc"   // root setup and iterative deepening
#include "search/searcher.inc"    // Searcher facade: helper threads, TT lifecycle
#include "search/tt_lockless.inc" // UCI LocklessTT: lockless TT access (last: keeps the default placement)
