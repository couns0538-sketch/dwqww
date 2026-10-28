// UCI IntendedThreefold (FIDE 9.2.1 intended-move threefold claim, GitHub issue #7): board-level claim
// detection against a make_move() brute-force reference, the non-root search/quiescence floor, and the
// transposition-table and statistics guards at claim nodes.
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

namespace forge {
// Non-root search at ply 1 with an explicit window (same probe as tests/rule50_tests.cpp): worker
// state is reset, the transposition table is kept.
struct SearcherTestProbe {
    static Worker& prepare(Searcher& searcher, const Board& board) {
        auto& worker = searcher.main_worker();
        worker.clear();
        worker.shared_.stop.store(false, std::memory_order_relaxed);
        worker.shared_.ponder_hit_ns.store(0, std::memory_order_relaxed);
        worker.all_workers_ = nullptr;
        worker.aborted_ = false;
        worker.local_nodes_ = 0;
        worker.nodes_.store(0, std::memory_order_relaxed);
        worker.node_limit_ = 0;
        worker.node_limit_specified_ = false;
        worker.hard_limit_ms_ = worker.soft_limit_ms_ = 0;
        worker.time_managed_ = worker.pondering_ = false;
        worker.start_ = std::chrono::steady_clock::now();
        worker.seldepth_ = 0;
        worker.root_history_index_ = board.history_size() - 1;
        return worker;
    }
    static int search(Worker& worker, Board& board, int depth, int alpha, int beta) {
        auto* ss = &worker.stack_[5];
        ss->ply = 1;
        nnue::refresh(board, ss->accumulator);
        return depth == 0 ? worker.qsearch(board, ss, alpha, beta)
                          : worker.search(board, ss, depth, alpha, beta, false);
    }
    static int run(Searcher& searcher, Board board, int depth, int alpha, int beta) {
        Worker& worker = prepare(searcher, board);
        return search(worker, board, depth, alpha, beta);
    }
    // As run(), with the two plies before the node set to the given quiet moves (piece = the piece now on
    // the move's target square): null-move pruning becomes possible and a fail-low continuation bonus of
    // the node has a parent move and a target entry.
    static int run_after(Searcher& searcher, Board board, int depth, int alpha, int beta, Move parent,
                         Move grandparent) {
        Worker& worker = prepare(searcher, board);
        auto& history = *worker.continuation_history_;
        SearchStack& p = worker.stack_[4];
        p.current_move = parent;
        p.moved_piece = board.piece_at(parent.to);
        p.continuation = &history[static_cast<std::size_t>(p.moved_piece)][parent.to];
        SearchStack& g = worker.stack_[3];
        g.current_move = grandparent;
        g.moved_piece = board.piece_at(grandparent.to);
        g.continuation = &history[static_cast<std::size_t>(g.moved_piece)][grandparent.to];
        return search(worker, board, depth, alpha, beta);
    }
    // The continuation-history entry that a fail-low bonus of the node writes.
    static int parent_bonus(Searcher& searcher, const Board& board, Move parent, Move grandparent) {
        const auto& history = *searcher.main_worker().continuation_history_;
        return history[static_cast<std::size_t>(board.piece_at(grandparent.to))][grandparent.to]
                      [static_cast<std::size_t>(board.piece_at(parent.to))][parent.to];
    }
    // True when no pawn or material correction entry of `side` was taught.
    static bool correction_untouched(Searcher& searcher, Color side) {
        const auto& worker = searcher.main_worker();
        const auto zero = [](std::int32_t value) { return value == 0; };
        const auto& pawn = (*worker.correction_history_)[static_cast<std::size_t>(side)];
        const auto& material = (*worker.material_correction_)[static_cast<std::size_t>(side)];
        return std::all_of(pawn.begin(), pawn.end(), zero) && std::all_of(material.begin(), material.end(), zero);
    }
};
} // namespace forge

