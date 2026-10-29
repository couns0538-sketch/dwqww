// Unit tests of the FB2-J3 options on the R3 stack (CorrHistV2, LmrTableV2, TtPruneV2), the CorrHist exclusivity
// rule and the UCI BundlePreset table (forge/fb2.hpp, BUNDLES.md). Adapted from FB2-J3's tests, extended for SingularV2 and independent
// SMP/time flags. Usage: forge_fb2_bundle_tests   (no arguments)
#include "forge/board.hpp"
#include "forge/fb2.hpp"
#include "forge/hist_rework.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace forge {
// Friend probe declared in search.hpp: reaches the worker's private correction tables and functions.
struct SearcherTestProbe {
    static int corrected_v2(Worker& w, const Board& b, int raw, const SearchStack* ss) { return w.corrected_eval_v2(b, raw, ss); }
    static int corrected_v1(Worker& w, const Board& b, int raw) { return w.corrected_eval(b, raw); }
    static void update_v2(Worker& w, const Board& b, const SearchStack* ss, int depth, int best, int se) { w.update_correction_v2(b, ss, depth, best, se); }
    static fb2::ContinuationCorrection& cont(Worker& w) { return *w.continuation_correction_; }
    static SearchStack* stack(Worker& w) { return w.stack_.data(); }
};
} // namespace forge

using namespace forge;

namespace {
int failures = 0;
int checks = 0;
void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) { ++failures; std::cout << "FAIL: " << what << '\n'; }
}

void set_all(bool v) { fb2::requested = fb2::Options{.corr_hist_v2 = v, .lmr_table_v2 = v, .tt_prune_v2 = v}; }
void set_defaults() {
    fb2::apply_bundle(fb2::Bundle::Off);
}

SearchInfo run(Searcher& s, const std::string& fen, int depth) {
    Board b;
    if (!b.set_fen(fen)) throw std::runtime_error("bad fen " + fen);
    SearchLimits limits;
    limits.depth = depth;
    s.clear();
    return s.search(b, limits, false, Searcher::TTAccess::Exclusive);
}

const char* kFens[] = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    "2r3k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1",
};
} // namespace

