// R3-5: mate scores and tablebase scores through the transposition table.
//
//   forge_tt_mate_tb_tests <syzygy_reference.tsv> [tablebase_dir]     (or FORGE_SYZYGY_PATH)
//
// Mate in the TT (always runs): a K+R v K mate in 3 with a unique key move (proved by the brute-force mate oracle
// below) is searched twice with the same TT, then searched again at every depth on that warm TT, then the
// positions two plies and one ply later are searched on it (their entries were stored at other plies), and in
// the reverse order (the defender's position first). Every result must be the exact mate distance
// (MateValue - plies), every mate claim must be true according to the oracle, and the warm TT must give the same
// values as fresh searches. With Threads 2 (one TT, two writers) every result must be a real mate, never shorter
// than the true distance.
// Tablebases (only with a folder holding the Syzygy tables; otherwise SKIP lines and exit 0): positions of the
// independent reference (tests/syzygy_reference.tsv: WDL and the DTZ of every root move, python-chess) are
// searched with the tables loaded: wins report a tablebase-range (or mate) score and play a move that keeps the
// win, draws report 0 and keep the draw, losses report a tablebase-range (or mate) loss; and an in-search
// tablebase win (a capture from a 6-piece root into a 5-piece table) keeps its exact score through the TT.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include "forge/search_options.hpp"
#include "forge/syzygy.hpp"

#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

using forge::Board;
using forge::MateInMaxPly;
using forge::MateValue;
using forge::Move;

int failures = 0;
int checks = 0;

void check(bool condition, const std::string& message) {
    ++checks;
    std::cout << (condition ? "PASS " : "FAIL ") << message << '\n';
    if (!condition) ++failures;
}

Board board_of(std::string_view fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid FEN: " + std::string(fen));
    return board;
}

Board after(Board board, std::initializer_list<std::string_view> moves) {
    for (const std::string_view text : moves) {
        const auto move = board.parse_uci(text);
        if (!move.has_value()) throw std::runtime_error("illegal fixture move " + std::string(text));
        forge::Undo undo;
        (void)board.make_move(*move, undo);
    }
    return board;
}

std::string uci(Move move) { return Board::move_to_uci(move); }

// ---------------------------------------------------------------------------------------------------------------
// Brute-force mate oracle (full legal move trees; only used on positions with few pieces).
bool replies_all_lose(Board& board, int moves);

// The side to move can force checkmate within `moves` moves (moves >= 1).
bool mates_within(Board& board, int moves) {
    for (const Move move : board.legal_moves()) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        const bool ok = board.has_legal_move() ? moves > 1 && replies_all_lose(board, moves - 1) : board.in_check();
        board.unmake_move(move, undo);
        if (ok) return true;
    }
    return false;
}

// The side to move has legal moves and every one of them lets the opponent mate within `moves` moves.
bool replies_all_lose(Board& board, int moves) {
    for (const Move reply : board.legal_moves()) {
        forge::Undo undo;
        (void)board.make_move(reply, undo);
        const bool ok = mates_within(board, moves);
        board.unmake_move(reply, undo);
        if (!ok) return false;
    }
    return true;
}

// The side to move is checkmated now or within `moves` moves of the opponent.
bool mated_within(Board board, int moves) {
    if (!board.has_legal_move()) return board.in_check();
    return moves > 0 && replies_all_lose(board, moves);
}

int shortest_mate(Board board, int limit) {
    for (int n = 1; n <= limit; ++n) {
        if (mates_within(board, n)) return n;
    }
    return 0;
}

// A mate score claims a forced mate (or being mated) within the corresponding number of moves: true?
// Memoized per (position, score): the oracle is a full tree walk and costly in sanitizer builds.
bool claim_is_true(const Board& board, int score) {
    static std::map<std::pair<std::string, int>, bool> memo;
    if (score < MateInMaxPly && score > -MateInMaxPly) return true;  // not a mate claim
    const auto key = std::make_pair(board.fen(), score);
    if (const auto it = memo.find(key); it != memo.end()) return it->second;
    bool result = false;
    if (score >= MateInMaxPly) {
        const int plies = MateValue - score;
        Board copy = board;
        result = plies % 2 == 1 && mates_within(copy, (plies + 1) / 2);
    } else {
        const int plies = MateValue + score;
        result = plies % 2 == 0 && mated_within(board, plies / 2);
    }
    memo[key] = result;
    return result;
}

forge::SearchInfo run(forge::Searcher& searcher, const Board& board, int depth) {
    forge::SearchLimits limits;
    limits.depth = depth;
    return searcher.search(board, limits);
}

