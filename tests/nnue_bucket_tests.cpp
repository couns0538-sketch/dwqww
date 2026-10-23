#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <array>
#include <iostream>
#include <string>

namespace {
struct Fixture {
    const char* fen;
    int pieces;
    int bucket;
};

// Literal boundaries catch counting one colour only, omitting kings, and
// selecting the next head one piece too early or too late.
constexpr std::array<Fixture, 16> Fixtures{{
    {"4k3/8/8/8/8/8/8/4K3 w - - 0 1", 2, 0},
    {"4k3/8/8/8/8/8/8/RN2K3 w - - 0 1", 4, 0},
    {"4k3/8/8/8/8/8/8/RNB1K3 w - - 0 1", 5, 1},
    {"4k3/8/8/8/8/8/8/RNBQKBN1 w - - 0 1", 8, 1},
    {"4k3/8/8/8/8/8/8/RNBQKBNR w - - 0 1", 9, 2},
    {"4k3/8/8/8/8/8/PPP5/RNBQKBNR w - - 0 1", 12, 2},
    {"4k3/8/8/8/8/8/PPPP4/RNBQKBNR w - - 0 1", 13, 3},
    {"4k3/8/8/8/8/8/PPPPPPP1/RNBQKBNR w - - 0 1", 16, 3},
    {"4k3/8/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 17, 4},
    {"4k3/ppp5/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 20, 4},
    {"4k3/pppp4/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 21, 5},
    {"4k3/ppppppp1/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 24, 5},
    {"4k3/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 25, 6},
    {"rnb1k3/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 28, 6},
    {"rnbqk3/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 29, 7},
    {"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1", 32, 7},
}};
}

int main() {
    int failures = 0;
    const int count = forge::nnue::output_bucket_count();
    if (count != 1 && count != 8) {
        std::cerr << "Unsupported compiled output bucket count: " << count << '\n';
        return 1;
    }
    for (const auto& fixture : Fixtures) {
        for (const bool black_to_move : {false, true}) {
            std::string fen(fixture.fen);
            if (black_to_move) fen.replace(fen.find(" w "), 3, " b ");
            forge::Board board;
            if (!board.set_fen(fen) || forge::popcount(board.occupied()) != fixture.pieces) {
                std::cerr << "Invalid piece-count fixture: " << fen << '\n';
                ++failures;
                continue;
            }
            const int expected = count == 1 ? 0 : fixture.bucket;
            const int actual = forge::nnue::output_bucket(board);
            if (actual != expected) {
                std::cerr << "Wrong output bucket for " << fixture.pieces << " pieces: "
                          << actual << " instead of " << expected << '\n';
                ++failures;
            }
        }
    }
    // Captures cross the 5 -> 4 boundary while the shared accumulator remains
    // incremental. Unmake must restore the original head and evaluation.
    for (const auto& item : std::array<std::array<const char*, 2>, 2>{{
             {{"b3k3/8/8/8/8/8/8/RN2K3 w - - 0 1", "a1a8"}},
             {{"rn2k3/8/8/8/8/8/8/B3K3 b - - 0 1", "a8a1"}},
         }}) {
        forge::Board board;
        if (!board.set_fen(item[0])) return 1;
        const auto move = board.parse_uci(item[1]);
        if (!move.has_value()) return 1;
        forge::nnue::Accumulator parent, incremental, refreshed;
        forge::nnue::refresh(board, parent);
        const int initial_score = forge::nnue::evaluate(board, parent);
        const int initial_bucket = count == 1 ? 0 : 1;
        if (forge::nnue::output_bucket(board) != initial_bucket) ++failures;
        forge::nnue::update(parent, incremental, forge::nnue::dirty_pieces(board, *move));
        forge::Undo undo;
        if (!board.make_move(*move, undo)) return 1;
        if (forge::popcount(board.occupied()) != 4 || forge::nnue::output_bucket(board) != 0) ++failures;
        forge::nnue::refresh(board, refreshed);
        if (incremental.values != refreshed.values ||
            forge::nnue::evaluate(board, incremental) != forge::nnue::evaluate(board, refreshed)) ++failures;
        board.unmake_move(*move, undo);
        if (forge::nnue::output_bucket(board) != initial_bucket ||
            forge::nnue::evaluate(board, parent) != initial_score) ++failures;
    }
    if (failures != 0) return 1;
    std::cout << "Output-bucket boundaries: 32 cases, two capture/unmake transitions, compiled heads " << count << '\n';
    return 0;
}