int main() {
    // 1. The options are live and leave no state behind: OFF -> ON changes the tree, OFF again restores the node count.
    {
        Searcher s(16, 1);
        set_all(false);
        std::vector<std::uint64_t> base;
        for (const char* fen : kFens) base.push_back(run(s, fen, 10).nodes);
        const char* names[] = {"CorrHistV2", "LmrTableV2", "TtPruneV2"};
        bool* flags[] = {&fb2::requested.corr_hist_v2, &fb2::requested.lmr_table_v2, &fb2::requested.tt_prune_v2};
        for (int k = 0; k < 3; ++k) {
            set_all(false);
            *flags[k] = true;
            int changed = 0;
            for (std::size_t i = 0; i < base.size(); ++i) {
                const SearchInfo info = run(s, kFens[i], 10);
                check(!info.best_move.is_none() && info.score > -Infinite && info.score < Infinite, std::string(names[k]) + " search sane");
                changed += info.nodes != base[i];
            }
            check(changed > 0, std::string(names[k]) + " changes at least one depth-10 tree");
            set_all(false);
            for (std::size_t i = 0; i < base.size(); ++i) check(run(s, kFens[i], 10).nodes == base[i], std::string(names[k]) + " off again: identical node count");
            std::cout << names[k] << ": " << changed << "/" << base.size() << " trees differ with the option on\n";
        }
        // determinism with everything on
        set_all(true);
        for (const char* fen : kFens) check(run(s, fen, 10).nodes == run(s, fen, 10).nodes, "all options on: deterministic");
        set_all(false);
    }

    // 2. CorrHistV2 arithmetic through the probe: continuation entries add to the correction and move with the updates.
    {
        Searcher s(1, 1);
        Worker& w = s.main_worker();
        s.clear();
        Board b;
        (void)b.set_fen(kFens[1]);
        SearchStack* ss = SearcherTestProbe::stack(w) + 4;
        for (int i = -4; i <= 1; ++i) ss[i] = SearchStack{};
        ss->ply = 2;
        (ss - 1)->moved_piece = BN;
        (ss - 1)->current_move = Move{};
        (ss - 1)->current_move.from = 57; (ss - 1)->current_move.to = 42;
        (ss - 2)->moved_piece = WB;
        (ss - 2)->current_move = Move{};
        (ss - 2)->current_move.from = 5; (ss - 2)->current_move.to = 26;
        const int raw = 37;
        check(SearcherTestProbe::corrected_v2(w, b, raw, ss) == SearcherTestProbe::corrected_v1(w, b, raw), "empty tables: v2 == v1");
        auto& cont = SearcherTestProbe::cont(w);
        cont[0][BN][42] = 3 * CorrectionGrain;
        cont[1][WB][26] = -1 * CorrectionGrain;
        check(SearcherTestProbe::corrected_v2(w, b, raw, ss) == SearcherTestProbe::corrected_v1(w, b, raw) + 2, "continuation entries add (3 - 1 pawns of grain)");
        // a null move / root carries no continuation key
        (ss - 1)->moved_piece = Empty;
        check(SearcherTestProbe::corrected_v2(w, b, raw, ss) == SearcherTestProbe::corrected_v1(w, b, raw) - 1, "empty moved piece: only the 2-ply entry counts");
        (ss - 1)->moved_piece = BN;
        // updates move the entries towards the search result and stay clamped
        cont[0][BN][42] = 0;
        cont[1][WB][26] = 0;
        for (int i = 0; i < 2000; ++i) SearcherTestProbe::update_v2(w, b, ss, 8, 400, 100);
        check(cont[0][BN][42] == CorrectionLimit && cont[1][WB][26] == CorrectionLimit, "positive differences saturate at the limit");
        for (int i = 0; i < 4000; ++i) SearcherTestProbe::update_v2(w, b, ss, 8, -400, 100);
        check(cont[0][BN][42] == -CorrectionLimit, "negative differences saturate at -limit");
        const int before = SearcherTestProbe::corrected_v1(w, b, raw);
        cont[0][BN][42] = cont[1][WB][26] = 0;
        for (int i = 0; i < 3; ++i) SearcherTestProbe::update_v2(w, b, ss, 4, 150, 50);
        check(cont[0][BN][42] > 0 && cont[0][BN][42] == cont[1][WB][26], "small updates: both continuation entries grow equally");
        check(SearcherTestProbe::corrected_v1(w, b, raw) >= before, "pawn/material entries also updated by v2");
        std::cout << "CorrHistV2 probe: entries after 3 updates " << cont[0][BN][42] << '\n';
    }

    // 3. LmrTableV2: non-negative, bounded, and reductions never grow with better history.
    {
        int max_r = 0;
        bool monotone = true, bounded = true;
        for (int depth = 1; depth < 64; ++depth) {
            for (int moves = 1; moves < 64; ++moves) {
                for (int quiet = 0; quiet < 2; ++quiet) {
                    int prev = 1 << 20;
                    for (int h = -16384; h <= 16384; h += 2048) {
                        const int r = fb2::lmr_v2_reduction(quiet != 0, depth, moves, h, false, false, false);
                        if (r < 0 || r > 16) bounded = false;
                        if (r > prev) monotone = false;
                        prev = r;
                        max_r = std::max(max_r, r);
                    }
                }
            }
        }
        check(bounded, "lmr_v2_reduction in [0, 16]");
        check(monotone, "lmr_v2_reduction non-increasing in history");
        check(fb2::lmr_v2_reduction(true, 20, 40, 0, false, true, false) >= fb2::lmr_v2_reduction(true, 2, 2, 0, false, true, false), "deeper/later moves reduced at least as much");
        std::cout << "LmrTableV2: max reduction " << max_r << '\n';
    }

    // 4. All options on: tactics still found, random positions searched sanely.
    {
        Searcher s(16, 1);
        set_all(true);
        struct Mate { const char* fen; int depth; int mate_in; };
        const Mate mates[] = {
            {"6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 8, 1},
            {"r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", 8, 1},
            {"r2qkb1r/pp2nppp/3p4/2pNN1B1/2BnP3/3P4/PPP2PPP/R2bK2R w KQkq - 1 1", 10, 2},
        };
        for (const Mate& m : mates) {
            const SearchInfo info = run(s, m.fen, m.depth);
            check(info.score >= MateValue - 2 * m.mate_in, std::string("mate found with all options on: ") + m.fen);
        }
        // random playouts from the start position (engine RNG only)
        std::uint64_t seed = 12345;
        int positions = 0;
        for (int g = 0; g < 25; ++g) {
            Board b;
            (void)b.set_fen(kFens[0]);
            for (int ply = 0; ply < 10 + g; ++ply) {
                const MoveList moves = b.legal_moves();
                if (moves.empty()) break;
                seed = seed * 6364136223846793005ULL + 1442695040888963407ULL;
                Undo u;
                (void)b.make_move(moves[static_cast<std::size_t>((seed >> 33U) % moves.size())], u);
            }
            if (!b.has_legal_move()) continue;
            SearchLimits limits;
            limits.depth = 8;
            s.clear();
            const SearchInfo info = s.search(b, limits, false, Searcher::TTAccess::Exclusive);
            const MoveList legal = b.legal_moves();
            bool found = false;
            for (const Move& mv : legal) found = found || (mv.from == info.best_move.from && mv.to == info.best_move.to && mv.promotion == info.best_move.promotion);
            check(found, "all options on: best move legal in " + b.fen());
            check(info.score > -Infinite && info.score < Infinite, "all options on: finite score");
            ++positions;
        }
        set_all(false);
        std::cout << "all options on: " << positions << " random positions at depth 8\n";
    }

    // 5. CorrHist exclusivity: effective() drops CorrHistV2 whenever CorrHistPlus is nonzero, so a search with both
    //    requested runs exactly the CorrHistPlus search.
    {
        constexpr fb2::Options all{.corr_hist_v2 = true, .lmr_table_v2 = true, .tt_prune_v2 = true};
        static_assert(fb2::effective(all, 0) == all);
        for (int chp = 1; chp <= 7; ++chp) {
            const fb2::Options e = fb2::effective(all, chp);
            check(!e.corr_hist_v2 && e.lmr_table_v2 && e.tt_prune_v2, "effective: CorrHistV2 dropped with CorrHistPlus=" + std::to_string(chp));
        }
        Searcher s(16, 1);
        set_defaults();
        options::corr_hist_plus = 1;
        std::vector<std::uint64_t> plus_only;
        for (const char* fen : kFens) plus_only.push_back(run(s, fen, 10).nodes);
        fb2::requested.corr_hist_v2 = true;   // (UCI refuses this; the snapshot must still enforce the rule)
        for (std::size_t i = 0; i < plus_only.size(); ++i) check(run(s, kFens[i], 10).nodes == plus_only[i], "CorrHistPlus=1 + CorrHistV2 requested == CorrHistPlus=1 alone");
        // A caller-supplied SearchLimits::fb2 is replaced by the snapshot (no per-call bypass of the rule).
        Board b;
        (void)b.set_fen(kFens[2]);
        SearchLimits limits;
        limits.depth = 10;
        limits.fb2 = fb2::Options{.corr_hist_v2 = true};
        s.clear();
        check(s.search(b, limits, false, Searcher::TTAccess::Exclusive).nodes == plus_only[2], "SearchLimits::fb2 from the caller is overwritten by the snapshot");
        set_defaults();
    }

    // 6. BundlePreset table and its application.
    {
        using fb2::Bundle;
        const auto b1 = fb2::bundle_settings(Bundle::B1), b2 = fb2::bundle_settings(Bundle::B2),
                   b3 = fb2::bundle_settings(Bundle::B3), b4 = fb2::bundle_settings(Bundle::B4),
                   off = fb2::bundle_settings(Bundle::Off);
        check(b1.corr_hist_plus == 1 && b1.hist_rework == 2 && b1.cuckoo_rep && b1.fb2 == fb2::Options{.tt_prune_v2 = true}, "B1 = CorrHistPlus + HistRework=2 + CuckooRep + TtPruneV2");
        check(b2.corr_hist_plus == 0 && b2.hist_rework == 0 && b2.cuckoo_rep && b2.fb2 == fb2::Options{.corr_hist_v2 = true, .lmr_table_v2 = true, .tt_prune_v2 = true}, "B2 = CorrHistV2 + LmrTableV2 + CuckooRep + TtPruneV2");
        check(b3.corr_hist_plus == 1 && b3.hist_rework == 0 && b3.cuckoo_rep && b3.fb2 == fb2::Options{.lmr_table_v2 = true, .tt_prune_v2 = true}, "B3 = CorrHistPlus + LmrTableV2 + CuckooRep + TtPruneV2");
        check(b4.corr_hist_plus == 0 && b4.hist_rework == 2 && b4.cuckoo_rep && b4.fb2 == fb2::Options{.corr_hist_v2 = true, .tt_prune_v2 = true}, "B4 = CorrHistV2 + HistRework=2 + CuckooRep + TtPruneV2");
        check(off.corr_hist_plus == 0 && off.hist_rework == 0 && !off.cuckoo_rep && off.fb2 == fb2::Options{}, "OFF = defaults");
        for (const Bundle bundle : {Bundle::B1, Bundle::B2, Bundle::B3, Bundle::B4}) {
            const auto b = fb2::bundle_settings(bundle);
            check(!(b.corr_hist_plus != 0 && b.fb2.corr_hist_v2), "no preset has both CorrHists");
        }
        Searcher s(16, 1);
        set_defaults();
        std::vector<std::uint64_t> base;
        for (const char* fen : kFens) base.push_back(run(s, fen, 10).nodes);
        for (const Bundle bundle : {Bundle::B1, Bundle::B2, Bundle::B3, Bundle::B4}) {
            fb2::apply_bundle(bundle);
            const auto b = fb2::bundle_settings(bundle);
            check(options::corr_hist_plus == b.corr_hist_plus && search_options::hist_rework == b.hist_rework &&
                      options::cuckoo_rep == b.cuckoo_rep && fb2::requested == b.fb2, "apply_bundle writes the seven owned options");
            int changed = 0;
            for (std::size_t i = 0; i < base.size(); ++i) {
                const SearchInfo info = run(s, kFens[i], 10);
                check(!info.best_move.is_none(), "bundle search sane");
                changed += info.nodes != base[i];
            }
            check(changed > 0, "bundle " + std::to_string(static_cast<int>(bundle)) + " changes at least one tree");
            fb2::apply_bundle(Bundle::Off);
            for (std::size_t i = 0; i < base.size(); ++i) check(run(s, kFens[i], 10).nodes == base[i], "OFF after a bundle: identical node count");
        }
        set_defaults();
    }

    // Integration regression: presets must preserve independent flags in every combination.
    for (bool smp : {false, true}) for (bool clamp : {false, true}) {
        for (auto bundle : {fb2::Bundle::Off, fb2::Bundle::B1, fb2::Bundle::B2,
                            fb2::Bundle::B3, fb2::Bundle::B4, fb2::Bundle::N1}) {
            fb2::requested.smp_v2 = smp;
            fb2::requested.tm_soft_hard_clamp = clamp;
            fb2::apply_bundle(bundle);
            check(fb2::requested.smp_v2 == smp && fb2::requested.tm_soft_hard_clamp == clamp,
                  "presets preserve both independent flags in every value combination");
            check(fb2::requested.singular_v2 == (bundle == fb2::Bundle::N1),
                  "only N1 enables SingularV2; OFF resets it");
        }
    }
    fb2::requested = {};
    set_defaults();
    std::cout << checks << " checks, " << failures << " failures\n";
    return failures == 0 ? 0 : 1;
}
