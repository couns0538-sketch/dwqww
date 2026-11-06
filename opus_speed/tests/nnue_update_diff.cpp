// nnue_update_diff.cpp - FORGE_SPD_NNUE_COLUMNS proof harness (speed hunt vs trial_w6, own code).
// The lock net's accumulator arithmetic is exact (every w1 / b1 value is k * 2^-12 and every partial sum stays below
// 2^24 units), so a correct incremental update() must give the refresh() of the child position bit for bit. For every
// legal move of every node of perft walks (bench positions + kiwipete + FENs from a file) this compares
// update(refresh(parent), dirty_pieces(move)) with refresh(child) byte for byte (memcmp of both perspectives).
// -DMUTANT=1 moves the added piece of quiet moves one square (must FAIL). Build from a hunt tree root:
//   g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -march=znver5 -Iinclude <defines>
//   tests/nnue_update_diff.cpp src/board.cpp src/bitboard.cpp src/nnue.cpp -o nnue_diff.exe
// run: nnue_diff.exe <fens file> <max fens> <depth>
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

namespace {
std::uint64_t compared = 0, mismatches = 0;
std::uint64_t by_count[5] = {0, 0, 0, 0, 0};

void walk(forge::Board& board, int depth) {
    forge::nnue::Accumulator parent;
    forge::nnue::refresh(board, parent);
    const forge::MoveList moves = board.legal_moves(false);
    for (const forge::Move move : moves) {
        forge::nnue::DirtyPieces dirty = forge::nnue::dirty_pieces(board, move);
#if MUTANT
        if (dirty.count == 2) dirty.changes[1].square = static_cast<std::uint8_t>(dirty.changes[1].square ^ 1U);
#endif
        forge::Undo undo;
        (void)board.make_move(move, undo);
        forge::nnue::Accumulator child, fresh;
        forge::nnue::update(parent, child, dirty);
        forge::nnue::refresh(board, fresh);
        ++compared;
        ++by_count[dirty.count];
        if (std::memcmp(child.values.data(), fresh.values.data(), sizeof(child.values)) != 0 && ++mismatches <= 5) {
            board.unmake_move(move, undo);
            std::printf("MISMATCH fen %s move %s count %d\n", board.fen().c_str(),
                        forge::Board::move_to_uci(move).c_str(), dirty.count);
            (void)board.make_move(move, undo);
        }
        if (depth > 1) walk(board, depth - 1);
        board.unmake_move(move, undo);
    }
}
} // namespace

int main(int argc, char** argv) {
    std::vector<std::string> fens{
        std::string(forge::Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
    };
    const int max_fens = argc > 2 ? std::atoi(argv[2]) : 2000;
    const int depth = argc > 3 ? std::atoi(argv[3]) : 2;
    if (argc > 1) {
        std::ifstream in(argv[1]);
        std::string line;
        int n = 0;
        while (n < max_fens && std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (!line.empty()) { fens.push_back(line); ++n; }
        }
    }
    int rejected = 0;
    for (const std::string& fen : fens) {
        forge::Board board;
        if (!board.set_fen(fen)) { ++rejected; continue; }
        walk(board, depth);
    }
    std::printf("nnue_update_diff: %zu FENs (%d rejected), depth %d, %llu updates compared (count 2: %llu, 3: %llu, 4: %llu),"
                " %llu mismatches -> %s\n", fens.size(), rejected, depth, static_cast<unsigned long long>(compared),
                static_cast<unsigned long long>(by_count[2]), static_cast<unsigned long long>(by_count[3]),
                static_cast<unsigned long long>(by_count[4]), static_cast<unsigned long long>(mismatches),
                mismatches == 0 ? "PASS" : "FAIL");
    return mismatches == 0 ? 0 : 1;
}
