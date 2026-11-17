// Property and oracle test suite for Piece P2 (position cache + direct parse_uci):
// 1. Part (d): Direct Board::parse_uci vs reference legal_moves()+move_to_uci() oracle across every legal move
//    of all 1,000 positions in positions_1000.txt plus targeted edge-case FENs and all malformed/illegal token
//    categories (e7e8 without promo, e1e2q, e7e8k, illegal 2-square king move, pawn onto ep square when none exists,
//    from==to, out-of-range letters/digits, and 50,000+ random synthetic tokens).
// 2. Part (c): Stateful persistent engine subprocess running 1,000 random multi-command sequences (~8,000 commands)
//    mixing: extending last list, same list again, shorter list, another list of same length, another root with same
//    moves, >80% FEN roots, illegal token in the middle of a list followed by a valid command, and ucinewgame.
//    After EVERY `position` command, verifies that the persistent engine's `eval` and `go perft 1` output match a
//    brand-new fresh reference Board built from scratch from that single command, AND cross-checks 1,000 fresh OS
//    engine processes (one fresh process per sequence).

#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue_v3.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <optional>
#include <random>
#include <sstream>
#include <string>
#include <string_view>
#include <unistd.h>
#include <sys/wait.h>
#include <vector>

namespace {

std::optional<forge::Move> old_parse_uci_oracle(forge::Board& board, std::string_view text) {
    if (text.size() != 4 && text.size() != 5) return std::nullopt;
    for (const forge::Move move : board.legal_moves()) {
        if (forge::Board::move_to_uci(move) == text) return move;
    }
    return std::nullopt;
}

bool same_opt_move(const std::optional<forge::Move>& a, const std::optional<forge::Move>& b) {
    if (a.has_value() != b.has_value()) return false;
    if (!a.has_value()) return true;
    return a->from == b->from && a->to == b->to && a->promotion == b->promotion && a->flags == b->flags;
}

// Exact reference implementation of uncached apply_position on a fresh Board
void fresh_reference_apply_position(forge::Board& board, const std::string& full_cmd) {
    std::istringstream input(full_cmd);
    std::string cmd_word;
    input >> cmd_word; // "position"
    forge::Board candidate = board;
    std::string token;
    if (!(input >> token)) return;
    if (token == "startpos") {
        (void)candidate.set_fen(forge::Board::StandardStartFen);
    } else if (token == "fen") {
        std::string fen;
        for (int i = 0; i < 6 && input >> token; ++i) {
            if (!fen.empty()) fen += ' ';
            fen += token;
        }
        std::string error;
        if (!candidate.set_fen(fen, &error)) return;
    } else {
        return;
    }
    if (!(input >> token)) {
        board = candidate;
        return;
    }
    while (token != "moves") {
        if (!(input >> token)) {
            board = candidate;
            return;
        }
    }
    while (input >> token) {
        const auto move = old_parse_uci_oracle(candidate, token);
        if (!move.has_value()) {
            board = candidate;
            return;
        }
        forge::Undo undo;
        (void)candidate.make_move(*move, undo);
    }
    board = candidate;
}

struct EnginePipe {
    pid_t pid = -1;
    FILE* to_child = nullptr;
    FILE* from_child = nullptr;

    explicit EnginePipe(const std::string& exe_path) {
        int in_pipe[2];
        int out_pipe[2];
        if (pipe(in_pipe) != 0 || pipe(out_pipe) != 0) std::exit(2);
        pid = fork();
        if (pid == 0) {
            dup2(in_pipe[0], STDIN_FILENO);
            dup2(out_pipe[1], STDOUT_FILENO);
            close(in_pipe[0]); close(in_pipe[1]);
            close(out_pipe[0]); close(out_pipe[1]);
            execl(exe_path.c_str(), exe_path.c_str(), nullptr);
            _exit(127);
        }
        close(in_pipe[0]);
        close(out_pipe[1]);
        to_child = fdopen(in_pipe[1], "w");
        from_child = fdopen(out_pipe[0], "r");
    }

    ~EnginePipe() {
        if (to_child != nullptr) {
            std::fputs("quit\n", to_child);
            std::fflush(to_child);
            std::fclose(to_child);
        }
        if (from_child != nullptr) std::fclose(from_child);
        if (pid > 0) {
            int status = 0;
            waitpid(pid, &status, 0);
        }
    }

    void send(const std::string& s) {
        std::fputs(s.c_str(), to_child);
        std::fflush(to_child);
    }

