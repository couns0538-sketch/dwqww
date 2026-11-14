#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace {

// Brute-force minimax mate judge over legal moves only (for N <= 3).
// Returns the smallest M in [1, max_moves] such that the side to move forces
// checkmate in at most M moves against every legal defense, or 0 if none exists.
int attacker_mate_in(forge::Board& board, std::size_t root_idx, int max_moves);

// Evaluates a single legal attacker move `m` already chosen at the current board.
// Returns the smallest M in [1, max_moves] forced by `m`, or 0 if the defender escapes.
int eval_attacker_move(forge::Board& board, std::size_t root_idx, const forge::Move& m, int max_moves) {
    forge::Undo u1;
    if (!board.make_move(m, u1)) return 0;

    const forge::MoveList replies = board.legal_moves();
    if (replies.empty()) {
        const bool mated = board.in_check();
        board.unmake_move(m, u1);
        return mated ? 1 : 0;
    }

    if (max_moves <= 1 || board.halfmove_clock() >= 100 ||
        board.is_repetition(root_idx) || board.is_insufficient_material()) {
        board.unmake_move(m, u1);
        return 0;
    }

    int worst_reply = 0;
    bool all_mated = true;
    for (const forge::Move r : replies) {
        forge::Undo u2;
        (void)board.make_move(r, u2);
        int sub = 0;
        if (board.halfmove_clock() < 100 && !board.is_repetition(root_idx) &&
            !board.is_insufficient_material() && !board.legal_moves().empty()) {
            sub = attacker_mate_in(board, root_idx, max_moves - 1);
        }
        board.unmake_move(r, u2);
        if (sub == 0) {
            all_mated = false;
            break;
        }
        worst_reply = std::max(worst_reply, sub);
    }

    board.unmake_move(m, u1);
    return all_mated ? (1 + worst_reply) : 0;
}

int attacker_mate_in(forge::Board& board, std::size_t root_idx, int max_moves) {
    if (max_moves <= 0) return 0;
    const forge::MoveList moves = board.legal_moves();
    if (moves.empty()) return 0;

    int best = 0;
    for (const forge::Move m : moves) {
        const int limit = best > 0 ? best - 1 : max_moves;
        if (limit <= 0) break;
        const int d = eval_attacker_move(board, root_idx, m, limit);
        if (d > 0 && (best == 0 || d < best)) {
            best = d;
            if (best == 1) break;
        }
    }
    return best;
}

int judge_mate_in(const forge::Board& root_board, int max_moves) {
    forge::Board copy = root_board;
    if (copy.legal_moves().empty() || copy.halfmove_clock() >= 100 ||
        copy.is_repetition() || copy.is_insufficient_material()) {
        return 0;
    }
    return attacker_mate_in(copy, copy.history_size() - 1, max_moves);
}

int judge_move_mate_in(const forge::Board& root_board, const forge::Move& move, int max_moves) {
    forge::Board copy = root_board;
    if (move.is_none() || !copy.is_pseudo_legal(move) || !copy.is_legal(move)) return 0;
    return eval_attacker_move(copy, copy.history_size() - 1, move, max_moves);
}

struct TestCase {
    const char* label;
    const char* fen;
    int query_n;
    bool expect_mate;
};

