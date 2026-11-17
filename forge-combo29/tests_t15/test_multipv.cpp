#include "forge/search.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

int g_failures = 0;
int g_explained = 0;

void fail(const std::string& message) {
    std::cout << "FAIL " << message << std::endl;
    ++g_failures;
}

void explain(const std::string& message) {
    std::cout << "EXPLAIN " << message << std::endl;
    ++g_explained;
}

std::vector<std::string> split_lines(const std::string& text) {
    std::vector<std::string> lines;
    std::istringstream input(text);
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) lines.push_back(line);
    }
    return lines;
}

std::string normalize(std::string line) {
    auto wipe = [&](const std::string& key) {
        const auto token = key;
        auto pos = line.find(token);
        if (pos == std::string::npos) return;
        pos += token.size();
        auto end = pos;
        while (end < line.size() && std::isdigit(static_cast<unsigned char>(line[end])) != 0) ++end;
        line.replace(pos, end - pos, "T");
    };
    wipe(" nps ");
    wipe(" time ");
    return line;
}

struct InfoLine {
    int depth = 0;
    int multipv = 1;
    bool has_multipv = false;
    std::string score;
    std::string move;
    std::string text;
};

bool parse_info(const std::string& text, InfoLine& out) {
    if (text.rfind("info depth ", 0) != 0) return false;
    out = InfoLine{};
    out.text = text;
    auto read_int = [&](const std::string& key, int& value) {
        const auto pos = text.find(key);
        if (pos == std::string::npos) return false;
        const auto start = pos + key.size();
        try {
            std::size_t used = 0;
            value = std::stoi(text.substr(start), &used);
            return used > 0;
        } catch (const std::exception&) {
            return false;
        }
    };
    if (!read_int("depth ", out.depth)) return false;
    out.has_multipv = read_int("multipv ", out.multipv);
    const auto score_pos = text.find(" score ");
    if (score_pos == std::string::npos) return false;
    std::istringstream score_in(text.substr(score_pos + 7));
    std::string kind;
    std::string value;
    if (!(score_in >> kind >> value)) return false;
    if (kind != "cp" && kind != "mate") return false;
    out.score = kind + " " + value;
    const auto pv_pos = text.find(" pv");
    if (pv_pos == std::string::npos) return false;
    std::istringstream pv_in(text.substr(pv_pos + 3));
    if (!(pv_in >> out.move)) return false;
    if (text.find("lowerbound") != std::string::npos || text.find("upperbound") != std::string::npos) return false;
    return true;
}

int rank_score(const std::string& score) {
    std::istringstream input(score);
    std::string kind;
    int value = 0;
    input >> kind >> value;
    if (kind == "cp") return value;
    // Positive mate N is better as N shrinks. Negative mate -N is worse as N shrinks.
    if (value > 0) return 100000 - value;
    return -(100000 + value);
}

forge::Board board_from_fen(const char* fen) {
    forge::Board board;
    const std::string text = (fen == nullptr || fen[0] == '\0') ? std::string(forge::Board::StandardStartFen) : fen;
    if (!board.set_fen(text)) fail(std::string("bad fen ") + text);
    return board;
}

bool is_legal(forge::Board board, const std::string& uci) {
    const auto parsed = board.parse_uci(uci);
    if (!parsed.has_value()) return false;
    for (const forge::Move move : board.legal_moves()) {
        if (move == *parsed) return true;
    }
    return false;
}

struct Captured {
    std::string text;
    forge::SearchInfo info;
};

Captured run_search(forge::Searcher& searcher, const forge::Board& board, const forge::SearchLimits& limits) {
    std::ostringstream buffer;
    std::streambuf* previous = std::cout.rdbuf(buffer.rdbuf());
    forge::SearchInfo info = searcher.search(board, limits, true, forge::Searcher::TTAccess::Exclusive);
    std::cout.rdbuf(previous);
    return Captured{buffer.str(), info};
}

