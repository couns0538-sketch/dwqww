// UCI CorrMargins (forge/corr_margins.hpp, test plan G-B3): correction-size
// pruning margins.
//   1. The margin functions against the AL1 s198 formulas written out here:
//      identical at |correction| = 0, monotonic in |correction| (margins never
//      shrink, the reduction never grows), no change at all when the weight is
//      0, a strict change when it is not; over default, zero and random tunables.
//   2. Node decisions of the CorrMargins search instance through the test
//      probe: with a correction planted in the pawn correction table, reverse
//      futility pruning and the null-move try happen exactly when the widened
//      margin allows them (boundary cases included); the default instance
//      ignores the correction size.
//   3. Whole searches through the public Searcher: CorrMargins 1 with every
//      weight 0 is node-for-node the default search; each weight alone changes
//      the search; the weights do nothing while CorrMargins is 0; ON is
//      deterministic.
#include "forge/board.hpp"
#include "forge/corr_margins.hpp"
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
        w.null_tries_ = w.null_cutoffs_ = 0;
        w.root_history_index_ = board.history_size() - 1;
        SearchStack* ss = &w.stack_[5];
        ss->ply = 1;
        nnue::refresh(board, ss->accumulator);
        return ss;
    }
    static int search(Searcher& searcher, Board& board, SearchStack* ss, int depth, int alpha, int beta, bool corr) {
        Worker& w = searcher.main_worker();
        return corr ? w.search_corr_margins(board, ss, depth, alpha, beta, false)
                    : w.search(board, ss, depth, alpha, beta, false);
    }
    static std::uint64_t nodes(Searcher& searcher) { return searcher.main_worker().local_nodes_; }
    static std::uint64_t null_tries(Searcher& searcher) { return searcher.main_worker().null_tries_; }
    static int raw_eval(Searcher& searcher, const Board& board, SearchStack* ss) {
        return searcher.main_worker().static_evaluate(board, ss);
    }
    static int corrected(Searcher& searcher, const Board& board, int raw) {
        return searcher.main_worker().corrected_eval(board, raw);
    }
    static CorrectionHistory& pawns(Searcher& searcher) { return *searcher.main_worker().correction_history_; }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;

namespace {

int failures = 0;
int checks = 0;

void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) {
        ++failures;
        if (failures <= 40) std::cout << "FAIL " << what << '\n';
        else if (failures == 41) std::cout << "(further failures not printed)\n";
    }
}

// The AL1 s198 formulas (src/search/alphabeta.inc of the lock), written out independently.
int lock_rfp_margin(int depth, bool improving) { return tune::RfpMargin * depth - tune::RfpImproving * improving; }
int lock_futility_margin(int lmr_depth) { return tune::FutilityBase + tune::FutilityMultiplier * lmr_depth; }
int lock_null_threshold(int beta, int depth) { return beta - 24 * depth + 180; }

struct Weights {
    int rfp, futility, null_move, lmr;
};

void set_weights(const Weights& w) {
    tune::CorrRfpPct = w.rfp;
    tune::CorrFutilityPct = w.futility;
    tune::CorrNullMovePct = w.null_move;
    tune::CorrLmrPct = w.lmr;
}

std::uint64_t lcg(std::uint64_t& state) {
    state = state * 6364136223846793005ULL + 1442695040888963407ULL;
    return state >> 33U;
}
int uniform(std::uint64_t& state, int lo, int hi) { return lo + static_cast<int>(lcg(state) % static_cast<std::uint64_t>(hi - lo + 1)); }

// Largest |correction| the tables can produce (MaterialCorrectionWeight at its maximum, 300).
constexpr int MaxCorrection = (CorrectionLimit + CorrectionLimit * 3) / CorrectionGrain;

