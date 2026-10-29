# B5 SingularV2 port notes — 2026-10-29

Base: `b7c177222038e9332965a95ec53ea3b94e90dbc9` (`forge-bundle-int`).
Source: this same Forge repository's **Fable FB2-J3**, `1efc0b2c9e09d38642eabd1d6282acceeb38c0b8`, `src/search.cpp:1200–1235`.
The request named an Opus branch, but the located implementation and bundle documentation attribute it to Fable J3. No Opus source attribution is claimed. Exact source bytes/hash and excerpt are in `astra2_evidence/B5/source_provenance.txt`.

IDEA_SOURCE: Forge FB2-J3's existing singular-extension experiment and the user's N1 combination. No code or tuned values from another engine were used. This is a same-repository port with newly written decision helpers, tests and integration glue.

## Behavior and compatibility

- `SingularV2` is advertised as a spin option, default **0**, range **0..1**. Its boolean value is snapshotted before workers start; recursive search reads the worker copy.
- With it OFF, the original positive, cutoff, negative-extension and path-counter decisions remain in place. The changed source is not claimed byte-identical; the required OFF node identity is a native qualification gate.
- Positive rules retained from J3: non-PV quiet TT move may triple-extend below the strict 80-cp margin with at most four prior events; PV nodes may double-extend below the strict 60-cp margin with at most three prior events. Existing non-PV double threshold remains 24 cp and at most six prior events.
- The original `singular_beta >= beta` cutoff retains precedence. The new excluded-search multicut requires its score >= beta and outside the mate-score band. The non-PV TT fail-high extension becomes -3; the cut-node extension becomes -2. PV TT fail-high remains -2.
- J3 counts each double or triple extension as **one event** (`extension >= 2`). This port preserves that convention. CorrExt instead counts extra plies (`extension - 1`), so the two policies are not mixed.
- UCI refuses SingularV2 while CorrExt is active and refuses enabling CorrExt while SingularV2 is active. Search snapshot enforcement independently drops SingularV2 whenever CorrExt is active, including native callers bypassing UCI.
- CorrHistPlus is **not CorrExt**. N1 uses its existing non-pawn correction bit (`CorrHistPlus=4`) with `SingularV2=1`; it remains allowed. No CorrHistPlus keys, tables, weights, update arithmetic or NNUE values change.
- All alphabeta instances compile the shared hooks. CorrMargins/CuckooRep instances can use SingularV2; CorrExt instances receive an OFF effective bit. There are no new make/unmake allocations.

## Preset ownership and future merges

`BundlePreset N1` sets seven owned options: CorrHistPlus=4, SingularV2=1, HistRework=0, CuckooRep=false, CorrHistV2=false, LmrTableV2=false and TtPruneV2=false. OFF/B1/B2/B3/B4 all reset SingularV2=0. N1 is refused before `apply_bundle` when CorrExt is active, leaving the previous seven option values intact.

This branch is independently based on b7c1772. It does not include the B1 SmpV2, B2 timing or B4 strict-UCI branch. When combining them, preserve independent SmpV2/timing fields while applying these seven preset-owned fields; an aggregate assignment to the expanded FB2 struct must not erase independent options. Merge N1 into B4's preset/override diagnostics rather than replacing them. Integration testing of that future combination is **UNVERIFIED** here.

## Tests and evidence

- `tests/singular_v2_uci_tests.py` ran against the untouched bundle executable before implementation and failed because SingularV2 was not advertised (`uci_red.json`, original transcript retained).
- `tests/singular_v2_tests.cpp` covers strict thresholds, PV/capture exclusions, budget boundaries, negative extensions, mate multicut exclusion, triple event accounting, snapshot exclusions, actual ON/OFF restoration, legal native PVs, N1/manual equivalence and CorrMargins/CuckooRep instances.
- UCI regression verifies N1/manual d11 identity, invalid values, both exclusivity directions, no partial preset mutation, old-preset reset and final pinned OFF restoration. Every observed bench record is printed in its JSON output and raw transcript.
- Syntax-only GCC C++20 and Python parsing passed before the frozen source inventory. Full builds, CTest, all five OFF benches, perft and FMA are recorded by the lead developer in `astra2_evidence/B5/`; missing results remain UNVERIFIED until those original logs exist.
- No speed, Elo or adoption claim. N1 still needs equal-time independent gating.

