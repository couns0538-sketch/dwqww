// gives_check_probe.cpp -- cross-checks Board::gives_check() against brute force.
//
// gives_check() decides check EXTENSIONS and quiet-check move ordering, so a wrong answer
// changes the tree in every search: a missed check loses an extension, a false check wastes
// one and corrupts the quiet-check ordering. The shortcut is inline in include/forge/board.hpp:333.
//
// Brute force: make the move on a copy; the position now gives check iff the opponent is in
// check. That is board.in_check() after the move, which is the engine's own definition and does
// not consult the king-lines cache.
#include "forge/board.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <string>

using namespace forge;

int main(int argc, char** argv) {
    const int games = argc > 1 ? std::atoi(argv[1]) : 40;
    const unsigned seed = argc > 2 ? static_cast<unsigned>(std::atoi(argv[2])) : 701u;
    std::mt19937_64 rng(seed);

    std::uint64_t compared = 0, mismatches = 0, said_check_no = 0, said_no_check_yes = 0;
    std::string first;
    for (int game = 0; game < games; ++game) {
        Board board;
        for (int ply = 0; ply < 250; ++ply) {
            const auto legal = board.legal_moves();
            if (legal.size() == 0) break;
            for (const Move move : legal) {
                const bool fast = board.gives_check(move);
                Board copy = board;
                Undo undo;
                (void)copy.make_move(move, undo);
                const bool brute = copy.in_check();   // the opponent, after the move
                ++compared;
                if (fast != brute) {
                    ++mismatches;
                    if (fast && !brute) ++said_check_no;
                    if (!fast && brute) ++said_no_check_yes;
                    if (first.empty()) {
                        first = "fen " + board.fen() + " move " + Board::move_to_uci(move) +
                                " gives_check " + (fast ? "yes" : "no") +
                                " brute " + (brute ? "yes" : "no");
                    }
                }
            }
            const Move pick = legal[static_cast<std::size_t>(rng() % legal.size())];
            Undo undo;
            (void)board.make_move(pick, undo);
        }
    }
    std::printf("games %d seed %u\n", games, seed);
    std::printf("moves compared %llu  mismatches %llu (false check %llu, missed check %llu)\n",
                static_cast<unsigned long long>(compared),
                static_cast<unsigned long long>(mismatches),
                static_cast<unsigned long long>(said_check_no),
                static_cast<unsigned long long>(said_no_check_yes));
    if (compared == 0) {
        std::printf("FAIL nothing compared\n");
        return 2;
    }
    if (mismatches != 0) {
        std::printf("FIRST MISMATCH %s\n", first.c_str());
        return 1;
    }
    std::printf("OK gives_check() agreed with make+in_check on every legal move\n");
    return 0;
}
