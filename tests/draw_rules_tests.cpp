// R3-5 draw-rule regression set: twofold repetition inside the search, threefold repetition through the game
// history, the GitHub issue #7 intended-threefold claim (UCI IntendedThreefold, FIDE 9.2.1) with the option off
// and on, and the 50-move rule (draw at half-move 100, mate delivered on the 100th half-move is still mate, the
// counter is reset by captures and pawn moves). Exact expectations throughout: draws are exactly 0, mates exactly
// MateValue - plies, and history that cannot matter gives exactly the value of a search without it.
// Fixtures were calibrated on the R3 stack (opus_r3/R3-5/README.md); tests/intended_threefold_tests.cpp (S-IT)
// and tests/rule50_tests.cpp hold the deeper option- and TT-level checks of the same rules.
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

namespace forge {
// Non-root search of `board` at ply 1 with the search root at key-history index `root_index` (worker state
// reset as in tests/rule50_tests.cpp; the transposition table is kept).
struct SearcherTestProbe {
    static int run(Searcher& searcher, Board board, int depth, int alpha, int beta, std::size_t root_index) {
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
        worker.root_history_index_ = root_index;
        auto* ss = &worker.stack_[5];
        ss->ply = 1;
        nnue::refresh(board, ss->accumulator);
        return depth == 0 ? worker.qsearch(board, ss, alpha, beta) : worker.search(board, ss, depth, alpha, beta, false);
    }
};
}  // namespace forge

namespace {

using forge::Board;
using forge::Infinite;
using forge::MateValue;
using forge::SearcherTestProbe;

int failures = 0;
int checks = 0;

void check(bool condition, const std::string& message) {
    ++checks;
    std::cout << (condition ? "PASS " : "FAIL ") << message << '\n';
    if (!condition) ++failures;
}

Board line(std::string_view fen, std::string_view moves) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid FEN: " + std::string(fen));
    std::size_t start = 0;
    while (start < moves.size()) {
        std::size_t end = moves.find(' ', start);
        if (end == std::string_view::npos) end = moves.size();
        const auto move = board.parse_uci(moves.substr(start, end - start));
        if (!move.has_value()) throw std::runtime_error("illegal fixture move " + std::string(moves.substr(start, end - start)));
        forge::Undo undo;
        (void)board.make_move(*move, undo);
        start = end + 1;
    }
    return board;
}

// A fresh single-thread searcher per call: no TT or history carried between searches.
forge::SearchInfo search(const Board& board, int depth, std::initializer_list<std::string_view> only = {},
                         std::size_t hash_mb = 16) {
    forge::Searcher searcher(hash_mb, 1);
    forge::SearchLimits limits;
    limits.depth = depth;
    Board copy = board;
    for (const std::string_view text : only) {
        const auto move = copy.parse_uci(text);
        if (!move.has_value()) throw std::runtime_error("illegal searchmoves fixture " + std::string(text));
        limits.search_moves_specified = true;
        limits.search_moves.push_back(*move);
    }
    return searcher.search(board, limits);
}

bool is_legal(const Board& board, forge::Move move) {
    const forge::MoveList legal = board.legal_moves();
    return std::find(legal.begin(), legal.end(), move) != legal.end();
}

std::string uci(forge::Move move) { return Board::move_to_uci(move); }

std::string tag(int depth) { return " (depth " + std::to_string(depth) + ")"; }

struct Window {
    int alpha;
    int beta;
};

