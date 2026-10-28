// Search translation unit.
//
// The search is split into modules under src/search/ (one concern per file).
// They are compiled together as this single translation unit, each included
// exactly once below (except alphabeta.inc, included at the end once more
// once per search instance, see the head of alphabeta.inc), so that
//   - the build recipe is unchanged: CMakeLists.txt, 2_build/build_windows.ps1
//     and the PC gate scripts still compile the same eight .cpp files, and
//   - the generated code keeps the AL1 s198 shape: the modules are included in
//     the order the functions had in the former single-file search.cpp, small
//     helpers are header-inline, and the Worker data layout is unchanged
//     (forge/thread_data.hpp), so the hot functions are emitted with the same
//     code and placement (see opus_round1/O3/REPORT.md, NPS section).
// Public interfaces: forge/search.hpp (Worker, Searcher), forge/search_types.hpp,
// forge/tt.hpp, forge/history.hpp, forge/thread_data.hpp, forge/search_tune.hpp,
// forge/search_options.hpp, forge/corr_margins.hpp, forge/corr_ext.hpp.
#include "forge/search.hpp"
#include "forge/syzygy.hpp"
#include "forge/nnue_v2.hpp"
#include "forge/corr_margins.hpp"
#include "forge/corr_ext.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <new>
#include <optional>

#include "search/tune.inc"        // tunable constants, LMR / LMP tables
#include "search/options.inc"     // runtime search options (all OFF by default)
#include "search/scores.inc"      // mate scores and their TT encoding
#include "search/uci_info.inc"    // UCI info output (score formatting)
#include "search/tt.inc"          // transposition table
#include "search/movepicker.hpp"  // staged move picker
#include "search/worker.inc"      // per-thread state lifecycle
#include "search/evaluation_extra.inc" // v2 network with threat / pawn-pair inputs (O6 NNUEThreats, O7 NNUEPawnPairs)
#include "search/evaluation_v2.inc" // v2 network evaluation (NNUEFile + NNUEKingBuckets)
#include "search/evaluation.inc"  // static evaluation glue, correction history
#include "search/correction_plus.inc" // CorrHistPlus extra correction keys (cold)
#include "search/timeman.hpp"     // time budgets and the soft stop rule (inline)
#include "search/checks.inc"      // per-node clock / node / stop checks, draws
#include "search/history.inc"     // move-ordering history scoring and updates
#include "search/qsearch.inc"     // quiescence search
#define FORGE_SEARCH_FN search
#define FORGE_LMP_THRESHOLD lmp_threshold
#define FORGE_SEARCH_CORR_MARGINS 0
#define FORGE_SEARCH_CORR_EXT 0
#include "search/alphabeta.inc"   // main alpha-beta search (Worker::search)
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_FN
#include "search/iterative.inc"   // root setup and iterative deepening
#include "search/searcher.inc"    // Searcher facade: helper threads, TT lifecycle
#include "search/tt_lockless.inc" // UCI LocklessTT: lockless TT access (last: keeps the default placement)
// Syzygy tablebases (all [[gnu::cold]], placed after the search code).
#include "search/tablebase.inc"   // search glue: in-search probe, root filter
#include "search/syzygy.inc"      // table reader, WDL/DTZ probes, root ranking
// The main search once more for each combination of UCI CorrMargins and CorrExt
// (see the head of alphabeta.inc). Last in the file, so that the default search
// functions keep the AL1 s198 code and placement.
#include "search/corr_margins.inc" // CorrMargins: helpers of its instance
#define FORGE_SEARCH_FN search_corr_margins
#define FORGE_LMP_THRESHOLD lmp_threshold_corr_margins
#define FORGE_SEARCH_CORR_MARGINS 1
#define FORGE_SEARCH_CORR_EXT 0
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_FN
#include "search/corr_ext.inc"    // CorrExt: helpers of its instance
#define FORGE_SEARCH_FN search_corr_ext
#define FORGE_LMP_THRESHOLD lmp_threshold_corr_ext
#define FORGE_SEARCH_CORR_MARGINS 0
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_FN
// R3 stack: CorrMargins and CorrExt together.
#define FORGE_SEARCH_FN search_cm_ce
#define FORGE_LMP_THRESHOLD lmp_threshold_corr_margins
#define FORGE_SEARCH_CORR_MARGINS 1
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_FN
