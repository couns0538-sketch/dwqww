#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace {

int g_failures = 0;

void expect(bool condition, std::string_view name) {
    if (condition) {
        std::cout << "ok   " << name << '\n';
        return;
    }
    std::cout << "FAIL " << name << '\n';
    ++g_failures;
}

forge::Board board_from(std::string_view fen) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cerr << "bad fen: " << error << " | " << fen << '\n';
        std::exit(2);
    }
    return board;
}

forge::SearchInfo search_of(const forge::Board& board, int depth, std::uint64_t nodes = 0, bool nodes_specified = false) {
    forge::nnue::enabled = false;
    forge::Searcher searcher(16);
    forge::SearchLimits limits;
    limits.depth = depth;
    limits.nodes = nodes;
    limits.nodes_specified = nodes_specified;
    return searcher.search(board, limits);
}

} // namespace

namespace forge {

struct SearcherTestProbe {
    static void disarm(Worker& worker) {
        worker.all_workers_ = nullptr;
        worker.aborted_ = false;
        worker.node_limit_specified_ = false;
        worker.node_limit_ = 0;
        worker.pondering_ = false;
        worker.hard_limit_ms_ = 0;
        worker.soft_limit_ms_ = 0;
        worker.time_managed_ = false;
        worker.local_nodes_ = 1;
        worker.root_restricted_ = false;
#if FORGE_SPD_TT_NOTLS
        worker.tt_owned_ = false;
#endif
    }

    // Zero-window search at the root, after a normal search has built the stack.
    static int zero_window(Worker& worker, Board board, int depth, int beta) {
        disarm(worker);
        SearchStack* ss = &worker.stack_[4];
        ss->ply = 0;
        ss->excluded_move = Move::none();
        ss->current_move = Move::none();
        ss->null_move_allowed = true;
        ss->static_eval = ValueNone;
        ss->pv_length = 0;
        if (ss->continuation == nullptr) ss->continuation = &(*worker.continuation_history_)[Empty][0];
        (ss - 1)->continuation = ss->continuation;
        (ss - 2)->continuation = ss->continuation;
        (ss - 1)->current_move = Move::none();
        (ss - 2)->current_move = Move::none();
        (ss - 1)->static_eval = ValueNone;
        (ss - 2)->static_eval = ValueNone;
        (ss - 1)->moved_piece = Empty;
        (ss - 2)->moved_piece = Empty;
        return worker.search(board, ss, depth, beta - 1, beta, false);
    }

    static std::uint64_t pv_pruned(const Worker& worker) { return worker.pv_moves_pruned_; }
    static std::uint64_t qs_pv_pruned(const Worker& worker) { return worker.qs_pv_moves_pruned_; }
};

} // namespace forge