// ---------------------------------------------------------------------------------------------------------------
// Twofold repetition inside the search: a position that already occurred at or after the search root is a draw at
// its second occurrence; occurrences before the root need two (threefold).
void twofold_in_search() {
    std::cout << "== twofold repetition inside the search\n";
    constexpr std::string_view Krk = "4k3/8/8/8/8/8/8/R3K3 w - - 0 1";
    const Board back = line(Krk, "a1a2 e8d8 a2a1 d8e8");  // the start position again (history index 4)
    check(back.is_repetition(0) && !back.is_repetition(back.history_size() - 1) && !back.is_repetition(),
          "board: second occurrence is a draw with the root at index 0 only; not a game-level threefold");
    Board fresh;
    if (!fresh.set_fen("4k3/8/8/8/8/8/8/R3K3 w - - 4 3")) throw std::runtime_error("fresh FEN");
    for (const int depth : {0, 1, 2, 3, 4}) {
        for (const Window w : {Window{-Infinite, Infinite}, Window{-1, 1}, Window{100, 101}, Window{-300, -299}}) {
            const std::string where = tag(depth) + " window " + std::to_string(w.alpha) + "," + std::to_string(w.beta);
            forge::Searcher in_search(16, 1);
            const int draw = SearcherTestProbe::run(in_search, back, depth, w.alpha, w.beta, 0);
            check(draw == 0, "root at the first occurrence: the repetition scores exactly 0" + where + " -> " +
                                 std::to_string(draw));
            forge::Searcher before_root(16, 1);
            forge::Searcher no_history(16, 1);
            const int value = SearcherTestProbe::run(before_root, back, depth, w.alpha, w.beta, back.history_size() - 1);
            const int expected = SearcherTestProbe::run(no_history, fresh, depth, w.alpha, w.beta, fresh.history_size() - 1);
            check(value == expected && (w.alpha != -Infinite || value > 300),
                  "one occurrence before the root is no draw: value equals the history-free search" + where + " -> " +
                      std::to_string(value) + ", fresh " + std::to_string(expected));
        }
    }
    // Perpetual check: white (a rook down) forces a repetition with queen checks; the twofold rule scores the
    // search line as a draw long before a third occurrence fits into the depth.
    constexpr std::string_view Perpetual = "6k1/5p1p/8/8/8/8/qr1Q4/7K w - - 0 1";
    Board perpetual;
    if (!perpetual.set_fen(Perpetual)) throw std::runtime_error("perpetual FEN");
    for (const int depth : {8, 10, 12}) {
        const forge::SearchInfo info = search(perpetual, depth);
        check(info.score == 0 && is_legal(perpetual, info.best_move) && perpetual.gives_check(info.best_move),
              "perpetual check: score exactly 0 with a checking move" + tag(depth) + " -> " + std::to_string(info.score) +
                  " " + uci(info.best_move));
    }
    const forge::SearchInfo quiet = search(perpetual, 10, {"h1g1"});
    check(quiet.score < -300, "perpetual control: a quiet king move loses (" + std::to_string(quiet.score) + ")");
}

// ---------------------------------------------------------------------------------------------------------------
// Threefold repetition through the game history.
constexpr std::string_view IssueFen = "8/7k/8/8/8/8/8/K1R5 w - - 0 1";  // GitHub issue #7
constexpr std::string_view PositiveBefore = "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8";  // white to move; the start occurred twice
constexpr std::string_view ControlBefore = "a1b1 h7h8 b1b2 h8h7 b2a2 h7h8";   // same position, the start once
constexpr std::string_view ControlFen = "7k/8/8/8/8/8/K7/2R5 w - - 6 4";       // that position without history