// 30 forced-mate positions (7 rook endings, 7 queen endings, 6 two-bishop endings,
// 10 constructed middlegame positions) + 10 positions with no mate in N.
const std::vector<TestCase>& test_cases() {
    static const std::vector<TestCase> cases = {
        // --- Rook endings (7) ---
        {"R1_krk_m1",   "7k/R7/6K1/8/8/8/8/8 w - - 0 1", 1, true},
        {"R2_krk_m2",   "8/8/8/8/2R5/k7/8/1K6 w - - 0 1", 2, true},
        {"R3_krk_b_m2", "8/8/8/8/5r2/7K/8/6k1 b - - 0 1", 2, true},
        {"R4_krk_m2",   "k7/8/2K5/1R6/8/8/8/8 w - - 0 1", 2, true},
        {"R5_krk_m3",   "k7/8/8/2K5/8/2R5/8/8 w - - 0 1", 3, true},
        {"R6_krk_b_m3", "8/8/5r2/8/5k2/8/8/7K b - - 0 1", 3, true},
        {"R7_krkp_m3",  "8/8/8/8/1R6/p1K5/8/k7 w - - 0 1", 3, true},

        // --- Queen endings (7) ---
        {"Q1_kqk_m1",   "7k/5K2/8/6Q1/8/8/8/8 w - - 0 1", 1, true},
        {"Q2_kqk_m2",   "8/8/8/4Q3/8/2K5/k7/8 w - - 0 1", 2, true},
        {"Q3_kqk_m2",   "k7/3Q4/8/1K6/8/8/8/8 w - - 0 1", 2, true},
        {"Q4_kqk_b_m2", "7K/4q3/8/6k1/8/8/8/8 b - - 0 1", 2, true},
        {"Q5_kqk_m3",   "7k/8/3K4/8/6Q1/8/8/8 w - - 0 1", 3, true},
        {"Q6_kqk_m3",   "k7/8/4K3/8/8/1Q6/8/8 w - - 0 1", 3, true},
        {"Q7_kqk_b_m3", "8/8/8/8/1q6/8/4k3/K7 b - - 0 1", 3, true},

        // --- Two-bishops endings (6) ---
        {"B1_kbbk_m1",  "k7/8/1K1B4/8/6B1/8/8/8 w - - 0 1", 1, true},
        {"B2_kbbk_m2",  "1k6/8/1K6/6B1/6B1/8/8/8 w - - 0 1", 2, true},
        {"B3_kbbk_m2",  "1k6/8/1K6/8/6BB/8/8/8 w - - 0 1", 2, true},
        {"B4_kbbk_b_m2","8/8/8/bb6/8/6k1/8/6K1 b - - 0 1", 2, true},
        {"B5_kbbk_m3",  "k7/8/1K6/8/6BB/8/8/8 w - - 0 1", 3, true},
        {"B6_kbbk_m3",  "k7/8/2K1B3/8/7B/8/8/8 w - - 0 1", 3, true},

        // --- Constructed middlegame positions (10) ---
        // MG1: Mate in 1 in middlegame (Qxf7#).
        {"MG1_m1",      "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 4 4", 1, true},
        // MG2: Quiet queen move 1. Qd4!! threatening Qg7# while down a rook + two pieces, mate in 2.
        {"MG2_quiet_m2","r1b3k1/p4b1p/np4pB/p2p1p2/4p3/5P2/PPP4P/3Q3K w - - 0 14", 2, true},
        // MG3: Smothered Queen sacrifice 1. Qg8+! Rxg8 2. Nf7# in middlegame, mate in 2.
        {"MG3_smoth_m2","r1b2r1k/ppp3pp/2np4/3QN3/2B1P3/8/PPP2PPP/R4RK1 w - - 0 12", 2, true},
        // MG4: Morphy Opera Game Queen sacrifice 1. Qb8+! Rd8 2. Rxd8#, mate in 2.
        {"MG4_opera_m2","4kb1r/p2r1ppp/4q3/4p1B1/4P3/1Q6/PPP2PPP/2KR4 w k - 0 16", 2, true},
        // MG5: Quiet queen intrusion 1. Qa6!! threatening Qb7# against queenside king, mate in 2.
        {"MG5_quiet_m2","1kr4r/p1p1qp1p/1pP3pn/3P4/8/3Q3P/P4PB1/1R3RK1 w - - 0 16", 2, true},
        // MG6: Double-check + smothered mate 1. Nh6+! Kh8 2. Qg8+! Rxg8 3. Nf7#, mate in 3.
        {"MG6_smoth_m3","r1b2rk1/ppp2Npp/2npQ3/4p3/4P3/1B6/PPP2PPP/R4RK1 w - - 0 12", 3, true},
        // MG7: Anastasia sacrifice 1. Ne7+ Kh8 2. Qxh7+! Kxh7 3. Rh3#, mate in 3.
        {"MG7_anast_m3","r1b2rk1/pppp1ppp/8/3N3Q/4P3/4R3/PPP2PPP/R5K1 w - - 0 12", 3, true},
        // MG8: Queen sacrifice on f7 + back-rank mate 1. Qxf7+! Rxf7 2. Rxe8+ Rf8 3. Rxf8#, mate in 3.
        {"MG8_sac_m3",  "r1b1nrk1/pp3p1p/q1p3pB/3Q2N1/8/8/PPP2PPP/3RR1K1 w - - 0 14", 3, true},
        // MG9: Quiet first move 1. Qf4!! while down material (1... Rg7 2. Qxf6 ... 3. Qxg7#), mate in 3.
        {"MG9_quiet_m3","r1b3rk/p2p3p/np3ppB/2p5/2P5/5P2/PP1Q3P/7K w - - 0 14", 3, true},
        // MG10: Black-to-move middlegame Anastasia mate in 3 (1... Ne2+ 2. Kh1 Qxh2+! 3. Kxh2 Rh6#).
        {"MG10_blk_m3", "r5k1/ppp2ppp/4r3/4p3/3n3q/8/PPPP1PPP/R1B2RK1 b - - 0 12", 3, true},

        // --- No mate in N (10) ---
        {"NM1_krk_not1",   "8/8/8/8/2R5/k7/8/1K6 w - - 0 1", 1, false},
        {"NM2_krk_not2",   "k7/8/4K3/8/1R6/8/8/8 w - - 0 1", 2, false},
        {"NM3_krk_not3",   "8/8/8/3k4/8/8/8/R3K3 w - - 0 1", 3, false},
        {"NM4_kqk_not3",   "8/8/8/3k4/8/8/8/Q3K3 w - - 0 1", 3, false},
        {"NM5_kbbk_not3",  "8/8/3k4/8/8/2BB4/8/4K3 w - - 0 1", 3, false},
        {"NM6_start_not2", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 2, false},
        {"NM7_kiwi_not3",  "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, false},
        {"NM8_def_not2",   "r1b2r1k/ppp2qpp/2np4/4N2Q/2B1P3/8/PPP2PPP/R4RK1 w - - 0 12", 2, false},
        {"NM9_stale_not3", "8/8/8/8/8/2k5/2p5/2K4R b - - 0 1", 3, false},
        {"NM10_mid_not3",  "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", 3, false},
    };
    return cases;
}

int parse_last_mate_score(const std::string& output, bool& found_mate_tag) {
    found_mate_tag = false;
    int last_mate = 0;
    std::istringstream in(output);
    std::string line;
    while (std::getline(in, line)) {
        const auto pos = line.find(" score mate ");
        if (pos != std::string::npos) {
            std::istringstream tail(line.substr(pos + 12));
            int m = 0;
            if (tail >> m) {
                found_mate_tag = true;
                last_mate = m;
            }
        }
    }
    return last_mate;
}

} // namespace

