#include "forge/board.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) throw std::runtime_error("expected cases.tsv");
    std::ifstream input(argv[1]);
    if (!input) throw std::runtime_error("cannot open cases");
    std::string line;
    std::cout << "id\tinitial_legal\tsee0\tsee100\tsee101\tstatic_exchange\tlegal_recaptures\n";
    int cases = 0;
    while (std::getline(input, line)) {
        const auto a = line.find('\t');
        const auto b = line.find('\t', a + 1);
        if (a == std::string::npos || b == std::string::npos) throw std::runtime_error("bad row");
        const std::string id = line.substr(0, a);
        const std::string fen = line.substr(a + 1, b - a - 1);
        const std::string uci = line.substr(b + 1);
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) throw std::runtime_error(error);
        const auto moves = board.pseudo_legal_moves();
        const auto found = std::find_if(moves.begin(), moves.end(), [&](const forge::Move& move) {
            return forge::Board::move_to_uci(move) == uci;
        });
        if (found == moves.end() || !board.is_pseudo_legal(*found) || !found->is_capture())
            throw std::runtime_error("initial capture not found");
        const forge::Move move = *found;
        const bool legal = board.is_legal(move);
        std::cout << id << '\t' << legal << '\t' << board.see_ge(move, 0) << '\t'
                  << board.see_ge(move, 100) << '\t' << board.see_ge(move, 101) << '\t'
                  << board.static_exchange(move) << '\t';
        if (legal) {
            forge::Undo undo;
            if (!board.make_move(move, undo)) throw std::runtime_error("make_move failed");
            bool first = true;
            for (const auto recapture : board.legal_moves(true)) {
                if (recapture.to != move.to || !recapture.is_capture()) continue;
                if (!first) std::cout << ',';
                first = false;
                std::cout << forge::Board::move_to_uci(recapture);
            }
            board.unmake_move(move, undo);
        } else {
            std::cout << "INITIAL_ILLEGAL";
        }
        std::cout << '\n';
        ++cases;
    }
    if (cases != 12 || input.bad()) throw std::runtime_error("incomplete matrix");
    return 0;
}
