// UCI IntendedThreefold (FIDE 9.2.1 intended-move threefold claim, GitHub issue #7): board-level claim
// detection against a make_move() brute-force reference, and the non-root search/quiescence floor.
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
#include <vector>

namespace forge {
// Non-root search at ply 1 with an explicit window (same probe as tests/rule50_tests.cpp): worker
// state is reset, the transposition table is kept.
struct SearcherTestProbe {
    static int run(Searcher& searcher, Board board, int depth, int alpha, int beta) {
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
        auto* ss = &worker.stack_[5];
        ss->ply = 1;
        nnue::refresh(board, ss->accumulator);
        return depth == 0 ? worker.qsearch(board, ss, alpha, beta)
                          : worker.search(board, ss, depth, alpha, beta, false);
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

constexpr std::string_view IssueFen = "8/7k/8/8/8/8/8/K1R5 w - - 0 1";
constexpr std::string_view Positive = "a1a2 h7h8 a2a1 h8h7 a1a2 h7h8 a2a1";
constexpr std::string_view Control = "a1b1 h7h8 b1b2 h8h7 b2a2 h7h8 a2a1";

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

void search_tests() {
    using forge::Infinite;
    using forge::SearcherTestProbe;
    const forge::Board positive = line(IssueFen, Positive);
    const forge::Board control = line(IssueFen, Control);
    struct Window {
        int alpha;
        int beta;
    };
    const std::vector<Window> windows = {{-Infinite, Infinite}, {-1, 0}, {0, 1}, {-500, -499}, {100, 101}, {-1000, 1000}};

    for (const int depth : {0, 1, 2}) {
        for (const Window w : windows) {
            const std::string tag = " (depth " + std::to_string(depth) + ", window " + std::to_string(w.alpha) +
                                    "," + std::to_string(w.beta) + ")";
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
    check(stored.hit, "control qsearch stores an entry for the shared key");
    check(SearcherTestProbe::run(warm, positive, 0, -Infinite, Infinite) == 0,
          "TT warmed by the control history: the positive claim node ignores the cached score (0)");
    forge::Searcher warm2(4, 1);
    check(SearcherTestProbe::run(warm2, positive, 0, -Infinite, Infinite) == 0, "positive first: 0");
    check(!warm2.transposition_table().probe(positive.key()).hit, "the claim node stores nothing");
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

} // namespace

int main() {
    try {
        board_tests();
        random_cross_check();
        search_tests();
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        return 2;
    }
    std::cout << (failures == 0 ? "ALL PASS" : "FAILURES: " + std::to_string(failures)) << '\n';
    return failures == 0 ? 0 : 1;
}