namespace {

int failures = 0;

void check(bool condition, const std::string& message) {
    std::cout << (condition ? "PASS " : "FAIL ") << message << '\n';
    if (!condition) ++failures;
}

forge::Board line(std::string_view fen, std::string_view moves) {
    forge::Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid FEN");
    std::size_t start = 0;
    while (start < moves.size()) {
        std::size_t end = moves.find(' ', start);
        if (end == std::string_view::npos) end = moves.size();
        const auto move = board.parse_uci(moves.substr(start, end - start));
        if (!move.has_value()) throw std::runtime_error("illegal move in fixture");
        forge::Undo undo;
        (void)board.make_move(*move, undo);
        start = end + 1;
    }
    return board;
}

forge::Move uci_move(std::string_view fen, std::string_view moves, std::string_view text) {
    forge::Board board = line(fen, moves);
    const auto move = board.parse_uci(text);
    if (!move.has_value()) throw std::runtime_error("illegal move in fixture");
    return *move;
}

// Reference: make every legal move and count earlier occurrences of the new key, same side to move,
// inside the new position's reversible window (fixtures without null moves).
bool reference_claim(forge::Board board) {
    for (const forge::Move move : board.legal_moves()) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        const auto& history = board.key_history();
        const std::ptrdiff_t last = static_cast<std::ptrdiff_t>(history.size()) - 1;
        const std::ptrdiff_t lo = last - board.halfmove_clock();
        int count = 0;
        for (std::ptrdiff_t i = last - 2; i >= 0 && i >= lo; i -= 2) {
            if (history[static_cast<std::size_t>(i)] == board.key()) ++count;
        }
        board.unmake_move(move, undo);
        if (count >= 2) return true;
    }
    return false;
}

// The claim node kept no usable score: no entry, or the placeholder (raw score ValueNone, BoundUpper,
// depth 0) that keeps only a move and the static evaluation.
bool no_score_stored(forge::Searcher& searcher, std::uint64_t key) {
    const auto probe = searcher.transposition_table().probe(key);
    return !probe.hit || (probe.entry.score == forge::ValueNone && probe.entry.bound() == forge::BoundUpper &&
                          probe.entry.depth == 0);
}

std::string window_tag(int depth, int alpha, int beta) {
    return " (depth " + std::to_string(depth) + ", window " + std::to_string(alpha) + "," + std::to_string(beta) + ")";
}

constexpr std::string_view IssueFen = "8/7k/8/8/8/8/8/K1R5 w - - 0 1";
constexpr std::string_view Positive = "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8 a2a1";
constexpr std::string_view Control = "a1b1 h7h8 b1b2 h8h7 b2a2 h7h8 a2a1";
// Fixtures in which the claiming side has material, so pruning and captures matter (code review: with a
// bare king the claiming move is always searched and a forced draw in qsearch is never wrong).
// QR: black (rook against queen) may claim with b8b7; at depth 1 the claiming quiet move is pruned.
constexpr std::string_view QrFen = "7k/1r6/8/8/8/8/8/K2Q4 w - - 0 1";
constexpr std::string_view QrMoves = "a1a2 b7b8 a2a1 b8b7 a1a2 b7b8 a2a1";
// QC: black may claim with h8h7 but wins the queen with Rc8xc1+, worth far more than the draw.
constexpr std::string_view QcFen = "2r5/7k/8/8/8/8/8/K1Q5 w - - 0 1";
constexpr std::string_view QcMoves = "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8 a2a1";
// WC: white (queen against rook) may claim with a2a1; its stand pat and best quiet move are far above 0.
constexpr std::string_view WcFen = "7k/1r6/8/8/8/8/8/K2Q4 b - - 0 1";
constexpr std::string_view WcMoves = "h8g8 a1a2 g8h8 a2a1 h8g8 a1a2 g8h8";

