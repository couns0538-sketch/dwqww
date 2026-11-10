// Validate each supplied PV against legal move generation at every ply.
#include "forge/board.hpp"
#include <iostream>
#include <sstream>
#include <string>
int main() {
    std::string line;
    unsigned checked = 0;
    while (std::getline(std::cin, line)) {
        const auto split = line.find('\t');
        if (split == std::string::npos) return 1;
        forge::Board board;
        if (!board.set_fen(line.substr(0, split))) return 2;
        std::istringstream moves(line.substr(split + 1));
        std::string text;
        while (moves >> text) {
            bool found = false;
            for (const auto move : board.legal_moves()) {
                if (forge::Board::move_to_uci(move) != text) continue;
                forge::Undo undo;
                if (!board.make_move(move, undo)) return 3;
                found = true;
                ++checked;
                break;
            }
            if (!found) { std::cerr << "Illegal PV move: " << text << '\n'; return 4; }
        }
    }
    std::cout << "Legal PV plies checked: " << checked << '\n';
    return checked == 0 ? 5 : 0;
}
