// Original Forge test helper; no external chess implementation.
// Build: g++ -std=c++20 -O2 -Iinclude astra_r8/tmfit/tmfit_referee.cpp src/board.cpp src/bitboard.cpp -o tmfit_referee
#include "forge/board.hpp"
#include <iostream>
#include <sstream>
#include <string>

int main() {
    forge::Board board;
    std::string command;
    while (std::getline(std::cin, command)) {
        if (command == "quit") break;
        bool ok = true;
        if (command.rfind("fen ", 0) == 0) ok = board.set_fen(command.substr(4));
        else if (command.rfind("push ", 0) == 0) {
            auto move = board.parse_uci(command.substr(5));
            forge::Undo undo;
            ok = move && board.is_legal(*move) && board.make_move(*move, undo);
        } else if (command != "state") ok = false;
        const auto moves = board.legal_moves();
        std::istringstream fields(board.fen());
        std::string placement, side, castling, ep;
        int halfmove = 0, fullmove = 0;
        fields >> placement >> side >> castling >> ep >> halfmove >> fullmove;
        std::string outcome = "ongoing";
        if (moves.empty()) outcome = board.in_check() ? "checkmate" : "stalemate";
        else if (board.is_repetition()) outcome = "threefold";
        else if (halfmove >= 100) outcome = "fifty_move";
        else if (board.is_insufficient_material()) outcome = "insufficient";
        std::cout << "{\"ok\":" << (ok ? "true" : "false")
                  << ",\"fen\":\"" << board.fen() << "\",\"outcome\":\"" << outcome
                  << "\",\"legal\":[";
        bool first = true;
        for (auto move : moves) {
            if (!first) std::cout << ',';
            first = false;
            std::cout << '"' << forge::Board::move_to_uci(move) << '"';
        }
        std::cout << "]}" << std::endl;
    }
}