int main() {
    const auto& cases = test_cases();
    if (cases.size() != 40) {
        std::cerr << "Expected 40 test cases, got " << cases.size() << "\n";
        return 2;
    }

    int mate_cases = 0;
    int non_mate_cases = 0;
    int setup_errors = 0;

    for (const auto& tc : cases) {
        forge::Board board;
        std::string err;
        if (!board.set_fen(tc.fen, &err)) {
            std::cerr << "INVALID FEN [" << tc.label << "]: " << err << "\n";
            ++setup_errors;
            continue;
        }
        const int judged = judge_mate_in(board, tc.query_n);
        const bool expected_ok = tc.expect_mate ? (judged == tc.query_n) : (judged == 0);
        if (!expected_ok) {
            std::cerr << "JUDGE MISMATCH [" << tc.label << "] N=" << tc.query_n
                      << " expected_mate=" << tc.expect_mate << " judged=" << judged << "\n";
            ++setup_errors;
        }
        if (tc.expect_mate) ++mate_cases;
        else ++non_mate_cases;
    }

    if (setup_errors > 0 || mate_cases != 30 || non_mate_cases != 10) {
        std::cerr << "Dataset validation failed: errors=" << setup_errors
                  << " mate=" << mate_cases << " non_mate=" << non_mate_cases << "\n";
        return 2;
    }

    forge::Searcher searcher(16, 1);
    int missed_mates = 0;
    int false_mates = 0;
    int illegal_or_bad = 0;

    for (const auto& tc : cases) {
        forge::Board board;
        (void)board.set_fen(tc.fen);
        const int judged = judge_mate_in(board, tc.query_n);

        searcher.clear();
        forge::SearchLimits limits;
        limits.mate_moves = tc.query_n;

        std::ostringstream captured;
        std::streambuf* old_buf = std::cout.rdbuf(captured.rdbuf());
        const forge::SearchInfo info =
            searcher.search(board, limits, true, forge::Searcher::TTAccess::Exclusive);
        std::cout.rdbuf(old_buf);

        bool has_mate_uci = false;
        const int uci_mate = parse_last_mate_score(captured.str(), has_mate_uci);
        const std::string best_uci = info.best_move.is_none()
            ? "0000" : forge::Board::move_to_uci(info.best_move);

        if (info.best_move.is_none() || !board.is_legal(info.best_move)) {
            std::cout << "FAIL [" << tc.label << "] N=" << tc.query_n
                      << " illegal bestmove " << best_uci << "\n";
            ++illegal_or_bad;
            continue;
        }

        if (tc.expect_mate) {
            const int move_mate = judge_move_mate_in(board, info.best_move, tc.query_n);
            const bool score_ok = forge::is_mate_score(info.score) && info.score > 0 &&
                                  ((forge::MateValue - info.score + 1) / 2) <= tc.query_n &&
                                  has_mate_uci && uci_mate >= 1 && uci_mate <= tc.query_n;
            const bool move_ok = move_mate >= 1 && move_mate <= tc.query_n;
            if (!score_ok || !move_ok) {
                ++missed_mates;
                std::cout << "MISS [" << tc.label << "] N=" << tc.query_n
                          << " judge_min=" << judged
                          << " move=" << best_uci << " (mates_in=" << move_mate << ")"
                          << " score=" << info.score
                          << " uci_mate=" << (has_mate_uci ? std::to_string(uci_mate) : "none")
                          << " depth=" << info.depth << " nodes=" << info.nodes << "\n";
            } else {
                std::cout << "OK   [" << tc.label << "] N=" << tc.query_n
                          << " judge_min=" << judged
                          << " move=" << best_uci << " (mates_in=" << move_mate << ")"
                          << " uci_mate=" << uci_mate
                          << " depth=" << info.depth << " nodes=" << info.nodes << "\n";
            }
        } else {
            const bool claimed_mate_in_n =
                (forge::is_mate_score(info.score) && info.score > 0 &&
                 ((forge::MateValue - info.score + 1) / 2) <= tc.query_n) ||
                (has_mate_uci && uci_mate >= 1 && uci_mate <= tc.query_n);
            if (claimed_mate_in_n) {
                ++false_mates;
                std::cout << "FALSE_MATE [" << tc.label << "] N=" << tc.query_n
                          << " move=" << best_uci << " score=" << info.score << "\n";
            } else {
                std::cout << "OK   [" << tc.label << "] N=" << tc.query_n
                          << " (no mate) move=" << best_uci << " score=" << info.score
                          << " depth=" << info.depth << " nodes=" << info.nodes << "\n";
            }
        }
    }

    std::cout << "SUMMARY: total=40 mate_positions=30 non_mate_positions=10"
              << " missed_mates=" << missed_mates
              << " false_mates=" << false_mates
              << " illegal=" << illegal_or_bad << "\n";

    return (missed_mates == 0 && false_mates == 0 && illegal_or_bad == 0) ? 0 : 1;
}
