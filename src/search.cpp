// Search translation unit.
//
// The search is split into modules under src/search/ (one concern per file).
// They are compiled together as this single translation unit, each included
// exactly once below (except qsearch.inc and alphabeta.inc, included a second
// time at the end for UCI CuckooRep, see the head of alphabeta.inc), so that
//   - the build recipe is unchanged: CMakeLists.txt, 2_build/build_windows.ps1
//     and the PC gate scripts still compile the same eight .cpp files, and
//   - the generated code keeps the AL1 s198 shape: the modules are included in
//     the order the functions had in the former single-file search.cpp, small
//     helpers are header-inline, and the Worker data layout is unchanged
//     (forge/thread_data.hpp), so the hot functions are emitted with the same
//     code and placement (see opus_round1/O3/REPORT.md, NPS section).
// Public interfaces: forge/search.hpp (Worker, Searcher), forge/search_types.hpp,
// forge/tt.hpp, forge/history.hpp, forge/thread_data.hpp, forge/search_tune.hpp,
// forge/search_options.hpp.
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
#define FORGE_SEARCH_FN search
#define FORGE_SEARCH_CALL search
#define FORGE_QSEARCH_FN qsearch
#define FORGE_QSEARCH_CALL qsearch
#define FORGE_LMP_THRESHOLD lmp_threshold
#include "search/qsearch.inc"     // quiescence search (Worker::qsearch)
#include "search/alphabeta.inc"   // main alpha-beta search (Worker::search)
#undef FORGE_LMP_THRESHOLD
#undef FORGE_QSEARCH_CALL
#undef FORGE_QSEARCH_FN
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#include "search/iterative.inc"   // root setup and iterative deepening
#include "search/searcher.inc"    // Searcher facade: helper threads, TT lifecycle
// The quiescence and main search once more, for UCI CuckooRep: their child
// calls go through the upcoming-repetition bound of cuckoo.inc (see the head
// of alphabeta.inc). Last in the file, so that the default search functions
// keep the AL1 s198 code and placement.
#include "search/cuckoo_lmp.inc"  // the CuckooRep instance's copy of lmp_threshold
#define FORGE_SEARCH_FN search_cuckoo_body
#define FORGE_SEARCH_CALL search_cuckoo
#define FORGE_QSEARCH_FN qsearch_cuckoo_body
#define FORGE_QSEARCH_CALL qsearch_cuckoo
#define FORGE_LMP_THRESHOLD lmp_threshold_cuckoo
#include "search/qsearch.inc"
#include "search/alphabeta.inc"
#undef FORGE_LMP_THRESHOLD
#undef FORGE_QSEARCH_CALL
#undef FORGE_QSEARCH_FN
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#include "search/cuckoo.inc"      // CuckooRep: upcoming-repetition draw bound