namespace {

void plant(forge::TranspositionTable& tt, std::uint64_t key, int score, int depth) {
    const forge::TTProbe probe = tt.probe(key);
    tt.store(probe, key, score, 0, forge::Move::none(), depth, forge::BoundExact, false, 0);
}

int cutoff_score(std::string_view fen, int stored, int depth) {
    forge::nnue::enabled = false;
    forge::Searcher searcher(8);
    forge::Board board = board_from(fen);
    forge::SearchLimits warmup;
    warmup.depth = 1;
    (void)searcher.search(board, warmup);
    searcher.clear_hash();
    plant(searcher.transposition_table(), board.key(), stored, 10);
    return forge::SearcherTestProbe::zero_window(searcher.main_worker(), board, depth, 1);
}

void test_aspiration_window() {
    constexpr int kInfinite = 32001;
    constexpr int kLastExact = 31990;
    constexpr int kAlpha = 31972;
    constexpr int kBeta = 32001;
    constexpr int kFailLow = 31950;
    constexpr int kDelta = 18;
    const forge::AspirationWindow locked = forge::aspiration_fail_low(
        kAlpha, kBeta, kFailLow, kDelta, kLastExact, false);
    const forge::AspirationWindow kept = forge::aspiration_fail_low(
        kAlpha, kBeta, kFailLow, kDelta, kLastExact, true);
    const int midpoint = (kAlpha + kBeta) / 2;
    expect(locked.beta == midpoint, "fail-low midpoint matches the lock formula");
    expect(locked.beta < kLastExact, "clamped fail-low drops beta under the last exact score");
    expect(locked.alpha == kFailLow - kDelta, "fail-low alpha steps back by delta");
    expect(kept.beta >= kLastExact, "keep-exact holds beta at the last exact score");
    expect(kept.alpha < kept.beta, "kept window is non-empty");
    expect(kept.alpha == locked.alpha, "keep-exact does not change the lowered alpha");

    const forge::AspirationWindow ordinary = forge::aspiration_fail_low(-18, 18, -18, 18, 0, true);
    const forge::AspirationWindow ordinary_lock = forge::aspiration_fail_low(-18, 18, -18, 18, 0, false);
    expect(ordinary.alpha == ordinary_lock.alpha && ordinary.beta == ordinary_lock.beta,
           "unclamped fail-low window is unchanged by keep-exact");
    expect(ordinary.alpha > -kInfinite && ordinary.beta < kInfinite, "ordinary window stays inside the mate range");
}

void test_fifty_move_mate_bounds() {
    constexpr int kMateValue = 32000;
    const std::string fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 80 40";
    const int room = 99 - 80;
    const int accepted = cutoff_score(fen, kMateValue - room, 2);
    const int rejected_win = cutoff_score(fen, kMateValue - (room + 1), 2);
    const int rejected_loss = cutoff_score(fen, -(kMateValue - (room + 1)), 2);
    const int ordinary = cutoff_score(fen, 40, 2);
    expect(accepted == kMateValue - room, "mate that fits in the fifty-move room is still a TT cutoff");
    expect(!forge::is_mate_score(rejected_win), "winning mate past the fifty-move room is not a TT cutoff");
    expect(!forge::is_mate_score(rejected_loss), "losing mate past the fifty-move room is not a TT cutoff");
    expect(ordinary == 40, "a non-mate exact score is still a TT cutoff");
    std::cout << "     fifty-move samples: fit " << accepted << " win " << rejected_win
              << " loss " << rejected_loss << " cp " << ordinary << '\n';
}

struct PruneCounts {
    std::uint64_t main = 0;
    std::uint64_t quiescence = 0;
};

PruneCounts prune_counts(const forge::Board& board, int depth, int fix) {
    forge::nnue::enabled = false;
    forge::tune::PvBoundFix = fix;
    forge::Searcher searcher(16);
    forge::SearchLimits limits;
    limits.depth = depth;
    (void)searcher.search(board, limits);
    const forge::Worker& worker = searcher.main_worker();
    return {forge::SearcherTestProbe::pv_pruned(worker), forge::SearcherTestProbe::qs_pv_pruned(worker)};
}

void test_pv_pruning() {
    const forge::Board start = board_from(forge::Board::StandardStartFen);
    const PruneCounts locked = prune_counts(start, 7, 0);
    expect(locked.main > 0, "lock search prunes moves inside PV nodes");
    expect(locked.quiescence > 0, "lock quiescence prunes moves inside PV nodes");
    std::cout << "     pv moves pruned at depth 7, fix off: main " << locked.main
              << " quiescence " << locked.quiescence << '\n';
    const PruneCounts repaired = prune_counts(start, 7, 1);
    expect(repaired.main == 0 && repaired.quiescence == 0,
           "PvBoundFix does not prune moves inside PV nodes");

    const std::vector<std::string> fens = {
        std::string(forge::Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "rnbq1rk1/pppp1ppp/5n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQ - 0 6",
        "8/8/8/2k5/2p5/2K5/1R6/8 w - - 0 1",
    };
    int differences = 0;
    for (int depth : {7, 9}) {
        for (const std::string& fen : fens) {
            const forge::Board board = board_from(fen);
            forge::tune::PvBoundFix = 0;
            const forge::SearchInfo locked = search_of(board, depth);
            forge::tune::PvBoundFix = 1;
            const forge::SearchInfo repaired = search_of(board, depth);
            if (locked.score != repaired.score || !(locked.best_move == repaired.best_move)) {
                ++differences;
                std::cout << "     pv fix changes depth " << depth << " " << fen
                          << " lock " << locked.score << ' ' << forge::Board::move_to_uci(locked.best_move)
                          << " fix " << repaired.score << ' ' << forge::Board::move_to_uci(repaired.best_move)
                          << '\n';
            }
        }
    }
    expect(differences > 0, "PvBoundFix changes a root score or move on the sample");
    forge::tune::PvBoundFix = 0;
}

void test_unfinished_aspiration() {
    const std::vector<std::string> fens = {
        std::string(forge::Board::StandardStartFen),
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    };
    int stale = 0;
    for (const std::string& fen : fens) {
        const forge::Board board = board_from(fen);
        std::vector<forge::SearchInfo> full(9);
        for (int depth = 1; depth <= 8; ++depth) full[static_cast<std::size_t>(depth)] = search_of(board, depth);
        const std::uint64_t ceiling = full[8].nodes;
        for (std::uint64_t nodes = 40; nodes < ceiling; nodes = nodes * 3 / 2 + 1) {
            const forge::SearchInfo limited = search_of(board, 10, nodes, true);
            if (limited.depth <= 0 || limited.depth > 8) continue;
            const forge::SearchInfo& done = full[static_cast<std::size_t>(limited.depth)];
            if (limited.score == done.score && !(limited.best_move == done.best_move)) {
                ++stale;
                std::cout << "     stale best move at nodes " << nodes << " depth " << limited.depth
                          << " score " << limited.score << " move " << forge::Board::move_to_uci(limited.best_move)
                          << " completed " << forge::Board::move_to_uci(done.best_move) << " fen " << fen << '\n';
            }
        }
    }
    expect(stale == 0, "an unfinished aspiration re-search does not replace the best move with a stale score");
}

// Every defender reply is searched. White mates in two only if some first move
// leaves no reply that escapes a mate in one.
bool white_mates_in_two(forge::Board board, forge::Move* mate_move) {
    const forge::MoveList first = board.legal_moves();
    for (std::size_t i = 0; i < first.size(); ++i) {
        forge::Undo undo;
        (void)board.make_move(first[i], undo);
        const forge::MoveList replies = board.legal_moves();
        bool all_replies_mate = true;
        if (replies.empty()) all_replies_mate = board.in_check();
        for (std::size_t j = 0; j < replies.size() && all_replies_mate; ++j) {
            forge::Undo reply_undo;
            (void)board.make_move(replies[j], reply_undo);
            const forge::MoveList finishes = board.legal_moves();
            bool mate_in_one = false;
            for (std::size_t k = 0; k < finishes.size(); ++k) {
                forge::Undo finish_undo;
                (void)board.make_move(finishes[k], finish_undo);
                mate_in_one = board.legal_moves().empty() && board.in_check();
                board.unmake_move(finishes[k], finish_undo);
                if (mate_in_one) break;
            }
            board.unmake_move(replies[j], reply_undo);
            if (!mate_in_one) all_replies_mate = false;
        }
        board.unmake_move(first[i], undo);
        if (all_replies_mate) {
            if (mate_move != nullptr) *mate_move = first[i];
            return true;
        }
    }
    return false;
}

void test_mate_and_pv_fix_cost() {
    const forge::Board board = board_from("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1");
    forge::Move proven = forge::Move::none();
    expect(white_mates_in_two(board, &proven), "exhaustive search proves a mate in two");
    expect(forge::Board::move_to_uci(proven) == "g3g6", "the proven mate move is g3g6");

    forge::tune::PvBoundFix = 0;
    forge::tune::AspirationKeepExact = 0;
    const forge::SearchInfo locked = search_of(board, 7);
    expect(forge::is_mate_score(locked.score) && locked.score > 0, "lock depth 7 reports the mate");
    expect(forge::Board::move_to_uci(locked.best_move) == "g3g6", "lock depth 7 plays g3g6");

    forge::tune::PvBoundFix = 1;
    const forge::SearchInfo shallow = search_of(board, 7);
    const forge::SearchInfo deeper = search_of(board, 11);
    std::cout << "     PvBoundFix depth 7 score " << shallow.score << ' '
              << forge::Board::move_to_uci(shallow.best_move) << " nodes " << shallow.nodes
              << "; depth 11 score " << deeper.score << ' ' << forge::Board::move_to_uci(deeper.best_move)
              << " nodes " << deeper.nodes << '\n';
    // Searching the moves the lock skips, in the main search and in
    // quiescence, raises reductions on the quiet mate. Depth 7 no longer
    // proves it. The mate is still there at depth 11.
    expect(!forge::is_mate_score(shallow.score), "PvBoundFix depth 7 does not yet prove the mate");
    expect(forge::is_mate_score(deeper.score) && forge::Board::move_to_uci(deeper.best_move) == "g3g6",
           "PvBoundFix depth 11 still finds g3g6");
    forge::tune::PvBoundFix = 0;
}

void test_reproduced_node_limit() {
    const forge::Board start = board_from(forge::Board::StandardStartFen);
    forge::tune::PvBoundFix = 0;
    forge::tune::AspirationKeepExact = 0;
    const forge::SearchInfo depth5 = search_of(start, 5);
    const forge::SearchInfo limited = search_of(start, 10, 2066, true);
    std::cout << "     nodes 2066 depth " << limited.depth << " score " << limited.score
              << " move " << forge::Board::move_to_uci(limited.best_move) << '\n';
    expect(!(limited.score == depth5.score && !(limited.best_move == depth5.best_move)),
           "the depth-5 score is not reported on a different best move");
}

void test_keep_exact_smoke() {
    const forge::Board start = board_from(forge::Board::StandardStartFen);
    forge::tune::AspirationKeepExact = 0;
    const forge::SearchInfo locked = search_of(start, 8);
    forge::tune::AspirationKeepExact = 1;
    const forge::SearchInfo kept = search_of(start, 8);
    forge::tune::AspirationKeepExact = 0;
    expect(!kept.best_move.is_none(), "keep-exact search returns a move");
    std::cout << "     AspirationKeepExact depth 8 nodes " << locked.nodes << " -> " << kept.nodes
              << " score " << locked.score << " -> " << kept.score << '\n';
}

} // namespace

int main() {
    test_aspiration_window();
    test_fifty_move_mate_bounds();
    test_pv_pruning();
    test_unfinished_aspiration();
    test_mate_and_pv_fix_cost();
    test_reproduced_node_limit();
    test_keep_exact_smoke();
    if (g_failures != 0) {
        std::cout << g_failures << " failed\n";
        return 1;
    }
    std::cout << "all passed\n";
    return 0;
}
