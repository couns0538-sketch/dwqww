#include "krk_oracle.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

// Scratch diagnostic: exact KRK retrograde values, not an alpha-beta search.
// This oracle ignores path repetition and the fifty-move rule.
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::ifstream input(argv[1]);
    if (!input) return 3;
    soak::KrkTablebase oracle;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream row(line);
        std::string tag, fen, raw_text, bound_text;
        if (!std::getline(row, tag, '\t') || !std::getline(row, fen, '\t') ||
            !std::getline(row, raw_text, '\t') || !std::getline(row, bound_text)) return 4;
        const int raw = std::stoi(raw_text), bound = std::stoi(bound_text);
        forge::Board board;
        if (!board.set_fen(fen)) return 5;
        const auto rook = board.pieces(forge::White, forge::Rook);
        if (forge::popcount(rook) != 1 || forge::popcount(board.occupied()) != 3) return 6;
        const int wk = board.king_square(forge::White), wr = forge::lsb(rook);
        const int bk = board.king_square(forge::Black);
        const int stm = board.side_to_move() == forge::White ? 0 : 1;
        const bool legal = oracle.is_legal_state(wk, wr, bk, stm);
        const int dtm = legal ? oracle.dtm(wk, wr, bk, stm) : -1;
        const int exact = dtm < 0 ? 0 : (stm == 0 ? 32000 - dtm : -32000 + dtm);
        const bool inequality = dtm >= 0 && (bound == 1 ? exact <= raw :
            bound == 2 ? exact >= raw : bound == 3 && exact == raw);
        std::cout << tag << "\tfen=" << fen << "\tlegal=" << legal << "\tdtm=" << dtm
                  << "\texact_normalized=" << exact << "\traw=" << raw << "\tbound=" << bound
                  << "\tbound_relation=" << inequality << "\tclock_plus_dtm="
                  << board.halfmove_clock() + dtm << '\n';
    }
}
