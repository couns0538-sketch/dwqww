// Microbenchmark: cost of hist_rework::lesser_threats(board), the per-node map build.
#include "forge/board.hpp"
#include "forge/hist_rework.hpp"
#include <chrono>
#include <cstdio>
#include <string>
#include <vector>
using namespace forge;
int main() {
    std::vector<std::string> fens = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    };
    std::vector<Board> boards;
    for (auto& f : fens) { Board b; if (!b.set_fen(f)) return 1; boards.push_back(b); }
    constexpr long N = 400000;
    std::uint64_t sink = 0;
    for (long i = 0; i < N; ++i) {  // warmup
        asm volatile("" ::: "memory");
        auto t = hist_rework::lesser_threats(boards[i & 7]);
        asm volatile("" : "+m"(t)::);
        sink ^= t.by_type[3];
    }
    const auto t0 = std::chrono::steady_clock::now();
    for (long i = 0; i < N * 8; ++i) {
        asm volatile("" ::: "memory");
        auto t = hist_rework::lesser_threats(boards[i & 7]);
        asm volatile("" : "+m"(t)::);
        sink ^= t.by_type[3];
    }
    const auto t1 = std::chrono::steady_clock::now();
    const double ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / (N * 8);
    std::printf("lesser_threats: %.1f ns per build (sink %llu)\n", ns, (unsigned long long)sink);
    return 0;
}
