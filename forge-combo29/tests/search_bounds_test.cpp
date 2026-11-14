#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

int failures = 0;

void expect(bool condition, const std::string& message) {
    if (condition) return;
    std::cerr << "FAIL " << message << '\n';
    ++failures;
}

void expect_eq(int got, int want, const std::string& message) {
    if (got == want) return;
    std::cerr << "FAIL " << message << " got " << got << " want " << want << '\n';
    ++failures;
}

// The previous aspiration update. Toward-zero division is what pinned
// [-Infinite, -Infinite + 1] in place.
bool legacy_widen(int& alpha, int& beta, int& delta, int score) {
    if (score > alpha && score < beta) return false;
    if (score <= alpha) {
        beta = (alpha + beta) / 2;
        alpha = std::max(score - delta, -forge::Infinite);
    } else {
        beta = std::min(score + delta, forge::Infinite);
    }
    delta += delta / 2 + 4;
    return true;
}

forge::Board board_from(const std::string& fen) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cerr << "FAIL fen: " << error << " [" << fen << "]\n";
        ++failures;
    }
    return board;
}

forge::SearchInfo search_depth(const std::string& fen, int depth, const forge::SearchLimits& extra = {}) {
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits = extra;
    limits.depth = depth;
    return searcher.search(board_from(fen), limits, false);
}

} // namespace

namespace forge {

struct SearcherTestProbe {
    static void prepare(Worker& worker, const Board& board) {
        for (SearchStack& entry : worker.stack_) {
            entry.pv_length = 0;
            entry.current_move = Move::none();
            entry.excluded_move = Move::none();
            entry.moved_piece = Empty;
            entry.static_eval = ValueNone;
            entry.raw_eval = ValueNone;
            entry.continuation = &(*worker.continuation_history_)[Empty][0];
            entry.double_extensions = 0;
            entry.null_move_allowed = true;
            entry.killers = {};
            entry.in_check = false;
            entry.tt_pv = false;
        }
        for (int i = 0; i < MaxPly + 4; ++i) {
            worker.stack_[static_cast<std::size_t>(i)].ply = i - 4;
        }
        worker.aborted_ = false;
        worker.local_nodes_ = 0;
        worker.root_restricted_ = false;
        worker.node_limit_specified_ = false;
        worker.all_workers_ = nullptr;
        worker.root_history_index_ = board.history_size() - 1;
        worker.audit_abort_after_worse_pv_ = false;
        worker.audit_have_guard_ = false;
        worker.audit_first_move_ = Move::none();
    }

    // Non-PV search at ply 1 so a poisoned root-position entry is eligible for
    // a transposition cutoff (the public root search is a PV node).
    static int null_window(Worker& worker, Board& board, int depth, int beta) {
        prepare(worker, board);
        SearchStack* ss = &worker.stack_[5];
        ss->ply = 1;
        return worker.search(board, ss, depth, beta - 1, beta, false);
    }
};

} // namespace forge