## Complete engine/build changed-line inventory

The following generated inventory compares the frozen candidate to exact base b7c1772. `-old` denotes a removed base line, `+new` an added candidate line. Every changed engine/build line is included, with its CorrHistPlus interaction stated per file. Unchanged lines are omitted.

### `include/forge/fb2.hpp`

Adds the snapshot bit and N1. CorrHistPlus=4 is compatible; its existing CorrHistV2 exclusion is unchanged. CorrExt suppresses SingularV2 in the effective snapshot.

```text
-old    4: // Three UCI check options, all default false; with every one false the search is the AL1 s198 search:
+new    4: // Three UCI check options and SingularV2 (spin 0..1), all default OFF; with every one off the search is unchanged:
-old    9: // FB2-J3 SingularV2 is not ported (it overlaps O8 CorrExt and is in no bundle); FB2-J4 TimeManV2 is not ported
-old   10: // (crew vote: gated separately).
+new    9: //   SingularV2 triple/PV-double extensions, excluded-search multicut and stronger negative extensions
+new   10: // FB2-J4 TimeManV2 remains outside this branch (crew vote: gated separately).
+new   11: // SingularV2 and CorrExt are exclusive: their path budgets count different quantities.
+new   12: // CorrHistPlus is distinct from CorrExt and is compatible with SingularV2 (preset N1).
+new   34:     bool singular_v2 = false;
-old   38: // The per-search snapshot: `options` with CorrHistV2 dropped while CorrHistPlus (`corr_hist_plus`) is nonzero.
-old   39: [[nodiscard]] constexpr Options effective(Options options, int corr_hist_plus) {
+new   41: // Per-search snapshot: CorrHistPlus wins over CorrHistV2, CorrExt wins over SingularV2.
+new   42: [[nodiscard]] constexpr Options effective(Options options, int corr_hist_plus, int corr_ext = 0) {
+new   44:     if (corr_ext != 0) options.singular_v2 = false;
-old   51: // UCI BundlePreset (crew bundle gates vs AL1 s198). Each preset sets exactly these six options:
-old   52: //   CorrHistPlus, HistRework, CuckooRep, CorrHistV2, LmrTableV2, TtPruneV2 (OFF = all six at their defaults).
+new   55: // UCI BundlePreset (crew bundle gates vs AL1 s198). Each preset sets exactly these seven options:
+new   56: //   CorrHistPlus, HistRework, CuckooRep, CorrHistV2, LmrTableV2, TtPruneV2, SingularV2.
+new   57: //   OFF/B1-B4 set SingularV2=0; N1 sets CorrHistPlus=4 and SingularV2=1 only.
-old   57: enum class Bundle : int { Off = 0, B1, B2, B3, B4 };
+new   62: enum class Bundle : int { Off = 0, B1, B2, B3, B4, N1 };
+new   75:         case Bundle::N1: return {4, 0, false, {false, false, false, true}};
-old   74: // Writes the six options of `bundle` (UCI thread only, no search running).
+new   80: // Writes the seven options of `bundle` (UCI thread only, no search running).
```

### `include/forge/singular_v2.hpp`

Pure extension decisions; no table access or updates. TT and excluded-search scores can reflect CorrHistPlus corrections. Event accounting is exclusive of CorrExt.

