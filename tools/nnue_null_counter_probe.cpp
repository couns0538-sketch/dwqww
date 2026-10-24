// Original bounded counter receipt using the existing tests.cpp friend API.
#include "forge/search.hpp"

#include <array>
#include <iostream>
#include <stdexcept>
#include <string_view>

#ifndef FORGE_NULL_INT16_API
#define FORGE_NULL_INT16_API 0
#endif

namespace forge {
struct SearcherTestProbe {
    static std::uint64_t null_tries(Searcher& searcher) { return searcher.main_worker().null_tries_; }
    static std::uint64_t null_cutoffs(Searcher& searcher) { return searcher.main_worker().null_cutoffs_; }
};
} // namespace forge

namespace {
void require(bool good, const char* message) {
    if (!good) throw std::runtime_error(message);
}
} // namespace

int main(int argc, char** argv) {
    try {
        bool integer = false;
#if FORGE_NULL_INT16_API
        require(argc == 2 && (std::string_view(argv[1]) == "--int16-off" ||
                             std::string_view(argv[1]) == "--int16-on"),
                "usage: null_counter_probe --int16-off|--int16-on");
        integer = std::string_view(argv[1]) == "--int16-on";
        require(forge::nnue::set_int16(integer) == integer && forge::nnue::int16_active() == integer,
                "int16 mode activation mismatch");
#else
        (void)argv;
        require(argc == 1, "usage: null_counter_probe");
#endif
        require(forge::nnue::available(), "NNUE network required");
        forge::nnue::enabled = true;
        struct Fixture { const char* name; const char* fen; bool expect_active; };
        const std::array<Fixture, 2> fixtures{{
            {"startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", true},
            {"pawn-only", "8/8/8/3k4/8/4K3/4P3/8 w - - 0 1", false}
        }};
        for (const auto& fixture : fixtures) {
            forge::Board board;
            require(board.set_fen(fixture.fen), "fixture FEN rejected");
            forge::Searcher searcher(16, 1);
            searcher.clear();
            forge::SearchLimits limits;
            limits.depth = 8;
            const auto info = searcher.search(board, limits, false);
#if FORGE_NULL_INT16_API
            require(forge::nnue::int16_active() == integer, "int16 mode changed during search");
#endif
            const auto tries = forge::SearcherTestProbe::null_tries(searcher);
            const auto cutoffs = forge::SearcherTestProbe::null_cutoffs(searcher);
            require(info.depth == 8, "search did not complete depth8");
            require(!info.best_move.is_none() && board.is_legal(info.best_move), "illegal bestmove");
            require(!info.pv.empty() && info.pv.front() == info.best_move, "bestmove/PV mismatch");
            auto replay = board;
            for (const auto move : info.pv) {
                require(replay.is_legal(move), "illegal PV move");
                forge::Undo undo;
                require(replay.make_move(move, undo), "legal PV move rejected");
            }
            const bool okay = fixture.expect_active ? tries > 0U && cutoffs > 0U
                                                    : tries == 0U && cutoffs == 0U;
            std::cout << "{\"kind\":\"null_counter\",\"fixture\":\"" << fixture.name
                      << "\",\"fen\":\"" << fixture.fen << "\",\"depth\":" << info.depth
                      << ",\"hash_mb\":16,\"threads\":1,\"int16_active\":" << (integer ? "true" : "false")
                      << ",\"null_tries\":" << tries << ",\"null_cutoffs\":" << cutoffs
                      << ",\"bestmove\":\"" << forge::Board::move_to_uci(info.best_move)
                      << "\",\"legal_bestmove\":true,\"legal_pv\":true,\"result\":\""
                      << (okay ? "PASS" : "FAIL") << "\"}\n" << std::flush;
            require(okay, "null-counter expectation failed");
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "null_counter_probe: " << error.what() << '\n';
        return 1;
    }
}
