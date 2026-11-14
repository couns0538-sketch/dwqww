#include "forge/board.hpp"
#include <iostream>

int main() {
    forge::Board board;
    if (!board.set_fen("8/8/8/8/8/5R2/1k1K4/8 b - - 15 8")) return 2;
    std::cout << "TARGET_KEY " << board.key() << " FEN " << board.fen() << '\n';
}