```text
+new    1: #pragma once
+new    2: 
+new    3: #include "forge/search_types.hpp"
+new    4: 
+new    5: // SingularV2 port of this repository's FB2-J3 search rules. These helpers are
+new    6: // used only by the default-off option; the original OFF decisions stay in place.
+new    7: // Unlike CorrExt's extra-ply budget, J3 counts each double/triple extension as
+new    8: // one event. The two options are therefore exclusive in UCI and the snapshot.
+new    9: namespace forge::singular_v2 {
+new   10: 
+new   11: // Called only after the excluded-move search failed below singular_beta.
+new   12: [[nodiscard]] constexpr int positive_extension(bool pv, bool tt_capture, int score, int singular_beta,
+new   13:                                                int prior_events) {
+new   14:     if (!pv && !tt_capture && prior_events <= 4 && score < singular_beta - 80) return 3;
+new   15:     if (pv) return prior_events <= 3 && score < singular_beta - 60 ? 2 : 1;
+new   16:     return prior_events <= 6 && score < singular_beta - 24 ? 2 : 1;
+new   17: }
+new   18: 
+new   19: // Reached only after the existing singular_beta >= beta cutoff has been tested.
+new   20: [[nodiscard]] constexpr bool multicut(int excluded_score, int beta) {
+new   21:     return excluded_score >= beta && !is_mate_score(excluded_score);
+new   22: }
+new   23: 
+new   24: [[nodiscard]] constexpr int negative_extension(bool pv, bool tt_fails_high, bool cut_node) {
+new   25:     if (tt_fails_high) return pv ? -2 : -3;
+new   26:     return cut_node ? -2 : 0;
+new   27: }
+new   28: 
+new   29: [[nodiscard]] constexpr int events_after(int prior_events, int extension) {
+new   30:     return prior_events + (extension >= 2 ? 1 : 0);
+new   31: }
+new   32: 
+new   33: } // namespace forge::singular_v2
```

### `src/search.cpp`

Includes the decision helpers; no CorrHistPlus behavior or storage change.

```text
+new   25: #include "forge/singular_v2.hpp"
```

### `src/search/alphabeta.inc`

Reads only the frozen SingularV2 bit. Changed depth/cutoffs can change later learned corrections and TT contents indirectly; no correction-table layout, keys, weights or update formula changes.

```text
-old  430:                 extension = 1;
-old  431:                 if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {
+new  430:                 if (fb2_.singular_v2) {
+new  431:                     extension = singular_v2::positive_extension(pv_node, tt_capture, singular_score, singular_beta,
+new  432:                                                                 inherited_double_extensions);
-old  433:                     prof::count(prof::Counter::SingularDoubleExtensions);
+new  434:                     if (extension >= 2) prof::count(prof::Counter::SingularDoubleExtensions);
-old  435:                     extension = 2;
+new  436:                 } else {
+new  437:                     extension = 1;
+new  438:                     if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {
+new  439: #ifdef FORGE_PROF
+new  440:                         prof::count(prof::Counter::SingularDoubleExtensions);
+new  441: #endif
+new  442:                         extension = 2;
+new  443:                     }
+new  451:             } else if (fb2_.singular_v2 && singular_v2::multicut(singular_score, beta)) {
+new  452: #ifdef FORGE_PROF
+new  453:                 prof::count(prof::Counter::SingularCutoffs);
+new  454: #endif
+new  455:                 return singular_score;
-old  444:                 extension = -2;
+new  457:                 extension = fb2_.singular_v2 ? singular_v2::negative_extension(pv_node, true, cut_node) : -2;
-old  446:                 extension = -1;
+new  459:                 extension = fb2_.singular_v2 ? singular_v2::negative_extension(pv_node, false, true) : -1;
-old  456:         ss->double_extensions = inherited_double_extensions + (extension == 2);
+new  469:         ss->double_extensions = fb2_.singular_v2
+new  470:             ? singular_v2::events_after(inherited_double_extensions, extension)
+new  471:             : inherited_double_extensions + (extension == 2);
```

### `src/search/searcher.inc`

Adds CorrExt to the effective snapshot call before helper launch; CorrHistPlus still controls only the existing CorrHistV2 exclusion.

