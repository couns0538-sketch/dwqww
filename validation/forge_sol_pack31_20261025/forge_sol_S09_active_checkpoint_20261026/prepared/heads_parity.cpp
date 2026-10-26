// buckets8 parity harness (own tool). Builds against any Forge core, old
// single-head or new 8-head, so the same source compares both.
// For each FEN line: refresh + evaluate, then `plies` seeded random legal
// moves with incremental update; at every step prints
//   <line> <ply> <pieces> <head> <net_cp> <hce_cp> <incremental==refresh>
// head = clamp((pieces-1)>>2, 0, 7), computed here so the lock core links too.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>

using namespace forge;

int main(int argc, char** argv) {
    if (argc < 2) { std::fprintf(stderr, "usage: heads_parity FENS [plies=8]\n"); return 2; }
    const int plies = argc > 2 ? std::atoi(argv[2]) : 8;
    std::ifstream in(argv[1]);
    std::string line;
    std::uint64_t rng = 0x9e3779b97f4a7c15ULL;
    long n = 0, acc_mismatch = 0;
    while (std::getline(in, line)) {
        std::string fen = line.substr(0, line.find('|'));
        while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\r')) fen.pop_back();
        Board board;
        if (!board.set_fen(fen)) { std::printf("%ld BAD\n", n++); continue; }
        nnue::Accumulator acc;
        nnue::refresh(board, acc);
        for (int ply = 0;; ++ply) {
            nnue::Accumulator fresh;
            nnue::refresh(board, fresh);
            const bool same = std::memcmp(&fresh.values, &acc.values, sizeof(acc.values)) == 0;
            if (!same) ++acc_mismatch;
            const int pieces = popcount(board.occupied());
            int head = (pieces - 1) >> 2; head = head < 0 ? 0 : (head > 7 ? 7 : head);
            std::printf("%ld %d %d %d %d %d %d\n", n, ply, pieces, head, nnue::evaluate(board, acc),
                        Evaluator::evaluate_uncached(board), same ? 1 : 0);
            if (ply == plies) break;
            const auto moves = board.legal_moves();
            if (moves.empty()) break;
            rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
            const auto move = moves[static_cast<std::size_t>((rng >> 33) % moves.size())];
            const auto dirty = nnue::dirty_pieces(board, move);
            Undo undo;
            if (!board.make_move(move, undo)) { std::printf("%ld ILLEGAL\n", n); break; }
            nnue::Accumulator child;
            nnue::update(acc, child, dirty);
            acc = child;
        }
        ++n;
    }
    std::fprintf(stderr, "lines %ld available=%d residual=%d hidden=%d acc_mismatch=%ld\n", n, (int)nnue::available(),
                 (int)nnue::residual(), (int)nnue::HiddenSize, acc_mismatch);
    return 0;
}