void board_tests() {
    const forge::Board positive = line(IssueFen, Positive);
    const forge::Board control = line(IssueFen, Control);
    check(positive.key() == control.key() && positive.halfmove_clock() == 7 && control.halfmove_clock() == 7,
          "issue fixture: positive and control reach the same key with halfmove clock 7");
    check(!positive.is_repetition() && !control.is_repetition(), "neither current position is already threefold");
    check(positive.can_claim_threefold_by_next_move() && reference_claim(positive),
          "positive history: h8h7 would create the third occurrence (claim)");
    check(!control.can_claim_threefold_by_next_move() && !reference_claim(control),
          "control history: h8h7 creates only the second occurrence (no claim)");

    const forge::Board current_only = line("7k/8/8/8/8/8/8/K1R5 b - - 7 4", "");
    check(current_only.key() == positive.key(), "historyless board has the same key as the positive end");
    check(!current_only.can_claim_threefold_by_next_move(), "same FEN without history: no claim");

    const std::uint64_t key = positive.key();
    const std::size_t size = positive.history_size();
    const bool first = positive.can_claim_threefold_by_next_move();
    const bool second = positive.can_claim_threefold_by_next_move();
    check(first && second && positive.key() == key && positive.history_size() == size,
          "the claim query leaves the board unchanged and is repeatable");

    forge::Board nulls = positive;
    forge::NullUndo n1;
    forge::NullUndo n2;
    nulls.make_null_move(n1);
    nulls.make_null_move(n2);
    check(nulls.key() == positive.key(), "two null moves return to the same key");
    check(!nulls.can_claim_threefold_by_next_move(), "history before a null move is not scanned (no claim)");
    nulls.unmake_null_move(n2);
    nulls.unmake_null_move(n1);
    check(nulls.can_claim_threefold_by_next_move(), "undoing the null moves restores the claim");

    // Castling rights: the start-looking position with rights must not count for the one without.
    constexpr std::string_view Castle = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1";
    const forge::Board two = line(Castle, "e1f1 e8f8 f1e1 f8e8 e1f1 e8f8 f1e1 f8e8");
    check(!two.can_claim_threefold_by_next_move() && !reference_claim(two),
          "lost castling rights: the earlier position with rights is a different position (no claim)");
    const forge::Board three = line(Castle, "e1f1 e8f8 f1e1 f8e8 e1f1 e8f8 f1e1 f8e8 e1f1 e8f8 f1e1 f8e8");
    check(three.can_claim_threefold_by_next_move() && reference_claim(three),
          "same rights twice before: e1f1 would create the third occurrence (claim)");

    // Material fixtures used by the search tests below.
    for (const auto& [fen, moves, name] : {std::tuple{QrFen, QrMoves, "QR: black (rook) may claim with b8b7"},
                                           std::tuple{QcFen, QcMoves, "QC: black may claim with h8h7"},
                                           std::tuple{WcFen, WcMoves, "WC: white (queen) may claim with a2a1"}}) {
        const forge::Board board = line(fen, moves);
        check(!board.is_repetition() && !board.in_check() && board.can_claim_threefold_by_next_move() &&
                  reference_claim(board), std::string("material fixture ") + name);
    }
}

// Random shuffling games from several positions: compare the claim with the reference at every ply.
void random_cross_check() {
    const std::vector<std::string_view> fens = {
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "4k3/8/8/3n4/8/8/8/2B1K2R w K - 0 1",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    };
    std::mt19937_64 rng(20261027);
    int compared = 0;
    int claims = 0;
    int mismatches = 0;
    for (int game = 0; game < 600; ++game) {
        forge::Board board;
        if (!board.set_fen(fens[static_cast<std::size_t>(game) % fens.size()])) throw std::runtime_error("fen");
        std::vector<forge::Move> played;
        for (int ply = 0; ply < 80; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) break;
            forge::Move move = legal[static_cast<std::size_t>(rng() % legal.size())];
            // Undo the own previous move most of the time, so positions repeat.
            if (played.size() >= 2 && rng() % 4 != 0) {
                const forge::Move previous = played[played.size() - 2];
                for (const forge::Move candidate : legal) {
                    if (candidate.from == previous.to && candidate.to == previous.from && !candidate.is_capture() &&
                        !candidate.is_promotion() && !candidate.is_castle()) {
                        move = candidate;
                        break;
                    }
                }
            }
            forge::Undo undo;
            (void)board.make_move(move, undo);
            played.push_back(move);
            if (board.is_repetition()) break;
            const bool claim = board.can_claim_threefold_by_next_move();
            const bool reference = reference_claim(board);
            ++compared;
            claims += claim ? 1 : 0;
            if (claim != reference) ++mismatches;
        }
    }
    std::cout << "random cross-check: " << compared << " positions, " << claims << " claims, " << mismatches
              << " mismatches\n";
    check(mismatches == 0 && claims >= 100 && compared - claims >= 1000,
          "claim equals the make_move reference on random shuffling games (both outcomes exercised)");
}

