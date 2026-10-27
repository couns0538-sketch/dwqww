// UCI CorrExt (forge/corr_ext.hpp, test plan G-C5): correction-history
// extensions with a per-path extension budget.
//   1. The decision rule against the AL1 s198 rule written out here: identical
//      at |correction| = 0 and with every CorrExt weight 0; extensions in
//      {1, 2, 3}, PV nodes 1; monotonic in |correction|, in the singular margin
//      and in the budget used; the double margin and the triple threshold at
//      their boundaries.
//   2. The per-path budget: for every budget, path count and decision the
//      extra plies on a path never exceed tune::CorrExtBudget; 20,000 random
//      paths (up to MaxPly plies, random tunables) never exceed it, and the
//      path count equals the sum of the extra plies granted.
//   3. Node decisions of the CorrExt search instance through the test probe:
//      a hugely singular TT move (planted TT entry) at a node with a planted
//      correction gets the double / triple extension exactly as the rule and
//      the remaining budget allow (read back from SearchStack::double_extensions),
//      and never more than the budget; the default instance keeps AL1 s198.
//   4. Whole searches through the public Searcher: CorrExt 1 with every weight
//      0 is node-for-node the default search (bench d11 total 312866), each
//      part alone changes the search, the weights are inert while CorrExt is 0,
//      ON is deterministic, and no stack frame ever ends above the budget.
#include "forge/board.hpp"
#include "forge/corr_ext.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
// Direct node searches as in tests/rule50_tests.cpp (non-root frame, ply 1).
struct SearcherTestProbe {
    static SearchStack* prepare(Searcher& searcher, const Board& board) {
        searcher.clear_hash();
        Worker& w = searcher.main_worker();
        w.clear();
        w.shared_.stop.store(false, std::memory_order_relaxed);
        w.shared_.ponder_hit_ns.store(0, std::memory_order_relaxed);
        w.all_workers_ = nullptr;
        w.aborted_ = false;
        w.local_nodes_ = 0;
        w.nodes_.store(0, std::memory_order_relaxed);
        w.node_limit_ = 0;
        w.node_limit_specified_ = false;
        w.hard_limit_ms_ = w.soft_limit_ms_ = 0;
        w.time_managed_ = w.pondering_ = false;
        w.start_ = std::chrono::steady_clock::now();
        w.seldepth_ = 0;
        w.root_history_index_ = board.history_size() - 1;
        SearchStack* ss = &w.stack_[5];
        ss->ply = 1;
        nnue::refresh(board, ss->accumulator);
        return ss;
    }
    static int search(Searcher& searcher, Board& board, SearchStack* ss, int depth, int alpha, int beta, bool corr) {
        Worker& w = searcher.main_worker();
        return corr ? w.search_corr_ext(board, ss, depth, alpha, beta, false)
                    : w.search(board, ss, depth, alpha, beta, false);
    }
    static CorrectionHistory& pawns(Searcher& searcher) { return *searcher.main_worker().correction_history_; }
    static int max_stack_extra(Searcher& searcher) {
        int m = 0;
        for (const SearchStack& s : searcher.main_worker().stack_) m = std::max(m, s.double_extensions);
        return m;
    }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;

namespace {

int failures = 0;
int checks = 0;
long long evaluated = 0;  // rule decisions compared inside the loops

void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) {
        ++failures;
        if (failures <= 40) std::cout << "FAIL " << what << '\n';
        else if (failures == 41) std::cout << "(further failures not printed)\n";
    }
}

// The AL1 s198 rule (src/search/alphabeta.inc of the lock), written out independently.
int lock_singular_extension(bool pv_node, int singular_score, int singular_beta, int inherited) {
    return (!pv_node && singular_score < singular_beta - 24 && inherited <= 6) ? 2 : 1;
}
int lock_path_after(int inherited, int extension) { return inherited + (extension == 2); }

struct Weights {
    int double_pct, triple_corr, triple_margin, budget;
};
Weights current() { return {tune::CorrExtDoublePct, tune::CorrExtTripleCorr, tune::CorrExtTripleMargin, tune::CorrExtBudget}; }
void set_weights(const Weights& w) {
    tune::CorrExtDoublePct = w.double_pct;
    tune::CorrExtTripleCorr = w.triple_corr;
    tune::CorrExtTripleMargin = w.triple_margin;
    tune::CorrExtBudget = w.budget;
}