void check_margin_functions(const std::string& label) {
    const std::array<int, 7> betas{-MateInMaxPly + 1, -1500, -37, 0, 41, 900, MateInMaxPly - 1};
    for (int depth = 0; depth <= 64; ++depth) {
        for (const bool improving : {false, true}) {
            const std::string at = label + " depth " + std::to_string(depth) + " improving " + std::to_string(improving);
            check(corr_margins::rfp_margin(depth, improving, 0) == lock_rfp_margin(depth, improving), "rfp lock identity " + at);
            for (int c = 0; c < MaxCorrection + 8; ++c) {
                const int m0 = corr_margins::rfp_margin(depth, improving, c);
                const int m1 = corr_margins::rfp_margin(depth, improving, c + 1);
                if (m1 < m0) check(false, "rfp monotonic " + at + " c " + std::to_string(c));
                if (tune::CorrRfpPct == 0 && m0 != lock_rfp_margin(depth, improving))
                    check(false, "rfp inert at weight 0 " + at + " c " + std::to_string(c));
            }
            if (tune::CorrRfpPct > 0)
                check(corr_margins::rfp_margin(depth, improving, 100) > lock_rfp_margin(depth, improving), "rfp widens " + at);
        }
        const std::string at = label + " lmr_depth " + std::to_string(depth);
        check(corr_margins::futility_margin(depth, 0) == lock_futility_margin(depth), "futility lock identity " + at);
        for (int c = 0; c < MaxCorrection + 8; ++c) {
            const int m0 = corr_margins::futility_margin(depth, c);
            if (corr_margins::futility_margin(depth, c + 1) < m0) check(false, "futility monotonic " + at + " c " + std::to_string(c));
            if (tune::CorrFutilityPct == 0 && m0 != lock_futility_margin(depth))
                check(false, "futility inert at weight 0 " + at + " c " + std::to_string(c));
        }
        if (tune::CorrFutilityPct > 0)
            check(corr_margins::futility_margin(depth, 100) > lock_futility_margin(depth), "futility widens " + at);
        for (const int beta : betas) {
            const std::string bt = label + " depth " + std::to_string(depth) + " beta " + std::to_string(beta);
            check(corr_margins::null_move_threshold(beta, depth, 0) == lock_null_threshold(beta, depth), "null-move lock identity " + bt);
            for (int c = 0; c < MaxCorrection + 8; ++c) {
                const int t0 = corr_margins::null_move_threshold(beta, depth, c);
                if (corr_margins::null_move_threshold(beta, depth, c + 1) < t0)
                    check(false, "null-move monotonic " + bt + " c " + std::to_string(c));
                if (tune::CorrNullMovePct == 0 && t0 != lock_null_threshold(beta, depth))
                    check(false, "null-move inert at weight 0 " + bt + " c " + std::to_string(c));
            }
            if (tune::CorrNullMovePct > 0)
                check(corr_margins::null_move_threshold(beta, depth, 100) > lock_null_threshold(beta, depth), "null-move widens " + bt);
        }
    }
    for (int r = -6; r <= 24; ++r) {
        const std::string at = label + " r " + std::to_string(r);
        check(corr_margins::lmr_reduction(r, 0) == r, "lmr lock identity " + at);
        for (int c = 0; c < MaxCorrection + 8; ++c) {
            const int v0 = corr_margins::lmr_reduction(r, c);
            const int v1 = corr_margins::lmr_reduction(r, c + 1);
            if (v1 > v0) check(false, "lmr monotonic " + at + " c " + std::to_string(c));
            if (r <= 0 && v0 != r) check(false, "lmr leaves r <= 0 alone " + at + " c " + std::to_string(c));
            if (r > 0 && (v0 < 0 || v0 > r)) check(false, "lmr stays in [0, r] " + at + " c " + std::to_string(c));
            if (tune::CorrLmrPct == 0 && v0 != r) check(false, "lmr inert at weight 0 " + at + " c " + std::to_string(c));
        }
    }
    // CorrLmrPct percent of the reduction per 64 cp, rounded down.
    if (tune::CorrLmrPct > 0) {
        const int r = 8;
        const int expected = r - std::min(r, r * 64 * tune::CorrLmrPct / 6400);
        check(corr_margins::lmr_reduction(r, 64) == expected, label + " lmr share at 64 cp");
        check(corr_margins::lmr_reduction(r, 64) < r || r * tune::CorrLmrPct < 100, label + " lmr relief happens");
    }
}

void test_correction_size() {
    check(corr_margins::correction_size(true, 120, 80) == 0, "correction size 0 in check");
    check(corr_margins::correction_size(false, ValueNone, ValueNone) == 0, "correction size 0 without evaluation");
    check(corr_margins::correction_size(false, ValueNone, 30) == 0, "correction size 0 without static eval");
    check(corr_margins::correction_size(false, 30, ValueNone) == 0, "correction size 0 without raw eval");
    for (int raw = -300; raw <= 300; raw += 17) {
        for (int corr = -70; corr <= 70; corr += 7) {
            const int size = corr_margins::correction_size(false, raw + corr, raw);
            if (size != (corr < 0 ? -corr : corr)) check(false, "correction size = |static - raw| raw " + std::to_string(raw));
        }
    }
}