struct Window {
    int alpha;
    int beta;
};

void search_tests() {
    using forge::Infinite;
    using forge::SearcherTestProbe;
    const forge::Board positive = line(IssueFen, Positive);
    const forge::Board control = line(IssueFen, Control);
    // (-1,1) and (-50,1) collapse to the null window (0,1) at a claim node.
    const std::vector<Window> windows = {{-Infinite, Infinite}, {-1, 0}, {0, 1}, {-500, -499}, {100, 101},
                                         {-1000, 1000}, {-1, 1}, {-50, 1}};

    for (const int depth : {0, 1, 2}) {
        for (const Window w : windows) {
            const std::string tag = window_tag(depth, w.alpha, w.beta);
            forge::options::intended_threefold = false;
            forge::Searcher off_a(4, 1);
            forge::Searcher off_b(4, 1);
            const int positive_off = SearcherTestProbe::run(off_a, positive, depth, w.alpha, w.beta);
            const int control_off = SearcherTestProbe::run(off_b, control, depth, w.alpha, w.beta);
            forge::options::intended_threefold = true;
            forge::Searcher on_a(4, 1);
            forge::Searcher on_b(4, 1);
            const int positive_on = SearcherTestProbe::run(on_a, positive, depth, w.alpha, w.beta);
            const int control_on = SearcherTestProbe::run(on_b, control, depth, w.alpha, w.beta);
            // With the claim the value is max(0, value without it): a window that contains 0 (or lies below
            // it) must return exactly 0; a window above 0 must fail low at a value in [0, alpha].
            bool floor_ok = positive_on >= 0;
            if (w.beta <= 0 || (w.alpha < 0 && w.beta > 0)) floor_ok = floor_ok && positive_on == 0;
            else floor_ok = floor_ok && positive_on <= w.alpha;
            if (w.alpha == -Infinite) floor_ok = floor_ok && positive_on == std::max(0, positive_off);
            check(floor_ok, "positive: the claim is a draw-score floor" + tag + " -> " + std::to_string(positive_on));
            check(control_on == control_off, "control: unchanged by the option" + tag);
            if (depth == 0 && w.alpha == -Infinite) {
                std::cout << "qsearch full window: positive off " << positive_off << " on " << positive_on
                          << ", control off " << control_off << " on " << control_on << '\n';
                check(positive_off < -100 && positive_on == 0 && control_on == control_off && control_off < -100,
                      "issue numbers: positive 0 cp with the option, control unchanged");
            }
        }
    }

    // TT warmed in both history orders (same key, different history).
    forge::options::intended_threefold = true;
    forge::Searcher fresh(4, 1);
    const int control_fresh = SearcherTestProbe::run(fresh, control, 0, -Infinite, Infinite);
    forge::Searcher warm(4, 1);
    (void)SearcherTestProbe::run(warm, control, 0, -Infinite, Infinite);
    const auto stored = warm.transposition_table().probe(control.key());
    check(stored.hit && stored.entry.score != forge::ValueNone, "control qsearch stores a scored entry for the shared key");
    check(SearcherTestProbe::run(warm, positive, 0, -Infinite, Infinite) == 0,
          "TT warmed by the control history: the positive claim node ignores the cached score (0)");
    forge::Searcher warm2(4, 1);
    check(SearcherTestProbe::run(warm2, positive, 0, -Infinite, Infinite) == 0, "positive first: 0");
    const auto placeholder = warm2.transposition_table().probe(positive.key());
    check(placeholder.hit && placeholder.entry.score == forge::ValueNone && placeholder.entry.bound() == forge::BoundUpper &&
              placeholder.entry.depth == 0 && placeholder.entry.eval != forge::ValueNone,
          "the claim node stores only a placeholder: static eval, raw score ValueNone, BoundUpper, depth 0");
    check(SearcherTestProbe::run(warm2, control, 0, -Infinite, Infinite) == control_fresh,
          "TT warmed by the positive history: control equals a fresh search");
    // Non-PV windows take TT cutoffs: after the control history cached its score for the shared key, the
    // positive claim node must still answer from the floor (a value in [0, alpha]).
    for (const int depth : {0, 1, 2}) {
        for (const Window w : {Window{0, 1}, Window{100, 101}, Window{-50, -49}}) {
            forge::Searcher warmed(4, 1);
            (void)SearcherTestProbe::run(warmed, control, depth, -Infinite, Infinite);
            const int r = SearcherTestProbe::run(warmed, positive, depth, w.alpha, w.beta);
            const bool ok = w.beta <= 0 ? r == 0 : (r >= 0 && r <= w.alpha);
            check(ok, "TT warmed by the control, null window (" + std::to_string(w.alpha) + "," +
                          std::to_string(w.beta) + ") depth " + std::to_string(depth) + ": no cached cutoff -> " +
                          std::to_string(r));
        }
    }

    // Mate precedence: a claim node whose side to move mates in one keeps the mate. The node itself is a
    // first occurrence; Ra3-a2 would recreate (Ra2, Kh8, black to move) for the third time; Ra3-a8 mates.
    const forge::Board mating = line("7k/8/6K1/8/8/8/8/R7 w - - 0 1", "a1a2 h8g8 a2a1 g8h8 a1a2 h8g8 a2a3 g8h8");
    check(!mating.is_repetition() && mating.can_claim_threefold_by_next_move() && reference_claim(mating),
          "mate fixture: white may claim (a3a2 would be the third occurrence)");
    for (const bool on : {false, true}) {
        forge::options::intended_threefold = on;
        forge::Searcher searcher(4, 1);
        const int score = SearcherTestProbe::run(searcher, mating, 1, -Infinite, Infinite);
        check(score >= forge::MateInMaxPly, std::string("mate in one beats the optional draw (option ") +
                                                (on ? "on" : "off") + ", score " + std::to_string(score) + ")");
    }
    forge::options::intended_threefold = false;
}