std::uint64_t lcg(std::uint64_t& state) {
    state = state * 6364136223846793005ULL + 1442695040888963407ULL;
    return state >> 33U;
}
int uniform(std::uint64_t& state, int lo, int hi) { return lo + static_cast<int>(lcg(state) % static_cast<std::uint64_t>(hi - lo + 1)); }

constexpr int MaxCorrection = (CorrectionLimit + CorrectionLimit * 3) / CorrectionGrain;  // 128 cp
const std::array<int, 6> SingularBetas{-MateInMaxPly + 300, -800, -13, 0, 250, MateInMaxPly - 300};

void test_correction_size() {
    check(corr_ext::correction_size(true, 120, 80) == 0, "correction size 0 in check");
    check(corr_ext::correction_size(false, ValueNone, ValueNone) == 0, "correction size 0 without evaluation");
    check(corr_ext::correction_size(false, 75, 30) == 45 && corr_ext::correction_size(false, 30, 75) == 45,
          "correction size = |static - raw|");
}

void test_lock_identity() {
    const Weights saved = current();
    // |correction| 0 with the default weights, and every |correction| with all weights 0.
    for (int variant = 0; variant < 2; ++variant) {
        if (variant == 1) set_weights({0, 0, saved.triple_margin, 7});
        for (const bool pv : {false, true})
            for (const int sb : SingularBetas)
                for (int ss = sb - 300; ss < sb; ++ss)
                    for (int inherited = 0; inherited <= 10; ++inherited)
                        for (int c = 0; c <= (variant == 0 ? 0 : MaxCorrection); c += 8) {
                            const int e = corr_ext::singular_extension(pv, ss, sb, c, inherited);
                            ++evaluated;
                            if (e != lock_singular_extension(pv, ss, sb, inherited))
                                check(false, "lock identity variant " + std::to_string(variant) + " pv " + std::to_string(pv) +
                                                 " margin " + std::to_string(sb - ss) + " inherited " + std::to_string(inherited) +
                                                 " c " + std::to_string(c));
                            if (corr_ext::path_extra_after(inherited, e) != lock_path_after(inherited, e))
                                check(false, "lock path accounting variant " + std::to_string(variant));
                        }
        check(true, "lock identity variant " + std::to_string(variant) + " done");
    }
    for (const int e : {-2, -1, 0, 1, 2})
        for (int inherited = 0; inherited <= 10; ++inherited)
            check(corr_ext::path_extra_after(inherited, e) == lock_path_after(inherited, e),
                  "path accounting = AL1 s198 for extension " + std::to_string(e));
    set_weights(saved);
}

void check_rule_properties(const std::string& label) {
    check(corr_ext::double_margin(0) == 24, label + ": double margin 24 at |correction| 0");
    for (int c = 0; c <= MaxCorrection + 8; ++c) {
        const int m = corr_ext::double_margin(c);
        if (m < 0 || m > 24) check(false, label + ": double margin in [0, 24] at c " + std::to_string(c));
        if (corr_ext::double_margin(c + 1) > m) check(false, label + ": double margin non-increasing at c " + std::to_string(c));
        if (tune::CorrExtDoublePct == 0 && m != 24) check(false, label + ": double margin inert at weight 0");
    }
    for (const bool pv : {false, true})
        for (const int sb : SingularBetas)
            for (int margin = 1; margin <= 260; margin += 3)
                for (int inherited = 0; inherited <= tune::CorrExtBudget + 2; ++inherited)
                    for (int c = 0; c <= MaxCorrection; c += 4) {
                        const int ss = sb - margin;
                        const int e = corr_ext::singular_extension(pv, ss, sb, c, inherited);
                        ++evaluated;
                        const std::string at = label + " pv " + std::to_string(pv) + " margin " + std::to_string(margin) +
                                               " inherited " + std::to_string(inherited) + " c " + std::to_string(c);
                        if (e < 1 || e > 3) check(false, at + ": extension in {1, 2, 3}");
                        if (pv && e != 1) check(false, at + ": PV node extension 1");
                        if (inherited <= tune::CorrExtBudget && corr_ext::path_extra_after(inherited, e) > tune::CorrExtBudget)
                            check(false, at + ": budget exceeded");
                        if (inherited > tune::CorrExtBudget && e != 1) check(false, at + ": no extra ply above the budget");
                        if (corr_ext::singular_extension(pv, ss, sb, c + 4, inherited) < e)
                            check(false, at + ": monotonic in |correction|");
                        if (corr_ext::singular_extension(pv, ss - 3, sb, c, inherited) < e)
                            check(false, at + ": monotonic in the singular margin");
                        if (corr_ext::singular_extension(pv, ss, sb, c, inherited + 1) > e)
                            check(false, at + ": monotonic in the budget used");
                        if (e == 3 && !(c >= tune::CorrExtTripleCorr && tune::CorrExtTripleCorr > 0 &&
                                        margin > tune::CorrExtTripleMargin))
                            check(false, at + ": triple only with a large correction and margin");
                    }
}

