// nnue_int16_dump (opus-sol-SA2): per "FEN | ..." line, the engine's own NNUE values on both paths.
// Built against the engine sources (forge::nnue with its compiled-in net), e.g. with the box recipe flags:
//   g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static
//       -Iinclude opus_round1/sol_SA2/nnue_int16_dump.cpp src/{nnue,bitboard,board,eval,eval_params}.cpp -o dump.exe
// (-march=x86-64 instead selects the scalar integer kernels). usage: dump <fens.txt> > out.tsv
// Output, one line per FEN: idx float_cp int_cp hce sigW sigB inc_int_bad inc_float_bad
//   float_cp / int_cp = nnue::evaluate after a fresh refresh with NnueInt16 OFF / ON (STM cp, the network term);
//   hce = Evaluator::evaluate_uncached (the residual base); sigW/sigB = sum_h (h+1)*A[h] of the int32
//   accumulator of each perspective (lets the Python reference check the accumulators, not only the cp);
//   inc_*_bad = plies (of up to 4 seeded random legal moves or null moves from this FEN) whose incrementally
//   updated accumulator differs from a fresh refresh, per mode.
// A header line "# hidden H available A int16_available I residual R" goes to stderr.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <string>

using namespace forge;

namespace {

std::uint64_t mix(std::uint64_t x) {
    x += 0x9E3779B97F4A7C15ULL;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31);
}

long long signature(const nnue::Accumulator& acc, Color perspective) {
    long long sum = 0;
    for (int h = 0; h < nnue::HiddenSize; ++h)
        sum += static_cast<long long>(h + 1) * acc.integer_values[static_cast<std::size_t>(perspective)][static_cast<std::size_t>(h)];
    return sum;
}

// Up to four seeded moves from `start`; counts plies where update != refresh in the current mode.
int incremental_mismatches(const Board& start, std::uint64_t seed, bool integer) {
    Board board = start;
    nnue::Accumulator parent;
    nnue::refresh(board, parent);
    int bad = 0;
    for (int ply = 0; ply < 4; ++ply) {
        const MoveList moves = board.legal_moves();
        if (moves.size() == 0) break;
        seed = mix(seed);
        nnue::Accumulator child;
        if (!board.in_check() && seed % 8 == 0) {
            NullUndo undo;
            nnue::update(parent, child, nnue::DirtyPieces{});
            board.make_null_move(undo);
        } else {
            const Move move = moves[static_cast<std::size_t>((seed >> 8) % moves.size())];
            const nnue::DirtyPieces dirty = nnue::dirty_pieces(board, move);
            nnue::update(parent, child, dirty);
            Undo undo;
            if (!board.make_move(move, undo)) return bad + 100;
        }
        nnue::Accumulator fresh;
        nnue::refresh(board, fresh);
        const bool same = integer ? (child.integer && fresh.integer && child.integer_values == fresh.integer_values)
                                  : (!child.integer && !fresh.integer && child.values == fresh.values);
        if (!same) ++bad;
        parent = child;
    }
    return bad;
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: %s <fens.txt>\n", argv[0]);
        return 2;
    }
    std::fprintf(stderr, "# hidden %d available %d int16_available %d residual %d\n", nnue::HiddenSize,
                 static_cast<int>(nnue::available()), static_cast<int>(nnue::int16_available()), static_cast<int>(nnue::residual()));
    if (!nnue::available() || !nnue::int16_available()) return 3;
    std::ifstream in(argv[1]);
    std::string line;
    long long index = 0;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::string fen = line.substr(0, line.find('|'));
        while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\r')) fen.pop_back();
        Board board;
        if (!board.set_fen(fen)) {
            std::printf("%lld BAD\n", index++);
            continue;
        }
        (void)nnue::set_int16(false);
        nnue::Accumulator acc;
        nnue::refresh(board, acc);
        const int float_cp = nnue::evaluate(board, acc);
        const int inc_float = incremental_mismatches(board, static_cast<std::uint64_t>(index), false);
        (void)nnue::set_int16(true);
        nnue::refresh(board, acc);
        const int int_cp = nnue::evaluate(board, acc);
        const long long sig_white = signature(acc, White);
        const long long sig_black = signature(acc, Black);
        const int inc_int = incremental_mismatches(board, static_cast<std::uint64_t>(index), true);
        const int hce = Evaluator::evaluate_uncached(board);
        std::printf("%lld %d %d %d %lld %lld %d %d\n", index, float_cp, int_cp, hce, sig_white, sig_black, inc_int, inc_float);
        ++index;
    }
    return 0;
}
