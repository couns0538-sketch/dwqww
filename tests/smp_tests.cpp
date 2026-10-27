// Lazy SMP housekeeping (O1): worker-list lifetime.
#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static const void* all_workers(Worker& worker) { return worker.all_workers_; }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;

namespace {

int failures = 0;
int checks = 0;

void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) {
        ++failures;
        std::cout << "FAIL " << name << '\n';
    }
}

Board position(const std::string& fen) {
    Board board;
    if (!board.set_fen(fen)) throw std::runtime_error("invalid fixture FEN: " + fen);
    return board;
}

bool legal(const Board& board, Move move) {
    for (const Move m : board.legal_moves()) {
        if (m == move) return true;
    }
    return false;
}

constexpr int Threads = 3;
const std::vector<std::string> Fens{
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
};

void test_worker_list_lifetime() {
    for (const int threads : {1, Threads}) {
        Searcher searcher(16, threads);
        SearchLimits limits;
        limits.depth = 8;
        (void)searcher.search(position(Fens[0]), limits);
        check(Probe::all_workers(searcher.main_worker()) == nullptr,
              "worker list pointer cleared after the search (threads " + std::to_string(threads) + ")");
    }
}

} // namespace

int main() {
    test_worker_list_lifetime();
    std::cout << "smp housekeeping: checks=" << checks << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " smp_tests\n";
    return failures == 0 ? 0 : 1;
}