void test_rule_and_budget() {
    const Weights saved = current();
    check(saved.double_pct == 12 && saved.triple_corr == 48 && saved.triple_margin == 100 && saved.budget == 7,
          "documented defaults 12/48/100/7");
    check_rule_properties("defaults");
    // Boundaries with the defaults: double margin 24 - c * 12 / 100, triple from c 48 and margin > 100.
    check(corr_ext::singular_extension(false, -25, 0, 0, 0) == 2 && corr_ext::singular_extension(false, -24, 0, 0, 0) == 1,
          "double margin 24 at c 0");
    check(corr_ext::double_margin(50) == 18 && corr_ext::singular_extension(false, -19, 0, 50, 0) == 2 &&
              corr_ext::singular_extension(false, -18, 0, 50, 0) == 1,
          "double margin 18 at c 50");
    check(corr_ext::singular_extension(false, -101, 0, 48, 0) == 3 && corr_ext::singular_extension(false, -100, 0, 48, 0) == 2,
          "triple needs margin > 100");
    check(corr_ext::singular_extension(false, -500, 0, 47, 0) == 2 && corr_ext::singular_extension(false, -500, 0, 48, 0) == 3,
          "triple needs |correction| >= 48");
    check(corr_ext::singular_extension(false, -500, 0, 64, 5) == 3 && corr_ext::singular_extension(false, -500, 0, 64, 6) == 2 &&
              corr_ext::singular_extension(false, -500, 0, 64, 7) == 1,
          "budget 7: triple needs 2 plies of room, double 1");
    check(corr_ext::singular_extension(true, -500, 0, 64, 0) == 1, "PV node: extension 1");
    for (int budget = 0; budget <= 12; ++budget) {
        set_weights({saved.double_pct, saved.triple_corr, saved.triple_margin, budget});
        check_rule_properties("budget " + std::to_string(budget));
    }
    std::uint64_t state = 0xc0ffee08ULL;
    for (int round = 0; round < 12; ++round) {
        set_weights({uniform(state, 0, 400), uniform(state, 0, 80), uniform(state, 0, 300), uniform(state, 0, 12)});
        check_rule_properties("random weights round " + std::to_string(round));
    }
    set_weights(saved);
}

