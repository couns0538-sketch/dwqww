// R5C M4: the engine's v4 network value for every FEN of a file (parity input for tools/nnue/export_fnn4.py).
// usage: r5c_v4_eval <net.fnn4> <fens.txt> > out.txt     one line per FEN: "<scalar> <avx2>" (cp, side to move's view,
// network part only); without AVX2 in the build the second value is the scalar one again. Exit 1 on a bad file/FEN.
// Build: g++ <box flags> -Iinclude opus_r5/r5c/tools/r5c_v4_eval.cpp src/nnue_v4.cpp src/bitboard.cpp src/board.cpp
//        src/nnue.cpp src/eval.cpp src/eval_params.cpp -static   (plus whatever those units need in the tree)
#include "forge/board.hpp"
#include "forge/nnue_v4.hpp"

#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: r5c_v4_eval <net.fnn4> <fens.txt>\n";
        return 2;
    }
    std::string error;
    if (!forge::nnue_v4::load(argv[1], error)) {
        std::cerr << "r5c_v4_eval: " << error << '\n';
        return 1;
    }
    const forge::nnue_v4::Net& net = *forge::nnue_v4::loaded();
    std::cerr << "r5c_v4_eval: " << forge::nnue_v4::describe(net) << '\n';
    const bool avx2 = forge::nnue_v4::kernel_available(forge::nnue_v4::Kernel::Avx2);
    std::ifstream in(argv[2]);
    std::string line;
    long count = 0;
    while (std::getline(in, line)) {
        const std::string fen = line.substr(0, line.find('|'));
        if (fen.find_first_not_of(" \t\r") == std::string::npos) continue;
        forge::Board board;
        if (!board.set_fen(fen)) {
            std::cerr << "r5c_v4_eval: bad FEN on line " << count + 1 << ": " << fen << '\n';
            return 1;
        }
        const int scalar = forge::nnue_v4::evaluate_with(net, board, forge::nnue_v4::Kernel::Scalar);
        const int fast = avx2 ? forge::nnue_v4::evaluate_with(net, board, forge::nnue_v4::Kernel::Avx2) : scalar;
        std::cout << scalar << ' ' << fast << '\n';
        ++count;
    }
    std::cerr << "r5c_v4_eval: " << count << " positions\n";
    return 0;
}