// The claiming side has material (code review): the search() floor must hold when the claiming quiet
// move is pruned, and the qsearch floor must not hide a winning capture.
void material_tests() {
    using forge::Infinite;
    using forge::SearcherTestProbe;
    const forge::Board qr = line(QrFen, QrMoves);
    const forge::Board qc = line(QcFen, QcMoves);
    for (const int depth : {1, 2, 3}) {
        for (const Window w : {Window{-Infinite, Infinite}, Window{-100, 100}, Window{-1, 1}, Window{100, 101}}) {
            forge::options::intended_threefold = false;
            forge::Searcher off(4, 1);
            const int value_off = SearcherTestProbe::run(off, qr, depth, w.alpha, w.beta);
            forge::options::intended_threefold = true;
            forge::Searcher on(4, 1);
            const int value_on = SearcherTestProbe::run(on, qr, depth, w.alpha, w.beta);
            const bool ok = w.alpha < 0 ? value_on == 0 : (value_on >= 0 && value_on <= w.alpha);
            check(ok, "QR: the search() floor holds although the claiming move is pruned" +
                          window_tag(depth, w.alpha, w.beta) + " -> on " + std::to_string(value_on) + ", off " +
                          std::to_string(value_off));
        }
    }
    for (const int depth : {0, 1, 2}) {
        forge::options::intended_threefold = false;
        forge::Searcher off(4, 1);
        const int value_off = SearcherTestProbe::run(off, qc, depth, -Infinite, Infinite);
        forge::options::intended_threefold = true;
        forge::Searcher on(4, 1);
        const int value_on = SearcherTestProbe::run(on, qc, depth, -Infinite, Infinite);
        check(value_on == value_off && value_on > 300,
              "QC: the claim is a floor, not a forced draw: Rxc1 keeps its value" +
                  window_tag(depth, -Infinite, Infinite) + " -> on " + std::to_string(value_on) + ", off " +
                  std::to_string(value_off));
    }
    forge::options::intended_threefold = false;
}