// Random paths: at each ply a random extension situation (singular with random margin and
// correction, or a check / negative / no extension); the path count must stay within the budget
// and equal the sum of the extra plies granted.
void test_random_paths() {
    const Weights saved = current();
    std::uint64_t state = 0x0b5e5510ULL;
    long long triples = 0, doubles = 0, at_cap = 0;
    for (int path = 0; path < 20000; ++path) {
        if (path % 1000 == 0)
            set_weights({uniform(state, 0, 400), uniform(state, 0, 80), uniform(state, 0, 300), uniform(state, 0, 12)});
        int count = 0, granted = 0;
        const int length = uniform(state, 1, MaxPly);
        for (int ply = 0; ply < length; ++ply) {
            int e;
            const int kind = uniform(state, 0, 9);
            if (kind <= 5) {
                const int sb = uniform(state, -600, 600);
                e = corr_ext::singular_extension(uniform(state, 0, 4) == 0, sb - uniform(state, 1, 400), sb,
                                                 uniform(state, 0, MaxCorrection), count);
            } else {
                e = std::array<int, 4>{-2, -1, 0, 1}[static_cast<std::size_t>(kind - 6)];
            }
            const int next = corr_ext::path_extra_after(count, e);
            granted += std::max(0, e - 1);
            triples += e == 3;
            doubles += e == 2;
            count = next;
            if (count > tune::CorrExtBudget) {
                check(false, "random path " + std::to_string(path) + " exceeded the budget at ply " + std::to_string(ply));
                break;
            }
            at_cap += count == tune::CorrExtBudget;
        }
        if (count != granted) check(false, "random path " + std::to_string(path) + ": count != extra plies granted");
    }
    std::cout << "random paths: doubles " << doubles << " triples " << triples << " plies at the cap " << at_cap << '\n';
    check(triples > 0 && doubles > 0 && at_cap > 0, "random paths exercise doubles, triples and the cap");
    set_weights(saved);
}

Board board_from(const std::string& fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid FEN " + fen);
    return board;
}

// White to move wins the black queen with exd5 (and keeps a rook): the TT move is singular by a
// very wide margin and fails high.
const std::string QueenWin = "4k3/8/8/3q4/4P3/8/8/R3K3 w - - 0 1";

struct NodeResult {
    int score;
    int path_extra;  // SearchStack::double_extensions of the node after the search (the TT move's)
    int max_extra;   // the largest double_extensions value left in any stack frame
};

NodeResult singular_node(bool corr_instance, int correction_cp, int inherited) {
    Searcher searcher(1, 1);
    Board board = board_from(QueenWin);
    SearchStack* ss = Probe::prepare(searcher, board);
    (ss - 1)->double_extensions = inherited;
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    Probe::pawns(searcher)[side][board.pawn_key() & (CorrectionSize - 1U)] = correction_cp * CorrectionGrain;
    const auto move = board.parse_uci("e4d5");
    if (!move) throw std::runtime_error("e4d5 not legal in the fixture");
    // Depth 6 >= 7 - 3 for the singular test, below 7 so there is no TT cutoff; lower bound 700.
    TranspositionTable& tt = searcher.transposition_table();
    const TTProbe probe = tt.probe(board.key());
    tt.store(probe, board.key(), 700, ValueNone, *move, 6, BoundLower, false, board.halfmove_clock());
    const int beta = 300;
    const int score = Probe::search(searcher, board, ss, 7, beta - 1, beta, corr_instance);
    return {score, ss->double_extensions, Probe::max_stack_extra(searcher)};
}

void test_singular_node() {
    const Weights saved = current();
    // Keep the node on the singular-extension path: no reverse futility, null move or ProbCut.
    const int rfp_depth = tune::RfpDepth, null_min = tune::NullMoveMinDepth, probcut = tune::ProbcutDepth;
    tune::RfpDepth = 0;
    tune::NullMoveMinDepth = 100;
    tune::ProbcutDepth = 100;
    struct Case { bool corr; int correction; int inherited; Weights weights; int extra; const char* what; };
    const Weights d = saved;
    const std::array<Case, 10> cases{{
        {false, 50, 0, d, 1, "default instance: AL1 s198 double"},
        {false, 50, 7, d, 0, "default instance: no double after 7"},
        {true, 0, 0, d, 1, "CorrExt, |correction| 0: double"},
        {true, 47, 0, d, 1, "CorrExt, |correction| 47: double (no triple below 48)"},
        {true, 50, 0, d, 2, "CorrExt, |correction| 50: triple"},
        {true, 50, 5, d, 2, "CorrExt, room 2: triple up to the cap"},
        {true, 50, 6, d, 1, "CorrExt, room 1: double only"},
        {true, 50, 7, d, 0, "CorrExt, budget used up: extension 1"},
        {true, 50, 0, {d.double_pct, 0, d.triple_margin, d.budget}, 1, "CorrExt, triple off: double"},
        {true, 50, 1, {d.double_pct, d.triple_corr, d.triple_margin, 2}, 1, "CorrExt, budget 2 with 1 used: double only"},
    }};
    for (const Case& c : cases) {
        set_weights(c.weights);
        const NodeResult r = singular_node(c.corr, c.correction, c.inherited);
        const std::string at = std::string(c.what) + " (inherited " + std::to_string(c.inherited) + ")";
        check(r.score >= 300, at + ": the TT move fails high");
        check(r.path_extra == c.inherited + c.extra,
              at + ": extra plies " + std::to_string(r.path_extra - c.inherited) + " expected " + std::to_string(c.extra));
        if (c.corr) check(r.max_extra <= tune::CorrExtBudget, at + ": no stack frame above the budget");
    }
    tune::RfpDepth = rfp_depth;
    tune::NullMoveMinDepth = null_min;
    tune::ProbcutDepth = probcut;
    set_weights(saved);
}