std::vector<InfoLine> info_lines(const std::string& text) {
    std::vector<InfoLine> lines;
    for (const std::string& line : split_lines(text)) {
        InfoLine info;
        if (parse_info(line, info)) lines.push_back(info);
    }
    return lines;
}

// Checks one finished search. `single` is the MultiPV 1 transcript of the same
// position and depth, or empty when that comparison is not required.
void check_lines(const std::string& label, const forge::Board& board, const std::vector<InfoLine>& lines,
                 int requested, const std::vector<InfoLine>& single) {
    if (lines.empty()) {
        fail(label + " printed no info lines");
        return;
    }
    const int legal = static_cast<int>(board.legal_moves().size());
    const int expect = std::min(requested, legal);
    int depth = 0;
    std::vector<InfoLine> group;
    auto finish = [&]() {
        if (group.empty()) return;
        if (static_cast<int>(group.size()) != expect) {
            fail(label + " depth " + std::to_string(depth) + " has " + std::to_string(group.size()) +
                 " lines, expected " + std::to_string(expect));
        }
        for (std::size_t i = 0; i < group.size(); ++i) {
            if (group[i].multipv != static_cast<int>(i + 1)) {
                fail(label + " depth " + std::to_string(depth) + " index " + std::to_string(group[i].multipv));
            }
            if (!group[i].has_multipv) fail(label + " missing multipv token");
            if (!is_legal(board, group[i].move)) {
                fail(label + " illegal move " + group[i].move);
            }
            if (i > 0 && group[i].move == group[i - 1].move) {
                fail(label + " repeated move " + group[i].move);
            }
            if (i > 0 && rank_score(group[i].score) > rank_score(group[i - 1].score)) {
                fail(label + " scores rise at depth " + std::to_string(depth) + ": " + group[i - 1].score +
                     " then " + group[i].score);
            }
        }
        if (!single.empty()) {
            std::string single_move;
            for (const InfoLine& line : single) {
                if (line.depth == depth) single_move = line.move;
            }
            if (!single_move.empty()) {
                bool found = false;
                for (const InfoLine& line : group) found = found || line.move == single_move;
                if (!found) {
                    fail(label + " depth " + std::to_string(depth) + " dropped MultiPV 1 move " + single_move);
                } else if (group[0].move != single_move) {
                    explain(label + " depth " + std::to_string(depth) + " line 1 is " + group[0].move +
                            " and MultiPV 1 is " + single_move +
                            ". Line 1 is the highest exact score. The other lines are fresh searches with earlier "
                            "root moves removed, so one of them can outscore the iterative-deepening result. The "
                            "MultiPV 1 move is still in the set.");
                }
            }
        }
    };
    for (const InfoLine& line : lines) {
        if (line.depth != depth) {
            finish();
            depth = line.depth;
            group.clear();
        }
        group.push_back(line);
    }
    finish();
}

