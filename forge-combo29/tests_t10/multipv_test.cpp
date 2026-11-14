#include "forge/board.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void expect(bool ok, const std::string& message) {
    if (ok) {
        std::cout << "ok " << message << '\n';
        return;
    }
    std::cout << "FAIL " << message << '\n';
    ++g_failures;
}

// Restores std::cout. The engine writes info lines there; the test does not
// start a process or write a file.
class CoutCapture {
public:
    explicit CoutCapture(std::string& out) : out_(out) { previous_ = std::cout.rdbuf(&buffer_); }
    ~CoutCapture() {
        out_ = buffer_.str();
        std::cout.rdbuf(previous_);
    }
    CoutCapture(const CoutCapture&) = delete;
    CoutCapture& operator=(const CoutCapture&) = delete;

private:
    std::string& out_;
    std::stringbuf buffer_;
    std::streambuf* previous_ = nullptr;
};

forge::SearchInfo search_of(const forge::Board& board, int depth, int multipv, bool set_multipv, std::string* printed) {
    forge::SearchLimits limits;
    limits.depth = depth;
    if (set_multipv) limits.multipv = multipv;
    forge::Searcher searcher(16, 1);
    if (printed == nullptr) return searcher.search(board, limits, false);
    CoutCapture capture(*printed);
    return searcher.search(board, limits, true);
}

bool legal_root(const forge::Board& board, const forge::Move& move) {
    for (const forge::Move candidate : board.legal_moves()) {
        if (candidate == move) return true;
    }
    return false;
}

bool lines_are_distinct_legal_roots(const forge::Board& board, const forge::SearchInfo& info) {
    if (info.lines.empty() || info.lines[0].pv.empty()) return false;
    if (info.best_move != info.lines[0].pv.front() || info.score != info.lines[0].score) return false;
    for (std::size_t i = 0; i < info.lines.size(); ++i) {
        if (info.lines[i].pv.empty() || !legal_root(board, info.lines[i].pv.front())) return false;
        for (std::size_t j = 0; j < i; ++j) {
            if (info.lines[i].pv.front() == info.lines[j].pv.front()) return false;
        }
    }
    return true;
}

void print_lines(const std::string& label, const forge::SearchInfo& info) {
    std::cout << label << " best " << forge::Board::move_to_uci(info.best_move) << " score " << info.score
              << " nodes " << info.nodes << " lines " << info.lines.size() << '\n';
    for (std::size_t i = 0; i < info.lines.size(); ++i) {
        std::cout << "  " << (i + 1) << " score " << info.lines[i].score << " pv";
        for (const forge::Move move : info.lines[i].pv) std::cout << ' ' << forge::Board::move_to_uci(move);
        std::cout << '\n';
    }
}

} // namespace

