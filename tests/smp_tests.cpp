// Lazy SMP housekeeping (O1): worker-list lifetime, SmpExactNodes node accounting for node-limited
// multi-thread searches, SmpBestThread result consistency, and options inert at Threads=1.
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

// A deep search leaves large published counts in the helpers; a following node-limited search must
// not stop on them. With SmpExactNodes the counters are reset before the helpers start (deterministic)
// and the reported total is exact after the helpers stopped.
void test_exact_nodes() {
    const std::uint64_t limit = 20000;
    int premature_off = 0;
    for (const bool exact : {false, true}) {
        options::smp_exact_nodes = exact;
        for (int round = 0; round < 10; ++round) {
            Searcher searcher(16, Threads);
            SearchLimits deep;
            deep.depth = 13;
            const Board board = position(Fens[static_cast<std::size_t>(round) % Fens.size()]);
            (void)searcher.search(board, deep);
            SearchLimits nodes;
            nodes.nodes = limit;
            nodes.nodes_specified = true;
            const SearchInfo result = searcher.search(board, nodes);
            if (!exact) {
                premature_off += result.depth == 0 ? 1 : 0;
                continue;
            }
            const std::string r = " (round " + std::to_string(round) + ")";
            check(result.depth >= 2, "SmpExactNodes: node-limited search completes iterations" + r);
            check(result.nodes >= limit, "SmpExactNodes: reported total reaches the limit" + r);
            check(result.nodes < limit + static_cast<std::uint64_t>(Threads) * 2100,
                  "SmpExactNodes: overshoot bounded by the publish cadence" + r + " nodes=" + std::to_string(result.nodes));
            check(legal(board, result.best_move), "SmpExactNodes: legal best move" + r);
        }
    }
    options::smp_exact_nodes = false;
    // Informational: how often the default (OFF) path hits the stale-counter stop. Timing dependent.
    std::cout << "INFO SmpExactNodes=false: " << premature_off << "/10 node-limited searches stopped before "
              << "completing depth 1 (stale helper counters)\n";
}

void test_best_thread() {
    options::smp_best_thread = true;
    for (const std::string& fen : Fens) {
        Searcher searcher(16, Threads);
        SearchLimits limits;
        limits.depth = 11;
        const Board board = position(fen);
        const SearchInfo result = searcher.search(board, limits);
        check(legal(board, result.best_move), "SmpBestThread: legal best move " + fen);
        check(!result.pv.empty() && result.pv.front() == result.best_move, "SmpBestThread: PV starts with the best move");
        check(result.depth >= 11, "SmpBestThread: reported depth is at least the requested depth");
        check(result.ponder_move == (result.pv.size() > 1 ? result.pv[1] : Move::none()), "SmpBestThread: ponder move from the PV");
    }
    options::smp_best_thread = false;
}

// SmpBestThread ranking rule (better_thread_result): a mate score is never
// replaced by a deeper line without a better score; without mate scores the
// deeper completed iteration wins, then the higher score.
void test_best_thread_ranking() {
    auto info = [](int depth, int score) {
        SearchInfo result;
        result.depth = depth;
        result.score = score;
        return result;
    };
    const int mate9 = MateValue - 9;     // we mate in 5 moves
    const int mate5 = MateValue - 5;     // we mate in 3 moves
    const int mated9 = -MateValue + 9;   // we are mated in 5 moves
    const int mated20 = -MateValue + 20; // we are mated in 10 moves
    struct Case {
        SearchInfo candidate, best;
        bool expected;
        const char* name;
    };
    const Case cases[] = {
        {info(12, 10), info(11, 50), true, "deeper iteration wins without mate scores"},
        {info(11, 60), info(11, 50), true, "equal depth: higher score wins"},
        {info(11, 40), info(11, 50), false, "equal depth: lower score loses"},
        {info(10, 900), info(11, 50), false, "shallower non-mate does not replace"},
        {info(15, 300), info(11, mate9), false, "a deeper line without a mate never replaces a found mate"},
        {info(20, 31000), info(11, mate9), false, "a deeper large non-mate score never replaces a found mate"},
        {info(15, mate9 - 2), info(11, mate9), false, "a deeper but longer mate does not replace a shorter one"},
        {info(9, mate5), info(11, mate9), true, "a shorter mate replaces a longer one at any depth"},
        {info(9, mate9), info(14, 250), true, "a found mate replaces a deeper line without one"},
        {info(13, -200), info(11, mated9), true, "a line that is not mated replaces a mated one"},
        {info(16, mated9), info(11, -500), false, "a deeper mated line never replaces one that is not mated"},
        {info(10, mated20), info(12, mated9), true, "of two mated lines the longer resistance wins"},
        {info(14, mated9), info(12, mated20), false, "a deeper but shorter mated line does not replace a longer one"},
    };
    for (const Case& c : cases) {
        check(better_thread_result(c.candidate, c.best) == c.expected, std::string("SmpBestThread ranking: ") + c.name);
    }
}

void test_inert_single_thread() {
    for (const std::string& fen : Fens) {
        SearchInfo results[2];
        for (const bool on : {false, true}) {
            options::smp_exact_nodes = options::smp_best_thread = on;
            Searcher searcher(16, 1);
            SearchLimits limits;
            limits.depth = 10;
            results[on ? 1 : 0] = searcher.search(position(fen), limits);
        }
        check(results[0].nodes == results[1].nodes && results[0].best_move == results[1].best_move &&
                  results[0].score == results[1].score && results[0].pv == results[1].pv,
              "options are inert at Threads=1 " + fen);
    }
    options::smp_exact_nodes = options::smp_best_thread = false;
}

} // namespace

int main() {
    test_worker_list_lifetime();
    test_exact_nodes();
    test_best_thread_ranking();
    test_best_thread();
    test_inert_single_thread();
    std::cout << "smp housekeeping: checks=" << checks << " failures=" << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " smp_tests\n";
    return failures == 0 ? 0 : 1;
}
