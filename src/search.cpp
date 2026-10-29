// Search translation unit.
//
// The search is split into modules under src/search/ (one concern per file).
// They are compiled together as this single translation unit, each included
// exactly once below (except qsearch.inc and alphabeta.inc, included at the end
// once more per search instance, see the head of alphabeta.inc), so that
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
#ifdef FORGE_PROF
#include "forge/profile.hpp"
#endif
#include "forge/syzygy.hpp"
#include "forge/nnue_v2.hpp"
#include "forge/nnue_v4.hpp"
#include "forge/corr_margins.hpp"
#include "forge/corr_ext.hpp"
#include "forge/material_key_table.hpp"
#include "forge/net_scale.hpp"
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
#define FORGE_SEARCH_FN search
#define FORGE_SEARCH_CALL search
#define FORGE_QSEARCH_FN qsearch
#define FORGE_QSEARCH_CALL qsearch
#define FORGE_LMP_THRESHOLD lmp_threshold
#define FORGE_SEARCH_CORR_MARGINS 0
#define FORGE_SEARCH_CORR_EXT 0
#include "search/qsearch.inc"     // quiescence search (Worker::qsearch)
#include "search/alphabeta.inc"   // main alpha-beta search (Worker::search)
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_QSEARCH_CALL
#undef FORGE_QSEARCH_FN
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#include "search/iterative.inc"   // root setup and iterative deepening
#include "search/searcher.inc"    // Searcher facade: helper threads, TT lifecycle
#include "search/tt_lockless.inc" // UCI LocklessTT: lockless TT access (last: keeps the default placement)
// Syzygy tablebases (all [[gnu::cold]], placed after the search code).
#include "search/tablebase.inc"   // search glue: in-search probe, root filter
#include "search/syzygy.inc"      // table reader, WDL/DTZ probes, root ranking
// The main search once more for every other combination of UCI CorrMargins,
// CorrExt and CuckooRep (see the head of alphabeta.inc). Last in the file, so
// that the default search functions keep the AL1 s198 code and placement.
// Child calls of the instances without CuckooRep go to the instance itself and
// to Worker::qsearch.
#define FORGE_QSEARCH_CALL qsearch
#include "search/corr_margins.inc" // CorrMargins: helpers of its instance
#define FORGE_SEARCH_FN search_corr_margins
#define FORGE_SEARCH_CALL search_corr_margins
#define FORGE_LMP_THRESHOLD lmp_threshold_corr_margins
#define FORGE_SEARCH_CORR_MARGINS 1
#define FORGE_SEARCH_CORR_EXT 0
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#include "search/corr_ext.inc"    // CorrExt: helpers of its instance
#define FORGE_SEARCH_FN search_corr_ext
#define FORGE_SEARCH_CALL search_corr_ext
#define FORGE_LMP_THRESHOLD lmp_threshold_corr_ext
#define FORGE_SEARCH_CORR_MARGINS 0
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
// R3 stack: CorrMargins and CorrExt together.
#define FORGE_SEARCH_FN search_cm_ce
#define FORGE_SEARCH_CALL search_cm_ce
#define FORGE_LMP_THRESHOLD lmp_threshold_corr_margins
#define FORGE_SEARCH_CORR_MARGINS 1
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_LMP_THRESHOLD
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#undef FORGE_QSEARCH_CALL
// The CuckooRep instances: their child calls go through the upcoming-repetition
// bound of cuckoo.inc (search_cuckoo / qsearch_cuckoo and, R3 stack, one
// wrapper per combination with CorrMargins / CorrExt).
#include "search/cuckoo_lmp.inc"  // the CuckooRep instances' copy of lmp_threshold
#define FORGE_QSEARCH_FN qsearch_cuckoo_body
#define FORGE_QSEARCH_CALL qsearch_cuckoo
#define FORGE_LMP_THRESHOLD lmp_threshold_cuckoo
#include "search/qsearch.inc"
#define FORGE_SEARCH_FN search_cuckoo_body
#define FORGE_SEARCH_CALL search_cuckoo
#define FORGE_SEARCH_CORR_MARGINS 0
#define FORGE_SEARCH_CORR_EXT 0
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
// R3 stack: CuckooRep with CorrMargins and / or CorrExt.
#define FORGE_SEARCH_FN search_cm_cu_body
#define FORGE_SEARCH_CALL search_cm_cu
#define FORGE_SEARCH_CORR_MARGINS 1
#define FORGE_SEARCH_CORR_EXT 0
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#define FORGE_SEARCH_FN search_ce_cu_body
#define FORGE_SEARCH_CALL search_ce_cu
#define FORGE_SEARCH_CORR_MARGINS 0
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#define FORGE_SEARCH_FN search_cm_ce_cu_body
#define FORGE_SEARCH_CALL search_cm_ce_cu
#define FORGE_SEARCH_CORR_MARGINS 1
#define FORGE_SEARCH_CORR_EXT 1
#include "search/alphabeta.inc"
#undef FORGE_SEARCH_CORR_EXT
#undef FORGE_SEARCH_CORR_MARGINS
#undef FORGE_SEARCH_CALL
#undef FORGE_SEARCH_FN
#undef FORGE_LMP_THRESHOLD
#undef FORGE_QSEARCH_CALL
#undef FORGE_QSEARCH_FN
#include "search/cuckoo.inc"      // CuckooRep: upcoming-repetition draw bound
#include "search/fb2.inc"           // FB2-J3 options (CorrHistV2, LmrTableV2, TtPruneV2) and UCI BundlePreset