void test_byte_compare() {
    const char* fens[] = {
        "",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    };
    std::ifstream golden_file("forge-combo29/tests_t15/depth12_lock.txt");
    if (!golden_file) {
        fail("cannot read forge-combo29/tests_t15/depth12_lock.txt");
        return;
    }
    std::stringstream golden_buffer;
    golden_buffer << golden_file.rdbuf();
    const std::vector<std::string> golden = split_lines(golden_buffer.str());
    std::vector<std::string> golden_info;
    std::vector<std::string> golden_best;
    for (const std::string& line : golden) {
        if (line.rfind("info depth ", 0) == 0) golden_info.push_back(normalize(line));
        else if (line.rfind("bestmove ", 0) == 0) golden_best.push_back(line);
    }
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = 12;
    std::string produced;
    std::vector<std::string> best;
    for (const char* fen : fens) {
        const Captured captured = run_search(searcher, board_from_fen(fen), limits);
        produced += captured.text;
        best.push_back(forge::Board::move_to_uci(captured.info.best_move));
        if (captured.text.find("multipv") != std::string::npos) fail("MultiPV 1 output contains multipv");
    }
    const std::vector<std::string> got = split_lines(produced);
    std::vector<std::string> got_norm;
    got_norm.reserve(got.size());
    for (const std::string& line : got) got_norm.push_back(normalize(line));
    if (got_norm != golden_info) {
        fail("depth 12 MultiPV 1 info differs from the lock");
        const std::size_t n = std::min(got_norm.size(), golden_info.size());
        for (std::size_t i = 0; i < n; ++i) {
            if (got_norm[i] != golden_info[i]) {
                std::cout << " lock " << golden_info[i] << std::endl;
                std::cout << " got  " << got_norm[i] << std::endl;
                break;
            }
        }
        std::cout << " info lines lock " << golden_info.size() << " got " << got_norm.size() << std::endl;
    } else {
        std::cout << "PASS a depth 12 info matches the lock except time and nps" << std::endl;
    }
    if (best.size() != golden_best.size()) {
        fail("bestmove count");
    } else {
        bool match = true;
        for (std::size_t i = 0; i < best.size(); ++i) {
            const std::string expected = golden_best[i].substr(std::string("bestmove ").size());
            const auto space = expected.find(' ');
            const std::string move = expected.substr(0, space);
            if (move != best[i]) {
                fail("bestmove " + best[i] + " != " + move);
                match = false;
            }
        }
        if (match) std::cout << "PASS a bestmoves match the lock" << std::endl;
    }
}

void test_varied_lines() {
    const char* fens[] = {
        "",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    };
    for (const char* fen : fens) {
        const forge::Board board = board_from_fen(fen);
        forge::SearchLimits limits;
        limits.depth = 8;
        forge::Searcher single(16, 1);
        const Captured one = run_search(single, board, limits);
        limits.multipv = 4;
        forge::Searcher multi(16, 1);
        const Captured four = run_search(multi, board, limits);
        const std::string label = std::string("b ") + (fen[0] == '\0' ? "startpos" : fen);
        const auto lines = info_lines(four.text);
        check_lines(label, board, lines, 4, info_lines(one.text));
        std::string line1;
        int last_depth = 0;
        for (const InfoLine& line : lines) last_depth = std::max(last_depth, line.depth);
        for (const InfoLine& line : lines) {
            if (line.depth == last_depth && line.multipv == 1) line1 = line.move;
        }
        if (line1.empty()) fail(label + " has no final line 1");
        else if (forge::Board::move_to_uci(four.info.best_move) != line1) {
            fail(label + " bestmove " + forge::Board::move_to_uci(four.info.best_move) + " != line 1 " + line1);
        }
    }
    std::cout << "PASS b checked 10 positions at depth 8" << std::endl;
}

void test_two_moves() {
    const forge::Board board = board_from_fen("8/8/8/8/8/6k1/6r1/6K1 w - - 0 1");
    const int legal = static_cast<int>(board.legal_moves().size());
    if (legal != 2) fail("two-move position has " + std::to_string(legal) + " legal moves");
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = 6;
    limits.multipv = 4;
    const Captured captured = run_search(searcher, board, limits);
    check_lines("c", board, info_lines(captured.text), 4, {});
    std::cout << "PASS c two legal moves" << std::endl;
}

void test_mate() {
    const forge::Board board = board_from_fen("6k1/5ppp/8/8/8/8/8/R6K w - - 0 1");
    forge::Searcher searcher(16, 1);
    forge::SearchLimits limits;
    limits.depth = 4;
    limits.multipv = 4;
    const Captured captured = run_search(searcher, board, limits);
    const std::vector<InfoLine> lines = info_lines(captured.text);
    check_lines("d", board, lines, 4, {});
    std::string line1;
    std::string score;
    for (const InfoLine& line : lines) {
        if (line.depth == 4 && line.multipv == 1) {
            line1 = line.move;
            score = line.score;
        }
    }
    if (score != "mate 1") fail("mate in 1 line 1 score is " + score);
    forge::Board after = board;
    const auto parsed = after.parse_uci(line1);
    if (!parsed.has_value()) fail("mate move does not parse");
    else {
        forge::Undo undo;
        (void)after.make_move(*parsed, undo);
        if (!after.in_check() || after.has_legal_move()) fail("line 1 does not mate");
    }
    if (forge::Board::move_to_uci(captured.info.best_move) != line1) fail("mate bestmove mismatch");
    std::cout << "PASS d mate in 1 line " << line1 << " " << score << std::endl;
}