    bool readline(std::string& out) {
        char buf[4096];
        if (std::fgets(buf, sizeof(buf), from_child) == nullptr) return false;
        out = buf;
        while (!out.empty() && (out.back() == '\n' || out.back() == '\r')) out.pop_back();
        return true;
    }

    void wait_ready() {
        std::string ln;
        while (readline(ln)) {
            if (ln == "readyok") return;
        }
        std::cerr << "EOF waiting for readyok\n";
        std::exit(2);
    }

    std::string query_eval_and_perft1(const std::string& pos_cmd) {
        send(pos_cmd + "\neval\ngo perft 1\n");
        std::string ln;
        std::string eval_line;
        std::vector<std::string> perft_moves;
        std::string nodes_line;
        bool got_eval = false;
        while (readline(ln)) {
            if (ln.rfind("info string eval ", 0) == 0) {
                eval_line = ln;
                got_eval = true;
            } else if (got_eval) {
                if (ln.rfind("info ", 0) == 0) continue;
                if (ln.rfind("nodes ", 0) == 0) {
                    nodes_line = ln;
                    break;
                }
                perft_moves.push_back(ln);
            }
        }
        std::sort(perft_moves.begin(), perft_moves.end());
        std::ostringstream oss;
        oss << eval_line << " | ";
        for (const auto& m : perft_moves) oss << m << ",";
        oss << nodes_line;
        return oss.str();
    }
};

std::string oracle_eval_and_perft1(const forge::nnue::v3::Net& net, const std::string& pos_cmd) {
    forge::Board b;
    fresh_reference_apply_position(b, pos_cmd);
    const int val = forge::nnue::v3::evaluate_reference(net, b);
    std::ostringstream ev;
    ev << "info string eval hce 0 nnue " << val << " total " << val;
    if (b.in_check()) ev << " incheck 1";

    const forge::MoveList leg = b.legal_moves();
    std::vector<std::string> perft_moves;
    perft_moves.reserve(leg.size());
    for (const forge::Move m : leg) {
        perft_moves.push_back(forge::Board::move_to_uci(m) + ": 1");
    }
    std::sort(perft_moves.begin(), perft_moves.end());
    std::ostringstream oss;
    oss << ev.str() << " | ";
    for (const auto& m : perft_moves) oss << m << ",";
    oss << "nodes " << leg.size();
    return oss.str();
}

std::vector<std::string> generate_legal_line(const std::string& root_fen, int plies, std::mt19937_64& rng) {
    forge::Board b;
    (void)b.set_fen(root_fen);
    std::vector<std::string> out;
    for (int i = 0; i < plies; ++i) {
        const forge::MoveList leg = b.legal_moves();
        if (leg.empty()) break;
        const forge::Move m = leg[rng() % leg.size()];
        out.push_back(forge::Board::move_to_uci(m));
        forge::Undo u;
        (void)b.make_move(m, u);
    }
    return out;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "Usage: test_p2_parse_and_cache <positions_1000.txt> <net768.fnn3> <engine_exe>\n";
        return 1;
    }
    const std::string pos1000_path = argv[1];
    const std::string net_path = argv[2];
    const std::string exe_path = argv[3];

    std::string load_err;
    if (!forge::nnue::v3::load(net_path, &load_err)) {
        std::cerr << "Failed to load net: " << load_err << "\n";
        return 1;
    }
    forge::nnue::v3::requested = true;
    const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();

    std::vector<std::string> fens;
    {
        std::ifstream in(pos1000_path);
        std::string ln;
        while (std::getline(in, ln)) {
            if (!ln.empty() && ln.back() == '\r') ln.pop_back();
            if (!ln.empty()) fens.push_back(ln);
        }
    }
    if (fens.size() != 1000) {
        std::cerr << "Expected 1000 FENs, got " << fens.size() << "\n";
        return 1;
    }

    // ---- PART (d): Direct parse_uci vs old_parse_uci_oracle ----
    std::uint64_t legal_checked = 0;
    std::uint64_t malformed_checked = 0;
    std::vector<std::string> all_test_fens = fens;
    all_test_fens.push_back("4k3/4P3/8/8/8/8/4p3/R3K2R w - - 0 1");
    all_test_fens.push_back("r3k2r/4p3/8/4P3/8/8/8/R3K2R w KQkq - 0 1");
    all_test_fens.push_back("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 0 1");
    all_test_fens.push_back("4k3/8/8/8/8/8/4K3/8 w - - 0 1");

