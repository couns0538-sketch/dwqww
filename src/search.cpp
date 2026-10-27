// Search translation unit.
//
// The search is split into modules under src/search/ (one concern per file).
// They are compiled together as this single translation unit, each included
// exactly once below (except alphabeta.inc, included a second time at the end
// for UCI CorrExt, see the head of alphabeta.inc), so that
//   - the build recipe is unchanged: CMakeLists.txt, 2_build/build_windows.ps1
//     and the PC gate scripts still compile the same eight .cpp files, and
//   - the generated code keeps the AL1 s198 shape: the modules are included in
//     the order the functions had in the former single-file search.cpp, small
//     helpers are header-inline, and the Worker data layout is unchanged
//     (forge/thread_data.hpp), so the hot functions are emitted with the same
//     code and placement (see opus_round1/O3/REPORT.md, NPS section).
// Public interfaces: forge/search.hpp (Worker, Searcher), forge/search_types.hpp,
// forge/tt.hpp, forge/history.hpp, forge/thread_data.hpp, forge/search_tune.hpp,
// forge/search_options.hpp, forge/corr_ext.hpp.
#include "forge/search.hpp"
#include "forge/corr_ext.hpp"
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
#define FORGE_SEARCH_FN search
#define FORGE_SEARCH_CORR_EXT 0
#include "search/alphabeta.inc"   // main alpha-beta search (Worker::search)
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_FN
#include "search/iterative.inc"   // root setup and iterative deepening
#include "search/searcher.inc"    // Searcher facade: helper threads, TT lifecycle
// The main search once more, for UCI CorrExt: the same function with the
// correction-history extensions (Worker::search_corr_ext). Last in the file,
// so that the default search functions keep the AL1 s198 code and placement.
#include "search/corr_ext.inc"    // CorrExt: helpers of the second instance
#define FORGE_SEARCH_FN search_corr_ext
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_FN