int main() {
    forge::Board start;

    const forge::SearchInfo baseline = search_of(start, 4, 1, false, nullptr);
    std::string printed_one;
    const forge::SearchInfo explicit_one = search_of(start, 4, 1, true, &printed_one);
    const forge::SearchInfo clamped_zero = search_of(start, 4, 0, true, nullptr);
    print_lines("default", baseline);
    print_lines("multipv1", explicit_one);
    expect(baseline.nodes > 0, "the depth-4 search visits nodes");
    expect(explicit_one.nodes == baseline.nodes, "MultiPV 1 visits the same nodes as the default");
    expect(explicit_one.best_move == baseline.best_move, "MultiPV 1 plays the default move");
    expect(explicit_one.score == baseline.score, "MultiPV 1 reports the default score");
    expect(explicit_one.pv == baseline.pv, "MultiPV 1 reports the default pv");
    expect(explicit_one.lines.empty() && baseline.lines.empty(), "MultiPV 1 does not publish extra lines");
    expect(printed_one.find("multipv") == std::string::npos, "MultiPV 1 info text has no multipv token");
    expect(printed_one.find("info depth ") != std::string::npos, "MultiPV 1 still prints info lines");
    expect(clamped_zero.nodes == baseline.nodes && clamped_zero.lines.empty(), "MultiPV 0 is clamped to 1");

    std::string printed_three;
    const forge::SearchInfo three = search_of(start, 1, 3, true, &printed_three);
    print_lines("depth1-multipv3", three);
    expect(three.lines.size() == 3, "depth 1 MultiPV 3 returns three lines");
    expect(lines_are_distinct_legal_roots(start, three), "the three lines are distinct legal root moves");
    bool ordered = three.lines.size() == 3;
    for (std::size_t i = 1; i < three.lines.size(); ++i) ordered = ordered && three.lines[i].score <= three.lines[i - 1].score;
    expect(ordered, "depth-1 lines are ordered by score");
    expect(printed_three.find(" multipv 1 score ") != std::string::npos, "info prints multipv 1 before score");
    expect(printed_three.find(" multipv 2 score ") != std::string::npos, "info prints multipv 2 before score");
    expect(printed_three.find(" multipv 3 score ") != std::string::npos, "info prints multipv 3 before score");
    expect(printed_three.find(" multipv 4 ") == std::string::npos, "MultiPV 3 does not print a fourth line");

    const forge::SearchInfo eight = search_of(start, 1, 100, true, nullptr);
    print_lines("depth1-multipv100", eight);
    expect(eight.lines.size() == 8, "MultiPV above 8 is clamped to 8");
    expect(lines_are_distinct_legal_roots(start, eight), "the eight lines are distinct legal root moves");

    const forge::SearchInfo last_depth = search_of(start, 3, 2, true, nullptr);
    print_lines("depth3-multipv2", last_depth);
    expect(last_depth.lines.size() == 2, "the result keeps the last depth's lines");
    expect(lines_are_distinct_legal_roots(start, last_depth), "both last-depth lines are legal root moves");

    forge::Board cramped;
    const bool fen_ok = cramped.set_fen("7k/8/8/6K1/8/8/7P/8 b - - 0 1");
    const auto legal = cramped.legal_moves();
    std::cout << "cramped legal " << legal.size() << '\n';
    for (const forge::Move move : legal) std::cout << "  " << forge::Board::move_to_uci(move) << '\n';
    const forge::SearchInfo all = search_of(cramped, 1, 8, true, nullptr);
    print_lines("cramped-multipv8", all);
    expect(fen_ok, "the cramped fen parses");
    expect(legal.size() > 1 && legal.size() < 8, "the cramped position has fewer than 8 legal moves");
    expect(all.lines.size() == legal.size(), "MultiPV stops when the legal root moves run out");
    bool covered = all.lines.size() == legal.size();
    for (const forge::Move move : legal) {
        const bool found = std::any_of(all.lines.begin(), all.lines.end(), [&](const forge::SearchInfo::MultiPvLine& line) {
            return !line.pv.empty() && line.pv.front() == move;
        });
        covered = covered && found;
    }
    expect(covered, "every legal root move is one of the lines");

    const forge::SearchInfo ranked = search_of(start, 4, 8, true, nullptr);
    print_lines("depth4-multipv8", ranked);
    bool ranked_ok = ranked.lines.size() == 8 && ranked.best_move == ranked.lines.front().pv.front() &&
                     ranked.score == ranked.lines.front().score && lines_are_distinct_legal_roots(start, ranked);
    for (std::size_t i = 1; i < ranked.lines.size(); ++i)
        ranked_ok = ranked_ok && ranked.lines[i].score <= ranked.lines[i - 1].score;
    expect(ranked_ok, "depth-4 MultiPV lines are ranked by score");

    forge::Board bare;
    std::string bare_text;
    const bool bare_fen = bare.set_fen("8/8/8/4k3/8/4K3/8/8 w - - 0 1");
    const forge::SearchInfo bare_info = search_of(bare, 2, 3, true, &bare_text);
    print_lines("bare-kings", bare_info);
    const int bare_expect = std::min(3, static_cast<int>(bare.legal_moves().size()));
    bool bare_ok = bare_fen && bare_expect > 1 && static_cast<int>(bare_info.lines.size()) == bare_expect &&
                   bare_info.score == 0 && bare_info.best_move == bare_info.lines.front().pv.front();
    for (const forge::SearchInfo::MultiPvLine& line : bare_info.lines) {
        bare_ok = bare_ok && line.score == 0 && line.pv.size() == 1 && legal_root(bare, line.pv.front());
        bare_ok = bare_ok && bare_text.find(" pv " + forge::Board::move_to_uci(line.pv.front())) != std::string::npos;
    }
    expect(bare_ok, "a drawn root prints its legal moves");

    forge::SearchLimits limited;
    limited.depth = 8;
    limited.multipv = 3;
    limited.nodes = 560;
    limited.nodes_specified = true;
    forge::Searcher limiter(16, 1);
    const forge::SearchInfo stopped = limiter.search(start, limited, false);
    print_lines("nodes560", stopped);
    bool stopped_ok = stopped.lines.size() == 3;
    for (std::size_t i = 0; i < stopped.lines.size(); ++i) {
        stopped_ok = stopped_ok && !stopped.lines[i].pv.empty() && legal_root(start, stopped.lines[i].pv.front());
        for (std::size_t j = 0; j < i; ++j)
            stopped_ok = stopped_ok && stopped.lines[i].pv.front() != stopped.lines[j].pv.front();
        if (i > 0) stopped_ok = stopped_ok && stopped.lines[i].score <= stopped.lines[i - 1].score;
    }
    stopped_ok = stopped_ok && stopped.best_move == stopped.lines.front().pv.front() &&
                 stopped.score == stopped.lines.front().score;
    expect(stopped_ok, "a node limit keeps the last complete MultiPV set");

    forge::Board restricted;
    const auto e2e4 = restricted.parse_uci("e2e4");
    const auto d2d4 = restricted.parse_uci("d2d4");
    bool two_ok = e2e4.has_value() && d2d4.has_value();
    if (two_ok) {
        forge::SearchLimits only_two;
        only_two.depth = 2;
        only_two.multipv = 4;
        only_two.search_moves_specified = true;
        only_two.search_moves = {*e2e4, *d2d4};
        forge::Searcher restricted_search(16, 1);
        const forge::SearchInfo two = restricted_search.search(restricted, only_two, false);
        print_lines("searchmoves", two);
        two_ok = two.lines.size() == 2 && two.best_move == two.lines.front().pv.front() &&
                 two.score == two.lines.front().score;
        for (const forge::SearchInfo::MultiPvLine& line : two.lines) {
            const bool allowed = !line.pv.empty() && (line.pv.front() == *e2e4 || line.pv.front() == *d2d4);
            two_ok = two_ok && allowed;
        }
        if (two.lines.size() == 2) {
            two_ok = two_ok && two.lines[0].pv.front() != two.lines[1].pv.front();
            two_ok = two_ok && two.lines[1].score <= two.lines[0].score;
        }
    }
    expect(two_ok, "MultiPV stays inside searchmoves");

    forge::Board checked;
    const bool checked_fen = checked.set_fen("4k3/8/8/8/8/8/8/4K2r w - - 0 1");
    const auto checked_legal = checked.legal_moves();
    const forge::SearchInfo evasions = search_of(checked, 2, 8, true, nullptr);
    print_lines("in-check", evasions);
    const int evasion_expect = std::min(8, static_cast<int>(checked_legal.size()));
    bool evasion_ok = checked_fen && checked.in_check() && evasion_expect > 1 &&
                      static_cast<int>(evasions.lines.size()) == evasion_expect &&
                      lines_are_distinct_legal_roots(checked, evasions);
    for (std::size_t i = 1; i < evasions.lines.size(); ++i)
        evasion_ok = evasion_ok && evasions.lines[i].score <= evasions.lines[i - 1].score;
    expect(evasion_ok, "a check search ranks the legal evasions");

    std::cout << "failures=" << g_failures << '\n';
    return g_failures == 0 ? 0 : 1;
}
