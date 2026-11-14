// t20: same commands, same result.
//
// Links the engine and drives it the way the UCI loop does with Threads 1,
// Hash 16 and the book off (the book lives in uci.cpp and is not consulted
// for depth or nodes searches):
//   ucinewgame -> Searcher::clear()
//   position   -> Board::set_fen()
//   go         -> Searcher::reset_stop() then Searcher::search()
//
// Ground-truth mate distances come from a separate minimax in this file,
// not from the engine's own score.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static int generation(Searcher& searcher) { return searcher.transposition_table().generation(); }
    static bool hit(Searcher& searcher, std::uint64_t key) { return searcher.transposition_table().probe(key).hit; }
    static int hashfull(Searcher& searcher) { return searcher.transposition_table().hashfull(); }
    static int main_history_nonzero(Worker& worker) {
        int count = 0;
        for (const auto& side : *worker.main_history_) {
            for (const auto& from : side) {
                for (const std::int16_t value : from) {
                    if (value != 0) ++count;
                }
            }
        }
        return count;
    }
};
} // namespace forge

namespace {

struct Signature {
    forge::Move move{};
    int score = 0;
    std::uint64_t nodes = 0;

    [[nodiscard]] bool operator==(const Signature& other) const {
        return move == other.move && score == other.score && nodes == other.nodes;
    }
};

struct MateCase {
    const char* name;
    const char* fen;
    int mate; // moves, side-to-move sign: +N mates, -N is mated
    bool krk;
    bool kqk;
};

struct TerminalCase {
    const char* name;
    const char* fen;
    bool checkmate;
};

[[nodiscard]] std::string format_score(int score) {
    if (forge::is_mate_score(score)) {
        const int distance = forge::MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

[[nodiscard]] int mate_number(int score) {
    if (!forge::is_mate_score(score)) return 0;
    const int distance = forge::MateValue - std::abs(score);
    const int mate = (distance + 1) / 2;
    return score > 0 ? mate : -mate;
}

[[nodiscard]] std::string move_text(forge::Move move) {
    if (move.is_none()) return "0000";
    return forge::Board::move_to_uci(move);
}

[[nodiscard]] forge::Board board_from_fen(std::string_view fen, std::string* error) {
    forge::Board board;
    if (!board.set_fen(fen, error)) return {};
    return board;
}

forge::SearchInfo go(forge::Searcher& searcher, const forge::Board& board, const forge::SearchLimits& limits, bool emit) {
    searcher.reset_stop();
    // uci.cpp runs each go with TTAccess::Exclusive when Threads is 1.
    return searcher.search(board, limits, emit, forge::Searcher::TTAccess::Exclusive);
}

[[nodiscard]] Signature signature_of(const forge::SearchInfo& info) {
    return Signature{info.best_move, info.score, info.nodes};
}

// Sound mate distance in moves, horizon `bound`. 0 means "not proven inside the horizon"
// (including stalemate). -1000 means the side to move is already checkmated.
class MateSolver {
public:
    [[nodiscard]] int solve(forge::Board& board, int bound) {
        if (bound < 1) {
            const forge::MoveList moves = board.legal_moves();
            if (moves.empty() && board.in_check()) return kCheckmate;
            return 0;
        }
        const Key key{board.key(), bound};
        if (const auto found = memo_.find(key); found != memo_.end()) return found->second;

        const forge::MoveList moves = board.legal_moves();
        if (moves.empty()) {
            const int result = board.in_check() ? kCheckmate : 0;
            memo_[key] = result;
            return result;
        }

        int best_win = 0;
        int best_loss = 0;
        bool all_losses = true;
        for (const forge::Move move : moves) {
            forge::Undo undo;
            if (!board.make_move(move, undo)) continue;
            const int got = score_after_move(board, bound);
            board.unmake_move(move, undo);
            if (got == 1) {
                memo_[key] = 1;
                return 1;
            }
            if (got > 0) {
                all_losses = false;
                if (best_win == 0 || got < best_win) best_win = got;
            } else if (got < 0) {
                if (best_loss == 0 || got < best_loss) best_loss = got;
            } else {
                all_losses = false;
            }
        }
        int result = 0;
        if (best_win > 0) result = best_win;
        else if (all_losses && best_loss < 0) result = best_loss;
        memo_[key] = result;
        return result;
    }

private:
    static constexpr int kCheckmate = -1000;
    struct Key {
        std::uint64_t key = 0;
        int bound = 0;
        [[nodiscard]] bool operator==(const Key& other) const { return key == other.key && bound == other.bound; }
    };
    struct KeyHash {
        [[nodiscard]] std::size_t operator()(const Key& key) const {
            return static_cast<std::size_t>(key.key ^ (static_cast<std::uint64_t>(key.bound) * 0x9E3779B97F4A7C15ULL));
        }
    };
    std::unordered_map<Key, int, KeyHash> memo_;

    [[nodiscard]] int score_after_move(forge::Board& board, int bound) {
        const forge::MoveList replies = board.legal_moves();
        if (replies.empty() && board.in_check()) return 1;
        const int child = solve(board, bound - 1);
        if (child == kCheckmate) return 1;
        if (child > 0) return -child;
        if (child < 0 && child > kCheckmate) return -child + 1;
        return 0;
    }
};

// Plies the minimax has to see. A mate in N for the side to move is 2*N-1 plies;
// a mate against the side to move is 2*|N| plies (the defender moves first).
[[nodiscard]] int mate_horizon(int mate) {
    return mate > 0 ? 2 * mate - 1 : 2 * -mate;
}

[[nodiscard]] bool move_keeps_mate(forge::Board board, forge::Move move, int mate, MateSolver& solver, std::string& why) {
    if (move.is_none()) {
        why = "no move";
        return false;
    }
    forge::Undo undo;
    if (!board.make_move(move, undo)) {
        why = "make_move failed";
        return false;
    }
    if (mate == 1) {
        const bool ok = board.in_check() && board.legal_moves().empty();
        if (!ok) why = "mate in 1 move did not checkmate";
        return ok;
    }
    if (mate > 1) {
        const int child = solver.solve(board, mate_horizon(-(mate - 1)));
        if (child != -(mate - 1)) {
            why = "after the move the defender's distance is " + std::to_string(child) +
                  ", expected " + std::to_string(-(mate - 1));
            return false;
        }
        return true;
    }
    const int child = solver.solve(board, mate_horizon(-mate));
    if (child != -mate) {
        why = "after the move the attacker's distance is " + std::to_string(child) +
              ", expected " + std::to_string(-mate);
        return false;
    }
    return true;
}

const std::array<const char*, 30> kRepeatFens{{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "8/8/8/4k3/8/3K4/7R/8 w - - 0 1",
    "8/8/4k3/8/8/8/3K4/7Q w - - 0 1",
    "8/8/8/k7/8/K7/P7/8 w - - 0 1",
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
    "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "8/2k5/8/2K5/8/8/2P5/8 w - - 0 1",
    "2k5/8/1K6/8/8/8/8/7R w - - 0 1",
    "8/8/8/8/8/6k1/4r3/6K1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
    "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
    "4k3/8/8/8/8/8/8/4K2R w K - 0 1",
    "8/8/8/3k4/8/8/4K3/R7 w - - 0 1",
    "8/k7/8/1K6/8/8/8/1R6 w - - 0 1",
    "7k/8/5K2/8/8/8/8/6Q1 w - - 0 1",
    "r2qkb1r/pp2nppp/3p4/2pP4/2P5/2N5/PP3PPP/R1BQKBNR w KQkq - 1 8",
    "8/8/8/8/1k6/8/1K6/2R5 w - - 0 1",
    "8/8/2k5/8/2K5/8/2P5/8 w - - 0 1",
    "1k1r4/pp1b1R2/3q2pp/4p3/2B5/4Q3/PPP2B2/2K5 b - - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    "8/8/8/8/8/1R6/8/k1K5 w - - 0 1",
    "8/8/8/8/3Q4/k7/8/1K6 w - - 0 1",
}};

const std::array<MateCase, 12> kMates{{
    {"KRK mate 1", "8/8/8/8/8/1R6/8/k1K5 w - - 0 1", 1, true, false},
    {"KQK mate 1", "8/8/8/8/8/8/8/k1KQ4 w - - 0 1", 1, false, true},
    {"KRK mate 2", "8/8/8/8/2R5/k7/8/1K6 w - - 0 1", 2, true, false},
    {"KQK mate 2", "8/8/8/8/3Q4/k7/8/1K6 w - - 0 1", 2, false, true},
    {"KRK mate 3", "8/8/8/8/8/8/8/k1K1R3 w - - 0 1", 3, true, false},
    {"KQK mate 3", "8/8/8/8/8/8/6Q1/K2k4 w - - 0 1", 3, false, true},
    {"KRK mate -1", "8/8/8/8/8/2R5/k7/2K5 b - - 0 1", -1, true, false},
    {"KQK mate -1", "8/8/8/8/8/8/8/k1KQ4 b - - 0 1", -1, false, true},
    {"KRK mate -2", "8/8/8/8/8/8/8/k1KR4 b - - 0 1", -2, true, false},
    {"KQK mate -2", "8/8/8/8/8/8/8/k1K1Q3 b - - 0 1", -2, false, true},
    {"KRK mate -3", "8/8/8/8/1R6/8/8/k1K5 b - - 0 1", -3, true, false},
    {"KQK mate -3", "8/8/8/8/8/8/6Q1/K1k5 b - - 0 1", -3, false, true},
}};

const std::array<TerminalCase, 3> kTerminals{{
    {"stalemate KPk", "4k3/4P3/4K3/8/8/8/8/8 b - - 0 1", false},
    {"stalemate KQk", "7k/5K2/6Q1/8/8/8/8/8 b - - 0 1", false},
    {"checkmate KQk", "k7/1Q6/1K6/8/8/8/8/8 b - - 0 1", true},
}};

int fail(const std::string& message) {
    std::cout << "FAIL " << message << std::endl;
    return 1;
}

int test_repeat(const std::vector<forge::Board>& boards, bool nodes_mode) {
    forge::Searcher searcher(16, 1);
    const char* mode = nodes_mode ? "nodes 5000" : "depth 10";
    int failures = 0;
    forge::SearchLimits measured;
    forge::SearchLimits dirty;
    if (nodes_mode) {
        measured.nodes = 5000;
        measured.nodes_specified = true;
        dirty.nodes = 4000;
        dirty.nodes_specified = true;
    } else {
        measured.depth = 10;
        dirty.depth = 8;
    }
    for (std::size_t i = 0; i < boards.size(); ++i) {
        std::array<Signature, 3> trials{};
        for (int trial = 0; trial < 3; ++trial) {
            for (int step = 1; step <= 4; ++step) {
                const forge::Board& other = boards[(i + static_cast<std::size_t>(step)) % boards.size()];
                (void)go(searcher, other, dirty, false);
            }
            searcher.clear();
            trials[static_cast<std::size_t>(trial)] = signature_of(go(searcher, boards[i], measured, false));
        }
        const bool same = trials[0] == trials[1] && trials[0] == trials[2];
        if (!same) {
            ++failures;
            std::cout << "FAIL repeat " << mode << " position " << i << std::endl;
            for (int trial = 0; trial < 3; ++trial) {
                const Signature& sig = trials[static_cast<std::size_t>(trial)];
                std::cout << "  trial " << (trial + 1) << " move " << move_text(sig.move)
                          << " score " << format_score(sig.score) << " nodes " << sig.nodes << std::endl;
            }
            std::cout << "  full engine output of the third search:" << std::endl;
            searcher.clear();
            (void)go(searcher, boards[i], measured, true);
        } else {
            std::cout << "PASS repeat " << mode << " [" << i << "] move " << move_text(trials[0].move)
                      << " score " << format_score(trials[0].score) << " nodes " << trials[0].nodes << std::endl;
        }
    }
    return failures;
}

int test_history_persists_inside_a_game() {
    forge::Searcher searcher(16, 1);
    std::string error;
    const forge::Board start = board_from_fen(forge::Board::StandardStartFen, &error);
    forge::SearchLimits limits;
    limits.depth = 10;
    searcher.clear();
    const Signature first = signature_of(go(searcher, start, limits, false));
    const Signature second = signature_of(go(searcher, start, limits, false));
    searcher.clear();
    const Signature third = signature_of(go(searcher, start, limits, false));
    if (!(first == third)) {
        return fail("ucinewgame did not restore the first depth-10 startpos search");
    }
    if (first == second) {
        return fail("a second search of the same game matched the first; history or the hash did not carry");
    }
    std::cout << "PASS in-game state carries: nodes " << first.nodes << " then " << second.nodes
              << ", after ucinewgame " << third.nodes << std::endl;
    return 0;
}

int test_hash_resize() {
    forge::Searcher searcher(16, 1);
    std::string error;
    const forge::Board start = board_from_fen(forge::Board::StandardStartFen, &error);
    const forge::Board other = board_from_fen(kRepeatFens[1], &error);
    if (!error.empty()) return fail("hash fens: " + error);
    forge::SearchLimits limits;
    limits.depth = 8;
    searcher.clear();
    (void)go(searcher, start, limits, false);
    (void)go(searcher, other, limits, false);
    const int filled_generation = forge::SearcherTestProbe::generation(searcher);
    const bool filled_hit = forge::SearcherTestProbe::hit(searcher, start.key());
    const int history_before = forge::SearcherTestProbe::main_history_nonzero(searcher.main_worker());
    if (filled_generation == 0 || !filled_hit || history_before == 0) {
        return fail("setup did not fill the hash and history");
    }
    searcher.resize_hash(16);
    const int resized_generation = forge::SearcherTestProbe::generation(searcher);
    const bool resized_hit = forge::SearcherTestProbe::hit(searcher, start.key());
    const int resized_full = forge::SearcherTestProbe::hashfull(searcher);
    const int history_after_resize = forge::SearcherTestProbe::main_history_nonzero(searcher.main_worker());
    if (resized_generation != 0 || resized_hit || resized_full != 0) {
        return fail("resize_hash did not empty the table the way ucinewgame does");
    }
    if (history_after_resize == 0) {
        return fail("resize_hash cleared history; only the hash table should reset");
    }

    (void)go(searcher, start, limits, false);
    searcher.clear_hash();
    const int cleared_generation = forge::SearcherTestProbe::generation(searcher);
    const bool cleared_hit = forge::SearcherTestProbe::hit(searcher, start.key());
    const int history_after_clear_hash = forge::SearcherTestProbe::main_history_nonzero(searcher.main_worker());
    if (cleared_generation != 0 || cleared_hit || history_after_clear_hash == 0) {
        return fail("Clear Hash did not match the observed hash-only reset");
    }

    forge::SearchLimits deep;
    deep.depth = 10;
    searcher.clear();
    const Signature after_clear = signature_of(go(searcher, start, deep, false));
    searcher.clear();
    searcher.resize_hash(32);
    searcher.resize_hash(16);
    const Signature after_resize = signature_of(go(searcher, start, deep, false));
    if (!(after_clear == after_resize)) {
        std::cout << "FAIL search after resize differs from search after ucinewgame" << std::endl;
        std::cout << "  clear  " << move_text(after_clear.move) << " " << format_score(after_clear.score)
                  << " nodes " << after_clear.nodes << std::endl;
        std::cout << "  resize " << move_text(after_resize.move) << " " << format_score(after_resize.score)
                  << " nodes " << after_resize.nodes << std::endl;
        return 1;
    }
    std::cout << "PASS hash resize: generation " << filled_generation << " -> 0, probe miss, hashfull 0, history kept ("
              << history_after_resize << " entries); Clear Hash generation " << cleared_generation
              << " probe miss, history kept (" << history_after_clear_hash
              << "); depth 10 after resize matches ucinewgame, nodes " << after_clear.nodes << std::endl;
    return 0;
}

int test_mates() {
    forge::Searcher searcher(16, 1);
    MateSolver solver;
    int failures = 0;
    int krk = 0;
    int kqk = 0;
    forge::SearchLimits limits;
    limits.depth = 8;
    for (const MateCase& mate_case : kMates) {
        if (mate_case.krk) ++krk;
        if (mate_case.kqk) ++kqk;
        std::string error;
        forge::Board board = board_from_fen(mate_case.fen, &error);
        if (!error.empty()) {
            ++failures;
            std::cout << "FAIL mate fen " << mate_case.name << ": " << error << std::endl;
            continue;
        }
        const int truth = solver.solve(board, mate_horizon(mate_case.mate));
        if (truth != mate_case.mate) {
            ++failures;
            std::cout << "FAIL ground truth " << mate_case.name << " solver " << truth
                      << " expected " << mate_case.mate << std::endl;
            continue;
        }
        searcher.clear();
        const forge::SearchInfo info = go(searcher, board, limits, false);
        const int got = mate_number(info.score);
        std::string why;
        const bool kept = got == mate_case.mate && move_keeps_mate(board, info.best_move, mate_case.mate, solver, why);
        if (got != mate_case.mate || !kept) {
            ++failures;
            std::cout << "FAIL " << mate_case.name << " expected mate " << mate_case.mate
                      << " got " << format_score(info.score) << " move " << move_text(info.best_move);
            if (!why.empty()) std::cout << " (" << why << ")";
            std::cout << std::endl << "full engine output:" << std::endl;
            searcher.clear();
            (void)go(searcher, board, limits, true);
            std::cout << "bestmove " << move_text(info.best_move) << std::endl;
        } else {
            std::cout << "PASS " << mate_case.name << " score " << format_score(info.score)
                      << " move " << move_text(info.best_move) << " keeps the mate" << std::endl;
        }
    }
    if (krk < 2 || kqk < 2) {
        ++failures;
        std::cout << "FAIL mate set has KRK " << krk << " KQK " << kqk << std::endl;
    }
    return failures;
}

int test_go_mate() {
    forge::Searcher searcher(16, 1);
    int failures = 0;
    std::string error;
    const forge::Board mate1 = board_from_fen("8/8/8/8/8/1R6/8/k1K5 w - - 0 1", &error);
    const forge::Board mate2 = board_from_fen("8/8/8/8/2R5/k7/8/1K6 w - - 0 1", &error);
    const forge::Board start = board_from_fen(forge::Board::StandardStartFen, &error);
    if (!error.empty()) return fail(error);

    auto run = [&](const char* label, const forge::Board& board, int mate_n) {
        forge::SearchLimits limits;
        limits.mate_moves = mate_n;
        searcher.clear();
        const forge::SearchInfo info = go(searcher, board, limits, false);
        const int cap = std::max(1, mate_n * 2 - 1);
        std::cout << "go mate " << mate_n << " " << label << ": depth " << info.depth
                  << " cap " << cap << " score " << format_score(info.score)
                  << " move " << move_text(info.best_move) << " nodes " << info.nodes << std::endl;
        if (info.depth > cap) {
            ++failures;
            std::cout << "FAIL " << label << " searched deeper than 2*N-1" << std::endl;
        }
        return info;
    };

    const forge::SearchInfo one = run("KRK mate in 1", mate1, 1);
    if (one.depth != 1 || mate_number(one.score) != 1) {
        ++failures;
        std::cout << "FAIL go mate 1 did not stop at mate in 1" << std::endl;
        searcher.clear();
        forge::SearchLimits limits;
        limits.mate_moves = 1;
        (void)go(searcher, mate1, limits, true);
    }
    const forge::SearchInfo early = run("KRK mate in 2", mate2, 6);
    if (mate_number(early.score) != 2 || early.depth >= 6 * 2 - 1) {
        ++failures;
        std::cout << "FAIL go mate 6 did not stop early on the mate in 2" << std::endl;
        searcher.clear();
        forge::SearchLimits limits;
        limits.mate_moves = 6;
        (void)go(searcher, mate2, limits, true);
    }
    const forge::SearchInfo capped = run("KRK mate in 2", mate2, 2);
    if (capped.depth != 3) {
        ++failures;
        std::cout << "FAIL go mate 2 did not stop at the depth cap" << std::endl;
    }
    const forge::SearchInfo none = run("startpos", start, 1);
    if (none.depth != 1 || forge::is_mate_score(none.score) || none.best_move.is_none()) {
        ++failures;
        std::cout << "FAIL go mate 1 from the start position" << std::endl;
    }
    if (failures == 0) std::cout << "PASS go mate" << std::endl;
    return failures;
}

int test_terminal() {
    forge::Searcher searcher(16, 1);
    int failures = 0;
    for (const TerminalCase& terminal : kTerminals) {
        std::string error;
        forge::Board board = board_from_fen(terminal.fen, &error);
        if (!error.empty()) {
            ++failures;
            std::cout << "FAIL terminal fen " << terminal.name << ": " << error << std::endl;
            continue;
        }
        const bool no_moves = board.legal_moves().empty();
        const bool in_check = board.in_check();
        if (!no_moves || in_check != terminal.checkmate) {
            ++failures;
            std::cout << "FAIL " << terminal.name << " legal moves or check flag is not the expected terminal"
                      << std::endl;
            continue;
        }
        forge::SearchLimits limits;
        limits.depth = 64;
        searcher.clear();
        const forge::SearchInfo info = go(searcher, board, limits, false);
        const bool move_ok = info.best_move.is_none();
        const bool score_ok = terminal.checkmate ? info.score == -forge::MateValue : info.score == 0;
        if (!move_ok || !score_ok || info.depth != 64) {
            ++failures;
            std::cout << "FAIL " << terminal.name << " move " << move_text(info.best_move)
                      << " score " << format_score(info.score) << " depth " << info.depth << std::endl;
            searcher.clear();
            (void)go(searcher, board, limits, true);
        } else {
            std::cout << "PASS " << terminal.name << " bestmove 0000 score " << format_score(info.score)
                      << " depth " << info.depth << std::endl;
        }
    }
    return failures;
}

} // namespace

int main() {
    std::cout << "t20 Searcher threads 1 hash 16 book off" << std::endl;
    std::vector<forge::Board> boards;
    boards.reserve(kRepeatFens.size());
    for (const char* fen : kRepeatFens) {
        std::string error;
        forge::Board board = board_from_fen(fen, &error);
        if (!error.empty()) {
            std::cout << "FAIL repeat fen: " << error << " | " << fen << std::endl;
            return 1;
        }
        boards.push_back(std::move(board));
    }
    int failures = 0;
    failures += test_repeat(boards, false);
    failures += test_repeat(boards, true);
    failures += test_history_persists_inside_a_game();
    failures += test_hash_resize();
    failures += test_mates();
    failures += test_go_mate();
    failures += test_terminal();
    if (failures != 0) {
        std::cout << "t20 result: FAIL " << failures << std::endl;
        return 1;
    }
    std::cout << "t20 result: PASS" << std::endl;
    return 0;
}
