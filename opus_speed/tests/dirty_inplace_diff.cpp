// dirty_inplace_diff.cpp - FORGE_SPD_DIRTY_INPLACE proof harness (speed hunt vs trial_w6, own code).
// For every pseudo-legal move of every node of perft walks (bench positions + kiwipete + FENs from a file), the in-place
// fill_dirty_pieces() into a 0xA5-poisoned DirtyPieces must give the same count and the same used slots (piece,
// square, add) as the lock's dirty_pieces(). -DMUTANT=1 swaps the first two entries of a capture (must FAIL).
// Build (from the hunt tree root): g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=znver5 -Iinclude
//   <six trial_w6 -D values> -DFORGE_SPD_DIRTY_INPLACE=1 tests/dirty_inplace_diff.cpp src/board.cpp src/bitboard.cpp
//   src/nnue.cpp -o dirty_diff.exe ; run: dirty_diff.exe <fens file> <max fens> <depth>
#include "forge/board.hpp"
#include "forge/nnue.hpp"

#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#if !FORGE_SPD_DIRTY_INPLACE
#error "build with -DFORGE_SPD_DIRTY_INPLACE=1"
#endif

namespace {
std::uint64_t compared = 0, mismatches = 0;

void check(const forge::Board& board, const forge::Move& move) {
    const forge::nnue::DirtyPieces want = forge::nnue::dirty_pieces(board, move);
    forge::nnue::DirtyPieces got;
    std::memset(static_cast<void*>(&got), 0xA5, sizeof(got));
    forge::nnue::fill_dirty_pieces(got, board, move);
#if MUTANT
    if (got.count == 3) std::swap(got.changes[0], got.changes[1]);
#endif
    ++compared;
    bool same = want.count == got.count;
    for (int i = 0; same && i < want.count; ++i) {
        const auto& a = want.changes[static_cast<std::size_t>(i)];
        const auto& b = got.changes[static_cast<std::size_t>(i)];
        same = a.piece == b.piece && a.square == b.square && a.add == b.add;
    }
    if (!same && ++mismatches <= 5) {
        std::printf("MISMATCH fen %s move %s count %d vs %d\n", board.fen().c_str(),
                    forge::Board::move_to_uci(move).c_str(), want.count, got.count);
    }
}

void walk(forge::Board& board, int depth) {
    const forge::MoveList moves = board.pseudo_legal_moves(false);
    for (const forge::Move move : moves) {
        check(board, move);
        if (depth <= 1 || !board.is_legal(move)) continue;
        forge::Undo undo;
        (void)board.make_move(move, undo);
        walk(board, depth - 1);
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
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",                       // promotions both ways
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",  // en passant
    };
    const int max_fens = argc > 2 ? std::atoi(argv[2]) : 2000;
    const int depth = argc > 3 ? std::atoi(argv[3]) : 3;
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
    std::printf("dirty_inplace_diff: %zu FENs (%d rejected), depth %d, %llu moves compared, %llu mismatches -> %s\n",
                fens.size(), rejected, depth, static_cast<unsigned long long>(compared),
                static_cast<unsigned long long>(mismatches), mismatches == 0 ? "PASS" : "FAIL");
    return mismatches == 0 ? 0 : 1;
}
