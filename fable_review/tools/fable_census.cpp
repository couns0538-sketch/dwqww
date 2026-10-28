#include "forge/board.hpp"
#include <iostream>
#include <string>
int main() {
    using namespace forge;
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        Board board; std::string error;
        if (!board.set_fen(line, &error)) { std::cout << "invalid " << error << '\n'; continue; }
        const MoveList noisy = board.pseudo_legal_moves(true);
        int losing = 0, legal_losing = 0, promotions = 0;
        for (const Move move : noisy) {
            if (move.is_promotion()) ++promotions;
            if (!board.see_ge(move, 0)) { ++losing; if (board.is_legal(move)) ++legal_losing; }
        }
        std::cout << "ok " << noisy.size() << ' ' << losing << ' ' << legal_losing << ' ' << (board.in_check() ? 1 : 0) << ' ' << promotions << '\n';
    }
}
