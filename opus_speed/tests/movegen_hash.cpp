// movegen_hash.cpp - FORGE_SPD_MOVE_STORE32 proof harness (speed hunt vs trial_w6, own code).
// Hashes (FNV-1a over count + every move's four bytes, in order) the pseudo-legal lists of all three GenModes at every
// node of perft walks (bench positions + specials + FENs from a file). Build it once with -DFORGE_SPD_MOVE_STORE32=0
// and once with =1 from the same tree: both must print the same hash and counts. -DMUTANT=1 drops the last move of
// every capture list before hashing (the hash must change). Build from a hunt tree root:
//   g++ -std=c++20 -O2 -DNDEBUG -march=znver5 -Iinclude <six trial_w6 -D values> -DFORGE_SPD_MOVE_STORE32=<0|1>
//   tests/movegen_hash.cpp src/board.cpp src/bitboard.cpp -o movegen_hash.exe ; run: <exe> <fens file> <max> <depth>
#include "forge/board.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

namespace {
std::uint64_t hash = 1469598103934665603ULL, lists = 0, moves_total = 0;

void mix(const void* data, std::size_t n) {
    const unsigned char* p = static_cast<const unsigned char*>(data);
    for (std::size_t i = 0; i < n; ++i) { hash ^= p[i]; hash *= 1099511628211ULL; }
}

void hash_list(const forge::Board& board, forge::Board::GenMode mode) {
    forge::MoveList list;
    board.generate_pseudo_legal(list, mode);
    std::size_t n = list.size();
#if MUTANT
    if (mode == forge::Board::GenMode::Captures && n > 0) --n;
#endif
    mix(&n, sizeof(n));
    for (std::size_t i = 0; i < n; ++i) mix(&list[i], sizeof(forge::Move));
    ++lists;
    moves_total += n;
}

void walk(forge::Board& board, int depth) {
    hash_list(board, forge::Board::GenMode::All);
    hash_list(board, forge::Board::GenMode::Captures);
    hash_list(board, forge::Board::GenMode::Quiets);
    if (depth <= 1) return;
    const forge::MoveList moves = board.legal_moves(false);
    for (const forge::Move move : moves) {
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
    std::printf("movegen_hash: STORE32=%d %zu FENs (%d rejected) depth %d: %llu lists, %llu moves, hash %016llx\n",
                FORGE_SPD_MOVE_STORE32, fens.size(), rejected, depth, static_cast<unsigned long long>(lists),
                static_cast<unsigned long long>(moves_total), static_cast<unsigned long long>(hash));
    return 0;
}
