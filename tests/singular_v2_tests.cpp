// Astra R2 B5: decision boundaries and native integration of Forge's own SingularV2.
// IDEA_SOURCE: FB2-J3 rules and the requested default-off N1 bundle; no other engine code.
#include "forge/search.hpp"
#include "forge/search_options.hpp"
#include "forge/hist_rework.hpp"
#include "forge/singular_v2.hpp"

#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace forge;
namespace {
int checks = 0, failures = 0;
void check(bool okay, const std::string& label) {
    ++checks;
    if (!okay) { ++failures; std::cout << "FAIL " << label << '\n'; }
}
void reset() {
    fb2::apply_bundle(fb2::Bundle::Off);
    options::corr_ext = 0;
    options::corr_margins = 0;
}
SearchInfo search(const char* fen, int depth = 9) {
    Board b;
    if (!b.set_fen(fen)) throw std::runtime_error("bad test FEN");
    Searcher engine(16, 1);
    SearchLimits limits; limits.depth = depth;
    const SearchInfo result = engine.search(b, limits, false, Searcher::TTAccess::Exclusive);
    bool legal = !result.pv.empty() && result.best_move == result.pv.front();
    for (const Move move : result.pv) {
        bool found = false;
        for (const Move allowed : b.legal_moves()) found = found || allowed == move;
        if (!found) { legal = false; break; }
        Undo undo;
        if (!b.make_move(move, undo)) { legal = false; break; }
    }
    check(legal && result.score > -Infinite && result.score < Infinite, "native search has legal PV and finite score");
    return result;
}
bool same(const SearchInfo& a, const SearchInfo& b) {
    return a.nodes == b.nodes && a.score == b.score && a.depth == b.depth &&
           a.best_move == b.best_move && a.ponder_move == b.ponder_move && a.pv == b.pv;
}
}