// No history-dependent score reaches the TT at a claim node, on every path that stores: the final stores of
// search() and qsearch() (placeholder only), the qsearch stand pat, ProbCut; and correction history is not
// taught by a claim node.
void store_guard_tests() {
    using forge::Infinite;
    using forge::SearcherTestProbe;
    forge::options::intended_threefold = true;
    const forge::Board positive = line(IssueFen, Positive);
    for (const int depth : {0, 1, 2, 3}) {
        for (const Window w : {Window{-Infinite, Infinite}, Window{0, 1}, Window{100, 101}, Window{-100, 100}, Window{-1, 1}}) {
            forge::Searcher searcher(4, 1);
            const int value = SearcherTestProbe::run(searcher, positive, depth, w.alpha, w.beta);
            check(no_score_stored(searcher, positive.key()),
                  "issue fixture: the claim node stores no score (final store)" + window_tag(depth, w.alpha, w.beta) +
                      " -> " + std::to_string(value));
        }
    }
    // Stand pat at a claim node: white (queen against rook) fails high on its static evaluation.
    const forge::Board wc = line(WcFen, WcMoves);
    for (const Window w : {Window{0, 1}, Window{100, 101}, Window{-100, 100}}) {
        forge::Searcher searcher(4, 1);
        const int value = SearcherTestProbe::run(searcher, wc, 0, w.alpha, w.beta);
        check(value >= w.beta && no_score_stored(searcher, wc.key()),
              "WC: a stand-pat fail high at a claim node stores no score" + window_tag(0, w.alpha, w.beta) + " -> " +
                  std::to_string(value));
    }
    // ProbCut at a claim node: black's Rc8xc1+ beats probcut_beta at depth >= 5 in a null window.
    const forge::Board qc = line(QcFen, QcMoves);
    for (const int depth : {5, 6}) {
        for (const Window w : {Window{0, 1}, Window{100, 101}}) {
            forge::Searcher searcher(4, 1);
            const int value = SearcherTestProbe::run(searcher, qc, depth, w.alpha, w.beta);
            check(value >= w.beta && no_score_stored(searcher, qc.key()),
                  "QC: a ProbCut fail high at a claim node stores no score" + window_tag(depth, w.alpha, w.beta) +
                      " -> " + std::to_string(value));
        }
    }
    // Correction history: at depth 1 the claim node (white to move) is the only white search node (no check
    // extension below depth 2), and its exact score from a quiet best move would teach the white
    // pawn/material correction without the guard.
    for (const int depth : {1}) {
        for (const bool on : {false, true}) {
            forge::options::intended_threefold = on;
            forge::Searcher searcher(4, 1);
            const int value = SearcherTestProbe::run(searcher, wc, depth, -Infinite, Infinite);
            const bool untouched = SearcherTestProbe::correction_untouched(searcher, forge::White);
            if (on) {
                check(untouched, "WC: a claim node does not teach correction history" +
                                     window_tag(depth, -Infinite, Infinite) + " -> " + std::to_string(value));
            } else {
                check(!untouched, "WC without the option: the same node teaches correction history (sanity)" +
                                      window_tag(depth, -Infinite, Infinite) + " -> " + std::to_string(value));
            }
        }
    }
    forge::options::intended_threefold = false;
}

