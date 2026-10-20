#include "forge/board.hpp"
#include <algorithm>
#include <array>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>

bool promotion_guard(const forge::Board& board, const forge::Move& move) {
    if (move.is_castle() || forge::piece_type(board.piece_at(move.from)) == forge::King) return false;
    const int rank = forge::rank_of(move.to);
    if (rank != 0 && rank != 7) return false;
    const auto promoter = rank == 7 ? forge::White : forge::Black;
    const int captured = (move.flags & forge::EnPassant) != 0U
        ? move.to - forge::pawn_push_delta(board.side_to_move()) : move.to;
    return (board.pieces(promoter, forge::Pawn) &
            forge::attacks::pawn(forge::opposite(promoter), move.to) &
            ~(forge::square_bb(move.from) | forge::square_bb(captured))) != 0;
}

int main(int argc, char** argv) {
    if (argc != 3) throw std::runtime_error("expected cases.tsv brackets.tsv");
    std::ifstream input(argv[1]), brackets(argv[2]);
    if (!input || !brackets) throw std::runtime_error("cannot open fixture");
    std::map<std::string, std::array<int, 3>> adjacent;
    std::string line;
    while (std::getline(brackets, line)) {
        std::istringstream row(line);
        std::string id;
        std::array<int, 3> values{};
        if (!(row >> id >> values[0] >> values[1] >> values[2])) throw std::runtime_error("bad bracket");
        adjacent.emplace(id, values);
    }
    constexpr std::array thresholds{-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700};
    std::cout << "id\tinitial_legal\tstatic_exchange\tlegal_recaptures";
    for (int threshold : thresholds) std::cout << "\tge" << threshold;
    std::cout << "\tpromotion_guard\tadjacent_thresholds\n";
    while (std::getline(input, line)) {
        const auto a = line.find('\t'), b = line.find('\t', a + 1);
        if (a == std::string::npos || b == std::string::npos) throw std::runtime_error("bad case");
        const std::string id = line.substr(0, a);
        forge::Board board;
        std::string error;
        if (!board.set_fen(line.substr(a + 1, b - a - 1), &error)) throw std::runtime_error(error);
        const auto moves = board.pseudo_legal_moves();
        const auto found = std::find_if(moves.begin(), moves.end(), [&](const forge::Move& move) {
            return forge::Board::move_to_uci(move) == line.substr(b + 1);
        });
        if (found == moves.end() || !board.is_pseudo_legal(*found)) throw std::runtime_error("initial move missing");
        const auto move = *found;
        const bool legal = board.is_legal(move);
        std::cout << id << '\t' << legal << '\t' << board.static_exchange(move) << '\t';
        if (legal) {
            forge::Undo undo;
            if (!board.make_move(move, undo)) throw std::runtime_error("make failed");
            bool first = true;
            for (const auto recapture : board.legal_moves(true)) {
                if (!recapture.is_capture() || recapture.to != move.to) continue;
                if (!first) std::cout << ',';
                first = false;
                std::cout << forge::Board::move_to_uci(recapture);
            }
            board.unmake_move(move, undo);
        } else {
            std::cout << "INITIAL_ILLEGAL";
        }
        for (int threshold : thresholds) std::cout << '\t' << board.see_ge(move, threshold);
        std::cout << '\t' << promotion_guard(board, move) << '\t';
        const auto bracket = adjacent.find(id);
        if (bracket == adjacent.end()) {
            std::cout << '-';
        } else {
            bool first = true;
            for (int threshold : bracket->second) {
                if (!first) std::cout << ',';
                first = false;
                std::cout << threshold << ':' << board.see_ge(move, threshold);
            }
        }
        std::cout << '\n';
    }
    if (input.bad() || brackets.bad()) throw std::runtime_error("fixture read failure");
}