```text
-old   51:     worker_limits.fb2 = fb2::effective(fb2::requested, options::corr_hist_plus);
+new   51:     worker_limits.fb2 = fb2::effective(fb2::requested, options::corr_hist_plus, options::corr_ext);
```

### `src/uci.cpp`

Advertises/parses SingularV2, enforces CorrExt exclusivity and applies N1 atomically. N1 selects CorrHistPlus=4 without changing its arithmetic. Old presets reset SingularV2.

```text
-old  491:                          "option name BundlePreset type combo default OFF var OFF var B1 var B2 var B3 var B4\n";
+new  491:                          "option name SingularV2 type spin default 0 min 0 max 1\n"
+new  492:                          "option name BundlePreset type combo default OFF var OFF var B1 var B2 var B3 var B4 var N1\n";
+new  712:                 } else if (value > 0 && forge::fb2::requested.singular_v2) {
+new  713:                     const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
+new  714:                     std::cout << "info string CorrExt refused: SingularV2 is on (exclusive path budgets)" << std::endl;
+new  717:                 }
+new  718:             } else if (name == "SingularV2") {
+new  719:                 int value = 0;
+new  720:                 const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
+new  721:                 const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
+new  722:                 if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size() || value < 0 || value > 1) {
+new  723:                     std::cout << "info string invalid value for option SingularV2" << std::endl;
+new  724:                 } else if (value != 0 && forge::options::corr_ext != 0) {
+new  725:                     std::cout << "info string SingularV2 refused: CorrExt is on (exclusive path budgets)" << std::endl;
+new  726:                 } else {
+new  727:                     forge::fb2::requested.singular_v2 = value != 0;
-old  745:                 static constexpr std::array<std::string_view, 5> Names{"OFF", "B1", "B2", "B3", "B4"};
+new  760:                 static constexpr std::array<std::string_view, 6> Names{"OFF", "B1", "B2", "B3", "B4", "N1"};
+new  765:                 } else if (*it == "N1" && forge::options::corr_ext != 0) {
+new  766:                     // Refuse before apply_bundle: no member of the previous preset is changed.
+new  767:                     std::cout << "info string BundlePreset N1 refused: CorrExt is on (exclusive path budgets)" << std::endl;
-old  758:                               << " TtPruneV2=" << (b.fb2.tt_prune_v2 ? "true" : "false") << std::endl;
+new  776:                               << " TtPruneV2=" << (b.fb2.tt_prune_v2 ? "true" : "false")
+new  777:                               << " SingularV2=" << (b.fb2.singular_v2 ? 1 : 0) << std::endl;
```

### `CMakeLists.txt`

Registers dedicated native/UCI regressions; no runtime correction-history behavior.

```text
+new  199: add_executable(forge_singular_v2_tests tests/singular_v2_tests.cpp)
+new  200: target_link_libraries(forge_singular_v2_tests PRIVATE forge_core Threads::Threads)
+new  398: add_test(NAME forge_singular_v2_tests COMMAND forge_singular_v2_tests)
+new  543:     add_test(NAME singular_v2_uci_regression
+new  544:         COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/singular_v2_uci_tests.py $<TARGET_FILE:forge>
+new  545:                 --log ${CMAKE_CURRENT_BINARY_DIR}/singular-v2-uci-regression.log)
+new  546:     set_tests_properties(singular_v2_uci_regression PROPERTIES TIMEOUT 300)
```

## Added regression files

- `tests/singular_v2_tests.cpp`: lines 1–135 are new. These tests configure or exercise the public options and assert behavior; they do not add production CorrHistPlus state. Source SHA256 `505fc7660eb6cd151aa6bd88c9910b17030a70c8abfb714e35612ef21ff8b275`.
- `tests/singular_v2_uci_tests.py`: lines 1–88 are new. These tests configure or exercise the public options and assert behavior; they do not add production CorrHistPlus state. Source SHA256 `4557e6bd4687ac45c62756901d2cc7025006326dc173d079875d0b502b7dd6a0`.
