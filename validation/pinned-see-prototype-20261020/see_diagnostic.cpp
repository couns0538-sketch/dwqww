#include "forge/board.hpp"
#include <algorithm>
#include <array>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) throw std::runtime_error("expected cases.tsv");
    std::ifstream input(argv[1]);
    if (!input) throw std::runtime_error("cannot open cases");
    constexpr std::array thresholds{-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700};
    std::cout << "id\tinitial_legal\tstatic_exchange\tlegal_recaptures";
    for (int threshold : thresholds) std::cout << "\tge" << threshold;
    std::cout << '\n';
    std::string line;
    while (std::getline(input, line)) {
        auto a = line.find('\t'), b = line.find('\t', a + 1);
        if (a == std::string::npos || b == std::string::npos) throw std::runtime_error("bad row");
        forge::Board board;
        std::string error;
        if (!board.set_fen(line.substr(a+1,b-a-1), &error)) throw std::runtime_error(error);
        auto moves = board.pseudo_legal_moves();
        auto found = std::find_if(moves.begin(), moves.end(), [&](const forge::Move& move) {
            return forge::Board::move_to_uci(move) == line.substr(b+1);
        });
        if (found == moves.end() || !board.is_pseudo_legal(*found)) throw std::runtime_error("initial move not found");
        const auto move = *found;
        bool legal = board.is_legal(move);
        std::cout << line.substr(0,a) << '\t' << legal << '\t' << board.static_exchange(move) << '\t';
        if (legal) {
            forge::Undo undo;
            if (!board.make_move(move, undo)) throw std::runtime_error("make failed");
            bool first = true;
            for (auto recapture : board.legal_moves(true)) {
                if (!recapture.is_capture() || recapture.to != move.to) continue;
                if (!first) std::cout << ',';
                first = false;
                std::cout << forge::Board::move_to_uci(recapture);
            }
            board.unmake_move(move, undo);
        } else std::cout << "INITIAL_ILLEGAL";
        for (int threshold : thresholds) std::cout << '\t' << board.see_ge(move, threshold);
        std::cout << '\n';
    }
    if (input.bad()) throw std::runtime_error("bad input");
}
