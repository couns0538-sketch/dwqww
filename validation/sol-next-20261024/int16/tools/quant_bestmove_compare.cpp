// Original cold-search sensitivity check; this is not a playing-strength test.
#include "forge/search.hpp"

#include <csignal>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {
volatile std::sig_atomic_t interrupted = 0;
void request_stop(int) { interrupted = 1; }
void require(bool good, const char* message) {
    if (!good) throw std::runtime_error(message);
}
void text(const std::string& value) {
    std::cout << '"';
    for (char c : value) {
        if (c == '"' || c == '\\') std::cout << '\\';
        std::cout << c;
    }
    std::cout << '"';
}
struct Selected {
    std::size_t target, index, skipped_clock = 0, skipped_insufficient = 0, skipped_terminal = 0;
    std::string fen;
};
void selection(const Selected& item) {
    std::cout << "{\"kind\":\"selection\",\"target_index_zero_based\":" << item.target
              << ",\"index_zero_based\":" << item.index << ",\"skipped_clock_ge90\":" << item.skipped_clock
              << ",\"skipped_insufficient\":" << item.skipped_insufficient
              << ",\"skipped_terminal\":" << item.skipped_terminal << ",\"fen\":";
    text(item.fen); std::cout << "}\n" << std::flush;
}
forge::SearchInfo run(const forge::Board& board, bool integer) {
    require(forge::nnue::set_int16(integer) == integer, "requested int16 state rejected");
    require(forge::nnue::int16_active() == integer, "int16 active state mismatch");
    forge::Searcher owner(16, 1);
    owner.clear(); // Explicitly empty TT, histories and worker caches for each side.
    forge::SearchLimits limits;
    limits.depth = 13;
    std::jthread canceller([&](std::stop_token done) {
        while (!done.stop_requested()) {
            if (interrupted) owner.stop();
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });
    const auto result = owner.search(board, limits, false);
    canceller.request_stop();
    require(forge::nnue::int16_active() == integer, "int16 state changed during search");
    require(!result.best_move.is_none() && board.is_legal(result.best_move), "illegal best move");
    require(!result.pv.empty() && result.pv.front() == result.best_move, "best move/PV mismatch");
    auto continuation = board;
    for (const auto move : result.pv) {
        require(continuation.is_legal(move), "illegal PV move");
        forge::Undo undo;
        require(continuation.make_move(move, undo), "legal PV move rejected");
    }
    return result;
}
void result(const forge::SearchInfo& info, bool integer) {
    std::cout << "{\"int16_active\":" << (integer ? "true" : "false")
              << ",\"depth\":" << info.depth << ",\"score_cp\":" << info.score << ",\"bestmove\":";
    text(forge::Board::move_to_uci(info.best_move));
    std::cout << ",\"legal_bestmove\":true,\"legal_pv\":true,\"pv\":[";
    bool comma = false;
    for (const auto move : info.pv) {
        if (comma) std::cout << ',';
        comma = true;
        text(forge::Board::move_to_uci(move));
    }
    std::cout << "]}";
}
} // namespace

int main(int argc, char** argv) {
    std::size_t completed = 0, changed = 0;
    try {
        require(argc == 2, "usage: quant_bestmove_compare corpus.fen");
        std::signal(SIGINT, request_stop);
        std::signal(SIGTERM, request_stop);
        require(forge::nnue::available() && forge::nnue::int16_available(), "float/int16 NNUE required");
        forge::nnue::enabled = true;
        std::ifstream input(argv[1]);
        require(static_cast<bool>(input), "cannot open corpus");
        std::vector<std::string> corpus;
        std::string line;
        while (std::getline(input, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            corpus.push_back(line);
        }
        require(corpus.size() == 100000U, "expected exactly 100000 corpus FENs");
        std::vector<Selected> selected;
        for (std::size_t bucket = 0; bucket < 32U; ++bucket) {
            Selected item{bucket * 3125U, bucket * 3125U, 0U, 0U, 0U, {}};
            const auto end = (bucket + 1U) * 3125U;
            for (; item.index < end; ++item.index) {
                forge::Board board;
                require(board.set_fen(corpus[item.index]), "invalid corpus FEN");
                if (board.halfmove_clock() >= 90) { ++item.skipped_clock; continue; }
                if (board.is_insufficient_material()) { ++item.skipped_insufficient; continue; }
                if (!board.has_legal_move()) { ++item.skipped_terminal; continue; }
                item.fen = corpus[item.index];
                break;
            }
            require(!item.fen.empty(), "no eligible FEN in deterministic stride bucket");
            selected.push_back(item);
            selection(item);
        }
        for (const auto& item : selected) {
            if (interrupted) break;
            forge::Board board;
            require(board.set_fen(item.fen), "selected FEN rejected");
            const auto off = run(board, false);
            if (interrupted || off.depth != 13) break;
            const auto on = run(board, true);
            if (interrupted || on.depth != 13) break;
            const bool different = off.best_move != on.best_move;
            changed += different ? 1U : 0U;
            ++completed;
            std::cout << "{\"kind\":\"comparison\",\"index_zero_based\":" << item.index << ",\"fen\":";
            text(item.fen);
            std::cout << ",\"off\":"; result(off, false);
            std::cout << ",\"on\":"; result(on, true);
            std::cout << ",\"bestmove_changed\":" << (different ? "true" : "false") << "}\n" << std::flush;
        }
        (void)forge::nnue::set_int16(false);
        std::cout << "{\"kind\":\"summary\",\"requested\":32,\"selected\":" << selected.size()
                  << ",\"completed_pairs\":" << completed << ",\"bestmove_changes\":" << changed
                  << ",\"depth\":13,\"hash_mb\":16,\"threads\":1,\"cold_search_each_side\":true"
                  << ",\"requested_stride\":3125,\"interrupted\":" << (interrupted ? "true" : "false")
                  << ",\"status\":\"" << (completed == 32U ? "COMPLETE" : "PARTIAL")
                  << "\",\"strength_claim\":false}\n" << std::flush;
        return completed == 32U || interrupted ? 0 : 1;
    } catch (const std::exception& error) {
        (void)forge::nnue::set_int16(false);
        std::cerr << "quant_bestmove_compare: " << error.what() << '\n';
        std::cout << "{\"kind\":\"error\",\"completed_pairs\":" << completed
                  << ",\"bestmove_changes\":" << changed << ",\"status\":\"FAIL\"}\n";
        return 1;
    }
}
