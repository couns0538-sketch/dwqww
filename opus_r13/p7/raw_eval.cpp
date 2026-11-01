// R13 P7 (own code): the lock's raw static eval (side to move, centipawns) of every FEN in a file, as
// Worker::static_evaluate computes it (lock d4f4312 = E3's base; E3 post-processes exactly this value):
//   residual net: clamp(HCE runtime eval + network, -(MateInMaxPly - 1), MateInMaxPly - 1); pure net: network.
// Build against the lock source (git d4f4312 src/include), e.g.
//   g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -static -Iinclude \
//       raw_eval.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o raw_eval.exe
// usage: raw_eval <fens.txt> > evals.txt   (one integer per FEN, or ERR)
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: raw_eval <fens.txt>\n";
        return 2;
    }
    if (!forge::nnue::available() || !forge::nnue::enabled) {
        std::cerr << "no compiled-in network\n";
        return 2;
    }
    std::ifstream in(argv[1]);
    std::string fen;
    forge::Evaluator evaluator;
    auto accumulator = std::make_unique<forge::nnue::Accumulator>();
    const bool residual = forge::nnue::residual();
    while (std::getline(in, fen)) {
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty()) continue;
        forge::Board board;
        if (!board.set_fen(fen)) {
            std::cout << "ERR\n";
            continue;
        }
        forge::nnue::refresh(board, *accumulator);
        const int network = forge::nnue::evaluate(board, *accumulator);
        int raw = network;
        if (residual) {
            raw = std::clamp(evaluator.evaluate_runtime(board, forge::Evaluator::refresh_runtime_psqt(board)) + network,
                             -forge::MateInMaxPly + 1, forge::MateInMaxPly - 1);
        }
        std::cout << raw << "\n";
    }
    return 0;
}
