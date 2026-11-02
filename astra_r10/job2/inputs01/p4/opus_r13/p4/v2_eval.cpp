// R13 P4 parity harness (own code): prints the Forge v2 static eval in centipawns of every FEN in a file, with a
// FORGENN2 net, through the engine's own loader (forge::nnue::v2::load), full refresh (piece-square + O6 threats +
// O7 pawn pairs from the engine's own feature code) and output kernel (forge::nnue::v2::evaluate).
// Build against forge-bundle-int b7c17722 (R3 stack) core sources, e.g.:
//   g++ -std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -Iinclude \
//       v2_eval.cpp src/{bitboard,board,book,datagen,eval,eval_params,nnue,search}.cpp -o v2_eval_avx2
//   (and -march=x86-64-v2 for the SSE path of nnue::v2::output)
// usage: v2_eval <net.nnue2> <fens.txt>   -> one line per FEN: the eval, or ERR
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v2.hpp"

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: v2_eval <net.nnue2> <fens.txt>\n";
        return 2;
    }
    std::string error;
    if (!forge::nnue::v2::load(argv[1], &error)) {
        std::cerr << "load failed: " << error << "\n";
        return 2;
    }
    const forge::nnue::v2::Net& net = *forge::nnue::v2::loaded();
    std::cerr << forge::nnue::v2::summary(net) << "\n";
    std::ifstream in(argv[2]);
    std::string fen;
    auto accumulator = std::make_unique<forge::nnue::Accumulator>();
    while (std::getline(in, fen)) {
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty()) continue;
        forge::Board board;
        if (!board.set_fen(fen)) {
            std::cout << "ERR\n";
            continue;
        }
        forge::nnue::v2::refresh(net, board, forge::White, accumulator->values[0].data());
        forge::nnue::v2::refresh(net, board, forge::Black, accumulator->values[1].data());
        std::cout << forge::nnue::v2::evaluate(net, board, *accumulator) << "\n";
    }
    return 0;
}
