#pragma once

// FB2-J3 search options ported onto the R3 stack (forge-bundle-int; see BUNDLES.md).
// Runtime UCI options, all default OFF; with every option off the search is unchanged:
//   CorrHistV2  continuation correction history (opponent's last move and our move before it)
//   LmrTableV2  statistically fitted LMR reduction with a continuous history term
//   TtPruneV2   TT-move pruning guards, cut-node IIR on a failed-low TT move, opponent-worsening RFP,
//               improving-aware futility / history margins
//   SmpV2        J5 helper diversification with protected completed-result selection
//   TmSoftHardClamp caps nominal and scaled soft budgets at hard time
//   SingularV2 triple/PV-double extensions, multicut and stronger negative extensions
// FB2-J4 TimeManV2 remains outside this branch.
// SingularV2 and CorrExt are exclusive: their path budgets count different quantities.
// CorrHistPlus is distinct from CorrExt and is compatible with SingularV2 (preset N1).
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
#include <vector>

namespace forge { struct SearchInfo; }

namespace forge::fb2 {

struct Options {
    bool corr_hist_v2 = false;
    bool lmr_table_v2 = false;
    bool tt_prune_v2 = false;
    bool singular_v2 = false;
    bool smp_v2 = false; // helper diversification and protected completed-result selection
    bool tm_soft_hard_clamp = false; // independent of presets
    [[nodiscard]] bool operator==(const Options&) const = default;
};

// The UCI values (UCI thread only, between searches).
extern Options requested;

// Per-search snapshot: CorrHistPlus wins over CorrHistV2, CorrExt wins over SingularV2.
[[nodiscard]] constexpr Options effective(Options options, int corr_hist_plus, int corr_ext = 0) {
    if (corr_hist_plus != 0) options.corr_hist_v2 = false;
    if (corr_ext != 0) options.singular_v2 = false;
    return options;
}

// B1: SmpV2 acts with multiple workers. Only helpers retain their completed tuple
// on abort; the main worker keeps its original partial-PV policy. A helper replaces a proven main/current
// result only at a strictly greater depth and with an equal-or-better proven score.
// Valid mate and TB scores (either sign, TB only while tables are loaded)
// are protected; SearchInfo has no independent proof tag. Sentinels are rejected.
[[nodiscard]] int smp_depth_skew(int id);
[[nodiscard]] int smp_aspiration_multiplier(int id);
// Depth ranking is capped at the requested go depth / mate-depth limit. A skewed
// helper at N+1 must not displace a completed main result at requested depth N.
[[nodiscard]] SearchInfo smp_select_result(const SearchInfo& main, const std::vector<SearchInfo>& helpers,
                                         int depth_cap = 64);

// LmrTableV2: reduction in plies for one LMR decision (before the shared tt_pv / improving / cut-node / check terms).
[[nodiscard]] int lmr_v2_reduction(bool quiet, int depth, int moves, int history, bool improving, bool cut_node,
                                   bool tt_pv);

// CorrHistV2 continuation correction: [0 = previous move, 1 = the move before][moved piece][to square].
using ContinuationCorrection = std::array<std::array<std::array<std::int32_t, 64>, 13>, 2>;

// UCI BundlePreset (crew bundle gates vs AL1 s198). Each preset sets exactly these seven options:
//   CorrHistPlus, HistRework, CuckooRep, CorrHistV2, LmrTableV2, TtPruneV2, SingularV2.
//   OFF/B1-B4 set SingularV2=0; N1 sets CorrHistPlus=4 and SingularV2=1 only.
//   B1 = CorrHistPlus=1 + HistRework=2 + CuckooRep + TtPruneV2
//   B2 = CorrHistV2     + LmrTableV2   + CuckooRep + TtPruneV2
//   B3 = CorrHistPlus=1 + LmrTableV2   + CuckooRep + TtPruneV2
//   B4 = CorrHistV2     + HistRework=2 + CuckooRep + TtPruneV2
enum class Bundle : int { Off = 0, B1, B2, B3, B4, N1 };
struct BundleSettings {
    int corr_hist_plus = 0;
    int hist_rework = 0;
    bool cuckoo_rep = false;
    Options fb2{};
};
[[nodiscard]] constexpr BundleSettings bundle_settings(Bundle bundle) {
    // Designators bind option names, never the ordinal position of a new bool.
    switch (bundle) {
        case Bundle::B1: return {.corr_hist_plus = 1, .hist_rework = 2, .cuckoo_rep = true,
                                .fb2 = {.tt_prune_v2 = true}};
        case Bundle::B2: return {.cuckoo_rep = true,
                                .fb2 = {.corr_hist_v2 = true, .lmr_table_v2 = true, .tt_prune_v2 = true}};
        case Bundle::B3: return {.corr_hist_plus = 1, .cuckoo_rep = true,
                                .fb2 = {.lmr_table_v2 = true, .tt_prune_v2 = true}};
        case Bundle::B4: return {.hist_rework = 2, .cuckoo_rep = true,
                                .fb2 = {.corr_hist_v2 = true, .tt_prune_v2 = true}};
        case Bundle::N1: return {.corr_hist_plus = 4, .fb2 = {.singular_v2 = true}};
        case Bundle::Off: return {.corr_hist_plus = 0, .hist_rework = 0, .cuckoo_rep = false, .fb2 = {}};
    }
    return {.fb2 = {}};
}
static_assert(bundle_settings(Bundle::N1).fb2.singular_v2);
static_assert(!bundle_settings(Bundle::N1).fb2.smp_v2);
static_assert(!bundle_settings(Bundle::N1).fb2.tm_soft_hard_clamp);
static_assert([] {
    for (const Bundle bundle : {Bundle::Off, Bundle::B1, Bundle::B2, Bundle::B3, Bundle::B4}) {
        const Options options = bundle_settings(bundle).fb2;
        if (options.singular_v2 || options.smp_v2 || options.tm_soft_hard_clamp) return false;
    }
    return true;
}());
// Writes the seven options of `bundle` (UCI thread only, no search running).
void apply_bundle(Bundle bundle);

} // namespace forge::fb2
