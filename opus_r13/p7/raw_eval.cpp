// R13 P7 (own code): the lock's raw static eval (side to move, centipawns) of every FEN in a file, as
// Worker::static_evaluate computes it (lock d4f4312 = E3's base; E3 post-processes exactly this value):
//   residual net: clamp(HCE + network, -(MateInMaxPly - 1), MateInMaxPly - 1); pure net: network.
// CR R13 fix: the first version called Evaluator::refresh_runtime_psqt / evaluate_runtime, which are private on the lock
// (friend class Worker) and did not compile. The HCE term now comes from the public Evaluator::evaluate_uncached ("evaluation
// without any cache, for tests and tools"); the runtime PSQT path is the search's incremental form of the same value
// (the lock's tests/runtime_psqt_tests.cpp checks that equality).
// Build against the lock source (git d4f4312 src/include), e.g.
//   g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -static -Iinclude \
//       raw_eval.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o raw_eval.exe
// usage: raw_eval <fens.txt> > evals.txt   (one integer per FEN; exits 1 at the first FEN the board rejects)
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
    if (!in) {
        std::cerr << "cannot open " << argv[1] << "\n";
        return 2;
    }
    std::string fen;
    auto accumulator = std::make_unique<forge::nnue::Accumulator>();
    const bool residual = forge::nnue::residual();
    long line = 0;
    while (std::getline(in, fen)) {
        ++line;
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty()) continue;
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) {
            std::cerr << "line " << line << ": bad FEN (" << error << "): " << fen << "\n";
            return 1;
        }
        forge::nnue::refresh(board, *accumulator);
        const int network = forge::nnue::evaluate(board, *accumulator);
        int raw = network;
        if (residual) {
            raw = std::clamp(forge::Evaluator::evaluate_uncached(board) + network, -forge::MateInMaxPly + 1,
                             forge::MateInMaxPly - 1);
        }
        std::cout << raw << "\n";
    }
    return 0;
}