void test_margin_functions() {
    const Weights defaults{tune::CorrRfpPct, tune::CorrFutilityPct, tune::CorrNullMovePct, tune::CorrLmrPct};
    const std::array<int, 4> lock_values{tune::RfpMargin, tune::RfpImproving, tune::FutilityBase, tune::FutilityMultiplier};
    check(defaults.rfp == 50 && defaults.futility == 100 && defaults.null_move == 50 && defaults.lmr == 25,
          "documented default weights 50/100/50/25");
    check_margin_functions("default weights");
    set_weights({0, 0, 0, 0});
    check_margin_functions("zero weights");
    std::uint64_t state = 0x5eed0c0aULL;
    for (int round = 0; round < 40; ++round) {
        set_weights({uniform(state, 0, 400), uniform(state, 0, 400), uniform(state, 0, 400), uniform(state, 0, 400)});
        tune::RfpMargin = uniform(state, 10, 300);
        tune::RfpImproving = uniform(state, 0, 200);
        tune::FutilityBase = uniform(state, 0, 500);
        tune::FutilityMultiplier = uniform(state, 0, 500);
        check_margin_functions("random tunables round " + std::to_string(round));
    }
    set_weights(defaults);
    tune::RfpMargin = lock_values[0];
    tune::RfpImproving = lock_values[1];
    tune::FutilityBase = lock_values[2];
    tune::FutilityMultiplier = lock_values[3];
}

Board board_from(const std::string& fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid FEN " + fen);
    return board;
}

// White to move, a queen up, quiet: reverse futility and null-move candidates.
const std::string QueenUp = "4k3/pp6/8/8/8/8/PP1Q4/4K3 w - - 0 1";

struct NodeResult {
    int score;
    std::uint64_t nodes;
    std::uint64_t null_tries;
};

// One direct non-PV node search at ply 1 with `correction_cp` planted in the
// pawn correction entry of the position; beta is placed `beta_offset` below
// the corrected static evaluation.
NodeResult node_search(bool corr_instance, int depth, int correction_cp, int beta_offset, int* eval_out = nullptr) {
    Searcher searcher(1, 1);
    Board board = board_from(QueenUp);
    SearchStack* ss = Probe::prepare(searcher, board);
    if (depth >= tune::NullMoveMinDepth) (ss - 1)->current_move = Move{8, 16, 0, 0};  // a parent move (not none)
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    Probe::pawns(searcher)[side][board.pawn_key() & (CorrectionSize - 1U)] = correction_cp * CorrectionGrain;
    const int raw = Probe::raw_eval(searcher, board, ss);
    const int eval = Probe::corrected(searcher, board, raw);
    if (eval_out) *eval_out = eval;
    const int beta = eval - beta_offset;
    const int score = Probe::search(searcher, board, ss, depth, beta - 1, beta, corr_instance);
    return {score, Probe::nodes(searcher), Probe::null_tries(searcher)};
}

void test_rfp_decision() {
    const Weights saved{tune::CorrRfpPct, tune::CorrFutilityPct, tune::CorrNullMovePct, tune::CorrLmrPct};
    // Depth 1, improving (no earlier static evals): AL1 s198 margin 72 - 40 = 32; slack 10.
    const int margin = lock_rfp_margin(1, true);
    const int slack = 10;
    struct Case { int weight; int correction; bool prunes; };
    const std::array<Case, 9> cases{{
        {0, 40, true}, {100, 0, true}, {100, 40, false}, {100, -40, false},
        {20, 40, true},   // widening 8 < slack
        {25, 40, true},   // widening 10 == slack: eval - margin >= beta still holds
        {26, 40, true},   // 40 * 26 / 100 = 10 (rounded down)
        {28, 40, false},  // widening 11 > slack
        {28, -40, false},
    }};
    for (const Case& c : cases) {
        set_weights({c.weight, 0, 0, 0});
        int eval = 0;
        const NodeResult on = node_search(true, 1, c.correction, margin + slack, &eval);
        const NodeResult off = node_search(false, 1, c.correction, margin + slack);
        const std::string at = "rfp node weight " + std::to_string(c.weight) + " correction " + std::to_string(c.correction);
        check(eval != 0, at + ": evaluation available");
        check(off.nodes == 1 && off.score == eval, at + ": default instance prunes");
        if (c.prunes) check(on.nodes == 1 && on.score == eval, at + ": CorrMargins instance prunes");
        else check(on.nodes > 1, at + ": CorrMargins instance searches the node");
    }
    set_weights(saved);
}

