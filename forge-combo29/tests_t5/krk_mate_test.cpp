// KRK mate stability. On the unchanged lock this program fails two ways:
// a Threads 1 search keeps move-ordering history from an earlier position and
// then plays a different move (often without a mate score), and Threads 2
// stores helper transposition bounds that make the same depth-14 search
// disagree with Threads 1.
#include "forge/search.hpp"

#include <iostream>
#include <string>
#include <utility>

namespace {

struct Result {
    std::string move;
    int score = 0;
    bool ok = false;
};

std::string score_text(int score) {
    if (forge::is_mate_score(score)) {
        const int distance = forge::MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

Result search_fen(forge::Searcher& searcher, const std::string& fen, int depth) {
    Result result;
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "invalid fen: " << error << "\n";
        return result;
    }
    forge::SearchLimits limits;
    limits.depth = depth;
    const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
    result.move = forge::Board::move_to_uci(info.best_move);
    result.score = info.score;
    result.ok = true;
    return result;
}

bool same(const Result& a, const Result& b) {
    return a.ok && b.ok && a.move == b.move && a.score == b.score;
}

void print_result(const char* label, const std::string& fen, const Result& result) {
    std::cout << label << " " << fen << " " << score_text(result.score) << " " << result.move << "\n";
}

int check_history(const std::string& fen) {
    constexpr const char* kStart = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    forge::Searcher clean(16, 1);
    const Result expected = search_fen(clean, fen, 14);
    print_result("fresh", fen, expected);
    if (!expected.ok || !forge::is_mate_score(expected.score)) {
        std::cout << "history FAIL: fresh search did not prove a mate\n";
        return 1;
    }
    forge::Searcher stained(16, 1);
    const Result prelude = search_fen(stained, kStart, 10);
    if (!prelude.ok) return 1;
    // Drop the previous table only. History tables stay, which is the bug.
    stained.clear_hash();
    const Result after = search_fen(stained, fen, 14);
    print_result("after-startpos", fen, after);
    if (!same(expected, after)) {
        std::cout << "history FAIL\n";
        return 1;
    }
    std::cout << "history ok\n";
    return 0;
}

int check_threads(const std::string& fen, bool use_nnue, int runs) {
    forge::nnue::enabled = use_nnue;
    forge::Searcher one(16, 1);
    const Result expected = search_fen(one, fen, 14);
    print_result(use_nnue ? "nnue-t1" : "t1", fen, expected);
    if (!expected.ok) return 1;
    if (!use_nnue && !forge::is_mate_score(expected.score)) {
        std::cout << "threads FAIL: Threads 1 did not prove a mate\n";
        return 1;
    }
    forge::Searcher two(16, 2);
    int mismatches = 0;
    Result first_mismatch{};
    for (int i = 0; i < runs; ++i) {
        two.clear();
        const Result got = search_fen(two, fen, 14);
        if (!same(expected, got)) {
            if (mismatches == 0) first_mismatch = got;
            ++mismatches;
        }
    }
    std::cout << (use_nnue ? "nnue-threads2 " : "threads2 ") << fen << " runs " << runs
              << " mismatches " << mismatches;
    if (mismatches > 0) {
        std::cout << " first " << score_text(first_mismatch.score) << " " << first_mismatch.move;
    }
    std::cout << "\n";
    if (mismatches > 0) {
        std::cout << "threads FAIL\n";
        return 1;
    }
    std::cout << "threads ok\n";
    return 0;
}

} // namespace

int main() {
    forge::nnue::enabled = false;
    const char* positions[] = {
        "4K3/k7/8/8/2R5/8/8/8 w - - 0 1",
        "8/8/8/8/8/1R6/2k5/5K2 w - - 0 1",
        "3k4/8/3K4/8/8/8/8/3R4 w - - 0 1",
    };
    int failures = 0;
    for (const char* fen : positions) failures += check_history(fen);
    for (const char* fen : positions) failures += check_threads(fen, false, 30);
    failures += check_threads("4K3/k7/8/8/2R5/8/8/8 w - - 0 1", true, 20);
    if (failures != 0) {
        std::cout << "FAILED " << failures << "\n";
        return 1;
    }
    std::cout << "ok\n";
    return 0;
}
