// hce_hash.cpp - FORGE_SPD_HCE_LOCALS proof harness (speed hunt vs trial_w6, own code).
// Hashes (FNV-1a) the hand-crafted evaluation of every node of perft walks (bench positions + specials + FENs from a
// file): Evaluator::evaluate_uncached() and evaluate_traced() (white_eval, phase, scale and every trace coefficient).
// Build it with -DFORGE_SPD_HCE_LOCALS=0 and =1 from the same tree: both must print the same hash. -DMUTANT=1 adds 1 to
// every 97th evaluation before hashing (the hash must change). Build from a hunt tree root:
//   g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=znver5 -Iinclude <six trial_w6 -D values>
//   -DFORGE_SPD_HCE_LOCALS=<0|1> tests/hce_hash.cpp src/board.cpp src/bitboard.cpp src/eval.cpp src/eval_params.cpp
//   -o hce_hash.exe ; run: <exe> <fens file> <max fens> <depth>
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/eval_params.hpp"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

namespace {
std::uint64_t hash = 1469598103934665603ULL, evals = 0;

void mix(const void* data, std::size_t n) {
    const unsigned char* p = static_cast<const unsigned char*>(data);
    for (std::size_t i = 0; i < n; ++i) { hash ^= p[i]; hash *= 1099511628211ULL; }
}

void eval_node(const forge::Board& board) {
    int e = forge::Evaluator::evaluate_uncached(board);
#if MUTANT
    if (evals % 97 == 0) e += 1;
#endif
    mix(&e, sizeof(e));
    forge::EvalTrace trace;
    const int t = forge::evaluate_traced(board, trace);
    mix(&t, sizeof(t));
    mix(&trace.phase, sizeof(trace.phase));
    mix(&trace.scale, sizeof(trace.scale));
    mix(trace.coefficients.data(), sizeof(trace.coefficients));
    ++evals;
}

void walk(forge::Board& board, int depth) {
    eval_node(board);
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
    std::printf("hce_hash: HCE_LOCALS=%d %zu FENs (%d rejected) depth %d: %llu evaluations, hash %016llx\n",
                FORGE_SPD_HCE_LOCALS, fens.size(), rejected, depth, static_cast<unsigned long long>(evals),
                static_cast<unsigned long long>(hash));
    return 0;
}