int main() {
    struct ExtensionCase { bool pv, capture; int score, events, expected; const char* label; };
    const std::array cases{
        ExtensionCase{false, false, -81, 4, 3, "quiet triple below strict margin, last allowed event"},
        ExtensionCase{false, false, -80, 4, 2, "triple threshold equality remains double"},
        ExtensionCase{false, true, -100, 4, 2, "capture never triple extends"},
        ExtensionCase{false, false, -100, 5, 2, "triple event budget exhausted"},
        ExtensionCase{false, false, -25, 6, 2, "last ordinary double event"},
        ExtensionCase{false, false, -24, 6, 1, "double threshold equality remains single"},
        ExtensionCase{false, false, -100, 7, 1, "double event budget exhausted"},
        ExtensionCase{true, false, -61, 3, 2, "PV double below strict margin at last event"},
        ExtensionCase{true, true, -61, 3, 2, "PV capture may double extend"},
        ExtensionCase{true, false, -60, 3, 1, "PV threshold equality remains single"},
        ExtensionCase{true, false, -100, 4, 1, "PV budget exhausted, never triple"},
        ExtensionCase{false, false, -1, 0, 1, "narrow singularity remains single"},
    };
    for (const auto& c : cases) {
        check(singular_v2::positive_extension(c.pv, c.capture, c.score, 0, c.events) == c.expected, c.label);
        check(singular_v2::positive_extension(c.pv, c.capture, c.score + 700, 700, c.events) == c.expected,
              std::string(c.label) + ": score translation invariant");
    }
    check(!singular_v2::multicut(99, 100), "excluded score below beta is no multicut");
    check(singular_v2::multicut(100, 100), "excluded score equal beta is multicut");
    check(singular_v2::multicut(-50, -100), "negative ordinary excluded bound may multicut");
    check(!singular_v2::multicut(MateInMaxPly, 100), "positive mate excluded bound is not multicut");
    check(!singular_v2::multicut(-MateInMaxPly, -MateValue), "negative mate excluded bound is not multicut");
    for (bool pv : {false, true}) {
        check(singular_v2::negative_extension(pv, true, false) == (pv ? -2 : -3), "TT fail-high negative extension");
        check(singular_v2::negative_extension(pv, true, true) == (pv ? -2 : -3), "TT fail-high takes precedence over cut-node");
        check(singular_v2::negative_extension(pv, false, true) == -2, "cut-node negative extension");
        check(singular_v2::negative_extension(pv, false, false) == 0, "no negative-extension trigger");
    }
    for (int prior : {0, 3, 6}) {
        for (int extension : {-3, -2, -1, 0, 1}) check(singular_v2::events_after(prior, extension) == prior, "no budget charged below double");
        check(singular_v2::events_after(prior, 2) == prior + 1, "double costs one event");
        check(singular_v2::events_after(prior, 3) == prior + 1, "triple costs one event, not zero or two");
    }
    fb2::Options all{.corr_hist_v2 = true, .lmr_table_v2 = true, .tt_prune_v2 = true, .singular_v2 = true};
    const auto compatible = fb2::effective(all, 4, 0);
    check(!compatible.corr_hist_v2 && compatible.singular_v2, "CorrHistPlus4 remains compatible with SingularV2");
    const auto incompatible = fb2::effective(all, 4, 1);
    check(!incompatible.corr_hist_v2 && !incompatible.singular_v2 && incompatible.lmr_table_v2 && incompatible.tt_prune_v2,
          "snapshot independently enforces both exclusive pairs");
    const auto n1 = fb2::bundle_settings(fb2::Bundle::N1);
    check(n1.corr_hist_plus == 4 && n1.hist_rework == 0 && !n1.cuckoo_rep &&
          n1.fb2 == fb2::Options{.singular_v2 = true}, "N1 owns exactly CorrHistPlus4 and SingularV2");
    for (auto preset : {fb2::Bundle::Off, fb2::Bundle::B1, fb2::Bundle::B2, fb2::Bundle::B3, fb2::Bundle::B4}) {
        fb2::apply_bundle(fb2::Bundle::N1);
        fb2::apply_bundle(preset);
        check(!fb2::requested.singular_v2, "all old presets reset SingularV2");
    }
    constexpr const char* fens[]{
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10"
    };
    int solo_changes = 0, n1_changes = 0;
    for (std::size_t i = 0; i < std::size(fens); ++i) {
        reset(); const auto off = search(fens[i]);
        fb2::requested.singular_v2 = true; const auto solo = search(fens[i]);
        solo_changes += solo.nodes != off.nodes;
        options::corr_hist_plus = 4; const auto manual = search(fens[i]);
        reset(); fb2::apply_bundle(fb2::Bundle::N1); const auto preset = search(fens[i]);
        check(same(manual, preset), "native N1 equals manual CorrHistPlus4 plus SingularV2");
        n1_changes += preset.nodes != off.nodes;
        reset(); check(same(search(fens[i]), off), "OFF after N1 restores source-identical search");
        std::cout << "native fen=" << i << " depth=9 OFF=" << off.nodes << " SingularV2=" << solo.nodes
                  << " N1=" << preset.nodes << " manualN1=" << manual.nodes << '\n';
    }
    check(solo_changes > 0, "SingularV2 is active in actual native search");
    check(n1_changes > 0, "N1 is active in actual native search");
    // Direct caller bypass: requested SingularV2 must be dropped by the search snapshot under CorrExt.
    reset(); options::corr_ext = 1;
    const auto ce = search(fens[1]);
    fb2::requested.singular_v2 = true;
    check(same(ce, search(fens[1])), "native effective snapshot prevents mixed CorrExt/SingularV2 semantics");
    // The shared alphabeta module also instantiates CorrMargins and CuckooRep variants.
    for (bool cm : {false, true}) for (bool cu : {false, true}) {
        reset(); fb2::requested.singular_v2 = true;
        options::corr_margins = cm ? 1 : 0; options::cuckoo_rep = cu;
        const auto result = search(fens[1], 8);
        std::cout << "instance CorrMargins=" << cm << " CuckooRep=" << cu << " nodes=" << result.nodes << '\n';
    }
    reset();
    std::cout << "singular_v2 checks=" << checks << " failures=" << failures << '\n';
    return failures == 0 ? 0 : 1;
}