void threefold_by_history() {
    std::cout << "== threefold repetition through the game history\n";
    const std::string_view start = Board::StandardStartFen;
    const Board third = line(start, "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8");
    const Board second = line(start, "g1f3 g8f6 f3g1 f6g8");
    check(third.is_repetition() && !second.is_repetition(), "board: third occurrence is threefold, second is not");
    const forge::SearchInfo drawn = search(third, 8);
    check(drawn.score == 0 && drawn.nodes == 0 && drawn.depth == 8 && is_legal(third, drawn.best_move),
          "root at the third occurrence: draw without a search, still a legal move (" + uci(drawn.best_move) + ")");
    const forge::SearchInfo searched = search(second, 4);
    check(searched.nodes > 0 && is_legal(second, searched.best_move), "root at the second occurrence is searched");

    // Inside the search: after Ra2-a1 black's Kh8-h7 recreates the start position for the third time (two
    // occurrences before the root), so the restricted root move is a draw from depth 2 on; with the start position
    // only once in the history the same search equals the history-free one.
    const Board positive = line(IssueFen, PositiveBefore);
    const Board control = line(IssueFen, ControlBefore);
    Board history_free;
    if (!history_free.set_fen(ControlFen)) throw std::runtime_error("control FEN");
    check(positive.key() == control.key() && control.key() == history_free.key(),
          "issue fixture roots: same position (key) with and without the history");
    for (const int depth : {2, 3, 4}) {
        const int p = search(positive, depth, {"a2a1"}).score;
        const int c = search(control, depth, {"a2a1"}).score;
        const int f = search(history_free, depth, {"a2a1"}).score;
        check(p == 0, "history threefold reached in the search scores exactly 0" + tag(depth) + " -> " + std::to_string(p));
        check(c == f && c > 100, "one earlier occurrence: equals the history-free search" + tag(depth) + " -> " +
                                     std::to_string(c) + ", fresh " + std::to_string(f));
    }
}

// ---------------------------------------------------------------------------------------------------------------
// GitHub issue #7 (FIDE 9.2.1 intended threefold), UCI IntendedThreefold off (default) and on.
void intended_threefold_issue7() {
    std::cout << "== issue #7: intended threefold claim, IntendedThreefold off / on\n";
    const bool saved = forge::options::intended_threefold;
    // The issue's form: non-root quiescence search at ply 1, one worker, 4 MiB hash, full window, black to move
    // after a2a1. Only the positive history lets Kh8-h7 create the third occurrence.
    const Board positive = line(IssueFen, std::string(PositiveBefore) + " a2a1");
    const Board control = line(IssueFen, std::string(ControlBefore) + " a2a1");
    int value[2][2] = {};  // [option][positive = 0, control = 1]
    for (const bool on : {false, true}) {
        forge::options::intended_threefold = on;
        forge::Searcher a(4, 1);
        forge::Searcher b(4, 1);
        value[on][0] = SearcherTestProbe::run(a, positive, 0, -Infinite, Infinite, positive.history_size() - 1);
        value[on][1] = SearcherTestProbe::run(b, control, 0, -Infinite, Infinite, control.history_size() - 1);
    }
    std::cout << "issue #7 qsearch at ply 1: off positive " << value[0][0] << " control " << value[0][1]
              << ", on positive " << value[1][0] << " control " << value[1][1] << '\n';
    check(value[0][0] == value[0][1] && value[0][1] < -100, "option off: positive equals control (no claim), both < -100");
    check(value[1][0] == 0, "option on: positive history claims exactly 0");
    check(value[1][1] == value[0][1], "option on: control unchanged");

    // The UCI form (tools/uci_regression.py): white to move, `go depth 1 searchmoves a2a1`.
    const Board positive_root = line(IssueFen, PositiveBefore);
    const Board control_root = line(IssueFen, ControlBefore);
    int root[2][2] = {};
    for (const bool on : {false, true}) {
        forge::options::intended_threefold = on;
        root[on][0] = search(positive_root, 1, {"a2a1"}).score;
        root[on][1] = search(control_root, 1, {"a2a1"}).score;
    }
    std::cout << "issue #7 root depth 1 searchmoves a2a1: off positive " << root[0][0] << " control " << root[0][1]
              << ", on positive " << root[1][0] << " control " << root[1][1] << '\n';
    check(root[0][0] == root[0][1] && root[0][0] > 100, "root, option off: positive equals control (> 100)");
    check(root[1][0] == 0 && root[1][1] == root[0][1], "root, option on: positive exactly 0, control unchanged");
    for (const int depth : {2, 3}) {
        forge::options::intended_threefold = false;
        const int control_off = search(control_root, depth, {"a2a1"}).score;
        forge::options::intended_threefold = true;
        const int positive_on = search(positive_root, depth, {"a2a1"}).score;
        const int control_on = search(control_root, depth, {"a2a1"}).score;
        check(positive_on == 0 && control_on == control_off,
              "root, option on: positive 0, control unchanged" + tag(depth) + " -> " + std::to_string(positive_on) +
                  ", control " + std::to_string(control_on) + " / " + std::to_string(control_off));
    }
    forge::options::intended_threefold = saved;
}

