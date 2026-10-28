#pragma once

// FB2-J3 search options ported onto the R3 stack (forge-bundle-int; see BUNDLES.md).
// Three UCI check options, all default false; with every one false the search is the AL1 s198 search:
//   CorrHistV2  continuation correction history (opponent's last move and our move before it)
//   LmrTableV2  statistically fitted LMR reduction with a continuous history term
//   TtPruneV2   TT-move pruning guards, cut-node IIR on a failed-low TT move, opponent-worsening RFP,
//               improving-aware futility / history margins
// FB2-J3 SingularV2 is not ported (it overlaps O8 CorrExt and is in no bundle); FB2-J4 TimeManV2 is not ported
// (crew vote: gated separately).
//
// Threading rule: `requested` is written only by the UCI thread, and uci.cpp stops and joins any running search
// before it applies a setoption. Searcher::search copies effective(requested, ...) into SearchLimits once, before
// the helpers start, and every Worker copies it into its own member at the start of its search. No search code
// reads `requested`.
//
// CorrHist exclusivity rule: CorrHistV2 and CorrHistPlus (Opus C2) both update the shared pawn / material
// correction tables, so they are mutually exclusive. The UCI layer refuses to switch one on while the other is on
// (info string, value unchanged), and effective() drops CorrHistV2 whenever CorrHistPlus is nonzero, so the two
// can never write the same table in one search. CorrHistV2's continuation table is its own
// (ThreadData::continuation_correction_), separate from CorrHistPlus's corrplus::Tables.

#include <array>
#include <cstdint>

namespace forge::fb2 {

struct Options {
    bool corr_hist_v2 = false;
    bool lmr_table_v2 = false;
    bool tt_prune_v2 = false;
    [[nodiscard]] bool operator==(const Options&) const = default;
};

// The UCI values (UCI thread only, between searches).
extern Options requested;

// The per-search snapshot: `options` with CorrHistV2 dropped while CorrHistPlus (`corr_hist_plus`) is nonzero.
[[nodiscard]] constexpr Options effective(Options options, int corr_hist_plus) {
    if (corr_hist_plus != 0) options.corr_hist_v2 = false;
    return options;
}

// LmrTableV2: reduction in plies for one LMR decision (before the shared tt_pv / improving / cut-node / check terms).
[[nodiscard]] int lmr_v2_reduction(bool quiet, int depth, int moves, int history, bool improving, bool cut_node,
                                   bool tt_pv);

// CorrHistV2 continuation correction: [0 = previous move, 1 = the move before][moved piece][to square].
using ContinuationCorrection = std::array<std::array<std::array<std::int32_t, 64>, 13>, 2>;

// UCI BundlePreset (crew bundle gates vs AL1 s198). Each preset sets exactly these six options:
//   CorrHistPlus, HistRework, CuckooRep, CorrHistV2, LmrTableV2, TtPruneV2 (OFF = all six at their defaults).
//   B1 = CorrHistPlus=1 + HistRework=2 + CuckooRep + TtPruneV2
//   B2 = CorrHistV2     + LmrTableV2   + CuckooRep + TtPruneV2
//   B3 = CorrHistPlus=1 + LmrTableV2   + CuckooRep + TtPruneV2
//   B4 = CorrHistV2     + HistRework=2 + CuckooRep + TtPruneV2
enum class Bundle : int { Off = 0, B1, B2, B3, B4 };
struct BundleSettings {
    int corr_hist_plus = 0;
    int hist_rework = 0;
    bool cuckoo_rep = false;
    Options fb2{};
};
[[nodiscard]] constexpr BundleSettings bundle_settings(Bundle bundle) {
    switch (bundle) {
        case Bundle::B1: return {1, 2, true, {false, false, true}};
        case Bundle::B2: return {0, 0, true, {true, true, true}};
        case Bundle::B3: return {1, 0, true, {false, true, true}};
        case Bundle::B4: return {0, 2, true, {true, false, true}};
        case Bundle::Off: break;
    }
    return {};
}
// Writes the six options of `bundle` (UCI thread only, no search running).
void apply_bundle(Bundle bundle);

} // namespace forge::fb2