// ---------------------------------------------------------------------------------------------------------------
void mate_in_tt() {
    std::cout << "== mate scores through the TT\n";
    constexpr std::string_view Fen = "4R3/8/8/k2K4/8/8/8/8 w - - 0 1";  // mate in 3, key move Kd5-c5 only
    constexpr int Plies = 5;
    const Board root = board_of(Fen);
    {
        Board b = root;
        check(shortest_mate(b, 3) == 3, "oracle: the fixture is a mate in exactly 3");
        int keys = 0;
        bool key_ok = false;
        for (const Move move : b.legal_moves()) {
            forge::Undo undo;
            (void)b.make_move(move, undo);
            const bool mates = replies_all_lose(b, 2);
            b.unmake_move(move, undo);
            keys += mates ? 1 : 0;
            key_ok = key_ok || (mates && uci(move) == "d5c5");
        }
        check(keys == 1 && key_ok, "oracle: d5c5 is the only move that mates in 3");
    }

    // Same root twice, then every depth, on one TT.
    forge::Searcher warm(16, 1);
    const forge::SearchInfo first = run(warm, root, 12);
    const forge::SearchInfo second = run(warm, root, 12);
    std::cout << "first search " << first.score << " " << uci(first.best_move) << ", second " << second.score << " "
              << uci(second.best_move) << '\n';
    check(first.score == MateValue - Plies && uci(first.best_move) == "d5c5",
          "first search (depth 12): exactly mate in 3 with the key move (" + std::to_string(first.score) + ")");
    check(second.score == first.score && second.best_move == first.best_move,
          "second search on the same TT: same mate distance and move");
    for (int depth = 1; depth <= 12; ++depth) {
        const forge::SearchInfo info = run(warm, root, depth);
        check(info.score == MateValue - Plies && uci(info.best_move) == "d5c5" && claim_is_true(root, info.score),
              "warm TT, depth " + std::to_string(depth) + ": exactly mate in 3 (" + std::to_string(info.score) + " " +
                  uci(info.best_move) + ")");
    }

    // Two plies later (every defence): the entries of the first search were stored two plies deeper.
    const Board key = after(root, {"d5c5"});
    for (const Move defence : key.legal_moves()) {
        const Board later = after(key, {uci(defence)});
        const int n = shortest_mate(later, 2);
        forge::Searcher fresh(16, 1);
        const forge::SearchInfo cold = run(fresh, later, 12);
        for (const int depth : {1, 3, 6, 12}) {
            const forge::SearchInfo info = run(warm, later, depth);
            check(n >= 1 && info.score == MateValue - (2 * n - 1) && info.score == cold.score &&
                      claim_is_true(later, info.score),
                  "after d5c5 " + uci(defence) + " (mate in " + std::to_string(n) + "), warm TT depth " +
                      std::to_string(depth) + ": " + std::to_string(info.score) + ", fresh " + std::to_string(cold.score));
        }
    }
    // One ply later, the defender to move: mated in 2.
    check(mated_within(key, 2) && !mated_within(key, 1), "oracle: after d5c5 black is mated in exactly 2");
    for (const int depth : {1, 4, 12}) {
        const forge::SearchInfo info = run(warm, key, depth);
        check(info.score == -(MateValue - 4) && claim_is_true(key, info.score),
              "defender on the warm TT, depth " + std::to_string(depth) + ": exactly mated in 2 (" +
                  std::to_string(info.score) + ")");
    }

    // Reverse order: the defender's position first (negative mate scores stored at ply 0 and below), then the
    // attacker's root reads them one ply deeper. A fresh depth-4 search does not see this mate; the TT supplies it.
    forge::Searcher reverse(16, 1);
    const forge::SearchInfo defender = run(reverse, key, 12);
    check(defender.score == -(MateValue - 4), "reverse order: defender first, mated in 2 (" + std::to_string(defender.score) + ")");
    forge::Searcher cold_root(16, 1);
    const forge::SearchInfo shallow_cold = run(cold_root, root, 4);
    for (const int depth : {1, 2, 4}) {
        const forge::SearchInfo info = run(reverse, root, depth);
        check(info.score == MateValue - Plies && uci(info.best_move) == "d5c5",
              "reverse order, attacker at depth " + std::to_string(depth) + " reads the stored mate: exactly mate in 3 (" +
                  std::to_string(info.score) + ")");
    }
    std::cout << "INFO fresh depth-4 search of the root: " << shallow_cold.score << " " << uci(shallow_cold.best_move) << '\n';
    check(claim_is_true(root, shallow_cold.score), "every mate claim of the fresh shallow search is true");

    // Multi-threaded, the TT shared by two writers: every reported score is a real mate for the side to move and
    // never shorter than the true mate in 3. (Not the exact distance: rarely, about 1 run in 60 on the PC, the
    // two-thread search settles on a longer mate, e.g. mate in 11, and the warm TT keeps it at depth 12; see
    // opus_r3/R3-5/REPORT.md.)
    forge::Searcher smp(16, 2);
    for (int round = 1; round <= 2; ++round) {
        const forge::SearchInfo info = run(smp, root, 14);
        check(info.score >= MateInMaxPly && info.score <= MateValue - Plies,
              "Threads 2, search " + std::to_string(round) + " on the shared TT: a real mate, never shorter than mate in "
              "3 (" + std::to_string(info.score) + " " + uci(info.best_move) + ")");
        if (info.score != MateValue - Plies) {
            std::cout << "INFO Threads 2 reported a longer mate: " << info.score << " " << uci(info.best_move) << '\n';
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------
struct ReferenceRow {
    std::string fen;
    int wdl = 0;
    std::map<std::string, int> moves;  // uci -> DTZ of the move counted from the root (sign: the root's view)
    std::string material;
    std::vector<std::string> needs;
};

std::vector<ReferenceRow> read_reference(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open " + path);
    std::vector<ReferenceRow> rows;
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        std::vector<std::string> f;
        std::stringstream ss(line);
        std::string field;
        while (std::getline(ss, field, '\t')) f.push_back(field);
        if (f.size() < 5) continue;
        ReferenceRow row;
        row.fen = f[0];
        row.wdl = std::stoi(f[1]);
        std::stringstream ms(f[3]);
        std::string token;
        while (ms >> token) {
            const std::size_t colon = token.find(':');
            if (colon != std::string::npos) row.moves[token.substr(0, colon)] = std::stoi(token.substr(colon + 1));
        }
        std::stringstream ns(f[4]);
        ns >> row.material;
        std::string word;
        bool in_needs = false;
        while (ns >> word) {
            if (word == "needs:") in_needs = true;
            else if (in_needs) row.needs.push_back(word);
        }
        if (row.needs.empty()) row.needs.push_back(row.material);
        rows.push_back(row);
    }
    return rows;
}

void tablebases(const std::string& reference_path, const std::string& tb) {
    std::cout << "== tablebase scores and moves (tables: " << tb << ")\n";
    const forge::syzygy::LoadSummary summary = forge::syzygy::load(tb);
    std::cout << "loaded " << summary.wdl_tables << " WDL and " << summary.dtz_tables << " DTZ tables, up to "
              << summary.max_pieces << " pieces\n";
    if (summary.max_pieces < 4) {
        std::cout << "SKIP: tablebase checks need at least the 3-4 piece tables\n";
        (void)forge::syzygy::load("");
        return;
    }
    const bool saved_rule = forge::options::syzygy_50_move_rule;
    const int saved_depth = forge::options::syzygy_probe_depth;
    forge::options::syzygy_50_move_rule = true;
    forge::options::syzygy_probe_depth = 1;
    using forge::syzygy::TbWin;
    using forge::syzygy::TbWinInMaxPly;

    // Known positions: up to 8 wins, draws and losses each, one per material, from the reference file.
    const std::vector<ReferenceRow> rows = read_reference(reference_path);
    std::map<int, std::set<std::string>> taken;
    int used[5] = {};
    for (const ReferenceRow& row : rows) {
        if (row.wdl != 2 && row.wdl != 0 && row.wdl != -2) continue;  // cursed / blessed results: skipped
        if (used[row.wdl + 2] >= 8 || taken[row.wdl].count(row.material) != 0) continue;
        bool present = true;
        for (const std::string& name : row.needs) present = present && forge::syzygy::has_table(name);
        if (!present) continue;
        const Board board = board_of(row.fen);
        if (board.castling_rights() != 0) continue;
        taken[row.wdl].insert(row.material);
        ++used[row.wdl + 2];
        // The move keeps the tablebase result: its reference value (DTZ of the move, the root's view) has the sign
        // of the root's WDL (0 for draws).
        const auto keeps_result = [&row](Move m, int& value) {
            const auto it = row.moves.find(uci(m));
            if (it == row.moves.end()) return false;
            value = it->second;
            return row.wdl == 2 ? value > 0 : row.wdl == 0 ? value == 0 : value < 0;
        };
        forge::Searcher searcher(16, 1);
        const forge::SearchInfo info = run(searcher, board, 6);
        const int shown = forge::syzygy::display_score(info.score);  // the score UCI reports for this search
        int value = 0;
        const bool move_ok = keeps_result(info.best_move, value);
        bool score_ok = false;
        if (row.wdl == 2) score_ok = shown >= MateInMaxPly || (shown >= TbWinInMaxPly && shown <= TbWin);
        else if (row.wdl == 0) score_ok = shown == 0;
        else score_ok = shown <= -MateInMaxPly || (shown <= -TbWinInMaxPly && shown >= -TbWin);
        check(score_ok && move_ok, row.material + " wdl " + std::to_string(row.wdl) + " " + row.fen + ": reported " +
                                       std::to_string(shown) + ", move " + uci(info.best_move) + " (reference DTZ " +
                                       std::to_string(value) + ")");
        // Same position again on the same TT: the same reported score, and a move that still keeps the result.
        // (Several moves can share the best tablebase rank, e.g. every win that converts within the 50-move rule;
        // the search chooses among them by its own score, which a warm TT may change.)
        const forge::SearchInfo again = run(searcher, board, 6);
        const int shown_again = forge::syzygy::display_score(again.score);
        int value_again = 0;
        const bool again_ok = keeps_result(again.best_move, value_again);
        check(shown_again == shown && again_ok,
              row.material + " searched again on the same TT: same reported score " + std::to_string(shown_again) +
                  ", move " + uci(again.best_move) + " keeps the result (reference DTZ " + std::to_string(value_again) +
                  (again.best_move == info.best_move ? ", same move)" : ", another equally ranked move)"));
    }
    check(used[4] >= 4 && used[2] >= 4 && used[0] >= 4,
          "tablebase sample: " + std::to_string(used[4]) + " wins, " + std::to_string(used[2]) + " draws, " +
              std::to_string(used[0]) + " losses (at least 4 each)");

    // In-search tablebase win through the TT: from a 6-piece root (no 6-piece tables) Qxd4 enters a won 5-piece
    // ending, probed at ply 1: exactly TbWin - 1, also on the warm TT at every depth.
    if (summary.max_pieces >= 5 && forge::syzygy::has_table("KQRvKN")) {
        const Board root = board_of("4k3/8/8/8/3r4/8/3Q4/3RK2n w - - 0 1");
        forge::Searcher searcher(16, 1);
        const forge::SearchInfo first = run(searcher, root, 6);
        const forge::SearchInfo second = run(searcher, root, 6);
        check(first.score == TbWin - 1 && uci(first.best_move) == "d2d4" && second.score == first.score &&
                  second.best_move == first.best_move,
              "6-piece root: capture into a TB win, exactly TbWin - 1 twice on one TT (" + std::to_string(first.score) +
                  ", " + std::to_string(second.score) + ")");
        for (int depth = 2; depth <= 7; ++depth) {
            const forge::SearchInfo info = run(searcher, root, depth);
            check(info.score == TbWin - 1 && uci(info.best_move) == "d2d4",
                  "6-piece root, warm TT depth " + std::to_string(depth) + ": exactly TbWin - 1 (" +
                      std::to_string(info.score) + ")");
        }
    } else {
        std::cout << "SKIP: in-search TB score check (needs the 5-piece table KQRvKN)\n";
    }
    forge::options::syzygy_50_move_rule = saved_rule;
    forge::options::syzygy_probe_depth = saved_depth;
    (void)forge::syzygy::load("");
    check(forge::syzygy::max_pieces() == 0, "tables unloaded again");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_tt_mate_tb_tests <syzygy_reference.tsv> [tablebase_dir]\n";
        return 2;
    }
    std::string tb = argc >= 3 ? argv[2] : "";
    if (tb.empty()) {
        const char* env = std::getenv("FORGE_SYZYGY_PATH");
        if (env != nullptr) tb = env;
    }
    try {
        mate_in_tt();
        std::error_code ec;
        const std::filesystem::path dir(std::u8string(reinterpret_cast<const char8_t*>(tb.data()), tb.size()));
        if (tb.empty() || !std::filesystem::exists(dir / "KQvK.rtbw", ec)) {
            std::cout << "SKIP: tablebase checks (no Syzygy folder given: argument 2 or FORGE_SYZYGY_PATH)\n";
        } else {
            tablebases(argv[1], tb);
        }
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        return 2;
    }
    std::cout << "tt mate/tb: " << checks << " checks, " << failures << " failures\n";
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " forge_tt_mate_tb_tests\n";
    return failures == 0 ? 0 : 1;
}
