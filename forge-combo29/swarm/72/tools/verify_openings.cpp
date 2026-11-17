// Original MIT-licensed independent opening verifier.
// Build against the external Fastchess chess.hpp header; it is not part of Forge.
#include <chess.hpp>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

std::vector<std::string> legal(const chess::Board& board) {
    chess::Movelist moves;
    chess::movegen::legalmoves(moves, board);
    std::vector<std::string> result;
    for (const auto& move : moves) result.push_back(chess::uci::moveToUci(move));
    std::sort(result.begin(), result.end());
    return result;
}

std::string first_three(const std::string& fen) {
    std::istringstream stream(fen);
    std::string a, b, c;
    stream >> a >> b >> c;
    return a + ' ' + b + ' ' + c;
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: verify_openings FILE.moves");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open moves file");
        std::string row;
        std::size_t positions = 0, plies = 0;
        while (std::getline(input, row)) {
            const auto first = row.find('\t');
            const auto second = row.find('\t', first + 1);
            if (first == std::string::npos || second == std::string::npos) throw std::runtime_error("invalid row");
            const std::string expected = row.substr(first + 1, second - first - 1);
            chess::Board board;
            std::istringstream sequence(row.substr(second + 1));
            std::string token;
            int count = 0;
            while (sequence >> token) {
                const auto move = chess::uci::uciToMove(board, token);
                chess::Movelist choices;
                chess::movegen::legalmoves(choices, board);
                if (std::find(choices.begin(), choices.end(), move) == choices.end()) {
                    throw std::runtime_error("illegal move in opening " + row.substr(0, first) + ": " + token);
                }
                board.makeMove(move);
                ++count;
                ++plies;
            }
            chess::Board target(expected);
            // The two engines may serialize an uncapturable EP square differently.
            // Compare piece placement, side, castling, and ALL legal moves instead.
            if (count != 12 || first_three(board.getFen()) != first_three(expected) ||
                legal(board) != legal(target)) throw std::runtime_error("replay disagrees with stored FEN");
            ++positions;
        }
        if (positions == 0) throw std::runtime_error("empty corpus");
        std::cout << "independent legal replay PASS: " << positions << " positions, " << plies << " plies\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