// A claim node keeps a move and the static evaluation in a placeholder entry (raw score ValueNone). Such an
// entry must never act as a score: searches of the same key under another history equal a fresh search,
// whatever bound and depth the entry carries, and a claim node re-searched over its own placeholder keeps
// the floor.
void placeholder_tests() {
    using forge::Infinite;
    using forge::SearcherTestProbe;
    const forge::Board positive = line(IssueFen, Positive);
    const forge::Board control = line(IssueFen, Control);
    const std::vector<Window> windows = {{-Infinite, Infinite}, {0, 1}, {100, 101}, {-500, -499}, {-50, -49}};

    forge::options::intended_threefold = true;
    const auto clock = static_cast<std::uint16_t>(control.halfmove_clock());
    for (const int depth : {0, 1, 2, 3}) {
        for (const Window w : windows) {
            forge::Searcher searcher(4, 1);
            (void)SearcherTestProbe::run(searcher, positive, depth, -Infinite, Infinite);
            const auto entry = searcher.transposition_table().probe(positive.key());
            check(entry.hit && entry.entry.score == forge::ValueNone && entry.entry.bound() == forge::BoundUpper &&
                      entry.entry.depth == 0,
                  "the claim node leaves a placeholder (depth " + std::to_string(depth) + ")");
            // Only the placeholder, copied into an empty table: the same key under the control history (no
            // claim) must equal a fresh search.
            forge::Searcher isolated(4, 1);
            auto& tt = isolated.transposition_table();
            tt.store(tt.probe(control.key()), control.key(), entry.entry.score, entry.entry.eval, entry.entry.move,
                     entry.entry.depth, entry.entry.bound(), entry.entry.pv(), clock);
            forge::Searcher fresh(4, 1);
            const int control_fresh = SearcherTestProbe::run(fresh, control, depth, w.alpha, w.beta);
            const int control_isolated = SearcherTestProbe::run(isolated, control, depth, w.alpha, w.beta);
            check(control_isolated == control_fresh,
                  "placeholder from the positive history: control equals a fresh search" +
                      window_tag(depth, w.alpha, w.beta) + " -> " + std::to_string(control_isolated));
            // The claim node re-searched over its own placeholder (and its subtree's entries) keeps the floor.
            const int again = SearcherTestProbe::run(searcher, positive, depth, w.alpha, w.beta);
            const bool floor_ok = w.beta <= 0 || w.alpha < 0 ? again == 0 : (again >= 0 && again <= w.alpha);
            check(floor_ok, "claim node re-searched over its own placeholder keeps the floor" +
                                window_tag(depth, w.alpha, w.beta) + " -> " + std::to_string(again));
            if (depth == 2 && w.alpha == 0) {
                // Known limitation (also without placeholders): a non-claim ancestor of a claim node in the
                // positive search stores a score that contains the claim, and the control search reuses it.
                std::cout << "INFO known limitation, ancestor entries: control after the positive search"
                          << window_tag(depth, w.alpha, w.beta) << " -> "
                          << SearcherTestProbe::run(searcher, control, depth, w.alpha, w.beta) << ", fresh "
                          << control_fresh << '\n';
            }
        }
    }

    // Synthetic entries with a raw ValueNone score at depth 60, every bound: no cutoff, no eval refinement, no
    // null-move veto, no ProbCut veto, no singular extension. WC with the option off (material, no claim),
    // after two quiet plies so null-move pruning is live; the entry's move is none, its eval ValueNone.
    forge::options::intended_threefold = false;
    const forge::Board wc = line(WcFen, WcMoves);
    const forge::Move parent = uci_move(WcFen, "h8g8 a1a2 g8h8 a2a1 h8g8 a1a2", "g8h8");
    const forge::Move grandparent = uci_move(WcFen, "h8g8 a1a2 g8h8 a2a1 h8g8", "a1a2");
    const forge::Move some_move = uci_move(WcFen, WcMoves, "d1d8");
    for (const int depth : {0, 1, 3, 5, 7, 8}) {
        for (const Window w : {Window{-Infinite, Infinite}, Window{0, 1}, Window{300, 301}, Window{-300, -299}}) {
            forge::Searcher fresh(4, 1);
            const int expected = SearcherTestProbe::run_after(fresh, wc, depth, w.alpha, w.beta, parent, grandparent);
            std::vector<int> with_move;
            for (const forge::Bound bound : {forge::BoundUpper, forge::BoundLower, forge::BoundExact}) {
                forge::Searcher searcher(4, 1);
                auto& tt = searcher.transposition_table();
                tt.store(tt.probe(wc.key()), wc.key(), forge::ValueNone, forge::ValueNone, forge::Move::none(), 60, bound,
                         false, static_cast<std::uint16_t>(wc.halfmove_clock()));
                const int value = SearcherTestProbe::run_after(searcher, wc, depth, w.alpha, w.beta, parent, grandparent);
                check(value == expected, "a ValueNone entry (bound " + std::to_string(static_cast<int>(bound)) +
                                             ", depth 60) is never used as a score" + window_tag(depth, w.alpha, w.beta) +
                                             " -> " + std::to_string(value) + ", fresh " + std::to_string(expected));
                // Same entry with a hash move: the bound must not matter either (singular extension and the
                // null-move veto read the bound only together with a usable score).
                forge::Searcher moved(4, 1);
                auto& tt2 = moved.transposition_table();
                tt2.store(tt2.probe(wc.key()), wc.key(), forge::ValueNone, forge::ValueNone, some_move, 60, bound, false,
                          static_cast<std::uint16_t>(wc.halfmove_clock()));
                with_move.push_back(SearcherTestProbe::run_after(moved, wc, depth, w.alpha, w.beta, parent, grandparent));
            }
            check(with_move[0] == with_move[1] && with_move[1] == with_move[2],
                  "a ValueNone entry with a hash move gives the same value for every bound" +
                      window_tag(depth, w.alpha, w.beta) + " -> " + std::to_string(with_move[0]));
        }
    }
}

