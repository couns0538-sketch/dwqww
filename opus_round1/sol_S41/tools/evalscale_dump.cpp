// S41 evalscale_dump: per-position static evaluation of the compiled-in network, as the search computes it.
//
// Build once per network: copy src/nnue.cpp and the network (as nnue_weights.inc) into one scratch directory and
// compile this file with that nnue.cpp plus src/{bitboard,board,eval,eval_params}.cpp (see evalscale_20261027.py).
// Input: one position per line, "FEN" or "FEN | anything". Output, one line per input line:
//   <index> <stm> <in_check> <hce> <net> <total>
// hce   = Evaluator::evaluate_uncached (hand-crafted evaluation, side to move, cp)
// net   = nnue::evaluate after a fresh nnue::refresh (network output, side to move, cp)
// total = what Worker::static_evaluate returns for this position: clamp(hce + net, -MateInMaxPly + 1,
//         MateInMaxPly - 1) for a residual network, net for a stand-alone network.
// A line that is not a valid FEN prints "<index> BAD". The first stderr line names the network properties.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <cstdio>
#include <fstream>
#include <string>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: evalscale_dump <positions.txt>\n");
        return 2;
    }
    if (!forge::nnue::available()) {
        std::fprintf(stderr, "no network compiled in\n");
        return 3;
    }
    std::ifstream in(argv[1]);
    if (!in) {
        std::fprintf(stderr, "cannot open %s\n", argv[1]);
        return 2;
    }
    std::fprintf(stderr, "available=%d residual=%d hidden=%d\n", static_cast<int>(forge::nnue::available()),
                 static_cast<int>(forge::nnue::residual()), forge::nnue::HiddenSize);
    std::string line;
    long index = 0;
    forge::nnue::Accumulator accumulator;
    while (std::getline(in, line)) {
        std::string fen = line.substr(0, line.find('|'));
        while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\r' || fen.back() == '\t')) fen.pop_back();
        forge::Board board;
        if (fen.empty() || !board.set_fen(fen)) {
            std::printf("%ld BAD\n", index++);
            continue;
        }
        forge::nnue::refresh(board, accumulator);
        const int net = forge::nnue::evaluate(board, accumulator);
        const int hce = forge::Evaluator::evaluate_uncached(board);
        const int total = forge::nnue::residual()
            ? std::clamp(hce + net, -forge::MateInMaxPly + 1, forge::MateInMaxPly - 1)
            : net;
        std::printf("%ld %c %d %d %d %d\n", index++, board.side_to_move() == forge::White ? 'w' : 'b',
                    board.in_check() ? 1 : 0, hce, net, total);
    }
    return 0;
}
