// key_after_test.cpp -- compares Board::key_after() with make_move()'s own key,
// exhaustively over random legal play, on an instrumented COPY of 6b98f217.
//
// Why this matters for normal play: search.cpp:1504 and :1964 call key_after() to
// prefetch the child's transposition-table cluster before make_move. Its only
// in-tree guard is `assert(!early_key || child_key == board.key())` at
// search.cpp:1505 / :1965, and NDEBUG removes assertions from the Release build,
// so in the shipped engine nothing checks that the prefetched key is the real one.
// A wrong key puts the prefetch on the wrong cluster: not a crash, just a slower
// search -- unless a caller ever trusts the value.
#include "forge/board.hpp"

#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

using forge::Board;
using forge::Move;
using forge::Undo;

int main(int argc, char** argv) {
    const int games = argc > 1 ? std::atoi(argv[1]) : 200;
    const unsigned seed = argc > 2 ? static_cast<unsigned>(std::atoi(argv[2])) : 701u;
    std::mt19937_64 rng(seed);

    std::uint64_t checked = 0, refused = 0, mismatches = 0, first_mismatch_game = 0;
    std::string first_fen, first_move;
    std::uint64_t first_got = 0, first_want = 0;

    for (int game = 0; game < games; ++game) {
        Board board;  // startpos
        for (int ply = 0; ply < 400; ++ply) {
            const auto moves = board.legal_moves();
            if (moves.size() == 0) break;
            for (const Move move : moves) {
                std::uint64_t predicted = 0;
                const bool ok = board.key_after(move, predicted);
                if (!ok) { ++refused; continue; }
                Board copy = board;
                Undo undo;
                (void)copy.make_move(move, undo);
                const std::uint64_t actual = copy.key();
                ++checked;
                if (predicted != actual) {
                    ++mismatches;
                    if (mismatches == 1) {
                        first_mismatch_game = static_cast<std::uint64_t>(game);
                        first_fen = board.fen();
                        first_move = Board::move_to_uci(move);
                        first_got = predicted;
                        first_want = actual;
                    }
                }
            }
            // random continuation
            const Move pick = moves[static_cast<std::size_t>(rng() % moves.size())];
            Undo undo;
            (void)board.make_move(pick, undo);
        }
    }

    std::printf("games %d seed %u\n", games, seed);
    std::printf("key_after checked %llu  refused %llu\n",
                static_cast<unsigned long long>(checked), static_cast<unsigned long long>(refused));
    std::printf("mismatches %llu\n", static_cast<unsigned long long>(mismatches));
    if (mismatches != 0) {
        std::printf("FIRST MISMATCH game %llu fen %s move %s got %llu want %llu\n",
                    static_cast<unsigned long long>(first_mismatch_game), first_fen.c_str(),
                    first_move.c_str(), static_cast<unsigned long long>(first_got),
                    static_cast<unsigned long long>(first_want));
        return 1;
    }
    if (checked == 0) {
        std::printf("FAIL nothing was checked: this run proves nothing\n");
        return 2;
    }
    std::printf("OK every predicted key equalled make_move's key\n");
    return 0;
}