namespace {

void store_score(forge::TranspositionTable& tt, const forge::Board& board, int score, int depth, forge::Bound bound) {
    const forge::TTProbe probe = tt.probe(board.key());
    tt.store(probe, board.key(), score, forge::ValueNone, forge::Move::none(), depth, bound, false, 0);
}

void test_window_arithmetic() {
    int mismatches = 0;
    for (int alpha = -200; alpha <= 200; alpha += 40) {
        for (int width = 2; width <= 80; width += 13) {
            for (int delta : {4, 18, 50, 200}) {
                for (int shift : {-80, -1, 0, 1, 40, 90}) {
                    const int beta = alpha + width;
                    const int score = alpha + shift;
                    if (score > alpha && score < beta) continue;
                    int la = alpha, lb = beta, ld = delta;
                    int fa = alpha, fb = beta, fd = delta;
                    legacy_widen(la, lb, ld, score);
                    bool give_up = false;
                    const bool again = forge::widen_aspiration(fa, fb, fd, score, give_up);
                    const bool legacy_stuck = la == alpha && lb == beta;
                    const bool legacy_inverted = la >= lb;
                    if (!legacy_stuck && !legacy_inverted) {
                        if (fa != la || fb != lb || fd != ld || !again || give_up) {
                            if (mismatches < 8) {
                                std::cerr << "FAIL window mismatch a=" << alpha << " b=" << beta
                                          << " s=" << score << " d=" << delta << " legacy " << la << ',' << lb
                                          << " fixed " << fa << ',' << fb << '\n';
                            }
                            ++mismatches;
                        }
                    }
                }
            }
        }
    }
    expect(mismatches == 0, "fixed aspiration arithmetic matches the old update whenever the old update moves");

    int alpha = -forge::Infinite;
    int beta = -forge::Infinite + 1;
    int delta = 18;
    const int score = -forge::Infinite;
    int la = alpha, lb = beta, ld = delta;
    legacy_widen(la, lb, ld, score);
    expect(la == alpha && lb == beta, "old fail-low division leaves the floor window unchanged");
    bool give_up = false;
    const bool again = forge::widen_aspiration(alpha, beta, delta, score, give_up);
    expect(again && !give_up, "fixed update requests another search");
    expect(alpha == -forge::Infinite && beta == forge::Infinite, "fixed update opens a stuck floor window");
    give_up = false;
    const bool again_full = forge::widen_aspiration(alpha, beta, delta, score, give_up);
    expect(!again_full && give_up, "a second failure on the full window stops instead of spinning");
    std::cout << "PASS window arithmetic (stuck floor and normal steps)\n";
}

void test_mate_horizon() {
    constexpr int long_distance = 29; // mate in 15; needs 29 plies
    constexpr int short_distance = 5; // mate in 3; 5 plies
    constexpr int long_stored = forge::MateValue - long_distance;
    constexpr int short_stored = forge::MateValue - short_distance;
    constexpr int long_loss = -forge::MateValue + long_distance;
    const std::string crowded = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 80 40";

    auto cutoff = [&](const std::string& fen, int stored, int depth) {
        forge::Searcher searcher(8, 1);
        forge::Board board = board_from(fen);
        store_score(searcher.transposition_table(), board, stored, depth, forge::BoundExact);
        return forge::SearcherTestProbe::null_window(searcher.main_worker(), board, 3, 1);
    };

    forge::search_fixes().mate_horizon = false;
    const int stale = cutoff(crowded, long_stored, 8);
    // ply 1 subtracts one from a stored win.
    expect_eq(stale, long_stored - 1, "without the horizon check a 29-ply mate is replayed at clock 80");

    forge::search_fixes().mate_horizon = true;
    const int rejected = cutoff(crowded, long_stored, 8);
    expect(!forge::is_mate_score(rejected), "clock 80 cannot deliver a 29-ply mate");
    expect(rejected != long_stored - 1, "the rejected mate is not returned as a cutoff");

    const int kept = cutoff(crowded, short_stored, 8);
    expect_eq(kept, short_stored - 1, "a 5-ply mate still fits in the 20 plies left at clock 80");

    const int loss = cutoff(crowded, long_loss, 8);
    expect(!forge::is_mate_score(loss), "a 29-ply loss is not a bound at clock 80");

    // Distance 0 is "already mated". The horizon must not throw that away.
    const int already = cutoff(crowded, -forge::MateValue, 8);
    expect_eq(already, -forge::MateValue + 1, "an immediate loss stays a loss at clock 80");

    const std::string fresh = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const int early = cutoff(fresh, long_stored, 8);
    expect_eq(early, long_stored - 1, "the same 29-ply mate is kept when the clock is 0");

    std::cout << "PASS mate horizon (stale " << stale << ", rejected " << rejected << ", kept " << kept
              << ", loss " << loss << ", already " << already << ", early " << early << ")\n";
}

void test_qsearch_shallow_bound() {
    const std::string fen = "4k3/8/8/8/8/8/8/4KQ2 w - - 0 1";
    auto run = [&](bool fix) {
        forge::search_fixes().qsearch_shallow_bound = fix;
        forge::Searcher searcher(8, 1);
        forge::Board board = board_from(fen);
        store_score(searcher.transposition_table(), board, -400, 0, forge::BoundUpper);
        return forge::SearcherTestProbe::null_window(searcher.main_worker(), board, 0, 1);
    };
    forge::search_fixes().mate_horizon = true;
    const int stale = run(false);
    const int stand = run(true);
    expect_eq(stale, -400, "depth-0 upper bound below stand-pat is returned when the check is off");
    expect(stand > 200, "stand-pat of KQ vs K replaces that upper bound");
    std::cout << "PASS qsearch shallow bound (stale " << stale << ", stand " << stand << ")\n";
    forge::search_fixes().qsearch_shallow_bound = false;
}

void test_partial_pv() {
    const std::string fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const int saved_delta = forge::tune::AspirationDelta;
    forge::tune::AspirationDelta = 1000;
    forge::Board board = board_from(fen);
    const auto bad = board.parse_uci("a2a3");
    expect(bad.has_value(), "a2a3 parses");
    if (!bad.has_value()) return;

    const forge::SearchInfo depth3 = search_depth(fen, 3);
    expect(!depth3.best_move.is_none(), "depth 3 has a move");
    expect(!(depth3.best_move == *bad), "depth 3 does not choose a2a3");

    forge::SearchLimits only_bad;
    only_bad.search_moves_specified = true;
    only_bad.search_moves = {*bad};
    const forge::SearchInfo bad_line = search_depth(fen, 3, only_bad);
    expect(bad_line.score < depth3.score, "a2a3 scores below the depth-3 move");

    auto aborted = [&](bool fix) {
        forge::search_fixes().aspiration = fix;
        forge::SearchLimits limits;
        limits.audit_abort_after_worse_pv = true;
        limits.audit_first_move = *bad;
        return search_depth(fen, 4, limits);
    };
    const forge::SearchInfo buggy = aborted(false);
    const forge::SearchInfo fixed = aborted(true);
    expect(buggy.best_move == *bad, "old abort handler publishes a2a3");
    expect_eq(buggy.score, depth3.score, "old handler keeps the depth-3 score beside the new move");
    expect_eq(buggy.depth, 3, "old handler does not claim the aborted depth");
    expect(fixed.best_move == depth3.best_move, "fixed handler keeps the completed move");
    expect_eq(fixed.score, depth3.score, "fixed handler keeps the completed score");
    std::cout << "PASS partial PV (depth3 " << forge::Board::move_to_uci(depth3.best_move) << " cp " << depth3.score
              << ", a2a3 cp " << bad_line.score << ", buggy " << forge::Board::move_to_uci(buggy.best_move)
              << ", fixed " << forge::Board::move_to_uci(fixed.best_move) << ")\n";
    forge::tune::AspirationDelta = saved_delta;
    forge::search_fixes().aspiration = true;
}

void test_fail_high_kept() {
    // 1.e4 e5. With a 4cp window the depth-5 search fail-highs, then the test
    // aborts the re-search. Hand-crafted eval, so the scores are stable.
    const std::string fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2";
    const int saved_delta = forge::tune::AspirationDelta;
    forge::tune::AspirationDelta = 4;
    const forge::SearchInfo full4 = search_depth(fen, 4);
    auto run = [&](bool fix) {
        forge::search_fixes().aspiration = fix;
        forge::SearchLimits limits;
        limits.audit_abort_on_attempt = 2;
        return search_depth(fen, 5, limits);
    };
    const forge::SearchInfo buggy = run(false);
    const forge::SearchInfo fixed = run(true);
    expect_eq(full4.score, 18, "depth 4 score of 1.e4 e5");
    expect(forge::Board::move_to_uci(full4.best_move) == "g1f3", "depth 4 move is Nf3");
    expect_eq(buggy.score, full4.score, "old handler keeps the depth-4 score");
    expect_eq(buggy.depth, 4, "old handler does not advance the finished depth");
    expect(forge::Board::move_to_uci(buggy.best_move) == "f1c4", "old handler still switches to the fail-high move");
    expect(buggy.best_move == fixed.best_move, "both handlers saw the same fail-high move");
    expect(fixed.score > buggy.score, "fixed handler publishes the fail-high score");
    expect_eq(fixed.score, 22, "fail-high score of Bc4");
    expect_eq(fixed.depth, 5, "fixed handler records the depth that produced the fail-high");
    std::cout << "PASS fail-high preserve (Nf3 cp " << full4.score << " kept as Bc4 cp " << buggy.score
              << " by the old handler; fixed publishes cp " << fixed.score << ")\n";
    forge::tune::AspirationDelta = saved_delta;
    forge::search_fixes().aspiration = true;
}

void test_aspiration_nodes_unchanged() {
    const std::string fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    forge::search_fixes().aspiration = false;
    const forge::SearchInfo legacy = search_depth(fen, 5);
    forge::search_fixes().aspiration = true;
    const forge::SearchInfo fixed = search_depth(fen, 5);
    expect_eq(static_cast<int>(fixed.nodes), static_cast<int>(legacy.nodes),
              "opening the stuck-window case does not change a normal depth-5 search");
    expect(fixed.best_move == legacy.best_move, "normal depth-5 move matches");
    expect_eq(fixed.score, legacy.score, "normal depth-5 score matches");
    std::cout << "PASS aspiration node match (" << fixed.nodes << " nodes, "
              << forge::Board::move_to_uci(fixed.best_move) << ")\n";
}

void test_shallow_singular_survives() {
    const int saved = forge::tune::SingularDepth;
    forge::tune::SingularDepth = 2;
    const forge::SearchInfo info = search_depth("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4);
    expect(!info.best_move.is_none(), "SingularDepth 2 depth 4 returns a move");
    forge::tune::SingularDepth = saved;
    std::cout << "PASS shallow singular search (" << forge::Board::move_to_uci(info.best_move) << ")\n";
}

// std::clamp(value, 1, new_depth) is undefined when new_depth < 1. The reduced
// search now requires new_depth >= 1. This records the precondition the old
// call violated for a singular extension of -2 at depth 2: new_depth = -1.
bool reduction_clamp_defined(int new_depth) { return new_depth >= 1; }

void test_reduction_precondition() {
    expect(!reduction_clamp_defined(0), "depth 0 re-search must not clamp against hi < lo");
    expect(!reduction_clamp_defined(-1), "singular extension -2 at depth 2 used to clamp against hi = -1");
    expect(reduction_clamp_defined(1), "a one-ply re-search is a valid clamp range");
    std::cout << "PASS reduction clamp precondition\n";
}

void test_mate_in_one() {
    const std::string fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4";
    const forge::SearchInfo info = search_depth(fen, 2);
    expect(forge::is_mate_score(info.score) && info.score > 0, "depth 2 finds the mate");
    expect(forge::Board::move_to_uci(info.best_move) == "h5f7", "the mating move is Qxf7");
    std::cout << "PASS mate in one (" << forge::Board::move_to_uci(info.best_move) << " score " << info.score << ")\n";
}

} // namespace

std::uint64_t bench_nodes(bool nnue, int depth) {
    constexpr std::array<const char*, 8> fens = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    forge::nnue::enabled = nnue;
    forge::Searcher searcher(16, 1);
    std::uint64_t total = 0;
    for (const char* fen : fens) {
        forge::SearchLimits limits;
        limits.depth = depth;
        searcher.clear();
        total += searcher.search(board_from(fen), limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
    }
    return total;
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "isolate") {
        const int depth = argc > 2 ? std::atoi(argv[2]) : 11;
        for (int mask = 0; mask < 8; ++mask) {
            forge::search_fixes().mate_horizon = (mask & 1) != 0;
            forge::search_fixes().aspiration = (mask & 2) != 0;
            forge::search_fixes().qsearch_shallow_bound = (mask & 4) != 0;
            const auto hce = bench_nodes(false, depth);
            const auto net = bench_nodes(true, depth);
            std::cout << "mask " << mask << " hce " << hce << " nnue " << net << '\n';
        }
        return 0;
    }
    forge::nnue::enabled = false;
    test_window_arithmetic();
    test_reduction_precondition();
    test_mate_horizon();
    test_qsearch_shallow_bound();
    test_partial_pv();
    test_fail_high_kept();
    test_aspiration_nodes_unchanged();
    test_shallow_singular_survives();
    test_mate_in_one();
    if (failures != 0) {
        std::cerr << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "ALL PASS\n";
    return 0;
}
