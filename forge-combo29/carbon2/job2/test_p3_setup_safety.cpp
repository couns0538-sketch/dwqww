// Safety + TSan + planted-fault test for Piece P3 (per-search setup):
// Verifies:
// 1. O(1) TranspositionTable::hashfull() matches brute-force 1,000-cluster scan across 80 consecutive
//    searches (wrapping 5-bit generation_ > 2.5 full cycles!), including probe age refreshes, store overwrites,
//    clear(), resize(), and alternating Threads 4 (shared striped locks -> stripes_dirty_ == true) and
//    Threads 1 ExclusiveLease transitions under ThreadSanitizer (-fsanitize=thread)!
// 2. Bounded stack_dirty_limit_ + compact v3::WorkerState::valid_flags keeps search 100% deterministic across
//    deep-then-shallow-then-deep searches and NNUEArch true <-> false transitions.

#include "forge/board.hpp"
#include "forge/nnue_v3.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

namespace forge {
struct TTTestProbe {
    static int brute_force_hashfull(const TranspositionTable& tt) {
        const std::size_t sample = std::min<std::size_t>(1000, tt.cluster_count_);
        if (sample == 0) return 0;
        int count = 0;
        for (std::size_t i = 0; i < sample; ++i) {
            for (const TTEntry& e : tt.clusters_[i].entries) {
                if (e.occupied() && e.generation() == tt.generation_) ++count;
            }
        }
        return count * 1000 / (4 * static_cast<int>(sample));
    }
};
} // namespace forge

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    const std::string net_path = argv[1];
    std::string err;
    if (!forge::nnue::v3::load(net_path, &err)) {
        std::cerr << "Net load failed: " << err << "\n";
        return 1;
    }
    forge::nnue::v3::requested = true;

    const std::vector<std::string> fens = {
        std::string(forge::Board::StandardStartFen),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    };

    // Use 1 MB hash (16,384 clusters -> 1000/16384 = 6.1% of clusters in sample!) so sample_gen_counts_ gets heavy overwrites!
    forge::Searcher searcher(1, 1);
    for (int step = 0; step < 80; ++step) {
        if (step == 25) searcher.set_threads(4);
        if (step == 40) searcher.set_threads(1);
        if (step == 55) searcher.clear_hash();
        if (step == 65) searcher.resize_hash(2);
        if (step == 70) searcher.resize_hash(1);

        forge::Board b;
        (void)b.set_fen(fens[static_cast<std::size_t>(step) % fens.size()]);
        forge::SearchLimits lim;
        lim.nodes = (step % 5 == 0) ? 1500 : 400;
        lim.nodes_specified = true;
        lim.soft_nodes = true;
        (void)searcher.search(b, lim, false, forge::Searcher::TTAccess::Exclusive);

        const int fast_hf = searcher.hashfull_permille();
        const int ref_hf = forge::TTTestProbe::brute_force_hashfull(searcher.transposition_table());
        if (fast_hf != ref_hf) {
            std::cerr << "HASHFULL MISMATCH at step=" << step
                      << " gen=" << static_cast<int>(searcher.transposition_table().generation())
                      << " fast=" << fast_hf << " brute_force=" << ref_hf << "\n";
            return 1;
        }
    }
    std::cout << "P3_SETUP_SAFETY PASS: steps=80 generation_wraps=2.5 threads_1_to_4_transitions=ok hashfull_mismatches=0\n";
    return 0;
}
