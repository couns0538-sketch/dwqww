// Polyglot key conformance probe.
//
// Prints the engine's own polyglot_key for a FEN, so it can be compared with
// chess.polyglot.zobrist_hash(). Focus: en-passant, where this engine hashes the
// ep file when a pawn merely STANDS BESIDE the double-pushed pawn, while the
// reference implementation hashes it only when an en-passant capture is LEGAL.
//
// Build (from forge-combo29/):
//   g++ -std=c++20 -O2 -Iinclude -DFORGE_NNUE_HIDDEN=256 \
//       -DFORGE_NNUE_WEIGHTS=\"$PWD/src/nnue_weights.inc\" \
//       swarm/65/scripts/key_probe.cpp src/board.cpp src/bitboard.cpp src/book.cpp \
//       src/eval.cpp src/eval_params.cpp src/nnue.cpp -o /tmp/key_probe -lpthread
//
// Usage: key_probe "<fen>" [more fens as separate args]

#include "forge/board.hpp"
#include "forge/book.hpp"

#include <cstdio>
#include <string>

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: key_probe <fen> [fen ...]\n");
        return 2;
    }
    for (int i = 1; i < argc; ++i) {
        forge::Board board;
        std::string error;
        if (!board.set_fen(argv[i], &error)) {
            std::printf("INVALID\t%s\t%s\n", argv[i], error.c_str());
            continue;
        }
        std::printf("%016llx\t%s\n",
                    static_cast<unsigned long long>(forge::book::polyglot_key(board)), argv[i]);
    }
    return 0;
}
