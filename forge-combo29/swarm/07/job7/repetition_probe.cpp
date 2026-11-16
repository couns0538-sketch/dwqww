// repetition_probe.cpp -- does Board::is_repetition() agree with the real rule?
//
// Plays each move list given on stdin (one list per line, UCI moves separated by spaces,
// starting from startpos) and after every move prints:
//   ply, move, halfmove_clock, key, is_repetition(), is_repetition(root=0)
// A python driver compares is_repetition() with python-chess's is_repetition(3)
// (threefold) so a wrong answer in normal play -- declaring a draw where there is none, or
// missing a real one -- shows up as a disagreement.
#include "forge/board.hpp"

#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>

using namespace forge;

int main() {
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        Board board;
        std::istringstream moves(line);
        std::string token;
        int ply = 0;
        std::printf("LIST %s\n", line.c_str());
        std::printf("PLY 0 clock=%u key=%llu rep=%d rep0=%d\n",
                    static_cast<unsigned>(board.halfmove_clock()),
                    static_cast<unsigned long long>(board.key()),
                    int(board.is_repetition()), int(board.is_repetition(0)));
        while (moves >> token) {
            const auto move = board.parse_uci(token);
            if (!move.has_value()) {
                std::printf("BROKEN %s at ply %d (not legal)\n", token.c_str(), ply + 1);
                break;
            }
            Undo undo;
            (void)board.make_move(*move, undo);
            ++ply;
            std::printf("PLY %d %s clock=%u key=%llu rep=%d rep0=%d\n", ply, token.c_str(),
                        static_cast<unsigned>(board.halfmove_clock()),
                        static_cast<unsigned long long>(board.key()),
                        int(board.is_repetition()), int(board.is_repetition(0)));
        }
        std::printf("END\n");
    }
    return 0;
}