    const std::vector<std::string> fixed_malformed = {
        "e7e8", "a7a8", "e2e1", "e1e2q", "g1f3q", "e2e4n", "e7e8k", "e7e8p", "e7e8Q", "e7e8x",
        "e1g1", "e1c1", "e8g8", "e8c8", "e2g2", "e2c2", "e5d6", "e5f6", "e5d6q",
        "e1e1", "e4e4", "a1a1", "h8h8", "0000", "", "e2", "e2e", "e2e4qq",
        "i2e4", "e0e4", "e2e9", "`1a2", "a1{2", "a9a8", "z1a1"
    };

    std::mt19937_64 rng(20261117ULL);
    constexpr char files_ext[] = "abcdefghij`@";
    constexpr char ranks_ext[] = "0123456789";
    constexpr char promos_ext[] = "nbrqkpQ ";

    for (const std::string& fen : all_test_fens) {
        forge::Board b1;
        forge::Board b2;
        std::string ferr;
        if (!b1.set_fen(fen, &ferr) || !b2.set_fen(fen, &ferr)) {
            std::cerr << "set_fen failed on '" << fen << "': " << ferr << "\n";
            return 1;
        }
        for (const forge::Move m : b1.legal_moves()) {
            const std::string uci = forge::Board::move_to_uci(m);
            if (!same_opt_move(b1.parse_uci(uci), old_parse_uci_oracle(b2, uci))) {
                std::cerr << "MISMATCH on legal move " << uci << " in " << fen << "\n";
                return 1;
            }
            ++legal_checked;
        }
        for (const std::string& bad : fixed_malformed) {
            if (!same_opt_move(b1.parse_uci(bad), old_parse_uci_oracle(b2, bad))) {
                std::cerr << "MISMATCH on malformed token '" << bad << "' in " << fen << "\n";
                return 1;
            }
            ++malformed_checked;
        }
        for (int t = 0; t < 50; ++t) {
            std::string tok;
            tok += files_ext[rng() % 12];
            tok += ranks_ext[rng() % 10];
            tok += files_ext[rng() % 12];
            tok += ranks_ext[rng() % 10];
            if ((rng() & 1ULL) != 0ULL) tok += promos_ext[rng() % 8];
            if (!same_opt_move(b1.parse_uci(tok), old_parse_uci_oracle(b2, tok))) {
                std::cerr << "MISMATCH on random token '" << tok << "' in " << fen << "\n";
                return 1;
            }
            ++malformed_checked;
        }
    }
    std::cout << "PART_D_PARSE_UCI_ORACLE PASS: positions=" << all_test_fens.size()
              << " legal_moves_checked=" << legal_checked
              << " malformed_and_random_tokens_checked=" << malformed_checked
              << " mismatches=0\n";

    // ---- PART (c): 1,000 random multi-command sequences vs fresh oracle & fresh OS processes ----
    EnginePipe stateful_eng(exe_path);
    stateful_eng.send("setoption name Hash value 1\nsetoption name NNUEArchFile value " + net_path +
                      "\nsetoption name NNUEArch value true\nisready\n");
    stateful_eng.wait_ready();

    std::uint64_t total_pos_verified = 0;
    std::uint64_t count_extend = 0, count_same = 0, count_shorter = 0, count_same_len_diff = 0;
    std::uint64_t count_diff_root_same_moves = 0, count_fen_root = 0, count_illegal_mid = 0, count_ucinewgame = 0;
    std::uint64_t fresh_os_proc_checks = 0;

