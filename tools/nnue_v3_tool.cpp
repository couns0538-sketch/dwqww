// NNUE v3 command-line tool (job FB1).
//   forge_nnue_v3_tool info <net>
//   forge_nnue_v3_tool eval <net> <fen file>      one line per FEN: cp bucket kb_w flip_w kb_b flip_b
//   forge_nnue_v3_tool sum  <net> <fen file>      one line per FEN: raw int64 output sum (before b2/scaling)
// cp is the network output alone (side to move, centipawns); the residual flag is reported by `info`.
#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"

#include <fstream>
#include <iostream>
#include <string>

namespace {

int usage() {
    std::cerr << "usage: forge_nnue_v3_tool info <net> | eval <net> <fen file> | sum <net> <fen file>\n";
    return 2;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) return usage();
    const std::string command = argv[1];
    std::string error;
    if (!forge::nnue::v3::load(argv[2], &error)) {
        std::cerr << "ERROR NNUE v3: " << error << '\n';
        return 1;
    }
    const forge::nnue::v3::Net& net = *forge::nnue::v3::loaded();
    if (command == "info") {
        std::cout << forge::nnue::v3::describe(net) << '\n';
        return 0;
    }
    if ((command != "eval" && command != "sum") || argc < 4) return usage();
    std::ifstream in(argv[3]);
    if (!in) {
        std::cerr << "cannot open " << argv[3] << '\n';
        return 1;
    }
    std::string line;
    forge::Board board;
    int count = 0;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty()) continue;
        if (!board.set_fen(line)) {
            std::cout << "BADFEN\n";
            continue;
        }
        const forge::nnue::v3::KingKey white = forge::nnue::v3::king_key(net, forge::White, board.king_square(forge::White));
        const forge::nnue::v3::KingKey black = forge::nnue::v3::king_key(net, forge::Black, board.king_square(forge::Black));
        const int bucket = forge::nnue::v3::output_bucket(net, board);
        if (command == "eval") {
            std::cout << forge::nnue::v3::evaluate_reference(net, board) << ' ' << bucket << ' '
                      << static_cast<int>(white.bucket) << ' ' << static_cast<int>(white.flip) << ' '
                      << static_cast<int>(black.bucket) << ' ' << static_cast<int>(black.flip) << '\n';
        } else {
            forge::nnue::v3::Accumulator accumulator;
            forge::nnue::v3::refresh(net, board, accumulator);
            const forge::Color us = board.side_to_move();
            std::cout << forge::nnue::v3::output_sum_scalar(net, accumulator.values[static_cast<std::size_t>(us)].data(),
                                                             accumulator.values[static_cast<std::size_t>(forge::opposite(us))].data(), bucket)
                      << '\n';
        }
        ++count;
    }
    std::cerr << count << " positions\n";
    return 0;
}