// ---------------------------------------------------------------------------------------------------------------
// 50-move rule.
void fifty_move_rule() {
    std::cout << "== 50-move rule\n";
    // A quiet move that makes the counter 100 is a draw (also with check); a pawn move resets it.
    Board rook;
    if (!rook.set_fen("7k/8/8/8/8/8/1P6/K5R1 w - - 99 80")) throw std::runtime_error("rook FEN");
    for (const int depth : {1, 2, 3, 4}) {
        const int quiet = search(rook, depth, {"g1g2"}).score;
        const int checking = search(rook, depth, {"g1h1"}).score;
        check(quiet == 0 && checking == 0, "half-move 100 after a quiet move (with or without check) is exactly 0" +
                                                tag(depth) + " -> " + std::to_string(quiet) + ", " + std::to_string(checking));
    }
    const forge::SearchInfo pawn = search(rook, 3, {"b2b3"});
    check(pawn.score > 300, "a pawn move resets the counter: winning score " + std::to_string(pawn.score));
    const forge::SearchInfo best = search(rook, 4);
    check((uci(best.best_move) == "b2b3" || uci(best.best_move) == "b2b4") && best.score > 300,
          "unrestricted: a resetting pawn move is chosen (" + uci(best.best_move) + ", " + std::to_string(best.score) + ")");

    // A capture resets the counter: Kxb2 is the only move that is not a draw.
    Board capture;
    if (!capture.set_fen("7k/8/8/8/8/8/1r6/K1R5 w - - 99 80")) throw std::runtime_error("capture FEN");
    check(search(capture, 3, {"c1c2"}).score == 0, "half-move 100 after a quiet rook move is exactly 0");
    const forge::SearchInfo take = search(capture, 3, {"a1b2"});
    check(take.score > 300, "a capture resets the counter: winning score " + std::to_string(take.score));
    const forge::SearchInfo take_best = search(capture, 4);
    check(uci(take_best.best_move) == "a1b2" && take_best.score > 300,
          "unrestricted: the resetting capture is chosen (" + uci(take_best.best_move) + ")");

    // Mate delivered on the 100th half-move is still mate (both colours); the same quiet non-mating move is a draw.
    for (const auto& [fen, mate, other] : {std::tuple<std::string_view, std::string_view, std::string_view>{
                                               "6k1/5ppp/8/8/8/8/8/4R1K1 w - - 99 80", "e1e8", "g1f1"},
                                           std::tuple<std::string_view, std::string_view, std::string_view>{
                                               "4r1k1/8/8/8/8/8/5PPP/6K1 b - - 99 80", "e8e1", "g8f8"}}) {
        Board board;
        if (!board.set_fen(fen)) throw std::runtime_error("mate FEN");
        const forge::SearchInfo restricted = search(board, 1, {mate});
        const forge::SearchInfo full = search(board, 4);
        check(restricted.score == MateValue - 1 && full.score == MateValue - 1 && uci(full.best_move) == mate,
              std::string("mate on the 100th half-move scores MateValue - 1: ") + std::string(fen) + " -> " +
                  std::to_string(restricted.score) + ", " + std::to_string(full.score) + " " + uci(full.best_move));
        check(search(board, 3, {other}).score == 0, std::string("a non-mating quiet move there is exactly 0: ") + std::string(other));
    }

    // Roots: a checkmated root at half-move 100 is mate, not a draw; any other root at >= 100 is a draw, without a
    // search, even with a mate in one available (the documented root adjudication, src/search/iterative.inc).
    Board mated;
    if (!mated.set_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 100 80")) throw std::runtime_error("mated FEN");
    const forge::SearchInfo mated_info = search(mated, 4);
    check(mated_info.score == -MateValue && mated_info.best_move.is_none(), "checkmated root at half-move 100 is mate 0");
    Board adjudicated;
    if (!adjudicated.set_fen("6k1/5ppp/8/8/8/8/8/4R1K1 w - - 100 80")) throw std::runtime_error("root FEN");
    const forge::SearchInfo root = search(adjudicated, 6);
    check(root.score == 0 && root.nodes == 0 && is_legal(adjudicated, root.best_move),
          "root at half-move 100 is a draw without a search and still moves (" + uci(root.best_move) + ")");

    // Board level: which moves reset the counter (57 -> 0) and which advance it (57 -> 58); unmake restores it.
    struct Reset {
        std::string_view fen;
        std::string_view move;
        int expected;
    };
    const Reset resets[] = {
        {"4k3/8/8/8/8/8/8/R3K3 w - - 57 40", "a1a5", 58},       // quiet rook move
        {"4k3/8/8/8/8/8/8/R3K2R w KQ - 57 40", "e1g1", 58},     // short castling
        {"4k3/8/8/8/8/8/8/R3K2R w KQ - 57 40", "e1c1", 58},     // long castling
        {"4k3/8/8/8/8/8/r7/R3K3 w - - 57 40", "a1a2", 0},       // capture
        {"4k3/8/8/8/8/8/4P3/4K3 w - - 57 40", "e2e3", 0},       // single pawn push
        {"4k3/8/8/8/8/8/4P3/4K3 w - - 57 40", "e2e4", 0},       // double pawn push
        {"4k3/8/8/3pP3/8/8/8/4K3 w - d6 57 40", "e5d6", 0},     // en passant
        {"4k3/1P6/8/8/8/8/8/4K3 w - - 57 40", "b7b8q", 0},      // promotion
        {"r3k3/1P6/8/8/8/8/8/4K3 w - - 57 40", "b7a8n", 0},     // capture-promotion
        {"4k3/8/8/8/8/8/8/R3K3 b - - 57 40", "e8d7", 58},       // black quiet king move
        {"r3k3/8/8/8/8/8/R7/4K3 b - - 57 40", "a8a2", 0},       // black capture
        {"4k3/8/8/8/3pP3/8/8/4K3 b - e3 57 40", "d4e3", 0},     // black en passant
    };
    for (const Reset& r : resets) {
        Board board;
        if (!board.set_fen(r.fen)) {
            check(false, std::string("reset fixture parses: ") + std::string(r.fen));
            continue;
        }
        const auto move = board.parse_uci(r.move);
        if (!move.has_value()) {
            check(false, std::string("reset fixture move is legal: ") + std::string(r.move) + " in " + std::string(r.fen));
            continue;
        }
        forge::Undo undo;
        (void)board.make_move(*move, undo);
        const int after = board.halfmove_clock();
        board.unmake_move(*move, undo);
        check(after == r.expected && board.halfmove_clock() == 57,
              std::string("counter after ") + std::string(r.move) + " in " + std::string(r.fen) + ": " + std::to_string(after));
    }
}

}  // namespace

int main() {
    try {
        twofold_in_search();
        threefold_by_history();
        intended_threefold_issue7();
        fifty_move_rule();
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        return 2;
    }
    std::cout << "draw rules: " << checks << " checks, " << failures << " failures\n";
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " forge_draw_rules_tests\n";
    return failures == 0 ? 0 : 1;
}