void test_limits() {
    const forge::Board board = board_from_fen("");
    {
        forge::Searcher searcher(16, 1);
        forge::SearchLimits limits;
        limits.multipv = 3;
        limits.nodes = 4000;
        limits.nodes_specified = true;
        const Captured captured = run_search(searcher, board, limits);
        const std::vector<InfoLine> lines = info_lines(captured.text);
        bool full = false;
        int depth = 0;
        int count = 0;
        auto account = [&]() {
            if (count == 3) full = true;
        };
        for (const InfoLine& line : lines) {
            if (!is_legal(board, line.move)) fail("nodes illegal " + line.move);
            if (line.depth != depth) {
                account();
                depth = line.depth;
                count = 0;
            }
            ++count;
        }
        account();
        if (!full) fail("nodes search never printed 3 lines at one depth");
        if (captured.info.best_move.is_none() || !is_legal(board, forge::Board::move_to_uci(captured.info.best_move))) {
            fail("nodes bestmove");
        }
        std::cout << "PASS nodes best " << forge::Board::move_to_uci(captured.info.best_move) << std::endl;
    }
    {
        forge::Searcher searcher(16, 1);
        forge::SearchLimits limits;
        limits.multipv = 3;
        limits.movetime_ms = 80;
        const Captured captured = run_search(searcher, board, limits);
        const std::vector<InfoLine> lines = info_lines(captured.text);
        bool full = false;
        int depth = 0;
        int count = 0;
        auto account = [&]() {
            if (count == 3) full = true;
        };
        for (const InfoLine& line : lines) {
            if (!is_legal(board, line.move)) fail("movetime illegal " + line.move);
            if (line.depth != depth) {
                account();
                depth = line.depth;
                count = 0;
            }
            ++count;
        }
        account();
        if (!full) fail("movetime search never printed 3 lines at one depth");
        if (captured.info.best_move.is_none()) fail("movetime bestmove");
        std::cout << "PASS movetime best " << forge::Board::move_to_uci(captured.info.best_move) << std::endl;
    }
}

void test_threads_fallback() {
    const forge::Board board = board_from_fen("");
    forge::SearchLimits limits;
    limits.depth = 4;
    limits.multipv = 3;
    forge::Searcher one(16, 1);
    forge::Searcher four(16, 4);
    const Captured a = run_search(one, board, limits);
    const Captured b = run_search(four, board, limits);
    const auto left = split_lines(a.text);
    const auto right = split_lines(b.text);
    if (left.size() != right.size()) fail("thread fallback line count");
    bool match = left.size() == right.size();
    for (std::size_t i = 0; i < left.size() && i < right.size(); ++i) {
        if (normalize(left[i]) != normalize(right[i])) {
            fail("thread fallback differs");
            std::cout << " t1 " << left[i] << std::endl;
            std::cout << " t4 " << right[i] << std::endl;
            match = false;
            break;
        }
    }
    if (forge::Board::move_to_uci(a.info.best_move) != forge::Board::move_to_uci(b.info.best_move)) {
        fail("thread fallback bestmove");
        match = false;
    }
    if (match) std::cout << "PASS threads 4 falls back to threads 1" << std::endl;
}

} // namespace

int main() {
    test_byte_compare();
    test_varied_lines();
    test_two_moves();
    test_mate();
    test_limits();
    test_threads_fallback();
    std::cout << "explained " << g_explained << std::endl;
    std::cout << "failures " << g_failures << std::endl;
    if (g_failures == 0) std::cout << "RESULT passed" << std::endl;
    else std::cout << "RESULT failed" << std::endl;
    return g_failures == 0 ? 0 : 1;
}