void test_null_move_decision() {
    const Weights saved{tune::CorrRfpPct, tune::CorrFutilityPct, tune::CorrNullMovePct, tune::CorrLmrPct};
    // Depth 3, beta = eval - 120: no reverse futility (margin 3 * 72 - 40 = 176 > 120), and the
    // AL1 s198 null-move condition static_eval >= beta - 72 + 180 = eval - 12 holds with slack 12.
    const int depth = 3;
    const int beta_offset = 120;
    check(lock_rfp_margin(depth, true) > beta_offset, "null-move fixture has no reverse futility");
    struct Case { int weight; int correction; bool tries; };
    const std::array<Case, 7> cases{{
        {0, 40, true}, {100, 0, true}, {100, 40, false}, {100, -40, false},
        {100, 12, true},  // threshold + 12 == static eval: >= holds
        {100, 13, false},
        {30, 40, true},   // 40 * 30 / 100 = 12
    }};
    for (const Case& c : cases) {
        set_weights({0, 0, c.weight, 0});
        const NodeResult on = node_search(true, depth, c.correction, beta_offset);
        const NodeResult off = node_search(false, depth, c.correction, beta_offset);
        const std::string at = "null-move node weight " + std::to_string(c.weight) + " correction " + std::to_string(c.correction);
        check(off.null_tries == 1, at + ": default instance tries the null move");
        check(on.null_tries == (c.tries ? 1U : 0U), at + ": CorrMargins instance null-move try");
    }
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

std::vector<SearchResult> run_set(int depth) {
    std::vector<SearchResult> out;
    Searcher searcher(16, 1);
    for (const std::string& fen : BenchFens) {
        searcher.clear();
        SearchLimits limits;
        limits.depth = depth;
        const SearchInfo info = searcher.search(board_from(fen), limits, false, Searcher::TTAccess::Exclusive);
        out.push_back({info.nodes, info.best_move, info.score});
    }
    return out;
}

std::uint64_t total(const std::vector<SearchResult>& results) {
    std::uint64_t sum = 0;
    for (const SearchResult& r : results) sum += r.nodes;
    return sum;
}

void test_whole_search() {
    const Weights defaults{tune::CorrRfpPct, tune::CorrFutilityPct, tune::CorrNullMovePct, tune::CorrLmrPct};
    const int depth = 11;
    options::corr_margins = 0;
    const auto off = run_set(depth);
    std::cout << "whole search depth " << depth << ": off nodes " << total(off) << '\n';
    check(total(off) == 312866, "CorrMargins 0 reproduces the AL1 s198 bench d11 node count 312866");

    options::corr_margins = 1;
    set_weights({0, 0, 0, 0});
    const auto zero = run_set(depth);
    check(zero == off, "CorrMargins 1 with all weights 0 == default search (nodes, best move, score)");

    const std::array<std::pair<const char*, Weights>, 4> single{{
        {"CorrRfpPct", {400, 0, 0, 0}}, {"CorrFutilityPct", {0, 400, 0, 0}},
        {"CorrNullMovePct", {0, 0, 400, 0}}, {"CorrLmrPct", {0, 0, 0, 100}},
    }};
    for (const auto& [name, weights] : single) {
        set_weights(weights);
        const auto alone = run_set(depth);
        std::cout << "whole search depth " << depth << ": " << name << " alone nodes " << total(alone) << '\n';
        check(alone != off, std::string(name) + " alone changes the search");
    }

    set_weights(defaults);
    const auto on = run_set(depth);
    const auto again = run_set(depth);
    std::cout << "whole search depth " << depth << ": on (default weights) nodes " << total(on) << '\n';
    check(on != off, "CorrMargins 1 with the default weights changes the search");
    check(on == again, "CorrMargins 1 is deterministic");

    options::corr_margins = 0;
    set_weights({400, 400, 400, 400});
    const auto off_weighted = run_set(depth);
    check(off_weighted == off, "weights are inert while CorrMargins is 0");
    set_weights(defaults);
}

} // namespace

int main() {
    test_correction_size();
    test_margin_functions();
    test_rfp_decision();
    test_null_move_decision();
    test_whole_search();
    std::cout << "corr_margins: checks=" << checks << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " corr_margins_tests\n";
    return failures == 0 ? 0 : 1;
}