// FailLowContinuationBonus (a tunable, default 0): a node that fails low rewards the parent's quiet move.
// When the claim floor raised alpha the value 0 lies inside the original window, which is no fail low.
void fail_low_bonus_tests() {
    using forge::SearcherTestProbe;
    const int saved = forge::tune::FailLowContinuationBonus;
    forge::tune::FailLowContinuationBonus = 100;
    const forge::Board positive = line(IssueFen, Positive);
    const forge::Move parent = uci_move(IssueFen, "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8", "a2a1");
    const forge::Move grandparent = uci_move(IssueFen, "a1a2 h7h8 a2a1 h8h7 a1a2", "h7h8");
    struct Case {
        bool on;
        int alpha;
        int beta;
        bool bonus;
        const char* what;
    };
    for (const int depth : {1, 2}) {
        for (const Case c : {Case{false, 50, 100, true, "option off, value below alpha: fail low, bonus (sanity)"},
                             Case{true, -100, 100, false, "option on, floor raised alpha: value 0 inside the window, no bonus"},
                             Case{true, 50, 100, true, "option on, alpha already above 0: fail low, bonus"}}) {
            forge::options::intended_threefold = c.on;
            forge::Searcher searcher(4, 1);
            const int value = SearcherTestProbe::run_after(searcher, positive, depth, c.alpha, c.beta, parent, grandparent);
            const int bonus = SearcherTestProbe::parent_bonus(searcher, positive, parent, grandparent);
            check((bonus != 0) == c.bonus, std::string("fail-low continuation bonus: ") + c.what +
                                               window_tag(depth, c.alpha, c.beta) + " -> value " +
                                               std::to_string(value) + ", parent entry " + std::to_string(bonus));
        }
    }
    forge::tune::FailLowContinuationBonus = saved;
    forge::options::intended_threefold = false;
}

} // namespace

int main() {
    try {
        board_tests();
        random_cross_check();
        search_tests();
        material_tests();
        store_guard_tests();
        placeholder_tests();
        fail_low_bonus_tests();
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        return 2;
    }
    std::cout << (failures == 0 ? "ALL PASS" : "FAILURES: " + std::to_string(failures)) << '\n';
    return failures == 0 ? 0 : 1;
}