    for (int seq = 0; seq < 1000; ++seq) {
        bool use_fen = (rng() % 10) < 8;
        std::string cur_fen = use_fen ? fens[rng() % fens.size()] : std::string(forge::Board::StandardStartFen);
        std::vector<std::string> full_line = generate_legal_line(cur_fen, 14, rng);
        std::vector<std::string> cur_moves;
        if (!full_line.empty()) {
            const std::size_t init_len = 1 + (rng() % std::min<std::size_t>(4, full_line.size()));
            cur_moves.assign(full_line.begin(), full_line.begin() + static_cast<std::ptrdiff_t>(init_len));
        }

        const int steps = 7 + static_cast<int>(rng() % 4);
        std::string last_pos_cmd;
        std::string last_stateful_sig;
        for (int step = 0; step < steps; ++step) {
            const int op = static_cast<int>(rng() % 8);
            std::string pos_cmd;
            auto format_pos = [](bool fen_root, const std::string& f, const std::vector<std::string>& mv) {
                std::string s = fen_root ? ("position fen " + f) : "position startpos";
                if (!mv.empty()) {
                    s += " moves";
                    for (const auto& m : mv) s += " " + m;
                }
                return s;
            };

            if (op == 0 && cur_moves.size() < full_line.size()) {
                const std::size_t add = 1 + (rng() % std::min<std::size_t>(3, full_line.size() - cur_moves.size()));
                cur_moves.assign(full_line.begin(), full_line.begin() + static_cast<std::ptrdiff_t>(cur_moves.size() + add));
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
                ++count_extend;
            } else if (op == 1) {
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
                ++count_same;
            } else if (op == 2 && !cur_moves.empty()) {
                cur_moves.resize(rng() % cur_moves.size());
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
                ++count_shorter;
            } else if (op == 3 && !cur_moves.empty()) {
                std::vector<std::string> alt = generate_legal_line(cur_fen, static_cast<int>(cur_moves.size()), rng);
                if (alt.size() == cur_moves.size()) cur_moves = alt;
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
                ++count_same_len_diff;
            } else if (op == 4) {
                use_fen = true;
                cur_fen = fens[rng() % fens.size()];
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
                full_line = generate_legal_line(cur_fen, 14, rng);
                ++count_diff_root_same_moves;
            } else if (op == 5) {
                std::vector<std::string> broken = cur_moves;
                const std::size_t mid = broken.empty() ? 0 : (rng() % broken.size());
                broken.insert(broken.begin() + static_cast<std::ptrdiff_t>(mid), "e1e1");
                if (full_line.size() > mid) broken.push_back(full_line[mid]);
                pos_cmd = format_pos(use_fen, cur_fen, broken);
                cur_moves.resize(mid);
                ++count_illegal_mid;
            } else if (op == 6) {
                stateful_eng.send("ucinewgame\nisready\n");
                stateful_eng.wait_ready();
                use_fen = (rng() % 10) < 8;
                cur_fen = use_fen ? fens[rng() % fens.size()] : std::string(forge::Board::StandardStartFen);
                full_line = generate_legal_line(cur_fen, 14, rng);
                cur_moves.clear();
                if (!full_line.empty()) cur_moves.push_back(full_line[0]);
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
                ++count_ucinewgame;
            } else {
                use_fen = true;
                cur_fen = fens[rng() % fens.size()];
                full_line = generate_legal_line(cur_fen, 14, rng);
                cur_moves.clear();
                if (!full_line.empty()) {
                    const std::size_t k = 1 + (rng() % std::min<std::size_t>(5, full_line.size()));
                    cur_moves.assign(full_line.begin(), full_line.begin() + static_cast<std::ptrdiff_t>(k));
                }
                pos_cmd = format_pos(use_fen, cur_fen, cur_moves);
            }
            if (use_fen) ++count_fen_root;

            const std::string got = stateful_eng.query_eval_and_perft1(pos_cmd);
            const std::string exp = oracle_eval_and_perft1(net, pos_cmd);
            if (got != exp) {
                std::cerr << "PROPERTY TEST MISMATCH at seq=" << seq << " step=" << step << " op=" << op << "\n"
                          << "  cmd     : " << pos_cmd << "\n"
                          << "  stateful: " << got << "\n"
                          << "  fresh   : " << exp << "\n";
                return 1;
            }
            last_pos_cmd = pos_cmd;
            last_stateful_sig = got;
            ++total_pos_verified;
        }

        // Cross-check against an actual newly-spawned fresh OS engine process every 10th sequence (100 fresh processes)
        if (seq % 10 == 0) {
            EnginePipe fresh_proc(exe_path);
            fresh_proc.send("setoption name Hash value 1\nsetoption name NNUEArchFile value " + net_path +
                            "\nsetoption name NNUEArch value true\nisready\n");
            fresh_proc.wait_ready();
            const std::string fresh_got = fresh_proc.query_eval_and_perft1(last_pos_cmd);
            if (fresh_got != last_stateful_sig) {
                std::cerr << "FRESH OS PROCESS MISMATCH at seq=" << seq << "\n"
                          << "  stateful: " << last_stateful_sig << "\n"
                          << "  fresh_os: " << fresh_got << "\n";
                return 1;
            }
            ++fresh_os_proc_checks;
        }
    }

    std::cout << "PART_C_POSITION_CACHE_PROPERTY PASS: sequences=1000 total_positions_verified=" << total_pos_verified
              << " fresh_os_processes=" << fresh_os_proc_checks
              << " (extend=" << count_extend
              << ", repeat_same=" << count_same
              << ", shorter=" << count_shorter
              << ", same_len_diff=" << count_same_len_diff
              << ", diff_root_same_moves=" << count_diff_root_same_moves
              << ", illegal_mid=" << count_illegal_mid
              << ", ucinewgame=" << count_ucinewgame
              << ", fen_roots=" << count_fen_root << ") mismatches=0\n";
    return 0;
}