struct SearchResult {
    std::uint64_t nodes;
    Move best;
    int score;
    bool operator==(const SearchResult&) const = default;
};

const std::array<std::string, 8> BenchFens{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
};

std::vector<SearchResult> run_set(int depth, int* max_extra = nullptr) {
    std::vector<SearchResult> out;
    Searcher searcher(16, 1);
    int worst = 0;
    for (const std::string& fen : BenchFens) {
        searcher.clear();
        SearchLimits limits;
        limits.depth = depth;
        const SearchInfo info = searcher.search(board_from(fen), limits, false, Searcher::TTAccess::Exclusive);
        out.push_back({info.nodes, info.best_move, info.score});
        worst = std::max(worst, Probe::max_stack_extra(searcher));
    }
    if (max_extra) *max_extra = worst;
    return out;
}

std::uint64_t total(const std::vector<SearchResult>& results) {
    std::uint64_t sum = 0;
    for (const SearchResult& r : results) sum += r.nodes;
    return sum;
}

void test_whole_search() {
    const Weights saved = current();
    const int depth = 11;
    options::corr_ext = 0;
    const auto off = run_set(depth);
    std::cout << "whole search depth " << depth << ": off nodes " << total(off) << '\n';
    check(total(off) == 312866, "CorrExt 0 reproduces the AL1 s198 bench d11 node count 312866");

    options::corr_ext = 1;
    set_weights({0, 0, saved.triple_margin, 7});
    check(run_set(depth) == off, "CorrExt 1 with every weight 0 (budget 7) == default search");

    const std::array<std::pair<const char*, Weights>, 3> single{{
        {"double margin alone (CorrExtDoublePct 400)", {400, 0, saved.triple_margin, 7}},
        {"triple alone (CorrExtTripleCorr 1, margin 0)", {0, 1, 0, 7}},
        {"budget alone (CorrExtBudget 0)", {0, 0, saved.triple_margin, 0}},
    }};
    for (const auto& [name, weights] : single) {
        set_weights(weights);
        int worst = 0;
        const auto alone = run_set(depth, &worst);
        std::cout << "whole search depth " << depth << ": " << name << " nodes " << total(alone) << '\n';
        check(alone != off, std::string(name) + " changes the search");
        check(worst <= tune::CorrExtBudget, std::string(name) + ": no stack frame above the budget");
    }
    for (int budget = 0; budget <= 3; ++budget) {
        set_weights({400, 1, 0, budget});
        int worst = 0;
        (void)run_set(9, &worst);
        check(worst <= budget, "aggressive extensions, budget " + std::to_string(budget) + ": stack frames within the budget");
    }

    set_weights(saved);
    const auto on = run_set(depth);
    const auto again = run_set(depth);
    std::cout << "whole search depth " << depth << ": on (default weights) nodes " << total(on) << '\n';
    check(on != off, "CorrExt 1 with the default weights changes the search");
    check(on == again, "CorrExt 1 is deterministic");

    options::corr_ext = 0;
    set_weights({400, 1, 0, 64});
    check(run_set(depth) == off, "weights are inert while CorrExt is 0");
    set_weights(saved);
}

} // namespace

int main() {
    test_correction_size();
    test_lock_identity();
    test_rule_and_budget();
    test_random_paths();
    test_singular_node();
    test_whole_search();
    std::cout << "corr_ext: checks=" << checks << " rule decisions evaluated=" << evaluated << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " corr_ext_tests\n";
    return failures == 0 ? 0 : 1;
}
